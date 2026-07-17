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

"""
Unit tests for config/storm_control.py — JSON overlay for storm stress params.

Covers: load, save, get_defaults, apply (patching config modules), edge cases.
"""

import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SAMPLE_CONTROL = {
    "version": "1.0.0",
    "sections": {
        "storm_generation": {
            "event_window_hours": 120,
            "min_drainage_window_hours": 8,
            "intensity_variation": 0.25,
            "first_storm_dominant_prob": 0.35,
            "correlation_prob": 0.65,
            "default_type_weights": [0.50, 0.35, 0.15],
            "sequence_probability": {"minimal": 0.10, "baseline": 0.20},
            "default_intensity_weights": {"moderate": 0.50, "severe": 0.30,
                                          "extreme": 0.15, "catastrophic": 0.05},
            "catchment_base_precip": {"thames": 40.0},
            "duration_params": {"minimal": [3, 7, 14]},
            "gap_params": {"short": [8, 20, 40]},
            "base_intensity_params": {"minimal": [0.4, 0.12]},
            "sequence_type_weights": {"moderate": [0.45, 0.40, 0.15]},
        },
        "hydrograph_synthesis": {
            "hydro_alpha": {"isolated": 0.4},
            "saturation_beta": 0.3,
            "saturation_p0_mm": 60.0,
            "infiltration_rate_per_hour": 0.008,
            "infiltration_ymax_ref_m": 0.12,
            "default_imperv_fraction": 0.5,
            "superposition_cap_factor": 3.0,
            "depth_points": [0, 0.1, 1.0],
            "damage_points": [0, 0.1, 0.5],
        },
        "gauge_propagation": {
            "default_roughness": 0.05,
            "terrain_velocity_scale": {"urban": 1.0, "rural": 0.4},
            "default_retention_length": 8000.0,
            "min_slope": 0.002,
            "default_recession_factor": 1.8,
            "bankfull_offset_m": 0.6,
            "n_nearest_gauges": 4,
        },
        "spatial_correlation": {
            "spatial_corr_enabled": False,
            "spatial_corr_base_range_km": 50.0,
            "spatial_corr_nugget": 0.08,
            "spatial_corr_rho_intensity": 0.50,
            "spatial_corr_sigma_lognormal": 0.45,
        },
        "stress_catalogue": {
            "stress_storms_min_count": 75,
            "stress_storm_default_duration_hours": 120,
            "stress_storm_default_peak_position": 0.4,
        },
    },
}


# ---------------------------------------------------------------------------
# load_storm_control
# ---------------------------------------------------------------------------

class TestLoadStormControl:
    """load_storm_control: read JSON from catchment input dir."""

    def test_returns_empty_dict_when_missing(self, tmp_path, monkeypatch):
        """storm_control.py line 95: missing file returns {}."""
        from config import config
        monkeypatch.setattr(config, 'get_input_dir', lambda: tmp_path)
        from config.storm_control import load_storm_control
        result = load_storm_control()
        assert result == {}

    def test_reads_valid_json(self, tmp_path, monkeypatch):
        """storm_control.py line 97-99: reads and parses JSON."""
        from config import config
        monkeypatch.setattr(config, 'get_input_dir', lambda: tmp_path)
        p = tmp_path / "storm_control.json"
        p.write_text(json.dumps(SAMPLE_CONTROL))
        from config.storm_control import load_storm_control
        result = load_storm_control()
        assert result["version"] == "1.0.0"
        assert result["sections"]["storm_generation"]["event_window_hours"] == 120

    def test_returns_all_sections(self, tmp_path, monkeypatch):
        """All five sections should be present in loaded data."""
        from config import config
        monkeypatch.setattr(config, 'get_input_dir', lambda: tmp_path)
        (tmp_path / "storm_control.json").write_text(json.dumps(SAMPLE_CONTROL))
        from config.storm_control import load_storm_control
        result = load_storm_control()
        assert set(result["sections"].keys()) == {
            "storm_generation", "hydrograph_synthesis", "gauge_propagation",
            "spatial_correlation", "stress_catalogue",
        }


# ---------------------------------------------------------------------------
# save_storm_control
# ---------------------------------------------------------------------------

