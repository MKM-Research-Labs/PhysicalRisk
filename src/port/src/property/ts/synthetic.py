# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""
Synthetic gauge creation for property PRS pricing.

Creates a virtual gauge at the nearest point on the river centreline
to a property, interpolating properties from the two flanking real
gauges.  This replaces the most-distant third gauge in the traditional
3-nearest-gauge approach and provides a distance metric consistent
with the location generator's perpendicular "distance from river".
"""

import logging
from typing import Dict, List, Optional, Tuple

from models.floodrisk.spatial import (
    haversine_distance,
    nearest_point_on_polyline,
)

logger = logging.getLogger(__name__)

SYNTH_PREFIX = "SYNTH"


def create_synthetic_gauge(
    prop_lat: float,
    prop_lon: float,
    gauge_lookup: Dict,
    gauge_polyline: List[Tuple],
) -> Optional[Tuple[Dict, str, str, float, float]]:
    """
    Create a synthetic gauge at the nearest river point to the property.

    Args:
        prop_lat, prop_lon: Property coordinates (degrees).
        gauge_lookup: Dict keyed by gauge_id with lat, lon, elevation,
            alert_level, warning_level, severe_level.
        gauge_polyline: Ordered list of (lat, lon, elevation, gauge_id)
            tuples representing the river centreline.

    Returns:
        Tuple of (synth_gauge_dict, gauge_a_id, gauge_b_id, perp_dist_m, alpha)
        or None if the polyline has fewer than 2 points or the property
        projects onto a polyline endpoint (no true interpolation possible).
    """
    if not gauge_polyline or len(gauge_polyline) < 2:
        return None

    nx, ny, dist_m, seg_idx, t = nearest_point_on_polyline(
        prop_lat, prop_lon, gauge_polyline
    )

    # If the projection clamps to the very start or end of the polyline,
    # the synthetic gauge degenerates to a single real gauge — fall back.
    if seg_idx == 0 and t < 1e-6:
        return None
    if seg_idx == len(gauge_polyline) - 2 and t > 1 - 1e-6:
        return None

    pt_a = gauge_polyline[seg_idx]
    pt_b = gauge_polyline[seg_idx + 1]
    gauge_a_id = pt_a[3]
    gauge_b_id = pt_b[3]

    ga = gauge_lookup.get(gauge_a_id)
    gb = gauge_lookup.get(gauge_b_id)
    if ga is None or gb is None:
        return None

    alpha = t  # 0 = at gauge A, 1 = at gauge B

    synth_id = f"{SYNTH_PREFIX}-{gauge_a_id[-8:]}-{gauge_b_id[-8:]}"

    synth = {
        'gauge_id': synth_id,
        'lat': nx,
        'lon': ny,
        'elevation': _lerp(ga['elevation'], gb['elevation'], alpha),
        'alert_level': _lerp(ga['alert_level'], gb['alert_level'], alpha),
        'warning_level': _lerp(ga['warning_level'], gb['warning_level'], alpha),
        'severe_level': _lerp(ga['severe_level'], gb['severe_level'], alpha),
    }

    return synth, gauge_a_id, gauge_b_id, dist_m, alpha


def create_synthetic_gaugets(
    alpha: float,
    gauge_a_id: str,
    gauge_b_id: str,
    gaugets: Dict,
) -> Dict:
    """
    Interpolate gaugets (storm responses + flood simulation) for a
    synthetic gauge from two flanking gauges.

    Args:
        alpha: Interpolation weight (0 = gauge A, 1 = gauge B).
        gauge_a_id, gauge_b_id: Flanking gauge IDs.
        gaugets: Full gaugets dict keyed by gauge_id.

    Returns:
        A gaugets-format dict for the synthetic gauge.
    """
    gt_a = gaugets.get(gauge_a_id, {})
    gt_b = gaugets.get(gauge_b_id, {})

    # --- Storm responses ---
    resps_a = {r['storm_id']: r
               for r in gt_a.get('storm_responses', {}).get('responses', [])}
    resps_b = {r['storm_id']: r
               for r in gt_b.get('storm_responses', {}).get('responses', [])}

    all_storm_ids = set(resps_a) | set(resps_b)
    synth_responses = []
    for sid in sorted(all_storm_ids):
        ra = resps_a.get(sid)
        rb = resps_b.get(sid)
        if ra and rb:
            peak = _lerp(ra['peak_level_m'], rb['peak_level_m'], alpha)
            exceeded = ra.get('exceeded_alert', False) or rb.get('exceeded_alert', False)
        elif ra:
            peak = ra['peak_level_m']
            exceeded = ra.get('exceeded_alert', False)
        else:
            peak = rb['peak_level_m']
            exceeded = rb.get('exceeded_alert', False)

        synth_responses.append({
            'storm_id': sid,
            'peak_level_m': round(peak, 4),
            'exceeded_alert': exceeded,
        })

    # --- Flood simulation readings ---
    readings_a = gt_a.get('flood_simulation', {}).get('readings', [])
    readings_b = gt_b.get('flood_simulation', {}).get('readings', [])

    synth_readings = _interpolate_readings(readings_a, readings_b, alpha)

    return {
        'storm_responses': {'responses': synth_responses},
        'flood_simulation': {'readings': synth_readings},
    }


def create_synthetic_hazard_curve(
    alpha: float,
    gauge_a_hc: Dict,
    gauge_b_hc: Dict,
) -> Dict:
    """
    Create a composite hazard curve by weighted average of two gauge
    hazard curves.

    Args:
        alpha: Interpolation weight (0 = gauge A, 1 = gauge B).
        gauge_a_hc, gauge_b_hc: Gauge hazard curve dicts from gaugehc.json.

    Returns:
        A gaugehc-format dict for the synthetic gauge.
    """
    result = {}

    # Scalar fields: weighted average
    for key in ('annual_hazard_rate_alert', 'annual_hazard_rate_warning',
                'annual_hazard_rate_severe', 'annual_flood_prob_alert',
                'annual_flood_prob_warning', 'annual_flood_prob_severe',
                'elevation_m', 'gev_location', 'gev_scale', 'gev_shape'):
        va = gauge_a_hc.get(key)
        vb = gauge_b_hc.get(key)
        if va is not None and vb is not None:
            result[key] = round(_lerp(va, vb, alpha), 6)
        elif va is not None:
            result[key] = va
        elif vb is not None:
            result[key] = vb

    # Lat/lon: interpolate
    result['latitude'] = _lerp(
        gauge_a_hc.get('latitude', 0), gauge_b_hc.get('latitude', 0), alpha)
    result['longitude'] = _lerp(
        gauge_a_hc.get('longitude', 0), gauge_b_hc.get('longitude', 0), alpha)

    # Term structures: interpolate survival/probability year by year
    for ts_key in ('term_structure_alert', 'term_structure_warning',
                   'term_structure_severe'):
        ts_a = gauge_a_hc.get(ts_key, [])
        ts_b = gauge_b_hc.get(ts_key, [])
        result[ts_key] = _interpolate_term_structure(ts_a, ts_b, alpha)

    # Curve points: interpolate probabilities at matching thresholds
    cp_a = gauge_a_hc.get('curve_points', [])
    cp_b = gauge_b_hc.get('curve_points', [])
    result['curve_points'] = _interpolate_curve_points(cp_a, cp_b, alpha)

    return result


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation: a*(1-t) + b*t."""
    return a * (1 - t) + b * t


