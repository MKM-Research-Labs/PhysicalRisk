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

"""Geometry helpers for property location placement.

Pulled out of ``locations.py`` to keep that file focused on the
location-generation strategies.  ``LocationsMixin`` inherits from
``GeometryMixin`` so all helpers remain available as instance methods.
"""

import math
import random
from typing import Tuple

from models.floodrisk.spatial import (
    haversine_distance as _haversine_shared,
    nearest_point_on_segment as _nearest_on_segment_shared,
    nearest_point_on_polyline as _nearest_on_polyline_shared,
)


class GeometryMixin:
    """Geometry helpers used by the location generation strategies.

    Class-level constants (``MIN_RIVER_DISTANCE_M``, ``MIN_OFFSET_M``,
    ``MAX_OFFSET_M``) are defined on ``LocationsMixin``; they are looked
    up via ``self`` and so resolve through the subclass.
    """

    def _perpendicular_offset(self, base_lat, base_lon, seg_start, seg_end):
        """
        Offset a point perpendicular to a river segment.

        Places the property on a random side (north or south) of the river
        at a distance between MIN_OFFSET_M and MAX_OFFSET_M from the
        centreline.  Also adds a small along-river jitter.
        """
        seg_lat = seg_end[0] - seg_start[0]
        seg_lon = seg_end[1] - seg_start[1]

        cos_lat = math.cos(math.radians(base_lat))
        perp_lat = -seg_lon * cos_lat
        perp_lon = seg_lat / cos_lat if cos_lat > 0 else seg_lat
        norm = math.sqrt(perp_lat ** 2 + perp_lon ** 2)
        if norm < 1e-12:
            offset_m = random.uniform(self.MIN_OFFSET_M, self.MAX_OFFSET_M)
            offset_deg = offset_m / 111_000
            side = random.choice([-1, 1])
            return base_lat + side * offset_deg, base_lon

        perp_lat /= norm
        perp_lon /= norm

        side = random.choice([-1, 1])
        offset_m = random.uniform(self.MIN_OFFSET_M, self.MAX_OFFSET_M)
        offset_deg = offset_m / 111_000

        along_jitter_deg = random.uniform(-200, 200) / 111_000
        along_lat = seg_lat / (math.sqrt(seg_lat**2 + seg_lon**2) + 1e-12)
        along_lon = seg_lon / (math.sqrt(seg_lat**2 + seg_lon**2) + 1e-12)

        new_lat = (base_lat
                   + side * perp_lat * offset_deg
                   + along_lat * along_jitter_deg)
        new_lon = (base_lon
                   + side * perp_lon * offset_deg
                   + along_lon * along_jitter_deg)
        return new_lat, new_lon

    @staticmethod
    def _nearest_on_segment(px, py, ax, ay, bx, by):
        """Project point P onto segment AB.  Returns (nx, ny, dist_m)."""
        nx, ny, dist_m, _t = _nearest_on_segment_shared(px, py, ax, ay, bx, by)
        return nx, ny, dist_m

    @staticmethod
    def _haversine(lat1, lon1, lat2, lon2):
        return _haversine_shared(lat1, lon1, lat2, lon2)

    def _min_river_distance(self, lat, lon, gauge_points) -> float:
        """Return minimum distance (m) from (lat, lon) to the river centreline."""
        _, _, dist_m, _, _ = _nearest_on_polyline_shared(lat, lon, gauge_points)
        return dist_m

    def _ensure_off_river(self, lat, lon, gauge_points) -> Tuple[float, float]:
        """
        If (lat, lon) is within MIN_RIVER_DISTANCE_M of the river
        centreline, push it perpendicular to the nearest segment.
        """
        best_dist = float('inf')
        best_nx = lat
        best_ny = lon
        best_seg = (0, 1)

        for i in range(len(gauge_points) - 1):
            ax, ay = gauge_points[i][0], gauge_points[i][1]
            bx, by = gauge_points[i + 1][0], gauge_points[i + 1][1]
            nx, ny, d = self._nearest_on_segment(lat, lon, ax, ay, bx, by)
            if d < best_dist:
                best_dist = d
                best_nx, best_ny = nx, ny
                best_seg = (i, i + 1)

        if best_dist >= self.MIN_RIVER_DISTANCE_M:
            return lat, lon

        ai, bi = best_seg
        seg_lat = gauge_points[bi][0] - gauge_points[ai][0]
        seg_lon = gauge_points[bi][1] - gauge_points[ai][1]

        cos_lat = math.cos(math.radians(lat))
        perp_lat = -seg_lon * cos_lat
        perp_lon = seg_lat / cos_lat if cos_lat > 0 else seg_lat
        norm = math.sqrt(perp_lat ** 2 + perp_lon ** 2)
        if norm < 1e-12:
            return lat, lon

        perp_lat /= norm
        perp_lon /= norm

        side = (lat - best_nx) * perp_lat + (lon - best_ny) * perp_lon
        if side < 0:
            perp_lat = -perp_lat
            perp_lon = -perp_lon

        push_deg = self.MIN_RIVER_DISTANCE_M / 111_000
        new_lat = best_nx + perp_lat * push_deg
        new_lon = best_ny + perp_lon * push_deg
        return new_lat, new_lon