class TestSaveStormControl:
    """save_storm_control: write JSON to catchment input dir."""

    def test_writes_json_file(self, tmp_path, monkeypatch):
        """storm_control.py line 104-107: writes formatted JSON."""
        from config import config
        monkeypatch.setattr(config, 'get_input_dir', lambda: tmp_path)
        from config.storm_control import save_storm_control
        save_storm_control(SAMPLE_CONTROL)
        p = tmp_path / "storm_control.json"
        assert p.exists()
        data = json.loads(p.read_text())
        assert data["version"] == "1.0.0"

    def test_overwrites_existing(self, tmp_path, monkeypatch):
        """Saving overwrites the existing file."""
        from config import config
        monkeypatch.setattr(config, 'get_input_dir', lambda: tmp_path)
        from config.storm_control import save_storm_control
        save_storm_control({"version": "0.9.0", "sections": {}})
        save_storm_control(SAMPLE_CONTROL)
        data = json.loads((tmp_path / "storm_control.json").read_text())
        assert data["version"] == "1.0.0"

    def test_round_trip(self, tmp_path, monkeypatch):
        """Save then load returns identical data."""
        from config import config
        monkeypatch.setattr(config, 'get_input_dir', lambda: tmp_path)
        from config.storm_control import save_storm_control, load_storm_control
        save_storm_control(SAMPLE_CONTROL)
        loaded = load_storm_control()
        assert loaded == SAMPLE_CONTROL


# ---------------------------------------------------------------------------
# get_defaults
# ---------------------------------------------------------------------------

class TestGetDefaults:
    """get_defaults: build JSON from live Python config values."""

    def test_returns_version(self):
        from config.storm_control import get_defaults
        d = get_defaults()
        assert "version" in d
        assert d["version"] == "1.0.0"

    def test_has_all_sections(self):
        from config.storm_control import get_defaults
        d = get_defaults()
        assert set(d["sections"].keys()) == {
            "storm_generation", "hydrograph_synthesis", "gauge_propagation",
            "spatial_correlation", "stress_catalogue",
        }

    def test_storm_generation_matches_config_port(self):
        """Default values should match config.port constants."""
        from config.storm_control import get_defaults
        import config.port as cp
        d = get_defaults()
        sg = d["sections"]["storm_generation"]
        assert sg["event_window_hours"] == cp.EVENT_WINDOW_HOURS
        assert sg["min_drainage_window_hours"] == cp.MIN_DRAINAGE_WINDOW_HOURS
        assert sg["intensity_variation"] == cp.INTENSITY_VARIATION
        assert sg["first_storm_dominant_prob"] == cp.FIRST_STORM_DOMINANT_PROB
        assert sg["correlation_prob"] == cp.CORRELATION_PROB

    def test_hydrograph_matches_config_models(self):
        """Default values should match config.models constants."""
        from config.storm_control import get_defaults
        import config.models as cm
        d = get_defaults()
        hs = d["sections"]["hydrograph_synthesis"]
        assert hs["saturation_beta"] == cm.SATURATION_BETA
        assert hs["infiltration_rate_per_hour"] == cm.INFILTRATION_RATE_PER_HOUR
        assert hs["superposition_cap_factor"] == cm.SUPERPOSITION_CAP_FACTOR

    def test_gauge_propagation_matches_configs(self):
        """Gauge propagation pulls from both config.port and config.models."""
        from config.storm_control import get_defaults
        import config.port as cp
        import config.models as cm
        d = get_defaults()
        gp = d["sections"]["gauge_propagation"]
        assert gp["default_roughness"] == cm.DEFAULT_ROUGHNESS
        assert gp["bankfull_offset_m"] == cp.BANKFULL_OFFSET_M
        assert gp["n_nearest_gauges"] == cp.N_NEAREST_GAUGES

    def test_spatial_correlation_matches_config_port(self):
        from config.storm_control import get_defaults
        import config.port as cp
        d = get_defaults()
        sc = d["sections"]["spatial_correlation"]
        assert sc["spatial_corr_enabled"] == cp.SPATIAL_CORR_ENABLED
        assert sc["spatial_corr_base_range_km"] == cp.SPATIAL_CORR_BASE_RANGE_KM

    def test_stress_catalogue_matches_config_port(self):
        from config.storm_control import get_defaults
        import config.port as cp
        d = get_defaults()
        st = d["sections"]["stress_catalogue"]
        assert st["stress_storms_min_count"] == cp.STRESS_STORMS_MIN_COUNT

    def test_json_serializable(self):
        """Defaults must be JSON-serializable (no tuples, enums)."""
        from config.storm_control import get_defaults
        d = get_defaults()
        serialized = json.dumps(d)
        assert isinstance(serialized, str)
        round_tripped = json.loads(serialized)
        assert round_tripped == d


# ---------------------------------------------------------------------------
# apply_storm_control
# ---------------------------------------------------------------------------

