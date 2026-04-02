# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Location generation mixin for PropertyPortfolioGenerator."""

import math
import random
from typing import Dict, List, Tuple

from models.floodrisk.spatial import (
    haversine_distance as _haversine_shared,
    nearest_point_on_segment as _nearest_on_segment_shared,
    nearest_point_on_polyline as _nearest_on_polyline_shared,
)


class LocationsMixin:
    """Mixin providing spatial/location generation methods."""

    # Minimum distance from river centreline in metres.  The Thames is
    # roughly 200-250m wide through central London and 400-800m in the
    # estuary, so 400m from centreline keeps properties safely on dry land.
    MIN_RIVER_DISTANCE_M = 400

    # Range for perpendicular offset when generating property locations.
    # Properties are placed 400-1200m from the river centreline.
    MIN_OFFSET_M = 400
    MAX_OFFSET_M = 1200

    def _generate_locations(self, count: int) -> List[Dict]:
        """
        Generate property locations based on triangles of 3 gauges.

        Each property is placed relative to 3 specific gauges (a primary gauge
        and its two neighbours along the river).  This ensures every property
        has a well-defined relationship to 3 gauges, which is required for
        IDW-based PRS pricing.

        The location is a barycentric combination of the 3 gauge positions
        (with random weights) then pushed perpendicular to the river to keep
        the property on dry land.
        """
        areas = self.params.AREAS

        # Handle both naming conventions for area value factors
        if hasattr(self.params, 'AREA_VALUE_FACTORS'):
            area_value_factors = self.params.AREA_VALUE_FACTORS
        elif hasattr(self.params, 'AREAVALUEFACTORS'):
            area_value_factors = self.params.AREAVALUEFACTORS
        else:
            area_value_factors = {}

        # Get STREETS data if available
        streets_data = {}
        if hasattr(self.params, 'STREETS'):
            streets_data = self.params.STREETS

        # Use gauge points if available, otherwise fall back to centre point
        gauge_points = getattr(self.params, 'GAUGE_POINTS',
                               getattr(self.params, 'GAUGEPOINTS', None))

        if not gauge_points or len(gauge_points) < 3:
            # Fallback: spread around centre with random offsets
            return self._generate_locations_fallback(
                count, areas, area_value_factors, streets_data)

        n_gauges = len(gauge_points)
        locations = []

        for i in range(count):
            # Select primary gauge (cycle evenly across all gauges)
            primary_idx = i % n_gauges

            # Build the triangle: primary gauge + its two neighbours
            # Ensure 3 distinct gauge indices for proper IDW triangulation
            if primary_idx == 0:
                left_idx, right_idx = 1, 2
            elif primary_idx == n_gauges - 1:
                left_idx, right_idx = n_gauges - 3, n_gauges - 2
            else:
                left_idx = primary_idx - 1
                right_idx = primary_idx + 1

            g_primary = gauge_points[primary_idx]
            g_left = gauge_points[left_idx]
            g_right = gauge_points[right_idx]

            # Barycentric weights — primary gauge gets most weight (closer)
            w_primary = random.uniform(0.4, 0.7)
            w_left = random.uniform(0.1, (1.0 - w_primary) * 0.8)
            w_right = 1.0 - w_primary - w_left

            base_lat = w_primary * g_primary[0] + w_left * g_left[0] + w_right * g_right[0]
            base_lon = w_primary * g_primary[1] + w_left * g_left[1] + w_right * g_right[1]
            river_elev = w_primary * g_primary[2] + w_left * g_left[2] + w_right * g_right[2]

            # Property elevation must be ABOVE gauge/river elevation.
            # Gauges sit at river level (local minima); properties are on
            # higher ground.  Add a vertical offset that increases with
            # distance from the river (set after perpendicular push below).
            elev = river_elev  # will be adjusted after offset

            # Push perpendicular to river (use primary segment direction)
            seg_a = max(0, primary_idx - 1)
            seg_b = min(n_gauges - 1, primary_idx + 1)
            lat, lon = self._perpendicular_offset(
                base_lat, base_lon, gauge_points[seg_a], gauge_points[seg_b])

            # Now compute the actual distance from the river centreline
            # and add a proportional vertical rise above river level.
            # Typical floodplain gradient: ~2-5m rise per km from the river.
            river_dist_m = self._min_river_distance(lat, lon, gauge_points)
            # Rise: 2-5m per km, randomised per property
            gradient_m_per_km = random.uniform(2.0, 5.0)
            vertical_offset = (river_dist_m / 1000.0) * gradient_m_per_km
            # Allow properties at river level (vertical_offset = 0) for Zone 3b
            vertical_offset = max(0.0, vertical_offset)
            elev = river_elev + vertical_offset

            area_name = areas[primary_idx % len(areas)]

            # Record the 3 reference gauge indices (1-based GAUGE-xxx IDs)
            ref_gauges = sorted(set([left_idx, primary_idx, right_idx]))

            locations.append({
                "lat": lat,
                "lon": lon,
                "name": area_name,
                "elevation": max(0, elev),
                "vertical_offset": vertical_offset,
                "value_factor": area_value_factors.get(area_name, 1.0),
                "streets_data": streets_data,
                "reference_gauge_indices": ref_gauges,
            })

        # Push any location that sits in/on the river away from it
        for loc in locations:
            loc['lat'], loc['lon'] = self._ensure_off_river(
                loc['lat'], loc['lon'], gauge_points)

        # Shuffle so properties aren't ordered by gauge index
        random.shuffle(locations)
        return locations

    def _generate_locations_fallback(self, count, areas, area_value_factors, streets_data):
        """Fallback location generation when no gauge points available."""
        locations = []
        for i in range(count):
            area_name = areas[i % len(areas)]
            lat = self.params.CENTER_LAT + random.uniform(-0.02, 0.02)
            lon = self.params.CENTER_LON + random.uniform(-0.02, 0.02)

            if hasattr(self.params, 'get_elevation'):
                elevation = self.params.get_elevation(lat, lon)
            else:
                elevation = random.uniform(2, 30)

            locations.append({
                "lat": lat,
                "lon": lon,
                "name": area_name,
                "elevation": elevation,
                "vertical_offset": random.uniform(0.0, 5.0),
                "value_factor": area_value_factors.get(area_name, 1.0),
                "streets_data": streets_data,
            })
        return locations

    def _perpendicular_offset(self, base_lat, base_lon, seg_start, seg_end):
        """
        Offset a point perpendicular to a river segment.

        Places the property on a random side (north or south) of the river
        at a distance between MIN_OFFSET_M and MAX_OFFSET_M from the
        centreline.  Also adds a small along-river jitter.
        """
        seg_lat = seg_end[0] - seg_start[0]
        seg_lon = seg_end[1] - seg_start[1]

        # Perpendicular direction (rotate segment 90°)
        cos_lat = math.cos(math.radians(base_lat))
        perp_lat = -seg_lon * cos_lat
        perp_lon = seg_lat / cos_lat if cos_lat > 0 else seg_lat
        norm = math.sqrt(perp_lat ** 2 + perp_lon ** 2)
        if norm < 1e-12:
            # Degenerate segment — use pure lat offset
            offset_m = random.uniform(self.MIN_OFFSET_M, self.MAX_OFFSET_M)
            offset_deg = offset_m / 111_000
            side = random.choice([-1, 1])
            return base_lat + side * offset_deg, base_lon

        perp_lat /= norm
        perp_lon /= norm

        # Random side (north/south of river) and distance
        side = random.choice([-1, 1])
        offset_m = random.uniform(self.MIN_OFFSET_M, self.MAX_OFFSET_M)
        offset_deg = offset_m / 111_000

        # Small along-river jitter (±200m)
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
        centreline (approximated by the gauge-point polyline), push it
        perpendicular to the nearest segment so it lands on dry ground.
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

        # Compute perpendicular direction away from the segment
        ai, bi = best_seg
        seg_lat = gauge_points[bi][0] - gauge_points[ai][0]
        seg_lon = gauge_points[bi][1] - gauge_points[ai][1]

        # Normal to segment (rotate 90 degrees)
        cos_lat = math.cos(math.radians(lat))
        perp_lat = -seg_lon * cos_lat
        perp_lon = seg_lat / cos_lat if cos_lat > 0 else seg_lat
        norm = math.sqrt(perp_lat ** 2 + perp_lon ** 2)
        if norm < 1e-12:
            return lat, lon

        perp_lat /= norm
        perp_lon /= norm

        # Decide which side the point is on (keep the same side)
        side = (lat - best_nx) * perp_lat + (lon - best_ny) * perp_lon
        if side < 0:
            perp_lat = -perp_lat
            perp_lon = -perp_lon

        # Push out to MIN_RIVER_DISTANCE_M
        push_deg = self.MIN_RIVER_DISTANCE_M / 111_000  # rough deg offset
        new_lat = best_nx + perp_lat * push_deg
        new_lon = best_ny + perp_lon * push_deg
        return new_lat, new_lon
