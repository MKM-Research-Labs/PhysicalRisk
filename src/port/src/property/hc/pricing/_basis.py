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

"""Gauge-basis computation for the property/commercial pricing leg.

Split out of ``_process.py`` (which had grown past the 300-line limit): the
basis against the nearest gauges, the summary it rolls up to, and the
inverse-distance-weighted gauge spread. Pure extraction — the arithmetic is
unchanged from when it lived inline.
"""

from typing import Dict, List

import numpy as np

from models.floodrisk.depth_damage import is_prs_flood

from ..constants import TENORS


def gauge_severe_count(gauge_hc: Dict, num_storms: int = 0) -> int:
    """Get the number of severe flood events from a gauge.

    Prefers the raw catalogue count written by the hazard builder. That count
    and the property's flood-event count are both plain tallies over the same
    event catalogue, so the transmission rate formed from them is a genuine
    ratio.

    The older path — annual probability x scenario count — is retained only for
    curves predating the frequency layer. It cannot be used once the probability
    is annualised: multiplying an annual probability by an event count mixes
    bases and produced transmission rates near 200%, where the quantity is
    bounded by 1 by construction.
    """
    raw = gauge_hc.get('severe_event_count')
    if raw:
        return raw
    prob = gauge_hc.get('annual_flood_prob_severe', 0)
    if prob > 0 and num_storms > 0:
        return round(prob * num_storms)
    return 0


def nearest_gauge_basis(
    pdata: Dict,
    gauge_hazard: Dict,
    flood_events: List[Dict],
    spread_bps: float,
    num_storms: int,
) -> Dict:
    """Compute the basis of a property spread against its nearest gauges.

    Args:
        pdata: the asset timeseries record; its ``nearest_gauges`` drive the loop.
        gauge_hazard: gauge identifier to that gauge's hazard-curve dict.
        flood_events: the asset's flood events, for the property-side count.
        spread_bps: the asset's own PRS spread, the reference the basis is to.
        num_storms: denominator for a pre-frequency gauge count fallback.

    Returns:
        ``nearest_basis`` (per-gauge basis rows), the primary ``avg_basis`` and
        ``avg_transmission`` summary, and the IDW-blended ``idw_gauge_spreads``.
    """
    nearest_gauges_data = pdata.get('nearest_gauges', [])
    nearest_basis = []
    for ng in nearest_gauges_data:
        gid = ng['gauge_id']
        gauge_hc = gauge_hazard.get(gid)
        if not gauge_hc:
            continue

        # Gauge severe count, for the event-basis display. The gauge's own
        # annual probability now comes from the frequency layer, so the
        # count is expressed over events rather than storms.
        severe_count = gauge_severe_count(
            gauge_hc, gauge_hc.get('num_events_simulated') or num_storms)
        # Count property floods that came from severe gauge events
        # (not alert-only) — this is the hedged subset
        severe_and_flooded = sum(1 for e in flood_events if is_prs_flood(e))
        gauge_flood_count = severe_count
        # Transmission rate: fraction of severe gauge events that reach
        # the property.  By definition <= 1 (gauge is on the river).
        transmission_rate = (
            severe_and_flooded / gauge_flood_count
            if gauge_flood_count > 0 else 0.0
        )

        # The gauge leg is already annualised in gaugehc; use it directly
        # rather than re-deriving a ratio, so both sides of the basis are
        # on the same footing.
        gauge_annual = gauge_hc.get('annual_flood_prob_severe')
        if gauge_annual is None:
            gauge_annual = (severe_count / num_storms) if num_storms > 0 else 0.0
        gauge_spread_bps = round(gauge_annual * 10000, 2)

        basis_at_tenors = [round(gauge_spread_bps - spread_bps, 2)] * len(TENORS)
        basis_bps = {
            'severe': {
                'tenors': TENORS,
                'values': basis_at_tenors,
            },
        }

        # Gauge threshold levels for visualisation
        gauge_thresholds = {}
        g_info = ng.get('gauge_info') or {}
        if g_info:
            gauge_thresholds = {
                'alert_level': round(g_info.get('alert_level', 0), 2),
                'warning_level': round(g_info.get('warning_level', 0), 2),
                'severe_level': round(g_info.get('severe_level', 0), 2),
            }

        nearest_basis.append({
            'gauge_id': gid,
            'distance_km': round(ng.get('distance_m', 0) / 1000, 2),
            'gauge_elevation_m': round(ng.get('gauge_elevation_m', 0), 2),
            'gauge_flood_count': gauge_flood_count,
            'property_flood_count': severe_and_flooded,
            'event_basis': gauge_flood_count - severe_and_flooded,
            'flood_transmission_rate': round(transmission_rate, 4),
            'basis_bps': basis_bps,
            'gauge_thresholds': gauge_thresholds,
        })

    # Summary — use synthetic gauge basis as primary
    avg_basis = 0.0
    avg_transmission = 0.0
    if nearest_basis:
        synth_nb = next(
            (nb for nb in nearest_basis if nb['gauge_id'].startswith('SYNTH-')),
            None
        )
        if synth_nb:
            severe_basis = synth_nb['basis_bps'].get('severe', {}).get('values', [])
            avg_basis = severe_basis[0] if severe_basis else 0.0
            avg_transmission = synth_nb.get('flood_transmission_rate', 0.0)
        else:
            bases = [nb['basis_bps'].get('severe', {}).get('values', [0])[0]
                     for nb in nearest_basis]
            avg_basis = np.mean(bases) if bases else 0.0
            avg_transmission = np.mean([nb['flood_transmission_rate']
                                        for nb in nearest_basis])

    # Gauge spread: use synthetic gauge directly when present
    idw_gauge_spreads = {}
    synth_basis = next(
        (nb for nb in nearest_basis if nb['gauge_id'].startswith('SYNTH-')),
        None
    ) if nearest_basis else None

    if synth_basis:
        synth_spreads = []
        for j in range(len(TENORS)):
            basis_v = synth_basis['basis_bps'].get('severe', {}).get('values', [])
            b = basis_v[j] if j < len(basis_v) else 0
            synth_spreads.append(round(spread_bps + b, 2))
        idw_gauge_spreads['severe'] = synth_spreads
    elif nearest_basis:
        distances = [nb.get('distance_km', 1.0) for nb in nearest_basis]
        weights = [1.0 / max(d, 0.1) for d in distances]
        w_total = sum(weights)
        weights = [w / w_total for w in weights]
        weighted_spreads = []
        for j in range(len(TENORS)):
            gs = 0.0
            for k, nb in enumerate(nearest_basis):
                basis_v = nb['basis_bps'].get('severe', {}).get('values', [])
                b = basis_v[j] if j < len(basis_v) else 0
                gs += weights[k] * (spread_bps + b)
            weighted_spreads.append(round(gs, 2))
        idw_gauge_spreads['severe'] = weighted_spreads

    return {
        'nearest_basis': nearest_basis,
        'avg_basis': avg_basis,
        'avg_transmission': avg_transmission,
        'idw_gauge_spreads': idw_gauge_spreads,
    }
