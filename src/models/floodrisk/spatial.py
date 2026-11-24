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
Spatial functions of the flood risk model (MKM-SP-001 v2.0).

The haversine distance and the projection onto a river polyline are what the platform
uses: the property, gauge and seismic code call them. The IDW interpolation, the
gauge index and the correlation matrix are retained, with no production caller.

The index stores each gauge as a unit vector, so its straight-line (chord) distance
orders gauges exactly as the great-circle distance does. v1.0 indexed latitude and
longitude in radians as though a degree of each were the same length, and named the
wrong nearest gauge in 18% of queries over the Thames (Wolfram benchmark v0.1).
"""

import math
from math import atan2, cos, radians, sin, sqrt
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
from scipy.spatial.distance import cdist

from config.models import (
    spatial_earth_radius_m,
    spatial_idw_min_distance_m,
    spatial_idw_power,
    spatial_km_per_degree,
)

# geopandas is imported lazily inside build_correlation_matrix so that
# haversine_distance and the spatial utilities work without geopandas.


def _unit_vectors(lat, lon) -> np.ndarray:
    """Points on the unit sphere for latitudes and longitudes in degrees."""
    phi, lam = np.deg2rad(np.asarray(lat, dtype=float)), np.deg2rad(np.asarray(lon, dtype=float))
    return np.column_stack([np.cos(phi) * np.cos(lam), np.cos(phi) * np.sin(lam), np.sin(phi)])


def build_spatial_index(gauge_data: Optional[pd.DataFrame]) -> Optional[cKDTree]:
    """KDTree over the gauges' unit vectors, rows in ``gauge_data`` order (None if no gauges)."""
    if gauge_data is not None and len(gauge_data) > 0:
        return cKDTree(_unit_vectors(gauge_data['latitude'].values, gauge_data['longitude'].values))
    return None


def nearest_gauge(tree: cKDTree, lat: float, lon: float) -> Tuple[int, float]:
    """The nearest gauge to (lat, lon): its row in the indexed data, and its
    great-circle distance in metres, 2R asin(chord / 2)."""
    chord, row = tree.query(_unit_vectors([lat], [lon])[0])
    return int(row), float(2 * spatial_earth_radius_m * math.asin(min(1.0, chord / 2)))


def build_correlation_matrix(properties,
                              correlation_distance: float,
                              base_correlation: float) -> np.ndarray:
    """Spatial correlation matrix between properties: base * exp(-d / L), with d the
    Euclidean separation of (longitude, latitude) in degrees at ``spatial_km_per_degree``
    km a degree and L = ``correlation_distance`` in metres; 1 on the diagonal."""
    coords = np.column_stack([
        properties.geometry.x,
        properties.geometry.y
    ])

    distances = cdist(coords, coords)
    distances_km = distances * spatial_km_per_degree

    correlation_matrix = base_correlation * np.exp(
        -distances_km / (correlation_distance / 1000)
    )
    np.fill_diagonal(correlation_matrix, 1.0)

    return correlation_matrix


def haversine_distance(lat1: float, lon1: float,
                        lat2: float, lon2: float) -> float:
    """Calculate distance between two points using Haversine formula (in meters)."""
    R = spatial_earth_radius_m
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c


def nearest_point_on_segment(
    px: float, py: float,
    ax: float, ay: float,
    bx: float, by: float,
) -> Tuple[float, float, float, float]:
    """
    Project point P onto segment AB using flat-Earth approximation
    with cos(lat) longitude correction.

    Args:
        px, py: Point latitude, longitude (degrees)
        ax, ay: Segment start latitude, longitude (degrees)
        bx, by: Segment end latitude, longitude (degrees)

    Returns:
        (nx, ny, dist_m, t) where:
            nx, ny  = nearest point on segment (degrees)
            dist_m  = haversine distance from P to nearest point (meters)
            t       = parameter along segment (0.0 = at A, 1.0 = at B)
    """
    cos_lat = math.cos(math.radians(px))
    dx = bx - ax
    dy = (by - ay) * cos_lat
    seg2 = dx * dx + dy * dy
    if seg2 < 1e-18:
        return ax, ay, haversine_distance(px, py, ax, ay), 0.0
    t = max(0.0, min(1.0,
            ((px - ax) * dx + (py - ay) * cos_lat * dy) / seg2))
    nx = ax + t * (bx - ax)
    ny = ay + t * (by - ay)
    return nx, ny, haversine_distance(px, py, nx, ny), t


