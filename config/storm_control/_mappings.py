# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

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
