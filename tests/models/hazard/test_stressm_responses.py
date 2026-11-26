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

"""GH-001 v2.0: the GEV curves are built from the Storm-Gauge Response Model.

Covers: each sequence's per-storm peaks become one response per member storm,
keyed by the member storm's id; exceedance flags follow the gauge's levels; a
gauge the storm-gauge stage never covered sends the whole build back to the v1
simple model; and the builder uses supplied responses instead of its own model.
"""

import pytest

from models.hazard.builder import HazardCurveBuilder
from models.hazard.data_structures import GaugeResponse
from models.hazard.io import _stressm

GAUGES = [{"gauge_id": "G1", "flood_alert": 2.5, "flood_warning": 2.8,
           "severe_flood_warning": 3.1}]
SEQUENCES = {"sequences": [
    {"sequence_id": "SEQ-A", "storms": [{"storm_id": "S-A0"}, {"storm_id": "S-A1"}]},
    {"sequence_id": "SEQ-B", "storms": [{"storm_id": "S-B0"}]},
]}
SG_G1 = {"gauge_id": "G1", "sequences": [
    {"sequence_id": "SEQ-A", "peak_m": 3.2,
     "pulse_peaks": [{"storm_index": 0, "peak_m": 2.6}, {"storm_index": 1, "peak_m": 3.2}]},
    {"sequence_id": "SEQ-B", "peak_m": 2.1, "pulse_peaks": []},
]}


@pytest.fixture
def stressm_store(monkeypatch):
    store = {"G1": SG_G1}
    monkeypatch.setattr("database.get_sequence_gauge", lambda c, gid: store.get(gid))
    monkeypatch.setattr("port.src.stressm.gauge_parser._load_gaugehd_baselines",
                        lambda c: {"G1": {"mean_level": 2.0}})
    return store


def test_each_member_storm_gets_its_own_peak(stressm_store):
    out = _stressm.load_stressm_responses("thames", SEQUENCES, GAUGES)
    rows = {r.storm_id: r for r in out["G1"]}
    assert set(rows) == {"S-A0", "S-A1", "S-B0"}
    assert rows["S-A0"].peak_level_m == 2.6
    assert rows["S-A1"].peak_level_m == 3.2
    assert rows["S-B0"].peak_level_m == 2.1          # no pulses: the sequence peak
    assert rows["S-A1"].level_change_m == pytest.approx(1.2)


def test_exceedance_flags_follow_the_gauge_levels(stressm_store):
    rows = {r.storm_id: r for r in _stressm.load_stressm_responses("thames", SEQUENCES, GAUGES)["G1"]}
    assert (rows["S-A0"].exceeded_alert, rows["S-A0"].exceeded_warning) == (True, False)
    assert rows["S-A1"].exceeded_severe is True
    assert rows["S-B0"].exceeded_alert is False


def test_a_gauge_without_storm_gauge_output_means_no_responses(stressm_store):
    gauges = GAUGES + [{"gauge_id": "G2", "flood_alert": 1, "flood_warning": 2,
                        "severe_flood_warning": 3}]
    assert _stressm.load_stressm_responses("thames", SEQUENCES, gauges) is None


def test_builder_uses_supplied_responses_not_its_own_model(monkeypatch):
    supplied = {"G1": [GaugeResponse("G1", "S-A0", 2.0, 0.6, 2.6, True, False, False)]}
    b = HazardCurveBuilder(gauges=GAUGES, storms=[], verbose=False, responses=supplied)
    called = []
    monkeypatch.setattr(b.response_model, "compute_all_responses",
                        lambda storms: called.append(1) or {})
    assert b.responses is supplied
    assert called == []


def test_calibration_off_switch(monkeypatch):
    from port.src.gauge import calibration
    calibration.load_gauge_calibration.cache_clear()
    monkeypatch.setenv(calibration.OFF_SWITCH, "off")
    try:
        assert calibration.load_gauge_calibration("thames") is None
    finally:
        calibration.load_gauge_calibration.cache_clear()
