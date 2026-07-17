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

"""Hydraulic flood propagation: gauge → property flood computation."""

from typing import Dict, List, Optional

from config.models import TERRAIN_VELOCITY_SCALE, DEFAULT_TERRAIN_TYPE
from config.port import BANKFULL_OFFSET_M
from models.floodrisk import relative_elevation
from models.floodrisk.depth_damage import scalar_depth_damage
from models.floodrisk.hydrograph import build_compound_property_hydrograph
from models.floodrisk.velocity import (
    build_property_hydrograph,
    compute_retention,
    compute_slope,
    compute_travel_time,
)


def _scan_readings(readings):
    """Extract arrival_time, peak_time, and flood_depth from hydrograph readings."""
    arrival_time = None
    peak_time = None
    flood_depth = 0.0
    for r in readings:
        if r['flooded'] and arrival_time is None:
            arrival_time = r['hour']
        if r['depth_m'] > flood_depth:
            flood_depth = r['depth_m']
            peak_time = r['hour']
    return arrival_time, peak_time, flood_depth


class PropagationMixin:
    """Mixin providing flood propagation and event construction."""

    def _compute_property_flood(self, storm_id: str, gauge_responses: Dict,
                                 nearest: List[Dict],
                                 prop_lat: float, prop_lon: float,
                                 prop_elevation: float, floor_level: float,
                                 gaugets: Dict,
                                 mode: str = "normal",
                                 terrain_type: str = DEFAULT_TERRAIN_TYPE,
                                 ) -> Optional[Dict]:
        """
        Compute property-level flood for a single storm.

        Uses the synthetic gauge (position [0] in the nearest list) as
        the single controlling boundary condition.  The synthetic gauge
        represents the point on the river centreline nearest to the
        property.  Real gauges are retained for audit only.

        Falls back to the nearest real gauge only if the synthetic has
        no storm response for this event.

        v2.1: Replaced multi-gauge IDW with single nearest gauge.
        v2.3: Synthetic gauge always controls; explicit preference.

        Args:
            mode: "normal", "shd" (zero elevation diff), or "she" (zero distance).
        """
        # Use the synthetic gauge (first in list) as controlling boundary.
        # Fall back to real gauges only if synthetic has no response.
        for ng in nearest:
            gid = ng['gauge_id']
            dist = ng['distance_m']

            resp = gauge_responses.get(gid)
            if resp is None:
                continue

            # Apply synthetic overrides
            effective_dist = 0.0 if mode == "she" else dist
            g_elev = ng['gauge_info']['elevation']
            effective_elevation = g_elev if mode == "shd" else prop_elevation

            gauge_wse = resp.get('peak_level_m', 0)
            # Terrain velocity scaling: urban water flows faster (less
            # attenuation) than floodplain.  Scale the effective distance
            # inversely with velocity — faster flow = shorter effective distance.
            velocity_scale = TERRAIN_VELOCITY_SCALE.get(terrain_type, 1.0)
            scaled_dist = effective_dist / velocity_scale if velocity_scale > 0 else effective_dist
            retention = compute_retention(scaled_dist)

            # v2.2: use per-pulse superposition when pulse data is available
            pulse_peaks = resp.get('pulse_peaks', [])
            if pulse_peaks:
                return self._build_compound_flood_event(
                    storm_id, pulse_peaks, resp, effective_dist, retention,
                    effective_elevation, floor_level, gid, gaugets, ng
                )

            return self._build_flood_event(
                storm_id, gauge_wse, effective_dist, retention,
                effective_elevation, floor_level,
                gid, gaugets, ng
            )

        return None

    def _build_flood_event(self, storm_id: str, interpolated_wse: float,
                            distance_m: float, retention: float,
                            prop_elevation: float, floor_level: float,
                            source_gauge_id: str, gaugets: Dict,
                            nearest_gauge: Dict) -> Dict:
        """Build a complete flood event with hydrograph."""
        g_elev = nearest_gauge['gauge_info']['elevation']

        slope = compute_slope(g_elev, prop_elevation, distance_m)

        # peak_level_m is a gauge stage reading (height above gauge zero
        # datum).  Overbank flooding begins at bankfull level, NOT at the
        # severe warning threshold.  Bankfull is the point where water
        # spills onto the floodplain (typically 0.5-1.0m below severe for
        # UK rivers).  Severe is an administrative safety alert.
        severe_level = nearest_gauge['gauge_info'].get('severe_level', 0)
        bankfull_level = max(0.0, severe_level - BANKFULL_OFFSET_M)
        water_above_gauge = max(0.0, interpolated_wse - bankfull_level)
        # Propagate to property location with distance-based retention
        water_at_property = water_above_gauge * retention
        # Property floods when water exceeds the elevation difference + floor step
        flood_threshold = relative_elevation(prop_elevation, g_elev, floor_level)

        est_depth = max(0.0, water_at_property - flood_threshold)
        if est_depth <= 0:
            travel_time = 0.0
        else:
            travel_time = compute_travel_time(distance_m, est_depth, slope)
            if travel_time == float('inf'):
                travel_time = 0.0

        gt = gaugets.get(source_gauge_id, {})
        gauge_readings = gt.get('flood_simulation', {}).get('readings', [])

        # Convert gauge flood depth to absolute WSE for hydrograph scaling.
        # Flood depth at gauge = reading − severe_level; absolute WSE at
        # property = gauge_ground + flood_depth_at_gauge.
        absolute_peak_wse = g_elev + water_at_property

        readings = []
        if gauge_readings:
            mapped_readings = []
            for idx, r in enumerate(gauge_readings):
                mapped_readings.append({
                    'hour': r.get('hour', idx),
                    'water_level_m': r.get('waterLevel', r.get('water_level_m', 0)),
                })
            readings = build_property_hydrograph(
                mapped_readings,
                absolute_peak_wse,
                travel_time,
                retention,
                prop_elevation,
                floor_level,
            )

        return self._make_event_dict(
            storm_id, interpolated_wse, readings, travel_time, retention)

    @staticmethod
    def _make_event_dict(storm_id, interpolated_wse, readings,
                         travel_time, retention, **extras):
        """Build the canonical flood-event dict from computed readings.

        Shared by _build_flood_event and _build_compound_flood_event to
        avoid duplicating the scan → damage → serialise logic.
        """
        arrival_time, peak_time, flood_depth = _scan_readings(readings)
        damage_ratio = scalar_depth_damage(flood_depth)
        peak_wse = max((r['wse_m'] for r in readings), default=0.0) if readings else 0.0

        event = {
            'storm_id': storm_id,
            'interpolated_wse_m': round(interpolated_wse, 4),
            'attenuated_wse_m': round(peak_wse, 4),
            'flood_depth_m': round(flood_depth, 4),
            'damage_ratio': round(damage_ratio, 4),
            'flooded': flood_depth > 0,
            'arrival_time_hrs': arrival_time,
            'peak_time_hrs': peak_time,
            'travel_time_hrs': round(travel_time, 2),
            'retention_factor': round(retention, 4),
            **extras,
        }

        # Only store 168-hour readings for events that actually flood the
        # property.  Non-flooded events have all-zero depth readings which
        # bloat files from ~1 MB to ~54 MB.  Consumers that need readings
        # (animation, timeline) only render flooded events anyway.
        if flood_depth > 0:
            event['readings'] = readings

        return event

    def _build_compound_flood_event(self, storm_id: str,
                                     pulse_peaks: list, resp: Dict,
                                     distance_m: float, retention: float,
                                     prop_elevation: float, floor_level: float,
                                     source_gauge_id: str, gaugets: Dict,
                                     nearest_gauge: Dict) -> Dict:
        """Build a flood event using v2.2 per-pulse superposition.

        Replaces _build_flood_event when per-pulse peak data is available.
        Uses gamma-shaped templates per pulse, antecedent saturation,
        linear superposition, and flow-path infiltration.
        """
        g_elev = nearest_gauge['gauge_info']['elevation']
        base_level = resp.get('base_level_m', g_elev)
        sequence_type = resp.get('sequence_type', 'isolated')

        slope = compute_slope(g_elev, prop_elevation, distance_m)

        # Estimate travel time from overall peak
        # Overbank flow begins at bankfull, not severe
        severe_level = nearest_gauge['gauge_info'].get('severe_level', 0)
        bankfull_level = max(0.0, severe_level - BANKFULL_OFFSET_M)
        overall_peak = resp.get('peak_level_m', 0)
        water_above = max(0.0, overall_peak - bankfull_level)
        water_at_prop = water_above * retention
        est_depth = max(0.0, water_at_prop - relative_elevation(
            prop_elevation, g_elev, floor_level))

        if est_depth <= 0:
            travel_time = 0.0
        else:
            travel_time = compute_travel_time(distance_m, est_depth, slope)
            if travel_time == float('inf'):
                travel_time = 0.0

        # Compute superposition cap from gauge severe threshold
        gt = gaugets.get(source_gauge_id, {})
        severe = gt.get('severe_flood_warning', gt.get('severe_warning', 0))
        from config.models import SUPERPOSITION_CAP_FACTOR
        cap = None
        if severe and severe > base_level:
            cap = SUPERPOSITION_CAP_FACTOR * (severe - base_level)

        readings = build_compound_property_hydrograph(
            pulse_peaks=pulse_peaks,
            sequence_type=sequence_type,
            base_level=base_level,
            gauge_elevation=g_elev,
            prop_elevation=prop_elevation,
            floor_level=floor_level,
            travel_time_hrs=travel_time,
            retention=retention,
            severe_level=bankfull_level,
            cap=cap,
        )

        return self._make_event_dict(
            storm_id, overall_peak, readings, travel_time, retention,
            compound=True, num_pulses=len(pulse_peaks),
            sequence_type=sequence_type)

    @staticmethod
    def _depth_to_damage(depth: float) -> float:
        """Delegate to models.floodrisk.depth_damage.scalar_depth_damage."""
        return scalar_depth_damage(depth)
