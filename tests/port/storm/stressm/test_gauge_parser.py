# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""
Unit tests for gauge_parser.py — gauge JSON parsing and baseline loading.

Covers _load_gaugehd_baselines, _seasonal_base_level, and _parse_gauge
with historical baselines (gaugehd) and monthly seasonality.
"""

import json
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# _load_gaugehd_baselines
# ---------------------------------------------------------------------------

class TestLoadGaugehdBaselines:
    """Load historical water level baselines from gaugehd/ directory."""

    def test_empty_directory(self, tmp_path):
        from port.src.stressm.gauge_parser import _load_gaugehd_baselines
        d = tmp_path / "gaugehd"
        d.mkdir()
        assert _load_gaugehd_baselines(d) == {}

    def test_missing_directory(self, tmp_path):
        from port.src.stressm.gauge_parser import _load_gaugehd_baselines
        assert _load_gaugehd_baselines(tmp_path / "nonexistent") == {}

    def test_valid_gaugehd_files(self, tmp_path):
        from port.src.stressm.gauge_parser import _load_gaugehd_baselines
        d = tmp_path / "gaugehd"
        d.mkdir()
        data = {
            "gauge_metadata": {"gauge_id": "GAUGE-001"},
            "statistics": {
                "mean_level": 1.25,
                "monthly_means": {"01": 1.4, "07": 0.9},
            },
        }
        (d / "gauge_001_hd.json").write_text(json.dumps(data))
        baselines = _load_gaugehd_baselines(d)
        assert "GAUGE-001" in baselines
        assert baselines["GAUGE-001"]["mean_level"] == 1.25
        assert baselines["GAUGE-001"]["monthly_means"]["01"] == 1.4

    def test_multiple_gauges(self, tmp_path):
        from port.src.stressm.gauge_parser import _load_gaugehd_baselines
        d = tmp_path / "gaugehd"
        d.mkdir()
        for i in range(3):
            data = {
                "gauge_metadata": {"gauge_id": f"GAUGE-{i:03d}"},
                "statistics": {"mean_level": 1.0 + i * 0.1},
            }
            (d / f"gauge_{i:03d}_hd.json").write_text(json.dumps(data))
        baselines = _load_gaugehd_baselines(d)
        assert len(baselines) == 3

    def test_corrupt_file_skipped(self, tmp_path):
        from port.src.stressm.gauge_parser import _load_gaugehd_baselines
        d = tmp_path / "gaugehd"
        d.mkdir()
        (d / "gauge_bad_hd.json").write_text("NOT JSON")
        good = {
            "gauge_metadata": {"gauge_id": "GAUGE-OK"},
            "statistics": {"mean_level": 2.0},
        }
        (d / "gauge_ok_hd.json").write_text(json.dumps(good))
        baselines = _load_gaugehd_baselines(d)
        assert len(baselines) == 1
        assert "GAUGE-OK" in baselines

    def test_missing_mean_level_skipped(self, tmp_path):
        from port.src.stressm.gauge_parser import _load_gaugehd_baselines
        d = tmp_path / "gaugehd"
        d.mkdir()
        data = {
            "gauge_metadata": {"gauge_id": "GAUGE-NOLEVEL"},
            "statistics": {},
        }
        (d / "gauge_nolevel_hd.json").write_text(json.dumps(data))
        baselines = _load_gaugehd_baselines(d)
        assert len(baselines) == 0


# ---------------------------------------------------------------------------
# _seasonal_base_level
# ---------------------------------------------------------------------------

class TestSeasonalBaseLevel:
    """Monthly base level selection with fallback to annual mean."""

    def test_with_monthly_means(self):
        from port.src.stressm.gauge_parser import _seasonal_base_level
        monthly = {"01": 1.5, "07": 0.8}
        assert _seasonal_base_level(monthly, mean_level=1.0, month=1) == 1.5
        assert _seasonal_base_level(monthly, mean_level=1.0, month=7) == 0.8

    def test_missing_month_falls_back(self):
        from port.src.stressm.gauge_parser import _seasonal_base_level
        monthly = {"01": 1.5}
        # March not in monthly_means → fall back to mean_level
        assert _seasonal_base_level(monthly, mean_level=1.0, month=3) == 1.0

    def test_no_monthly_means(self):
        from port.src.stressm.gauge_parser import _seasonal_base_level
        assert _seasonal_base_level(None, mean_level=1.0, month=6) == 1.0

    def test_empty_monthly_means(self):
        from port.src.stressm.gauge_parser import _seasonal_base_level
        assert _seasonal_base_level({}, mean_level=1.0, month=6) == 1.0


# ---------------------------------------------------------------------------
# _parse_gauge with baselines
# ---------------------------------------------------------------------------

class TestParseGaugeWithBaselines:
    """_parse_gauge using gaugehd historical baselines and monthly means."""

    def _make_gauge(self, gauge_id="GAUGE-001"):
        return {
            "FloodGauge": {
                "Header": {"GaugeID": gauge_id},
                "Location": {"GaugeLatitude": 51.5, "GaugeLongitude": -0.1},
                "FloodStages": {
                    "FloodAlert": 3.5,
                    "FloodWarning": 4.6,
                    "SevereFloodWarning": 5.5,
                },
            }
        }

    def test_with_baseline(self):
        from port.src.stressm.gauge_parser import _parse_gauge
        baselines = {
            "GAUGE-001": {"mean_level": 1.25, "monthly_means": {"01": 1.4}},
        }
        result = _parse_gauge(self._make_gauge(), baselines)
        assert result["base_level"] == 1.25
        assert result["monthly_means"] == {"01": 1.4}

    def test_without_baseline_uses_heuristic(self):
        from port.src.stressm.gauge_parser import _parse_gauge
        result = _parse_gauge(self._make_gauge(), baselines={})
        assert result["base_level"] == pytest.approx(3.5 * 0.35)
        assert result["monthly_means"] is None

    def test_baseline_without_monthly_means(self):
        from port.src.stressm.gauge_parser import _parse_gauge
        baselines = {"GAUGE-001": {"mean_level": 1.5}}
        result = _parse_gauge(self._make_gauge(), baselines)
        assert result["base_level"] == 1.5
        assert result["monthly_means"] is None
