# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Shared fixtures and helpers for port.src.gauge tests."""

import json
from pathlib import Path


def make_gauge_file(gauge_id: str, responses: list) -> dict:
    """Build a minimal GAUGE-*.json structure."""
    return {
        "gauge_id": gauge_id,
        "flood_simulation": {"simulation_hours": 168, "readings": []},
        "storm_responses": {
            "responses": responses,
        },
    }


def make_response(storm_id: str, *, alert=False, warning=False, severe=False,
                  base=1.0, peak=1.5) -> dict:
    return {
        "storm_id": storm_id,
        "base_level_m": base,
        "peak_level_m": peak,
        "level_change_m": round(peak - base, 3),
        "exceeded_alert": alert,
        "exceeded_warning": warning,
        "exceeded_severe": severe,
    }


def write_nrfa_csv(path: Path, station_id: str = "39001",
                   station_name: str = "Thames at Kingston",
                   n_rows: int = 5) -> Path:
    """Write a minimal NRFA GDF CSV file."""
    from datetime import date, timedelta
    lines = [
        "file,timestamp,2024-01-01T00:00",
        "database,id,7",
        "database,name,NRFA",
        f"station,id,{station_id}",
        f"station,name,{station_name}",
        "station,gridReference,TQ170699",
        "dataType,id,33",
        "dataType,name,gauged daily flow",
        "dataType,parameter,flow",
        "dataType,units,m3/s",
        "dataType,period,day",
        "dataType,measurementType,mean",
        "data,first,1970-01-01",
        "data,last,2024-01-01",
    ]
    start = date(2020, 1, 1)
    for i in range(n_rows):
        d = start + timedelta(days=i)
        lines.append(f"{d.isoformat()},{10.0 + i * 0.5}")

    p = path / f"{station_id}_gdf.csv"
    p.write_text("\n".join(lines))
    return p


import pytest


def setup_gauge_env(tmp_path, monkeypatch, gauge_entries=None):
    """Set up gauge.json and gaugehd dir, returns (gauge_file, gaugehd_dir)."""
    from config import config
    if gauge_entries is None:
        gauge_entries = [SAMPLE_GAUGE_ENTRY]
    gauge_data = {"flood_gauges": gauge_entries}
    gauge_file = tmp_path / "gauge.json"
    gauge_file.write_text(json.dumps(gauge_data))
    gaugehd_dir = tmp_path / "gaugehd"
    gaugehd_dir.mkdir()
    monkeypatch.setattr(config, "get_input_path", lambda f: gauge_file)
    monkeypatch.setattr(config, "get_gaugehd_dir", lambda: gaugehd_dir)
    return gauge_file, gaugehd_dir


SAMPLE_GAUGE_ENTRY = {
    "FloodGauge": {
        "Header": {
            "GaugeID": "GAUGE-TEST01",
            "GaugeName": "Test Gauge",
            "CatchmentID": "thames",
        },
        "FloodStages": {
            "FloodAlert": 3.0,
            "FloodWarning": 4.5,
            "SevereFloodWarning": 5.5,
        },
        "Location": {
            "GaugeLatitude": 51.5,
            "GaugeLongitude": -0.1,
            "GaugeElevation": 5.0,
        },
        "SensorStats": {
            "HistoricalHighLevel": 7.2,
        },
    }
}
