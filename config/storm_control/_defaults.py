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

"""Source-default snapshot and JSON defaults builder."""

from typing import Any, Dict, Tuple

from config.storm_control._mappings import _CONFIG_MODELS_KEYS, _CONFIG_PORT_KEYS


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
    def _rows(attr: str) -> Dict[str, list]:
        return {k: list(v) for k, v in (_port_default(attr) or {}).items()}

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
                "duration_params": _rows("STORM_DURATION_PARAMS"),
                "gap_params": _rows("STORM_GAP_PARAMS"),
                "base_intensity_params": _rows("BASE_INTENSITY_PARAMS"),
                "sequence_type_weights": _rows("SEQUENCE_TYPE_WEIGHTS"),
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
