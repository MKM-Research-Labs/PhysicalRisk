# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""Source-default snapshot and JSON defaults builder."""

from typing import Any, Dict, Tuple

from config.storm_control._mappings import _CONFIG_MODELS_KEYS, _CONFIG_PORT_KEYS
from config.storm_control._helpers import _enum_keys_to_str, _safe_getattr


# ---------------------------------------------------------------------------
# Source-default snapshot
#
# ``apply_storm_control()`` mutates ``config.port`` and ``config.models``
# attributes in place. Once called, ``config.port.EVENT_WINDOW_HOURS`` no
# longer equals the Python source constant — it equals whatever was in
# ``storm_control.json``. If ``get_defaults()`` reads the live attributes
# after that, the "defaults" it returns are the applied-over values, and
# the Reset button can't restore the source. To avoid that, we snapshot
# the relevant attributes *at import time of this module*, which runs
# from ``config/__init__.py`` BEFORE ``apply_storm_control`` is invoked.
# ---------------------------------------------------------------------------

def _build_source_default_snapshot() -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Capture config.port / config.models attrs before any mutation."""
    import config.port as _cp
    import config.models as _cm
    port_snap: Dict[str, Any] = {}
    for attr in _CONFIG_PORT_KEYS.values():
        if hasattr(_cp, attr):
            port_snap[attr] = getattr(_cp, attr)
    models_snap: Dict[str, Any] = {}
    for attr in _CONFIG_MODELS_KEYS.values():
        if hasattr(_cm, attr):
            models_snap[attr] = getattr(_cm, attr)
    return port_snap, models_snap


_PORT_DEFAULTS, _MODELS_DEFAULTS = _build_source_default_snapshot()


def _port_default(attr: str, fallback: Any = None) -> Any:
    return _PORT_DEFAULTS.get(attr, fallback)


def _models_default(attr: str, fallback: Any = None) -> Any:
    return _MODELS_DEFAULTS.get(attr, fallback)


def get_defaults() -> Dict[str, Any]:
    """Build default JSON structure from source Python config values.

    Reads from the pre-apply snapshot captured at module import time, so
    the "defaults" returned here always match the source constants in
    ``config.port`` / ``config.models`` — even after ``apply_storm_control``
    has mutated the live attributes.
    """
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

    def _p(attr: str) -> Any:
        return _port_default(attr)

    def _m(attr: str) -> Any:
        return _models_default(attr)

    return {
        "version": "1.0.0",
        "sections": {
            "storm_generation": {
                "event_window_hours": _p("EVENT_WINDOW_HOURS"),
                "min_drainage_window_hours": _p("MIN_DRAINAGE_WINDOW_HOURS"),
                "sequence_probability": dict(_p("SEQUENCE_PROBABILITY") or {}),
                "default_type_weights": list(_p("DEFAULT_TYPE_WEIGHTS") or ()),
                "intensity_variation": _p("INTENSITY_VARIATION"),
                "first_storm_dominant_prob": _p("FIRST_STORM_DOMINANT_PROB"),
                "correlation_prob": _p("CORRELATION_PROB"),
                "default_intensity_weights": dict(_p("DEFAULT_INTENSITY_WEIGHTS") or {}),
                "duration_params": duration_params,
                "gap_params": gap_params,
                "base_intensity_params": base_intensity,
                "sequence_type_weights": seq_type_weights,
            },
            "hydrograph_synthesis": {
                "hydro_alpha": dict(_m("HYDRO_ALPHA") or {}),
                "saturation_beta": _m("SATURATION_BETA"),
                "saturation_p0_mm": _m("SATURATION_P0_MM"),
                "infiltration_rate_per_hour": _m("INFILTRATION_RATE_PER_HOUR"),
                "infiltration_ymax_ref_m": _m("INFILTRATION_YMAX_REF_M"),
                "default_imperv_fraction": _m("DEFAULT_IMPERV_FRACTION"),
                "superposition_cap_factor": _m("SUPERPOSITION_CAP_FACTOR"),
                "depth_points": list(_m("DEPTH_POINTS") or ()),
                "damage_points": list(_m("DAMAGE_POINTS") or ()),
            },
            "gauge_propagation": {
                "default_roughness": _m("DEFAULT_ROUGHNESS"),
                "terrain_velocity_scale": dict(_m("TERRAIN_VELOCITY_SCALE") or {}),
                "default_retention_length": _m("DEFAULT_RETENTION_LENGTH"),
                "min_slope": _m("MIN_SLOPE"),
                "default_recession_factor": _m("DEFAULT_RECESSION_FACTOR"),
                "bankfull_offset_m": _p("BANKFULL_OFFSET_M"),
                "n_nearest_gauges": _p("N_NEAREST_GAUGES"),
            },
            "spatial_correlation": {
                "spatial_corr_enabled": _p("SPATIAL_CORR_ENABLED"),
                "spatial_corr_base_range_km": _p("SPATIAL_CORR_BASE_RANGE_KM"),
                "spatial_corr_nugget": _p("SPATIAL_CORR_NUGGET"),
                "spatial_corr_rho_intensity": _p("SPATIAL_CORR_RHO_INTENSITY"),
                "spatial_corr_sigma_lognormal": _p("SPATIAL_CORR_SIGMA_LOGNORMAL"),
            },
            "stress_catalogue": {
                "stress_storms_min_count": _p("STRESS_STORMS_MIN_COUNT"),
                "stress_storm_default_duration_hours": _p("STRESS_STORM_DEFAULT_DURATION_HOURS"),
                "stress_storm_default_peak_position": _p("STRESS_STORM_DEFAULT_PEAK_POSITION"),
            },
        },
    }
