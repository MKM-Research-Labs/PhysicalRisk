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

"""Storm-control key mappings (JSON snake_case → Python UPPER_CASE)."""

from typing import Dict, Tuple


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
    "sequence_type_weights": "SEQUENCE_TYPE_WEIGHTS",
    "duration_params": "STORM_DURATION_PARAMS",
    "gap_params": "STORM_GAP_PARAMS",
    "base_intensity_params": "BASE_INTENSITY_PARAMS",
    # (catchment_base_precip removed — per-catchment storm calibration
    #  now lives in data/catch/<catchment>/storm.py)
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

# Tables keyed by category or gap type. A control file's rows are laid over the source
# table rather than replacing it, so a file that sets one category does not drop the
# others. (The generators read every one of these from config.port on each draw, so
# patching config.port is all an override needs; MKM-SS-001 v3.0 Q4.)
_TABLE_KEYS: Tuple[str, ...] = ("sequence_probability", "sequence_type_weights", "duration_params",
                                "gap_params", "base_intensity_params")
# The (min, mode, max) and (mean, std) tables, held as tuples.
_TUPLE_TABLES: Tuple[str, ...] = ("duration_params", "gap_params", "base_intensity_params")

_CONTROL_FILENAME = "storm_control.json"
