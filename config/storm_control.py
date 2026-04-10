# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""
Storm Sequence Control — JSON overlay for storm stress parameters.

Loads ``storm_control.json`` from the catchment input directory and patches
the live Python config modules (``config.port``, ``config.models``, and
generator-local constants) so that the rest of the codebase continues to
use ``from config import X`` without any changes.
"""

import importlib
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Mapping: JSON key (snake_case) -> Python module attribute (UPPER_CASE)
# ---------------------------------------------------------------------------

_CONFIG_PORT_KEYS: Dict[str, str] = {
    # Storm generation
    "event_window_hours": "EVENT_WINDOW_HOURS",
    "min_drainage_window_hours": "MIN_DRAINAGE_WINDOW_HOURS",
    "sequence_probability": "SEQUENCE_PROBABILITY",
    "default_type_weights": "DEFAULT_TYPE_WEIGHTS",
    "intensity_variation": "INTENSITY_VARIATION",
    "first_storm_dominant_prob": "FIRST_STORM_DOMINANT_PROB",
    "correlation_prob": "CORRELATION_PROB",
    "default_intensity_weights": "DEFAULT_INTENSITY_WEIGHTS",
    "catchment_base_precip": "CATCHMENT_BASE_PRECIP",
    # Gauge propagation (port.py entries)
    "bankfull_offset_m": "BANKFULL_OFFSET_M",
    "n_nearest_gauges": "N_NEAREST_GAUGES",
    # Spatial correlation
    "spatial_corr_enabled": "SPATIAL_CORR_ENABLED",
    "spatial_corr_base_range_km": "SPATIAL_CORR_BASE_RANGE_KM",
    "spatial_corr_nugget": "SPATIAL_CORR_NUGGET",
    "spatial_corr_rho_intensity": "SPATIAL_CORR_RHO_INTENSITY",
    "spatial_corr_sigma_lognormal": "SPATIAL_CORR_SIGMA_LOGNORMAL",
    # Stress catalogue
    "stress_storms_min_count": "STRESS_STORMS_MIN_COUNT",
    "stress_storm_default_duration_hours": "STRESS_STORM_DEFAULT_DURATION_HOURS",
    "stress_storm_default_peak_position": "STRESS_STORM_DEFAULT_PEAK_POSITION",
}

_CONFIG_MODELS_KEYS: Dict[str, str] = {
    # Hydrograph synthesis
    "hydro_alpha": "HYDRO_ALPHA",
    "saturation_beta": "SATURATION_BETA",
    "saturation_p0_mm": "SATURATION_P0_MM",
    "infiltration_rate_per_hour": "INFILTRATION_RATE_PER_HOUR",
    "infiltration_ymax_ref_m": "INFILTRATION_YMAX_REF_M",
    "default_imperv_fraction": "DEFAULT_IMPERV_FRACTION",
    "superposition_cap_factor": "SUPERPOSITION_CAP_FACTOR",
    "depth_points": "DEPTH_POINTS",
    "damage_points": "DAMAGE_POINTS",
    # Gauge propagation (models.py entries)
    "default_roughness": "DEFAULT_ROUGHNESS",
    "terrain_velocity_scale": "TERRAIN_VELOCITY_SCALE",
    "default_retention_length": "DEFAULT_RETENTION_LENGTH",
    "min_slope": "MIN_SLOPE",
    "default_recession_factor": "DEFAULT_RECESSION_FACTOR",
}

# Generator modules with locally-defined constants
_GENERATOR_PATCHES: Dict[str, Tuple[str, str]] = {
    "duration_params": (
        "src.port.src.storm_multi.generators.duration_sampler",
        "DURATION_PARAMS",
    ),
    "gap_params": (
        "src.port.src.storm_multi.generators.gap_sampler",
        "GAP_PARAMS",
    ),
    "base_intensity_params": (
        "src.port.src.storm_multi.generators.batch_generator",
        "BASE_INTENSITY_PARAMS",
    ),
    "sequence_type_weights": (
        "src.port.src.storm_multi.generators.intensity_sampler",
        "SEQUENCE_TYPE_WEIGHTS",
    ),
}

_CONTROL_FILENAME = "storm_control.json"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def _resolve_path(catchment_id: str = "thames") -> Path:
    """Return path to ``storm_control.json`` for the given catchment."""
    from config import config as _cfg
    return _cfg.get_input_dir() / _CONTROL_FILENAME


def load_storm_control(catchment_id: str = "thames") -> Dict[str, Any]:
    """Read storm_control.json and return parsed dict (empty if missing)."""
    path = _resolve_path(catchment_id)
    if not path.exists():
        return {}
    with open(path) as f:
        return json.load(f)


def save_storm_control(
    data: Dict[str, Any],
    catchment_id: str = "thames",
) -> None:
    """Write *data* to storm_control.json."""
    path = _resolve_path(catchment_id)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    logger.info("storm_control.json saved to %s", path)


def get_defaults() -> Dict[str, Any]:
    """Build default JSON structure from current Python config values."""
    import config.port as cp
    import config.models as cm

    # Read generator-local defaults (may not be importable in all contexts)
    duration_params = _safe_getattr(
        "src.port.src.storm_multi.generators.duration_sampler",
        "DURATION_PARAMS",
        {
            "minimal": [2, 6, 12], "baseline": [6, 12, 24],
            "moderate": [12, 30, 60], "severe": [24, 48, 96],
            "extreme": [36, 72, 144], "catastrophic": [48, 120, 240],
        },
    )
    gap_params = _safe_getattr(
        "src.port.src.storm_multi.generators.gap_sampler",
        "GAP_PARAMS",
        {"short": [6, 18, 36], "medium": [24, 48, 72], "long": [48, 96, 144]},
    )
    base_intensity = _safe_getattr(
        "src.port.src.storm_multi.generators.batch_generator",
        "BASE_INTENSITY_PARAMS",
        {
            "minimal": [0.3, 0.10], "baseline": [0.6, 0.15],
            "moderate": [1.0, 0.20], "severe": [1.8, 0.30],
            "extreme": [3.0, 0.50], "catastrophic": [5.0, 0.80],
        },
    )
    seq_type_weights = _safe_getattr(
        "src.port.src.storm_multi.generators.intensity_sampler",
        "SEQUENCE_TYPE_WEIGHTS",
        {
            "moderate": [0.50, 0.35, 0.15], "severe": [0.30, 0.50, 0.20],
            "extreme": [0.20, 0.45, 0.35], "catastrophic": [0.15, 0.45, 0.40],
        },
    )

    # Normalise enum-keyed dicts to string keys for JSON
    duration_params = _enum_keys_to_str(duration_params)
    gap_params = _enum_keys_to_str(gap_params)
    base_intensity = _enum_keys_to_str(base_intensity)
    seq_type_weights = _enum_keys_to_str(seq_type_weights)

    # Convert tuple values to lists for JSON serialisation
    duration_params = {k: list(v) for k, v in duration_params.items()}
    gap_params = {k: list(v) for k, v in gap_params.items()}
    base_intensity = {k: list(v) for k, v in base_intensity.items()}
    seq_type_weights = {k: list(v) for k, v in seq_type_weights.items()}

    return {
        "version": "1.0.0",
        "sections": {
            "storm_generation": {
                "event_window_hours": cp.EVENT_WINDOW_HOURS,
                "min_drainage_window_hours": cp.MIN_DRAINAGE_WINDOW_HOURS,
                "sequence_probability": dict(cp.SEQUENCE_PROBABILITY),
                "default_type_weights": list(cp.DEFAULT_TYPE_WEIGHTS),
                "intensity_variation": cp.INTENSITY_VARIATION,
                "first_storm_dominant_prob": cp.FIRST_STORM_DOMINANT_PROB,
                "correlation_prob": cp.CORRELATION_PROB,
                "default_intensity_weights": dict(cp.DEFAULT_INTENSITY_WEIGHTS),
                "catchment_base_precip": dict(cp.CATCHMENT_BASE_PRECIP),
                "duration_params": duration_params,
                "gap_params": gap_params,
                "base_intensity_params": base_intensity,
                "sequence_type_weights": seq_type_weights,
            },
            "hydrograph_synthesis": {
                "hydro_alpha": dict(cm.HYDRO_ALPHA),
                "saturation_beta": cm.SATURATION_BETA,
                "saturation_p0_mm": cm.SATURATION_P0_MM,
                "infiltration_rate_per_hour": cm.INFILTRATION_RATE_PER_HOUR,
                "infiltration_ymax_ref_m": cm.INFILTRATION_YMAX_REF_M,
                "default_imperv_fraction": cm.DEFAULT_IMPERV_FRACTION,
                "superposition_cap_factor": cm.SUPERPOSITION_CAP_FACTOR,
                "depth_points": list(cm.DEPTH_POINTS),
                "damage_points": list(cm.DAMAGE_POINTS),
            },
            "gauge_propagation": {
                "default_roughness": cm.DEFAULT_ROUGHNESS,
                "terrain_velocity_scale": dict(cm.TERRAIN_VELOCITY_SCALE),
                "default_retention_length": cm.DEFAULT_RETENTION_LENGTH,
                "min_slope": cm.MIN_SLOPE,
                "default_recession_factor": cm.DEFAULT_RECESSION_FACTOR,
                "bankfull_offset_m": cp.BANKFULL_OFFSET_M,
                "n_nearest_gauges": cp.N_NEAREST_GAUGES,
            },
            "spatial_correlation": {
                "spatial_corr_enabled": cp.SPATIAL_CORR_ENABLED,
                "spatial_corr_base_range_km": cp.SPATIAL_CORR_BASE_RANGE_KM,
                "spatial_corr_nugget": cp.SPATIAL_CORR_NUGGET,
                "spatial_corr_rho_intensity": cp.SPATIAL_CORR_RHO_INTENSITY,
                "spatial_corr_sigma_lognormal": cp.SPATIAL_CORR_SIGMA_LOGNORMAL,
            },
            "stress_catalogue": {
                "stress_storms_min_count": cp.STRESS_STORMS_MIN_COUNT,
                "stress_storm_default_duration_hours": cp.STRESS_STORM_DEFAULT_DURATION_HOURS,
                "stress_storm_default_peak_position": cp.STRESS_STORM_DEFAULT_PEAK_POSITION,
            },
        },
    }


def apply_storm_control(catchment_id: str = "thames") -> None:
    """Load storm_control.json and patch live config modules."""
    data = load_storm_control(catchment_id)
    if not data:
        logger.debug("No storm_control.json found — using Python defaults")
        return

    sections = data.get("sections", {})
    if not sections:
        return

    import config.port as cp
    import config.models as cm

    # Flatten all section params into one dict for lookup
    flat: Dict[str, Any] = {}
    for section_params in sections.values():
        flat.update(section_params)

    # Patch config.port
    _patch_module(cp, flat, _CONFIG_PORT_KEYS, "config.port")

    # Patch config.models
    _patch_module(cm, flat, _CONFIG_MODELS_KEYS, "config.models")

    # Patch config package re-exports (from config import X)
    config_pkg = sys.modules.get("config")
    if config_pkg:
        for json_key, attr in _CONFIG_PORT_KEYS.items():
            if json_key in flat and hasattr(config_pkg, attr):
                setattr(config_pkg, attr, flat[json_key])
                logger.debug("config.%s patched", attr)
        for json_key, attr in _CONFIG_MODELS_KEYS.items():
            if json_key in flat and hasattr(config_pkg, attr):
                setattr(config_pkg, attr, flat[json_key])
                logger.debug("config.%s patched", attr)

    # Patch generator-local constants
    for json_key, (mod_path, attr) in _GENERATOR_PATCHES.items():
        if json_key not in flat:
            continue
        value = flat[json_key]
        # Convert string-keyed dicts back to enum-keyed where needed
        if json_key == "gap_params":
            value = _str_keys_to_gap_type(value)
        elif json_key == "duration_params":
            # duration_params uses tuple values
            value = {k: tuple(v) for k, v in value.items()}
        elif json_key == "base_intensity_params":
            value = {k: tuple(v) for k, v in value.items()}

        mod = sys.modules.get(mod_path)
        if mod is not None:
            setattr(mod, attr, value)
            logger.debug("%s.%s patched from storm_control.json", mod_path, attr)
        else:
            try:
                mod = importlib.import_module(mod_path)
                setattr(mod, attr, value)
                logger.debug("%s.%s patched (lazy import)", mod_path, attr)
            except ImportError:
                logger.debug("Could not import %s — skipping patch", mod_path)

    logger.info("storm_control.json applied (%d params)", len(flat))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _patch_module(
    module: Any,
    flat: Dict[str, Any],
    mapping: Dict[str, str],
    label: str,
) -> None:
    """Set attributes on *module* for every key present in *flat*."""
    for json_key, attr in mapping.items():
        if json_key in flat:
            setattr(module, attr, flat[json_key])
            logger.debug("%s.%s = %r", label, attr, flat[json_key])


def _safe_getattr(mod_path: str, attr: str, default: Any) -> Any:
    """Import *mod_path* and return *attr*, or *default* on failure."""
    mod = sys.modules.get(mod_path)
    if mod is not None:
        return getattr(mod, attr, default)
    try:
        mod = importlib.import_module(mod_path)
        return getattr(mod, attr, default)
    except ImportError:
        return default


def _enum_keys_to_str(d: dict) -> dict:
    """Convert any enum keys to their ``.value`` string form."""
    return {(k.value if hasattr(k, "value") else str(k)): v for k, v in d.items()}


def _str_keys_to_gap_type(d: dict) -> dict:
    """Convert string keys back to GapType enum values."""
    try:
        from src.port.src.storm_multi.core.data_structures import GapType
        return {GapType(k): tuple(v) for k, v in d.items()}
    except ImportError:
        return {k: tuple(v) for k, v in d.items()}