def _interpolate_readings(
    readings_a: List[Dict],
    readings_b: List[Dict],
    alpha: float,
) -> List[Dict]:
    """Interpolate flood simulation readings hour-by-hour."""
    if not readings_a and not readings_b:
        return []
    if not readings_a:
        return readings_b
    if not readings_b:
        return readings_a

    map_a = {r.get('hour', r.get('Hour', 0)): r for r in readings_a}
    map_b = {r.get('hour', r.get('Hour', 0)): r for r in readings_b}

    all_hours = sorted(set(map_a) | set(map_b))
    result = []
    for h in all_hours:
        ra = map_a.get(h)
        rb = map_b.get(h)
        wl_a = _get_water_level(ra) if ra else 0.0
        wl_b = _get_water_level(rb) if rb else 0.0
        result.append({
            'hour': h,
            'waterLevel': round(_lerp(wl_a, wl_b, alpha), 4),
        })
    return result


def _get_water_level(reading: Dict) -> float:
    """Extract water level from a reading dict (handles key variants)."""
    return reading.get('waterLevel',
                       reading.get('water_level_m',
                                   reading.get('WaterLevel', 0.0)))


def _interpolate_term_structure(
    ts_a: List[Dict],
    ts_b: List[Dict],
    alpha: float,
) -> List[Dict]:
    """Interpolate term structure points year-by-year."""
    if not ts_a and not ts_b:
        return []
    if not ts_a:
        return ts_b
    if not ts_b:
        return ts_a

    map_a = {p['year']: p for p in ts_a}
    map_b = {p['year']: p for p in ts_b}
    all_years = sorted(set(map_a) | set(map_b))

    result = []
    for yr in all_years:
        pa = map_a.get(yr, {})
        pb = map_b.get(yr, {})
        point = {'year': yr}
        for field in ('expected_floods', 'prob_at_least_one',
                      'survival_prob', 'cumulative_default_prob'):
            va = pa.get(field)
            vb = pb.get(field)
            if va is not None and vb is not None:
                point[field] = round(_lerp(va, vb, alpha), 6)
            elif va is not None:
                point[field] = va
            elif vb is not None:
                point[field] = vb
        result.append(point)
    return result


def _interpolate_curve_points(
    cp_a: List[Dict],
    cp_b: List[Dict],
    alpha: float,
) -> List[Dict]:
    """Interpolate hazard curve points at matching thresholds."""
    if not cp_a and not cp_b:
        return []
    if not cp_a:
        return cp_b
    if not cp_b:
        return cp_a

    map_a = {round(p['threshold_m'], 4): p for p in cp_a}
    map_b = {round(p['threshold_m'], 4): p for p in cp_b}
    all_thresholds = sorted(set(map_a) | set(map_b))

    result = []
    for th in all_thresholds:
        pa = map_a.get(th, {})
        pb = map_b.get(th, {})
        prob_a = pa.get('annual_exceedance_prob', 0)
        prob_b = pb.get('annual_exceedance_prob', 0)
        prob = _lerp(prob_a, prob_b, alpha)
        rp = 1.0 / prob if prob > 0 else 9999.0
        result.append({
            'threshold_m': th,
            'annual_exceedance_prob': round(prob, 6),
            'return_period_years': round(rp, 2),
        })
    return result
