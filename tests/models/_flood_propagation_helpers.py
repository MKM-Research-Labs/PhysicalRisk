# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""
Shared helpers for flood propagation sensitivity tests.
"""

from models.floodrisk.velocity import (
    build_property_hydrograph,
    compute_retention,
    compute_travel_time,
    compute_slope,
)


def _triangular_gauge_readings(n_hours=168, peak_hour=84, base=2.0, peak=8.0):
    """Build a symmetric triangular gauge hydrograph."""
    readings = []
    for h in range(n_hours):
        if h <= peak_hour:
            level = base + (peak - base) * (h / peak_hour)
        else:
            level = peak - (peak - base) * ((h - peak_hour) / (n_hours - peak_hour))
            level = max(level, base)
        readings.append({'hour': h, 'water_level_m': level})
    return readings


def _compute_flood_depth(gauge_readings, peak_level_m, severe_level,
                         gauge_elevation, prop_elevation, floor_level,
                         distance_m):
    """
    Reproduce the v2.3 _build_flood_event logic for a single storm.

    Returns (flood_depth, retention, est_depth, n_flooded_hours).
    """
    water_above_gauge = max(0.0, peak_level_m - severe_level)
    retention = compute_retention(distance_m)
    water_at_property = water_above_gauge * retention

    height_diff = max(0.0, prop_elevation - gauge_elevation)
    flood_threshold = height_diff + floor_level
    est_depth = max(0.0, water_at_property - flood_threshold)

    # Hydrograph peak WSE — v2.3 uses attenuated value
    absolute_peak_wse = gauge_elevation + water_at_property

    slope = compute_slope(gauge_elevation, prop_elevation, distance_m)
    if est_depth > 0:
        travel_time = compute_travel_time(distance_m, est_depth, slope)
        if travel_time == float('inf'):
            travel_time = 0.0
    else:
        travel_time = 0.0

    readings = build_property_hydrograph(
        gauge_readings, absolute_peak_wse, travel_time,
        retention, prop_elevation, floor_level,
    )

    flood_depth = max((r['depth_m'] for r in readings), default=0.0)
    n_flooded = sum(1 for r in readings if r['flooded'])

    return flood_depth, retention, est_depth, n_flooded
