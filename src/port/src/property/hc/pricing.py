# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Property pricing and basis calculation mixin for PropertyHazardCurveGenerator.

v3.0: Replaced GEV/CDS pricing with simple severe event count.
Spread (bp) = N(severe floods) / N(total scenarios) × 10,000.
Term structure is flat (storms are independent).
"""

import json
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

from .constants import TENORS


class PricingMixin:
    """Mixin providing property processing, PRS pricing, and basis methods."""

    def _process_property(self, prop_file: Path, gauge_hazard: Dict,
                          price_prs_func, num_storms: int = 1000,
                          **kwargs) -> Optional[Dict]:
        """Process a single property: count severe floods, compute spread and basis."""
        with open(prop_file, 'r') as f:
            pdata = json.load(f)

        prop_id = pdata['property_id']
        flood_events = pdata.get('flood_events', [])
        flood_count = len([e for e in flood_events if e.get('flooded', False)])

        # Spread = severe flood count / total scenarios (in bp)
        spread_bps = round((flood_count / num_storms) * 10000, 2) if num_storms > 0 else 0.0

        # Term structure is flat — storms are independent
        term_structure = {
            'tenors': TENORS,
            'severe': {
                'prs_spread_bps': [spread_bps] * len(TENORS),
            },
        }

        # Compute basis vs nearest gauges
        nearest_gauges_data = pdata.get('nearest_gauges', [])
        nearest_basis = []
        for ng in nearest_gauges_data:
            gid = ng['gauge_id']
            gauge_hc = gauge_hazard.get(gid)
            if not gauge_hc:
                continue

            gauge_flood_count = len(flood_events)  # storms processed at gauge
            transmission_rate = (
                flood_count / gauge_flood_count
                if gauge_flood_count > 0 else 0.0
            )

            # Gauge spread from its severe event count
            gauge_severe_count = self._get_gauge_severe_count(gauge_hc)
            gauge_spread_bps = round((gauge_severe_count / num_storms) * 10000, 2) if num_storms > 0 else 0.0

            basis_at_tenors = [round(gauge_spread_bps - spread_bps, 2)] * len(TENORS)
            basis_bps = {
                'severe': {
                    'tenors': TENORS,
                    'values': basis_at_tenors,
                },
            }

            nearest_basis.append({
                'gauge_id': gid,
                'distance_km': round(ng.get('distance_m', 0) / 1000, 2),
                'gauge_elevation_m': round(ng.get('gauge_elevation_m', 0), 2),
                'gauge_flood_count': gauge_flood_count,
                'property_flood_count': flood_count,
                'event_basis': gauge_flood_count - flood_count,
                'flood_transmission_rate': round(transmission_rate, 4),
                'basis_bps': basis_bps,
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

        from models.audit import log_model_usage
        log_model_usage("prs", "prs_spread", parameters={
            "property_id": prop_id,
            "flood_count": flood_count,
            "num_storms": num_storms,
            "spread_bps": spread_bps,
        }, context="Property PRS spread (event count)")

        flood_depths = [e['flood_depth_m'] for e in flood_events if e.get('flooded', False)]
        summary_data = {
            'avg_basis_bps': round(float(avg_basis), 2),
            'flood_transmission_rate': round(float(avg_transmission), 4),
            'max_depth_m': round(float(max(flood_depths)), 4) if flood_depths else 0.0,
            'mean_depth_m': round(float(np.mean(flood_depths)), 4) if flood_depths else 0.0,
        }

        return {
            'property_id': prop_id,
            'location': pdata.get('location', {}),
            'elevation_m': pdata.get('elevation_m', 0),
            'floor_level_m': pdata.get('floor_level_m', 0),
            'flood_zone': pdata.get('flood_zone', 'Zone 1'),
            'flood_count': flood_count,
            'has_gev': False,
            'pricing_method': 'event_count',
            'gev_params': None,
            'depth_thresholds': {
                'severe': {
                    'threshold_m': 0.0,
                    'annual_probability': round(flood_count / num_storms, 8) if num_storms > 0 else 0,
                    'return_period_yrs': round(num_storms / flood_count, 2) if flood_count > 0 else None,
                },
            },
            'term_structure': term_structure,
            'nearest_gauges': nearest_basis,
            'idw_gauge_spreads': idw_gauge_spreads,
            'summary': summary_data,
        }

    @staticmethod
    def _get_gauge_severe_count(gauge_hc: Dict) -> int:
        """Get the number of severe flood events from a gauge hazard curve."""
        # gaugehc stores annual_flood_prob_severe and num_storms_simulated
        prob = gauge_hc.get('annual_flood_prob_severe', 0)
        n_storms = gauge_hc.get('num_storms_simulated', 20000)
        return round(prob * n_storms)
