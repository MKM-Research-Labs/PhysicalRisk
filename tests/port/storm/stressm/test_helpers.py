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

"""Tests for _extract_gauges, _parse_gauge, _build_summary, and storm response fields."""

import json
import pytest

from port.src.stressm.gauge_parser import _extract_gauges, _parse_gauge
from port.src.stressm.gaugets_writer import build_summary as _build_summary
from port.src.storm_multi.generators.batch_generator import generate_event_set

from .conftest import _G1, _G2


# ---------------------------------------------------------------------------
# _extract_gauges
# ---------------------------------------------------------------------------

class TestExtractGauges:

    def test_list_format(self):
        d = {"flood_gauges": [_G1, _G2]}
        result = _extract_gauges(d)
        assert result == [_G1, _G2]

    def test_dict_format(self):
        d = {"flood_gauges": {"g1": _G1, "g2": _G2}}
        result = _extract_gauges(d)
        assert len(result) == 2

    def test_empty_list(self):
        assert _extract_gauges({"flood_gauges": []}) == []

    def test_missing_key_returns_empty(self):
        assert _extract_gauges({}) == []


# ---------------------------------------------------------------------------
# _parse_gauge
# ---------------------------------------------------------------------------

class TestParseGauge:

    def test_valid_record_returns_dict(self):
        result = _parse_gauge(_G1)
        assert result is not None

    def test_gauge_id(self):
        assert _parse_gauge(_G1)["gauge_id"] == "GAUGE-test001"

    def test_lat_lon(self):
        r = _parse_gauge(_G1)
        assert r["lat"] == pytest.approx(51.46)
        assert r["lon"] == pytest.approx(-0.30)

    def test_flood_alert(self):
        assert _parse_gauge(_G1)["flood_alert"] == pytest.approx(3.5)

    def test_flood_warning(self):
        assert _parse_gauge(_G1)["flood_warning"] == pytest.approx(4.6)

    def test_severe_warning(self):
        assert _parse_gauge(_G1)["severe_warning"] == pytest.approx(5.5)

    def test_base_level_derived_from_alert(self):
        r = _parse_gauge(_G1)
        assert r["base_level"] == pytest.approx(3.5 * 0.35)

    def test_missing_gauge_id_returns_none(self):
        bad = {"FloodGauge": {
            "Header": {},
            "Location": {"GaugeLatitude": 51.5, "GaugeLongitude": -0.1},
            "FloodStages": {"FloodAlert": 3.0, "FloodWarning": 4.0, "SevereFloodWarning": 5.0},
        }}
        assert _parse_gauge(bad) is None

    def test_missing_lat_returns_none(self):
        bad = {"FloodGauge": {
            "Header": {"GaugeID": "GAUGE-x"},
            "Location": {},
            "FloodStages": {"FloodAlert": 3.0, "FloodWarning": 4.0, "SevereFloodWarning": 5.0},
        }}
        assert _parse_gauge(bad) is None

    def test_missing_alert_returns_none(self):
        bad = {"FloodGauge": {
            "Header": {"GaugeID": "GAUGE-x"},
            "Location": {"GaugeLatitude": 51.5, "GaugeLongitude": -0.1},
            "FloodStages": {},
        }}
        assert _parse_gauge(bad) is None

    def test_warning_defaults_when_absent(self):
        rec = {"FloodGauge": {
            "Header": {"GaugeID": "GAUGE-x"},
            "Location": {"GaugeLatitude": 51.5, "GaugeLongitude": -0.1},
            "FloodStages": {"FloodAlert": 4.0},
        }}
        r = _parse_gauge(rec)
        assert r is not None
        assert r["flood_warning"] == pytest.approx(4.0 * 1.33)
        assert r["severe_warning"] == pytest.approx(4.0 * 1.58)


# ---------------------------------------------------------------------------
# _build_summary
# ---------------------------------------------------------------------------

