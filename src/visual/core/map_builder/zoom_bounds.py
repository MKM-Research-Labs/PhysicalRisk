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
Zoom and bounds calculation utilities for map building.
"""

from typing import Dict, List, Tuple

import numpy as np


def calculate_zoom_for_range(coordinate_range: float, padding_factor: float = 1.0) -> int:
    """
    Calculate appropriate zoom level for a given coordinate range.

    Args:
        coordinate_range: Max range in degrees (lat or lon)
        padding_factor: Multiplier to add padding (default 1.0)

    Returns:
        Zoom level (1-18)
    """
    padded_range = coordinate_range * padding_factor

    if padded_range > 20:
        return 2
    elif padded_range > 10:
        return 3
    elif padded_range > 5:
        return 4
    elif padded_range > 2:
        return 5
    elif padded_range > 1:
        return 6
    elif padded_range > 0.5:
        return 7
    elif padded_range > 0.2:
        return 8
    elif padded_range > 0.1:
        return 9
    else:
        return 10


def calculate_bounds(coordinates: List[Tuple[float, float]]) -> Dict[str, float]:
    """
    Calculate bounding box for a set of coordinates.

    Args:
        coordinates: List of (latitude, longitude) tuples

    Returns:
        Dictionary with min/max lat/lon and center values
    """
    if not coordinates:
        return {}

    lats, lons = zip(*coordinates)

    return {
        'min_lat': min(lats),
        'max_lat': max(lats),
        'min_lon': min(lons),
        'max_lon': max(lons),
        'center_lat': float(np.mean(lats)),
        'center_lon': float(np.mean(lons)),
        'lat_range': max(lats) - min(lats),
        'lon_range': max(lons) - min(lons)
    }
