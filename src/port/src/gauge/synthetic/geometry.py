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
Geometry utilities for synthetic gauge placement — river polyline
loading, snapping, and linear interpolation.
"""

import json
import logging
import math
from pathlib import Path
from typing import List, Optional, Tuple

from config import config
from models.floodrisk.spatial import haversine_distance

logger = logging.getLogger(__name__)

_RIVER_POLYLINE_CACHE = None  # cached high-res river polyline


def _load_river_polyline() -> Optional[List[Tuple]]:
    """Load high-resolution river polyline from cached JSON.

    Falls back to None if the cache file doesn't exist, in which case
    synthetic gauges use the coarser gauge-point polyline coordinates.
    """
    global _RIVER_POLYLINE_CACHE
    if _RIVER_POLYLINE_CACHE is not None:
        return _RIVER_POLYLINE_CACHE

    cache_path = config.get_catch_dir(config.CATCHMENT) / "river_polyline.json"
    if not cache_path.exists():
        logger.info("No river polyline cache at %s — using gauge points", cache_path)
        return None

    with open(cache_path) as f:
        points = json.load(f)
    _RIVER_POLYLINE_CACHE = [(p[0], p[1]) for p in points]
    logger.info("Loaded river polyline: %d points from %s",
                len(_RIVER_POLYLINE_CACHE), cache_path.name)
    return _RIVER_POLYLINE_CACHE


def _snap_to_river(lat: float, lon: float) -> Tuple[float, float]:
    """Snap coordinates to the high-resolution river polyline.

    Returns the snapped (lat, lon) or the original coordinates if
    no river polyline is available.
    """
    river = _load_river_polyline()
    if river is None or len(river) < 2:
        return lat, lon

    best_lat, best_lon = lat, lon
    best_dist = float("inf")

    for i in range(len(river) - 1):
        ax, ay = river[i]
        bx, by = river[i + 1]

        # Project point onto segment (locally scaled Cartesian)
        cos_lat = math.cos(math.radians(lat))
        dx = bx - ax
        dy = (by - ay) * cos_lat
        seg_len_sq = dx * dx + dy * dy
        if seg_len_sq < 1e-18:
            continue

        t = ((lat - ax) * dx + (lon - ay) * cos_lat * dy) / seg_len_sq
        t = max(0.0, min(1.0, t))
        nx = ax + t * (bx - ax)
        ny = ay + t * (by - ay)

        d = haversine_distance(lat, lon, nx, ny)
        if d < best_dist:
            best_dist = d
            best_lat = nx
            best_lon = ny

    return round(best_lat, 6), round(best_lon, 6)


def _lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation: a*(1-t) + b*t."""
    return a * (1 - t) + b * t