class TestBuildSummary:

    def test_returns_required_keys(self):
        seqs = generate_event_set(count=5, seed=0)
        tc = {"isolated": 5}
        s = _build_summary(seqs, tc, gauge_params_list=[{"id": "x"}])
        for key in ("num_sequences", "num_gauges", "type_counts",
                    "alert_sequences", "warning_sequences", "severe_sequences",
                    "elapsed_seconds"):
            assert key in s

    def test_num_sequences(self):
        seqs = generate_event_set(count=7, seed=0)
        s = _build_summary(seqs, {}, gauge_params_list=[])
        assert s["num_sequences"] == 7

    def test_num_gauges(self):
        seqs = generate_event_set(count=3, seed=0)
        s = _build_summary(seqs, {}, gauge_params_list=[1, 2, 3, 4])
        assert s["num_gauges"] == 4

    def test_counts_default_to_zero(self):
        seqs = generate_event_set(count=3, seed=0)
        s = _build_summary(seqs, {}, gauge_params_list=[])
        assert s["alert_sequences"] == 0
        assert s["warning_sequences"] == 0
        assert s["severe_sequences"] == 0


# ---------------------------------------------------------------------------
# Storm response fields (base_level_m / level_change_m)
# ---------------------------------------------------------------------------

class TestStormResponseFields:
    """Verify populate_gaugets writes base_level_m and level_change_m."""

    def _build_responses(self):
        """Build storm responses using the same logic as gaugets_writer."""
        gauge_ids = ["GAUGE-A", "GAUGE-B"]
        gauge_params_list = [
            {"gauge_id": "GAUGE-A", "base_level": 1.5},
            {"gauge_id": "GAUGE-B", "base_level": 2.0},
        ]
        sequence_records = [
            {
                "sequence_id": "STORM-001",
                "peaks_m": [5.0, 7.0],
                "alert": [True, True],
                "warning": [True, True],
                "severe": [False, True],
            },
        ]
        gid_to_idx = {gid: i for i, gid in enumerate(gauge_ids)}
        responses = {gid: [] for gid in gauge_ids}
        for rec in sequence_records:
            for gid, idx in gid_to_idx.items():
                base = gauge_params_list[idx].get("base_level", 0.0)
                peak = rec["peaks_m"][idx]
                responses[gid].append({
                    "storm_id": rec["sequence_id"],
                    "base_level_m": base,
                    "peak_level_m": peak,
                    "level_change_m": round(peak - base, 4),
                    "exceeded_alert": rec["alert"][idx],
                    "exceeded_warning": rec["warning"][idx],
                    "exceeded_severe": rec["severe"][idx],
                })
        return responses, gauge_params_list

    def test_response_has_base_level_m(self):
        responses, _ = self._build_responses()
        for gid, resps in responses.items():
            for r in resps:
                assert "base_level_m" in r, f"Missing base_level_m in {gid}"

    def test_response_has_level_change_m(self):
        responses, _ = self._build_responses()
        for gid, resps in responses.items():
            for r in resps:
                assert "level_change_m" in r, f"Missing level_change_m in {gid}"

    def test_base_level_matches_gauge_params(self):
        responses, params = self._build_responses()
        assert responses["GAUGE-A"][0]["base_level_m"] == pytest.approx(1.5)
        assert responses["GAUGE-B"][0]["base_level_m"] == pytest.approx(2.0)

    def test_level_change_is_peak_minus_base(self):
        responses, _ = self._build_responses()
        for gid, resps in responses.items():
            for r in resps:
                expected = round(r["peak_level_m"] - r["base_level_m"], 4)
                assert r["level_change_m"] == pytest.approx(expected)

    def test_gauge_a_values(self):
        responses, _ = self._build_responses()
        r = responses["GAUGE-A"][0]
        assert r["base_level_m"] == pytest.approx(1.5)
        assert r["peak_level_m"] == pytest.approx(5.0)
        assert r["level_change_m"] == pytest.approx(3.5)

    def test_gauge_b_values(self):
        responses, _ = self._build_responses()
        r = responses["GAUGE-B"][0]
        assert r["base_level_m"] == pytest.approx(2.0)
        assert r["peak_level_m"] == pytest.approx(7.0)
        assert r["level_change_m"] == pytest.approx(5.0)
