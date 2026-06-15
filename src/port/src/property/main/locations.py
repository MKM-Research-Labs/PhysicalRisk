# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Location generation mixin for PropertyPortfolioGenerator.

v3.0: Properties are placed relative to synthetic gauges on the river.
Each property is assigned to a synthetic gauge and pushed perpendicular
to the river direction at that point, at a random distance (100-2000m).
"""

import json
import random
from typing import Dict, List

from config.port import EA_FLOOD_ZONE_ELEVATION_BOUNDS
from models.floodrisk.spatial import (
    haversine_distance as _haversine_shared,
    nearest_point_on_polyline as _nearest_on_polyline_shared,
)

from ._geometry import GeometryMixin


def _zone_from_offset(offset: float) -> str:
    """Derive EA flood zone from vertical offset above river (metres)."""
    for zone, (lo, hi) in EA_FLOOD_ZONE_ELEVATION_BOUNDS.items():
        # A None bound is unbounded on that side: Zone 3b (functional
        # floodplain) extends to/below river level (lo=None); Zone 1
        # extends arbitrarily high (hi=None).
        if (lo is None or offset >= lo) and (hi is None or offset < hi):
            return zone
    return 'Zone 1'


def _zone_seed_offsets() -> List[float]:
    """One representative in-band vertical offset (m) per EA flood zone.

    Used to guarantee every zone is represented in a generated portfolio.
    The distance x gradient placement model cannot reach the functional
    floodplain on its own — MIN_RIVER_DISTANCE_M (400 m) times the minimum
    gradient (2 m/km) already exceeds Zone 3b's 0.5 m ceiling — so a property
    would never naturally land in Zone 3b. Offsets are derived from
    EA_FLOOD_ZONE_ELEVATION_BOUNDS (not hard-coded) so they track the config.
    """
    seeds = []
    for _zone, (lo, hi) in EA_FLOOD_ZONE_ELEVATION_BOUNDS.items():
        if lo is None:        # unbounded below (Zone 3b): mid of [0, hi)
            seeds.append(hi / 2.0)
        elif hi is None:      # unbounded above (Zone 1): a bit into the band
            seeds.append(lo + 1.0)
        else:
            seeds.append((lo + hi) / 2.0)
    return seeds


class LocationsMixin(GeometryMixin):
    """Mixin providing spatial/location generation methods."""

    # Minimum distance from river centreline (metres).
    MIN_RIVER_DISTANCE_M = 400

    # Range for perpendicular offset from synthetic gauge to property.
    MIN_OFFSET_M = 100
    MAX_OFFSET_M = 2000

    def _generate_locations(self, count: int) -> List[Dict]:
        """
        Generate property locations relative to synthetic gauges.

        Each property is assigned to a synthetic gauge on the river and
        placed at a random perpendicular distance from it.  The elevation
        is the synthetic gauge elevation plus a vertical offset proportional
        to distance (2-5 m/km gradient).

        Requires gauge.json to contain synthetic gauges (run step 2 first).
        Falls back to the old gauge-point triangulation if no synthetics.
        """
        areas = self.params.AREAS

        if hasattr(self.params, 'AREA_VALUE_FACTORS'):
            area_value_factors = self.params.AREA_VALUE_FACTORS
        elif hasattr(self.params, 'AREAVALUEFACTORS'):
            area_value_factors = self.params.AREAVALUEFACTORS
        else:
            area_value_factors = {}

        streets_data = {}
        if hasattr(self.params, 'STREETS'):
            streets_data = self.params.STREETS

        gauge_points = getattr(self.params, 'GAUGE_POINTS',
                               getattr(self.params, 'GAUGEPOINTS', None))

        # Load synthetic gauges from gauge.json
        synthetics = self._load_synthetic_gauges()

        if not synthetics:
            # Fallback if no synthetics (shouldn't happen in normal pipeline)
            if not gauge_points or len(gauge_points) < 3:
                return self._generate_locations_fallback(
                    count, areas, area_value_factors, streets_data)
            return self._generate_locations_legacy(
                count, areas, area_value_factors, streets_data, gauge_points)

        # Place each property relative to a synthetic gauge
        locations = []
        n_synth = len(synthetics)

        # Seed the first property of each EA flood zone so every zone is
        # represented (the distance x gradient model alone can't reach the
        # functional floodplain — see _zone_seed_offsets). The shuffle at the
        # end removes any ordering bias these seeds introduce.
        zone_seeds = _zone_seed_offsets()

        for i in range(count):
            # Round-robin assignment to synthetic gauges
            synth = synthetics[i % n_synth]
            synth_lat = synth['lat']
            synth_lon = synth['lon']
            synth_elev = synth['elevation']
            synth_id = synth['gauge_id']

            # Compute river direction at the synthetic gauge.
            # Use the gauge polyline to find the local segment direction.
            if gauge_points and len(gauge_points) >= 2:
                _, _, _, seg_idx, _ = _nearest_on_polyline_shared(
                    synth_lat, synth_lon, gauge_points)
                seg_a = gauge_points[seg_idx]
                seg_b_idx = min(seg_idx + 1, len(gauge_points) - 1)
                seg_b = gauge_points[seg_b_idx]
            else:
                # Fallback: use a small delta for direction
                seg_a = (synth_lat - 0.001, synth_lon)
                seg_b = (synth_lat + 0.001, synth_lon)

            # Push perpendicular to river
            lat, lon = self._perpendicular_offset(
                synth_lat, synth_lon, seg_a, seg_b)

            # Compute actual distance from the synthetic gauge
            dist_m = _haversine_shared(lat, lon, synth_lat, synth_lon)

            # Vertical offset proportional to distance
            gradient_m_per_km = random.uniform(2.0, 5.0)
            vertical_offset = max(0.0, (dist_m / 1000.0) * gradient_m_per_km)

            # Seed one property per zone at a representative in-band offset so
            # every EA flood zone (incl. the functional floodplain) appears.
            if i < len(zone_seeds):
                vertical_offset = zone_seeds[i]
            elev = synth_elev + vertical_offset

            # Derive zone from offset
            flood_zone = _zone_from_offset(vertical_offset)

            area_name = areas[i % len(areas)]

            locations.append({
                "lat": lat,
                "lon": lon,
                "name": area_name,
                "elevation": max(0, elev),
                "vertical_offset": vertical_offset,
                "flood_zone": flood_zone,
                "synthetic_gauge_id": synth_id,
                "synthetic_gauge_elevation": synth_elev,
                "value_factor": area_value_factors.get(area_name, 1.0),
                "streets_data": streets_data,
            })

        # Ensure all locations are off the river
        if gauge_points and len(gauge_points) >= 2:
            for loc in locations:
                loc['lat'], loc['lon'] = self._ensure_off_river(
                    loc['lat'], loc['lon'], gauge_points)

        random.shuffle(locations)
        return locations

    def _load_synthetic_gauges(self) -> List[Dict]:
        """Load synthetic gauges from gauge.json."""
        gauge_file = getattr(self, 'output_dir', None)
        if gauge_file is None:
            return []
        gauge_path = gauge_file / 'gauge.json'
        if not gauge_path.exists():
            return []

        try:
            with open(gauge_path) as f:
                data = json.load(f)
        except (json.JSONDecodeError, ValueError):
            return []

        synthetics = []
        for g in data.get('flood_gauges', []):
            fg = g.get('FloodGauge', {})
            gid = fg.get('Header', {}).get('GaugeID', '')
            if not gid.startswith('SYNTH'):
                continue
            loc = fg.get('Location', {})
            sensor = fg.get('SensorDetails', {}).get('GaugeInformation', {})
            synthetics.append({
                'gauge_id': gid,
                'lat': loc.get('GaugeLatitude', sensor.get('GaugeLatitude', 0)),
                'lon': loc.get('GaugeLongitude', sensor.get('GaugeLongitude', 0)),
                'elevation': loc.get('GaugeElevation', sensor.get('GroundLevelMeters', 0)),
            })

        return synthetics

    def _generate_locations_legacy(self, count, areas, area_value_factors,
                                    streets_data, gauge_points):
        """Legacy location generation using gauge-point triangulation.

        Used only when no synthetic gauges are available.
        """
        n_gauges = len(gauge_points)
        locations = []

        for i in range(count):
            primary_idx = i % n_gauges
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

            w_primary = random.uniform(0.4, 0.7)
            w_left = random.uniform(0.1, (1.0 - w_primary) * 0.8)
            w_right = 1.0 - w_primary - w_left

            base_lat = w_primary * g_primary[0] + w_left * g_left[0] + w_right * g_right[0]
            base_lon = w_primary * g_primary[1] + w_left * g_left[1] + w_right * g_right[1]
            river_elev = w_primary * g_primary[2] + w_left * g_left[2] + w_right * g_right[2]

            seg_a = max(0, primary_idx - 1)
            seg_b = min(n_gauges - 1, primary_idx + 1)
            lat, lon = self._perpendicular_offset(
                base_lat, base_lon, gauge_points[seg_a], gauge_points[seg_b])

            river_dist_m = self._min_river_distance(lat, lon, gauge_points)
            gradient_m_per_km = random.uniform(2.0, 5.0)
            vertical_offset = max(0.0, (river_dist_m / 1000.0) * gradient_m_per_km)
            elev = river_elev + vertical_offset

            area_name = areas[primary_idx % len(areas)]
            ref_gauges = sorted(set([left_idx, primary_idx, right_idx]))

            locations.append({
                "lat": lat, "lon": lon, "name": area_name,
                "elevation": max(0, elev),
                "vertical_offset": vertical_offset,
                "value_factor": area_value_factors.get(area_name, 1.0),
                "streets_data": streets_data,
                "reference_gauge_indices": ref_gauges,
            })

        for loc in locations:
            loc['lat'], loc['lon'] = self._ensure_off_river(
                loc['lat'], loc['lon'], gauge_points)

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
                "lat": lat, "lon": lon, "name": area_name,
                "elevation": elevation,
                "vertical_offset": random.uniform(0.0, 5.0),
                "value_factor": area_value_factors.get(area_name, 1.0),
                "streets_data": streets_data,
            })
        return locations
