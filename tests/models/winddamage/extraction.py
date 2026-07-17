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

"""Tests for models.winddamage.extraction — load_event_peaks."""

import json

import pytest

from models.winddamage.extraction import (
    EventWindts,
    duration_above_threshold,
    load_event_peaks,
)


def _windts_payload(**overrides):
    base = {
        "event_id": "EVT-0001",
        "scenario_family": "moderate",
        "horizon_hours": 168.0,
        "dt_hours": 1.0,
        "property_windts": [
            {"point_id": "PROP-a", "peak_sustained_ms": 32.4},
            {"point_id": "PROP-b", "peak_sustained_ms": 18.1},
        ],
    }
    base.update(overrides)
    return base


class TestLoadEventPeaks:

    def test_round_trip_from_disk(self, tmp_path):
        path = tmp_path / "EVT-0001.json"
        path.write_text(json.dumps(_windts_payload()))

        result = load_event_peaks(path)
        assert isinstance(result, EventWindts)
        assert result.event_id == "EVT-0001"
        assert result.scenario_family == "moderate"
        assert result.horizon_hours == 168.0
        assert result.dt_hours == 1.0
        assert result.peaks_by_property == {"PROP-a": 32.4, "PROP-b": 18.1}

    def test_accepts_string_path(self, tmp_path):
        path = tmp_path / "EVT-0001.json"
        path.write_text(json.dumps(_windts_payload()))
        result = load_event_peaks(str(path))
        assert result.peaks_by_property == {"PROP-a": 32.4, "PROP-b": 18.1}

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_event_peaks(tmp_path / "does-not-exist.json")

    def test_skips_entries_with_missing_id(self, tmp_path):
        payload = _windts_payload(property_windts=[
            {"point_id": "PROP-a", "peak_sustained_ms": 32.4},
            {"peak_sustained_ms": 12.0},   # no point_id
        ])
        path = tmp_path / "EVT.json"
        path.write_text(json.dumps(payload))
        result = load_event_peaks(path)
        assert result.peaks_by_property == {"PROP-a": 32.4}

    def test_skips_entries_with_missing_peak(self, tmp_path):
        payload = _windts_payload(property_windts=[
            {"point_id": "PROP-a", "peak_sustained_ms": 32.4},
            {"point_id": "PROP-b"},   # no peak
        ])
        path = tmp_path / "EVT.json"
        path.write_text(json.dumps(payload))
        result = load_event_peaks(path)
        assert result.peaks_by_property == {"PROP-a": 32.4}

    def test_empty_property_windts(self, tmp_path):
        path = tmp_path / "EVT.json"
        path.write_text(json.dumps(_windts_payload(property_windts=[])))
        result = load_event_peaks(path)
        assert result.peaks_by_property == {}

    def test_falls_back_to_stem_when_event_id_missing(self, tmp_path):
        payload = _windts_payload()
        payload.pop("event_id")
        path = tmp_path / "EVT-FALLBACK.json"
        path.write_text(json.dumps(payload))
        result = load_event_peaks(path)
        assert result.event_id == "EVT-FALLBACK"

    def test_loads_per_property_series_when_present(self, tmp_path):
        payload = _windts_payload(property_windts=[
            {"point_id": "PROP-a", "peak_sustained_ms": 40.0,
             "time_hours": [0.0, 1.0, 2.0], "sustained_ms": [10.0, 40.0, 20.0]},
            {"point_id": "PROP-b", "peak_sustained_ms": 18.0},   # peak-only
        ])
        path = tmp_path / "EVT.json"
        path.write_text(json.dumps(payload))
        result = load_event_peaks(path)
        assert result.series_by_property["PROP-a"] == ([0.0, 1.0, 2.0], [10.0, 40.0, 20.0])
        assert "PROP-b" not in result.series_by_property   # no series stored

    def test_series_skipped_when_lengths_mismatch(self, tmp_path):
        payload = _windts_payload(property_windts=[
            {"point_id": "PROP-a", "peak_sustained_ms": 40.0,
             "time_hours": [0.0, 1.0], "sustained_ms": [10.0]},   # mismatch
        ])
        path = tmp_path / "EVT.json"
        path.write_text(json.dumps(payload))
        result = load_event_peaks(path)
        assert result.peaks_by_property == {"PROP-a": 40.0}
        assert result.series_by_property == {}

    def test_series_defaults_empty_for_legacy(self, tmp_path):
        path = tmp_path / "EVT.json"
        path.write_text(json.dumps(_windts_payload()))   # no series fields
        result = load_event_peaks(path)
        assert result.series_by_property == {}


class TestDurationAboveThreshold:

    def test_counts_intervals_where_value_exceeds_threshold(self):
        # values 10,40,40,20 at t=0,1,2,3 -> above 30 at i=1,2 -> 2 h.
        t = [0.0, 1.0, 2.0, 3.0]
        v = [10.0, 40.0, 40.0, 20.0]
        assert duration_above_threshold(t, v, 30.0) == pytest.approx(2.0)

    def test_zero_when_never_exceeds(self):
        assert duration_above_threshold([0.0, 1.0, 2.0], [5.0, 6.0, 7.0], 30.0) == 0.0

    def test_empty_or_single_sample_is_zero(self):
        assert duration_above_threshold([], [], 1.0) == 0.0
        assert duration_above_threshold([0.0], [99.0], 1.0) == 0.0