def nearest_point_on_polyline(
    lat: float, lon: float,
    polyline: List[Tuple[float, float]],
) -> Tuple[float, float, float, int, float]:
    """
    Find the closest point on a polyline to (lat, lon).

    Args:
        lat, lon: Query point (degrees)
        polyline: Ordered list of (lat, lon, ...) tuples; extra elements ignored.

    Returns:
        (nx, ny, dist_m, seg_idx, t) where:
            nx, ny   = nearest point on polyline (degrees)
            dist_m   = haversine distance to nearest point (meters)
            seg_idx  = index of the segment (between polyline[seg_idx] and [seg_idx+1])
            t        = parameter along that segment (0.0 = at start, 1.0 = at end)
    """
    best_dist = float('inf')
    best_nx = polyline[0][0]
    best_ny = polyline[0][1]
    best_seg = 0
    best_t = 0.0

    for i in range(len(polyline) - 1):
        ax, ay = polyline[i][0], polyline[i][1]
        bx, by = polyline[i + 1][0], polyline[i + 1][1]
        nx, ny, d, t = nearest_point_on_segment(lat, lon, ax, ay, bx, by)
        if d < best_dist:
            best_dist = d
            best_nx, best_ny = nx, ny
            best_seg = i
            best_t = t

    return best_nx, best_ny, best_dist, best_seg, best_t


def spatial_interpolate_wse(target_lat: float, target_lon: float,
                             gauge_flood_data: dict,
                             gauge_metadata: dict,
                             power: float = spatial_idw_power,
                             min_distance: float = spatial_idw_min_distance_m) -> float:
    """
    Spatially interpolate water surface elevation using inverse distance weighting.

    Args:
        target_lat: Target latitude
        target_lon: Target longitude
        gauge_flood_data: Dict of gauge_id -> flood depth at gauge
        gauge_metadata: Dict of gauge_id -> gauge info with elevation, lat, lon
        power: IDW exponent
        min_distance: Distance (m) within which a gauge's own WSE is returned

    Returns:
        Interpolated water surface elevation: each gauge's depth plus its elevation,
        weighted by its haversine distance. 0.0 if there are no gauges.
    """
    pairs = []
    for gauge_id, gauge_depth in gauge_flood_data.items():
        info = gauge_metadata[gauge_id]
        pairs.append((haversine_distance(target_lat, target_lon, info['latitude'], info['longitude']),
                      gauge_depth + info['elevation']))
    return idw_interpolate_from_gauges(pairs, power=power, min_distance=min_distance)


def idw_interpolate_from_gauges(
    gauge_wse_values: list[tuple[float, float]],
    power: float = spatial_idw_power,
    min_distance: float = spatial_idw_min_distance_m,
) -> float:
    """
    Inverse-distance-weighted interpolation of WSE from multiple gauges.

    Args:
        gauge_wse_values: List of (distance_m, wse_m) tuples per gauge
        power: IDW exponent (default 2 = inverse-square)
        min_distance: Distance below which to return the gauge value directly

    Returns:
        Interpolated water surface elevation in meters.
        Returns 0.0 if no valid inputs.
    """
    if not gauge_wse_values:
        return 0.0

    total_weight = 0.0
    weighted_wse = 0.0

    for dist, wse in gauge_wse_values:
        if dist < min_distance:
            return wse
        weight = 1.0 / (dist ** power)
        weighted_wse += weight * wse
        total_weight += weight

    if total_weight == 0:
        return 0.0

    return weighted_wse / total_weight
