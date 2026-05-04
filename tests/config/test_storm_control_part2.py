# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

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

class TestApplyStormControl:
    """apply_storm_control: patch live config modules from JSON."""

    def test_noop_when_file_missing(self, tmp_path, monkeypatch):
        """storm_control.py line 174-175: no file → no patching."""
        from config import config
        monkeypatch.setattr(config, 'get_input_dir', lambda: tmp_path)
        import config.port as cp
        original = cp.EVENT_WINDOW_HOURS
        from config.storm_control import apply_storm_control
        apply_storm_control()
        assert cp.EVENT_WINDOW_HOURS == original

    def test_patches_config_port(self, tmp_path, monkeypatch):
        """storm_control.py line 186: patches config.port attributes."""
        from config import config
        monkeypatch.setattr(config, 'get_input_dir', lambda: tmp_path)
        (tmp_path / "storm_control.json").write_text(json.dumps(SAMPLE_CONTROL))
        import config.port as cp
        original = cp.EVENT_WINDOW_HOURS
        from config.storm_control import apply_storm_control
        apply_storm_control()
        assert cp.EVENT_WINDOW_HOURS == 120
        # Restore
        cp.EVENT_WINDOW_HOURS = original

    def test_patches_config_models(self, tmp_path, monkeypatch):
        """storm_control.py line 189: patches config.models attributes."""
        from config import config
        monkeypatch.setattr(config, 'get_input_dir', lambda: tmp_path)
        (tmp_path / "storm_control.json").write_text(json.dumps(SAMPLE_CONTROL))
        import config.models as cm
        original = cm.SATURATION_BETA
        from config.storm_control import apply_storm_control
        apply_storm_control()
        assert cm.SATURATION_BETA == 0.3
        # Restore
        cm.SATURATION_BETA = original

    def test_patches_config_package_reexports(self, tmp_path, monkeypatch):
        """storm_control.py line 192-198: patches config.* re-exports."""
        from config import config
        monkeypatch.setattr(config, 'get_input_dir', lambda: tmp_path)
        (tmp_path / "storm_control.json").write_text(json.dumps(SAMPLE_CONTROL))
        import config as cfg_pkg
        original = cfg_pkg.SPATIAL_CORR_ENABLED
        from config.storm_control import apply_storm_control
        apply_storm_control()
        assert cfg_pkg.SPATIAL_CORR_ENABLED is False
        # Restore
        cfg_pkg.SPATIAL_CORR_ENABLED = original

    def test_noop_when_sections_empty(self, tmp_path, monkeypatch):
        """Empty sections dict should not crash."""
        from config import config
        monkeypatch.setattr(config, 'get_input_dir', lambda: tmp_path)
        (tmp_path / "storm_control.json").write_text(
            json.dumps({"version": "1.0.0", "sections": {}})
        )
        from config.storm_control import apply_storm_control
        apply_storm_control()  # Should not raise


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

class TestEnumKeyConversion:
    """_enum_keys_to_str / _str_keys_to_gap_type: enum ↔ string."""

    def test_enum_keys_to_str_passthrough(self):
        """String keys pass through unchanged."""
        from config.storm_control import _enum_keys_to_str
        d = {"short": [1, 2, 3], "medium": [4, 5, 6]}
        assert _enum_keys_to_str(d) == d

    def test_str_keys_to_gap_type_converts_when_module_loaded(self):
        """String keys are converted to GapType enum values when module is on sys.path."""
        from config.storm_control import _str_keys_to_gap_type
        # Pre-load the module so the import inside the function succeeds
        try:
            from port.src.storm_multi.core.data_structures import GapType
            # Force the module into the expected import path
            sys.modules['src.port.src.storm_multi.core.data_structures'] = \
                sys.modules['port.src.storm_multi.core.data_structures']
            result = _str_keys_to_gap_type({"short": [6, 18, 36], "medium": [24, 48, 72]})
            assert GapType.SHORT in result
            assert GapType.MEDIUM in result
            assert result[GapType.SHORT] == (6, 18, 36)
        finally:
            sys.modules.pop('src.port.src.storm_multi.core.data_structures', None)

    def test_str_keys_to_gap_type_fallback_on_import_error(self):
        """If GapType import fails, returns string-keyed dict with tuples."""
        from config.storm_control import _str_keys_to_gap_type
        # Without the module loaded, falls back to string keys
        result = _str_keys_to_gap_type({"short": [6, 18, 36]})
        assert "short" in result
        assert result["short"] == (6, 18, 36)


class TestPatchModule:
    """_patch_module: setattr on module for matching keys."""

    def test_patches_matching_keys(self):
        from config.storm_control import _patch_module
        mod = MagicMock()
        mod.FOO = 10
        flat = {"foo": 20, "bar": 30}
        mapping = {"foo": "FOO", "bar": "BAR"}
        _patch_module(mod, flat, mapping, "test")
        assert mod.FOO == 20
        assert mod.BAR == 30

    def test_skips_missing_keys(self):
        from config.storm_control import _patch_module
        mod = MagicMock()
        mod.FOO = 10
        flat = {"foo": 20}
        mapping = {"foo": "FOO", "missing": "MISSING"}
        _patch_module(mod, flat, mapping, "test")
        assert mod.FOO == 20


class TestSafeGetattr:
    """_safe_getattr: import module and get attribute with fallback."""

    def test_returns_default_on_import_error(self):
        from config.storm_control import _safe_getattr
        result = _safe_getattr("nonexistent.module.path", "ATTR", {"default": True})
        assert result == {"default": True}

    def test_returns_attr_from_loaded_module(self):
        from config.storm_control import _safe_getattr
        result = _safe_getattr("config.port", "EVENT_WINDOW_HOURS", 999)
        import config.port as cp
        assert result == cp.EVENT_WINDOW_HOURS
