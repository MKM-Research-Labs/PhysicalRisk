# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial 
# research and educational use only. Any commercial use, including 
# but not limited to use in or for products or services offered for sale, 
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Spatial infrastructure for flood risk model.

KDTree construction, correlation matrix, haversine distance,
and inverse-distance-weighted interpolation.
"""

import math
from math import atan2, cos, radians, sin, sqrt
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
from scipy.spatial.distance import cdist

# geopandas is imported lazily inside build_correlation_matrix so that
# haversine_distance and the spatial utilities work without geopandas.


def build_spatial_index(gauge_data: Optional[pd.DataFrame]) -> Optional[cKDTree]:
    """Build KDTree for efficient spatial queries on gauge data."""
    if gauge_data is not None and len(gauge_data) > 0:
        gauge_coords = np.deg2rad(
            gauge_data[['latitude', 'longitude']].values
        )
        return cKDTree(gauge_coords)
    return None


def build_correlation_matrix(properties,
                              correlation_distance: float,
                              base_correlation: float) -> np.ndarray:
    """Build spatial correlation matrix between properties."""
    coords = np.column_stack([
        properties.geometry.x,
        properties.geometry.y
    ])

    distances = cdist(coords, coords)
    distances_km = distances * 111.0

    correlation_matrix = base_correlation * np.exp(
        -distances_km / (correlation_distance / 1000)
    )
    np.fill_diagonal(correlation_matrix, 1.0)

    return correlation_matrix


def haversine_distance(lat1: float, lon1: float,
                        lat2: float, lon2: float) -> float:
    """Calculate distance between two points using Haversine formula (in meters)."""
    R = 6371000
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
                             gauge_metadata: dict) -> float:
    """
    Spatially interpolate water surface elevation using inverse distance weighting.

    Args:
        target_lat: Target latitude
        target_lon: Target longitude
        gauge_flood_data: Dict of gauge_id -> flood depth at gauge
        gauge_metadata: Dict of gauge_id -> gauge info with elevation, lat, lon

    Returns:
        Interpolated water surface elevation
    """
    if not gauge_flood_data:
        return 0.0

    gauge_wse_data = {}
    for gauge_id, gauge_depth in gauge_flood_data.items():
        gauge_info = gauge_metadata[gauge_id]
        gauge_wse = gauge_depth + gauge_info['elevation']
        gauge_wse_data[gauge_id] = {
            'wse': gauge_wse,
            'lat': gauge_info['latitude'],
            'lon': gauge_info['longitude']
        }

    total_weight = 0.0
    weighted_wse = 0.0

    for gauge_id, gauge_data in gauge_wse_data.items():
        distance = haversine_distance(
            target_lat, target_lon,
            gauge_data['lat'], gauge_data['lon']
        )

        if distance < 1.0:
            return gauge_data['wse']

        weight = 1.0 / (distance ** 2)
        weighted_wse += weight * gauge_data['wse']
        total_weight += weight

    if total_weight == 0:
        return 0.0

    return weighted_wse / total_weight


def idw_interpolate_from_gauges(
    gauge_wse_values: list[tuple[float, float]],
    power: float = 2.0,
    min_distance: float = 1.0,
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
