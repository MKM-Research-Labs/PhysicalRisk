# Copyright (c) 2022-2026 MKM Research Labs.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Gauge calibration to observed river levels (MKM-SG-001 / GHD-001 / GH-001 v2.0).

Covers: the shipped Thames file, entry lookup and the provisional default, the
fixed normal level, writing flood levels into gauge.json (idempotent), the history
generator's normal level and shrunken swings, and the storm-gauge sensitivity.
"""

import statistics

import pytest

from port.src.gauge import calibration as cal

CAL = {
    "gauges": {"River A Lock": {"sensitivity": 0.25, "rise_exponent": 0.6,
                                "historical_high_date": "2014-02-10",
                                "rise_m": {"alert": 0.4, "warning": 0.8, "severe": 1.2,
                                           "historical_high": 1.0}}},
    "default": {"provisional": True, "sensitivity": 0.3,
                "rise_m": {"alert": 0.5, "warning": 0.9, "severe": 1.3, "historical_high": 1.1}},
}


def _gauge(name, alert=4.0):
    return {"FloodGauge": {
        "Header": {"GaugeName": name, "GaugeID": f"G-{name[:3]}"},
        "FloodStages": {"FloodAlert": alert, "FloodWarning": 5.0, "SevereFloodWarning": 6.0,
                        "HistoricalHighLevel": 7.0},
        "FloodStage": {"UK": {"FloodAlert": alert, "SevereFloodWarning": 6.0}},
        "SensorStats": {"HistoricalHighLevel": 7.0}}}


class TestShippedThamesFile:

    def test_thames_calibration_loads(self):
        doc = cal.load_gauge_calibration("thames")
        assert len(doc["gauges"]) == 12
        assert doc["default"]["provisional"] is True
        assert set(doc["model_versions"].values()) == {"2.0.0"}

    def test_every_gauge_has_ordered_rises_and_a_rating_curve(self):
        for name, e in cal.load_gauge_calibration("thames")["gauges"].items():
            r = e["rise_m"]
            assert 0 < r["alert"] < r["warning"] < r["severe"], name
            assert 0 < e["sensitivity"] < 1, name
            assert 0.2 < e["rise_exponent"] < 1, name      # stage rises slower than flow
            assert e["record_years"] >= 20, name

    def test_uncalibrated_catchment_has_no_file(self):
        assert cal.load_gauge_calibration("halong") is None
        assert cal.load_gauge_calibration(None) is None


class TestLookup:

    def test_own_entry_then_default_then_none(self):
        assert cal.entry_for(CAL, "River A Lock")["sensitivity"] == 0.25
        assert cal.entry_for(CAL, "Tidal Pier")["provisional"] is True
        assert cal.entry_for(None, "River A Lock") is None

    def test_normal_level_is_fixed_per_name_and_in_range(self):
        a = cal.normal_level("River A Lock")
        assert a == cal.normal_level("River A Lock")
        assert cal.NORMAL_LEVEL_MIN <= a < cal.NORMAL_LEVEL_MIN + cal.NORMAL_LEVEL_SPAN


class TestApply:

    def test_levels_are_normal_level_plus_observed_rise(self):
        doc = {"flood_gauges": [_gauge("River A Lock"), _gauge("Tidal Pier")]}
        assert cal.apply_gauge_calibration(doc, CAL) == 2
        fg = doc["flood_gauges"][0]["FloodGauge"]
        base = cal.normal_level("River A Lock")
        assert fg["FloodStages"]["FloodAlert"] == pytest.approx(base + 0.4)
        assert fg["FloodStages"]["SevereFloodWarning"] == pytest.approx(base + 1.2)
        assert fg["SensorStats"]["HistoricalHighLevel"] == pytest.approx(base + 1.0)
        assert fg["SensorStats"]["HistoricalHighDate"] == "2014-02-10"
        assert fg["FloodStage"]["UK"]["FloodAlert"] == pytest.approx(base + 0.4)
        tidal = doc["flood_gauges"][1]["FloodGauge"]["FloodStages"]
        assert tidal["FloodWarning"] == pytest.approx(cal.normal_level("Tidal Pier") + 0.9)

    def test_reapplying_changes_nothing(self):
        doc = {"flood_gauges": [_gauge("River A Lock")]}
        cal.apply_gauge_calibration(doc, CAL)
        once = repr(doc)
        cal.apply_gauge_calibration(doc, CAL)
        assert repr(doc) == once

    def test_no_calibration_leaves_the_document_alone(self):
        doc = {"flood_gauges": [_gauge("River A Lock")]}
        before = repr(doc)
        assert cal.apply_gauge_calibration(doc, None) == 0
        assert repr(doc) == before


class TestReaders:

    @pytest.fixture(autouse=True)
    def _calibrated(self, monkeypatch):
        monkeypatch.setattr(cal, "load_gauge_calibration",
                            lambda c: CAL if c == "testcatch" else None)

    def test_history_normal_level_is_alert_minus_alert_rise(self):
        p = cal.history_params("testcatch", _gauge("River A Lock", alert=2.4))
        assert p == {"base_level": 2.0, "variability_scale": 0.25}
        assert cal.history_params("other", _gauge("River A Lock")) is None

    def test_sensitivity_defaults_to_one_when_uncalibrated(self):
        assert cal.sensitivity_for("testcatch", "River A Lock") == 0.25
        assert cal.sensitivity_for("testcatch", "Tidal Pier") == 0.3
        assert cal.sensitivity_for("other", "River A Lock") == 1.0

    def test_gauge_parser_carries_the_rating_curve(self):
        from port.src.stressm.gauge_parser import _parse_gauge
        g = _gauge("River A Lock")
        g["FloodGauge"]["Header"]["CatchmentID"] = "testcatch"
        g["FloodGauge"]["Location"] = {"GaugeLatitude": 51.5, "GaugeLongitude": -0.9}
        assert (_parse_gauge(g)["sensitivity"], _parse_gauge(g)["rise_exponent"]) == (0.25, 0.6)
        g["FloodGauge"]["Header"]["CatchmentID"] = "other"
        assert (_parse_gauge(g)["sensitivity"], _parse_gauge(g)["rise_exponent"]) == (1.0, 1.0)


class TestRatingCurveRouting:

    def _rise(self, storm_size=1.0, **kw):
        import numpy as np

        from port.src.storm_multi.models.sequence_response import SequenceGaugeParams, _route_quickflow_to_level
        p = SequenceGaugeParams("G", base_level=1.0, flood_alert=2, flood_warning=3,
                                severe_warning=4, **kw)
        q = np.zeros(48)
        q[2:6] = np.array([1.0, 4.0, 4.0, 1.0]) * storm_size
        return _route_quickflow_to_level(q, p) - 1.0

    def test_linear_by_default_and_scaled_by_sensitivity(self):
        assert self._rise(sensitivity=0.5) == pytest.approx(0.5 * self._rise())

    def test_a_bigger_storm_raises_the_river_less_than_proportionally(self):
        # 16x the runoff: 16x the rise when linear, 16 ** 0.5 = 4x on the curve.
        lin = self._rise(16).max() / self._rise(1).max()
        curved = (self._rise(16, rise_exponent=0.5).max()
                  / self._rise(1, rise_exponent=0.5).max())
        assert lin == pytest.approx(16)
        assert curved == pytest.approx(4)
        assert (self._rise(16, rise_exponent=0.5) >= 0).all()


class TestCalibratedHistory:

    def test_history_sits_on_the_given_level_with_smaller_swings(self):
        from models.statistics.synthetic import generate_synthetic_timeseries
        # Flood levels as calibration writes them: normal level 2.0 + observed rises.
        g = _gauge("River A Lock", alert=2.4)
        g["FloodGauge"]["FloodStages"].update(FloodWarning=2.8, SevereFloodWarning=3.2)
        g["FloodGauge"]["SensorStats"] = {}
        raw = [o["level_meters"] for o in generate_synthetic_timeseries(g, years=5, seed=7)]
        tuned = [o["level_meters"] for o in generate_synthetic_timeseries(
            g, years=5, seed=7, calibration={"base_level": 2.0, "variability_scale": 0.25})]
        assert statistics.median(tuned) == pytest.approx(2.0, abs=0.15)
        assert statistics.pstdev(tuned) < statistics.pstdev(raw) / 2
