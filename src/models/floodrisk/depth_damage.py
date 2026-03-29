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
Flood depth and damage calculations for flood risk model.

Gauge-based interpolation, synthetic flood depths, and
depth-damage vulnerability curves with property type adjustments.
"""

from typing import Optional

import numpy as np
import pandas as pd
from scipy.interpolate import interp1d

from config.models import DAMAGE_POINTS, DEPTH_POINTS
from models.floodrisk.spatial import haversine_distance

# geopandas is imported lazily inside the GeoDataFrame-consuming functions so
# that scalar_depth_damage and the pipeline generators (propertyts, book) can
# be used without geopandas being installed.


def calculate_flood_depths(properties,
                            gauge_data: Optional[pd.DataFrame]) -> np.ndarray:
    """
    Calculate flood depth at each property location.

    Returns:
        Array of flood depths in meters
    """
    if gauge_data is None or len(gauge_data) == 0:
        return calculate_synthetic_flood_depths(properties, gauge_data)

    n_properties = len(properties)
    flood_depths = np.zeros(n_properties)

    # Use gauge-based approach via synthetic method which handles both cases
    return calculate_synthetic_flood_depths(properties, gauge_data)


def calculate_synthetic_flood_depths(properties,
                                      gauge_data: Optional[pd.DataFrame]) -> np.ndarray:
    """
    Calculate flood depths using gauge data with elevation and distance decay.

    If gauge data is available, uses max water level vs severe level to
    determine flooding, then applies elevation correction and distance decay
    from central Thames.
    """
    n_properties = len(properties)
    flood_depths = np.zeros(n_properties)

    if gauge_data is not None and len(gauge_data) > 0:
        max_water_level = gauge_data['water_level'].max()
        mean_severe_level = gauge_data['severe_level'].mean()

        if max_water_level > mean_severe_level:
            flood_wse = max_water_level

            for i, (_, property_row) in enumerate(properties.iterrows()):
                prop_elevation = property_row.get('elevation', 20.0)
                depth = max(0.0, flood_wse - prop_elevation)

                prop_lat = property_row.geometry.y
                prop_lon = property_row.geometry.x

                thames_lat, thames_lon = 51.5, -0.1
                distance = haversine_distance(thames_lat, thames_lon, prop_lat, prop_lon)

                max_distance = 25000
                if distance < max_distance:
                    distance_factor = 1.0 - (distance / max_distance)
                    depth = depth * distance_factor
                else:
                    depth = 0.0

                flood_depths[i] = min(depth, 5.0)

    return flood_depths



def scalar_depth_damage(depth: float) -> float:
    """
    Scalar depth-damage lookup using UK-calibrated vulnerability curve.

    Linear interpolation between control points. Returns damage ratio 0-1.

    Args:
        depth: Flood depth in meters (above floor level)

    Returns:
        Damage ratio (0.0 to 1.0)
    """
    if depth <= 0:
        return 0.0
    if depth >= DEPTH_POINTS[-1]:
        return 1.0
    for i in range(len(DEPTH_POINTS) - 1):
        if DEPTH_POINTS[i] <= depth < DEPTH_POINTS[i + 1]:
            t = (depth - DEPTH_POINTS[i]) / (DEPTH_POINTS[i + 1] - DEPTH_POINTS[i])
            return DAMAGE_POINTS[i] + t * (DAMAGE_POINTS[i + 1] - DAMAGE_POINTS[i])
    return 0.0


def depth_damage_function(depths: np.ndarray,
                           properties) -> np.ndarray:
    """
    Advanced depth-damage function with property type and floor level adjustments.

    Uses an interpolated vulnerability curve calibrated to UK flood damage data,
    then adjusts for property type and floor level.

    Args:
        depths: Array of flood depths in meters
        properties: GeoDataFrame with property_type and floor_level_metres

    Returns:
        Array of damage ratios (0 to 1)
    """
    depth_points = np.array([0, 0.05, 0.5, 1, 1.5, 2, 3, 4, 5, 6])
    vulnerability_points = np.array([0, 0.05, 0.25, 0.4, 0.5, 0.6, 0.75, 0.85, 0.95, 1])

    vulnerability_curve = interp1d(
        depth_points, vulnerability_points,
        kind='linear', fill_value=(0, 1), bounds_error=False
    )

    property_type_factors = {
        'residential': 1.0,
        'commercial': 1.2,
        'industrial': 0.9
    }

    type_adjustments = np.array([
        property_type_factors.get(str(pt).lower(), 1.0)
        for pt in properties['property_type']
    ])

    floor_levels = properties['floor_level_metres'].values
    adjusted_depths = np.maximum(depths - floor_levels, 0)
    adjusted_damage = vulnerability_curve(adjusted_depths)

    final_damage = adjusted_damage * type_adjustments

    return np.clip(final_damage, 0, 1)
