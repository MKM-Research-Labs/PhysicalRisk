# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Tests for models.winddamage.extraction — load_event_peaks."""

import json

import pytest

from models.winddamage.extraction import EventWindts, load_event_peaks


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
