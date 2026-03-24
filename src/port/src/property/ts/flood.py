# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Flood propagation mixin for PropertyTimeSeriesGenerator."""

import json
from pathlib import Path
from typing import Dict, List, Optional

from models.floodrisk.depth_damage import scalar_depth_damage
from models.floodrisk.spatial import haversine_distance, idw_interpolate_from_gauges
from models.floodrisk.velocity import (
    build_property_hydrograph,
    compute_attenuation,
    compute_slope,
    compute_travel_time,
)

from .constants import N_NEAREST_GAUGES
from .encoder import DateTimeEncoder
from .synthetic import SYNTH_PREFIX, create_synthetic_gauge, create_synthetic_gaugets


class FloodMixin:
    """Mixin providing flood propagation and property processing methods."""

    def _find_nearest_gauges(
        self,
        prop_lat: float,
        prop_lon: float,
        gauge_lookup: Dict,
        gaugets: Optional[Dict] = None,
        gauge_polyline: Optional[List] = None,
        n: int = N_NEAREST_GAUGES,
    ) -> List[Dict]:
        """
        Find the n nearest gauges to a property.

        When *gauge_polyline* is provided, a synthetic gauge is created at
        the nearest point on the river centreline and replaces the most
        distant of the three gauges.  The two flanking real gauges are
        always included.
        """
        synth_result = None
        if gauge_polyline and len(gauge_polyline) >= 2:
            synth_result = create_synthetic_gauge(
                prop_lat, prop_lon, gauge_lookup, gauge_polyline)

        if synth_result is not None:
            synth_gauge, ga_id, gb_id, perp_dist, alpha = synth_result

            # Inject synthetic gauge into gauge_lookup for downstream code
            gauge_lookup[synth_gauge['gauge_id']] = synth_gauge

            # Inject synthetic gaugets if available
            if gaugets is not None:
                synth_gt = create_synthetic_gaugets(
                    alpha, ga_id, gb_id, gaugets)
                gaugets[synth_gauge['gauge_id']] = synth_gt

            # Pick 2 nearest REAL gauges by haversine (same as original
            # approach) — don't force flanking gauges which may be far away.
            # The synthetic gauge replaces the 3rd-most-distant real gauge.
            real_distances = []
            for gid, ginfo in gauge_lookup.items():
                if gid.startswith(SYNTH_PREFIX):
                    continue
                dist = haversine_distance(
                    prop_lat, prop_lon, ginfo['lat'], ginfo['lon'])
                real_distances.append((gid, dist, ginfo))
            real_distances.sort(key=lambda x: x[1])

            result = []
            for gid, dist, ginfo in real_distances[:n - 1]:
                result.append({
                    'gauge_id': gid,
                    'distance_m': dist,
                    'gauge_info': ginfo,
                })

            result.append({
                'gauge_id': synth_gauge['gauge_id'],
                'distance_m': perp_dist,
                'gauge_info': synth_gauge,
                'is_synthetic': True,
                'alpha': alpha,
                'flanking_gauges': [ga_id, gb_id],
            })

            # Sort so closest gauge is first (synthetic will typically be closest)
            result.sort(key=lambda x: x['distance_m'])
            return result

        # Fallback: original haversine 3-nearest approach
        distances = []
        for gid, ginfo in gauge_lookup.items():
            if gid.startswith(SYNTH_PREFIX):
                continue
            dist = haversine_distance(prop_lat, prop_lon, ginfo['lat'], ginfo['lon'])
            distances.append((gid, dist, ginfo))
        distances.sort(key=lambda x: x[1])
        result = []
        for gid, dist, ginfo in distances[:n]:
            result.append({
                'gauge_id': gid,
                'distance_m': dist,
                'gauge_info': ginfo,
            })
        return result

    def _process_property(self, prop: Dict, gauge_lookup: Dict,
                           gaugets: Dict, pts_dir: Path) -> Optional[Dict]:
        """Process a single property: find floods and build hydrographs."""
        ph = prop.get('PropertyHeader', {})
        hdr = ph.get('Header', {})
        loc = ph.get('Location', {})
        risk = loc.get('RiskAssessment', ph.get('RiskAssessment', {}))
        construction = ph.get('Construction', {})
        attrs = ph.get('PropertyAttributes', {})
        ph_risk = ph.get('RiskAssessment', {})

        prop_id = (hdr.get('PropertyID', '')
                   or attrs.get('PropertyID', '')
                   or ph.get('PropertyAttributes', {}).get('PropertyID', ''))
        prop_lat = loc.get('LatitudeDegrees', 0)
        prop_lon = loc.get('LongitudeDegrees', 0)
        prop_elevation = risk.get('GroundLevelMeters', 0)
        floor_level = construction.get('FloorLevelMeters', 0)

        if not prop_id or prop_lat == 0:
            return None

        gauge_polyline = getattr(self, '_gauge_polyline', None)
        nearest = self._find_nearest_gauges(
            prop_lat, prop_lon, gauge_lookup,
            gaugets=gaugets, gauge_polyline=gauge_polyline)
        if not nearest:
            return None

        # Collect storms that exceeded alert at ANY of the nearest gauges.
        # Group by sequence_id — a sequence is the storm event; individual
        # pulses within a sequence are implementation detail.  When multiple
        # pulses from the same sequence hit a gauge, keep the worst response.
        alert_storms = {}  # sequence_id -> {gauge_id: response}
        for ng in nearest:
            gid = ng['gauge_id']
            gt = gaugets.get(gid, {})
            responses = gt.get('storm_responses', {}).get('responses', [])
            for resp in responses:
                if resp.get('exceeded_alert', False):
                    sid = resp.get('storm_id', '')
                    seq_id = self._storm_to_sequence.get(sid, sid)
                    if seq_id not in alert_storms:
                        alert_storms[seq_id] = {}
                    # Keep worst response per gauge within a sequence
                    existing = alert_storms[seq_id].get(gid)
                    if existing is None or resp.get('peak_level_m', 0) > existing.get('peak_level_m', 0):
                        alert_storms[seq_id][gid] = resp

        floods_at_gauge = len(alert_storms)

        flood_events = []
        for storm_id, gauge_responses in alert_storms.items():
            event = self._compute_property_flood(
                storm_id, gauge_responses, nearest,
                prop_lat, prop_lon, prop_elevation, floor_level,
                gaugets
            )
            if event:
                flood_events.append(event)

        floods_at_property = sum(1 for e in flood_events if e.get('flooded'))

        max_depth = max((e['flood_depth_m'] for e in flood_events), default=0.0)
        max_damage = max((e['damage_ratio'] for e in flood_events), default=0.0)

        summary = {
            'property_id': prop_id,
            'elevation_m': round(prop_elevation, 2),
            'floor_level_m': round(floor_level, 2),
            'nearest_gauges': [
                {
                    'gauge_id': ng['gauge_id'],
                    'distance_m': round(ng['distance_m'], 1),
                }
                for ng in nearest
            ],
            'floods_at_nearest_gauge': floods_at_gauge,
            'floods_at_property': floods_at_property,
            'gauge_to_property_ratio': round(
                floods_at_property / floods_at_gauge * 100, 1
            ) if floods_at_gauge > 0 else 0.0,
            'max_depth_m': round(max_depth, 4),
            'max_damage_ratio': round(max_damage, 4),
        }

        prop_file = pts_dir / f'{prop_id}.json'
        prop_data = {
            'property_id': prop_id,
            'location': {
                'lat': prop_lat,
                'lon': prop_lon,
            },
            'elevation_m': round(prop_elevation, 4),
            'floor_level_m': round(floor_level, 4),
            'flood_zone': ph_risk.get('EAFloodZone', 'Zone 1'),
            'property_type': attrs.get('PropertyResi', 'Detached'),
            'construction_year': attrs.get('ConstructionYear', 2000),
            'property_period': attrs.get('PropertyPeriod', '2000-2008'),
            'nearest_gauges': [
                self._nearest_gauge_entry(ng)
                for ng in nearest
            ],
            'flood_events': flood_events,
            'summary': summary,
        }
        with open(prop_file, 'w') as f:
            json.dump(prop_data, f, indent=2, cls=DateTimeEncoder)

        return {'summary': summary}

    def _compute_property_flood(self, storm_id: str, gauge_responses: Dict,
                                 nearest: List[Dict],
                                 prop_lat: float, prop_lon: float,
                                 prop_elevation: float, floor_level: float,
                                 gaugets: Dict) -> Optional[Dict]:
        """
        Compute property-level flood for a single storm.

        Uses IDW from nearest gauges (models.floodrisk.spatial) to
        interpolate WSE at property, applies attenuation, and builds
        hydrograph if flooded.
        """
        gauge_wse_values = []

        for ng in nearest:
            gid = ng['gauge_id']
            dist = ng['distance_m']

            resp = gauge_responses.get(gid)
            if resp is None:
                continue

            gauge_wse = resp.get('peak_level_m', 0)

            if dist < 1.0:
                return self._build_flood_event(
                    storm_id, gauge_wse, 0.0, 1.0,
                    prop_elevation, floor_level,
                    gid, gaugets, ng
                )

            gauge_wse_values.append((dist, gauge_wse))

        if not gauge_wse_values:
            return None

        interpolated_wse = idw_interpolate_from_gauges(gauge_wse_values)

        closest = nearest[0]
        dist = closest['distance_m']
        attenuation = compute_attenuation(dist)

        return self._build_flood_event(
            storm_id, interpolated_wse, dist, attenuation,
            prop_elevation, floor_level,
            closest['gauge_id'], gaugets, closest
        )

    def _build_flood_event(self, storm_id: str, interpolated_wse: float,
                            distance_m: float, attenuation: float,
                            prop_elevation: float, floor_level: float,
                            source_gauge_id: str, gaugets: Dict,
                            nearest_gauge: Dict) -> Dict:
        """Build a complete flood event with hydrograph."""
        g_elev = nearest_gauge['gauge_info']['elevation']

        slope = compute_slope(g_elev, prop_elevation, distance_m)

        # Water height above gauge ground level
        water_above_gauge = max(0.0, interpolated_wse - g_elev)
        # Propagate to property location with distance attenuation
        water_at_property = water_above_gauge * attenuation
        # Property floods when water exceeds the elevation difference + floor step
        height_diff = max(0.0, prop_elevation - g_elev)
        flood_threshold = height_diff + floor_level

        est_depth = max(0.0, water_at_property - flood_threshold)
        if est_depth <= 0:
            travel_time = 0.0
        else:
            travel_time = compute_travel_time(distance_m, est_depth, slope)
            if travel_time == float('inf'):
                travel_time = 0.0

        gt = gaugets.get(source_gauge_id, {})
        gauge_readings = gt.get('flood_simulation', {}).get('readings', [])

        readings = []
        if gauge_readings:
            mapped_readings = []
            for r in gauge_readings:
                mapped_readings.append({
                    'hour': r.get('hour', 0),
                    'water_level_m': r.get('waterLevel', r.get('water_level_m', 0)),
                })
            readings = build_property_hydrograph(
                mapped_readings,
                interpolated_wse,
                travel_time,
                attenuation,
                prop_elevation,
                floor_level,
            )

        arrival_time = None
        peak_time = None
        flood_depth = 0.0
        for r in readings:
            if r['flooded'] and arrival_time is None:
                arrival_time = r['hour']
            if r['depth_m'] > flood_depth:
                flood_depth = r['depth_m']
                peak_time = r['hour']

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
            'attenuation_factor': round(attenuation, 4),
        }

        # Only store 168-hour readings for events that actually flood the
        # property.  Non-flooded events have all-zero depth readings which
        # bloat files from ~1 MB to ~54 MB.  Consumers that need readings
        # (animation, timeline) only render flooded events anyway.
        if flood_depth > 0:
            event['readings'] = readings

        return event

    @staticmethod
    def _nearest_gauge_entry(ng: Dict) -> Dict:
        """Build a nearest_gauge dict for propertyts JSON output."""
        entry = {
            'gauge_id': ng['gauge_id'],
            'distance_m': round(ng['distance_m'], 1),
            'gauge_elevation_m': round(ng['gauge_info']['elevation'], 2),
        }
        if ng.get('is_synthetic'):
            entry['is_synthetic'] = True
            entry['alpha'] = round(ng['alpha'], 6)
            entry['flanking_gauges'] = ng['flanking_gauges']
        return entry

    @staticmethod
    def _depth_to_damage(depth: float) -> float:
        """Delegate to models.floodrisk.depth_damage.scalar_depth_damage."""
        return scalar_depth_damage(depth)
