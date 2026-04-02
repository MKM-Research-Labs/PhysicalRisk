# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Property pricing and basis calculation mixin for PropertyHazardCurveGenerator."""

import json
import math
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

from .constants import (
    DEPTH_THRESHOLDS,
    MIN_ANNUAL_PROBABILITY,
    MIN_EVENTS_FOR_GEV,
    MIN_PRS_SPREAD_BPS,
    RECOVERY_RATES,
    TENORS,
    compute_prs_spread,
)


class PricingMixin:
    """Mixin providing property processing, PRS pricing, and basis methods."""

    def _process_property(self, prop_file: Path, gauge_hazard: Dict,
                          price_prs_func, num_storms: int = 1000,
                          **kwargs) -> Optional[Dict]:
        """Process a single property: fit GEV (or use floor), compute PRS, calculate basis."""
        with open(prop_file, 'r') as f:
            pdata = json.load(f)

        prop_id = pdata['property_id']
        flood_events = pdata.get('flood_events', [])
        flood_depths = [e['flood_depth_m'] for e in flood_events if e.get('flooded', False)]

        has_gev = False
        gev_params = None
        shape, loc, scale = None, None, None

        if len(flood_depths) >= MIN_EVENTS_FOR_GEV:
            depths_arr = np.array(flood_depths)
            try:
                shape, loc, scale = self.gev_fitter.fit(depths_arr)
                has_gev = True
                gev_params = {
                    'shape': round(float(shape), 8),
                    'loc': round(float(loc), 8),
                    'scale': round(float(scale), 8),
                }
                from models.audit import log_model_usage
                log_model_usage("gev", "gev_fit", parameters={
                    "property_id": prop_id,
                    "flood_count": len(flood_depths),
                    "shape": round(float(shape), 6),
                    "loc": round(float(loc), 6),
                    "scale": round(float(scale), 6),
                }, context="Property hazard curve GEV fit")
            except Exception:
                pass  # Fall through to floor pricing

        # Base rate: fraction of all storms that cause property flooding
        base_rate = len(flood_depths) / num_storms if flood_depths else 0.0

        # Minimum annual probability from floor spread
        min_annual_prob = MIN_PRS_SPREAD_BPS / 10000

        # Compute exceedance probabilities at each threshold
        depth_thresholds = {}
        for name, threshold in DEPTH_THRESHOLDS.items():
            if has_gev:
                cond_exceedance = self.gev_fitter.exceedance_probability(
                    threshold, shape, loc, scale
                )
                cond_exceedance = max(0.0, min(1.0, cond_exceedance))
                annual_prob = base_rate * cond_exceedance
                annual_prob = max(0.0, min(1.0, annual_prob))
                if 0 < annual_prob < MIN_ANNUAL_PROBABILITY:
                    annual_prob = MIN_ANNUAL_PROBABILITY
            else:
                annual_prob = min_annual_prob

            annual_prob = max(annual_prob, min_annual_prob)
            return_period = 1.0 / annual_prob if annual_prob > 0 else float('inf')
            depth_thresholds[name] = {
                'threshold_m': threshold,
                'annual_probability': round(annual_prob, 8),
                'return_period_yrs': round(return_period, 2) if return_period != float('inf') else None,
                'capped': bool(annual_prob == MIN_ANNUAL_PROBABILITY),
            }

        # Compute term structure and PRS pricing for each threshold
        term_structure = {'tenors': TENORS}
        for name, threshold_info in depth_thresholds.items():
            annual_prob = threshold_info['annual_probability']
            if annual_prob <= 0:
                term_structure[name] = {
                    'survival': [1.0] * len(TENORS),
                    'prs_spread_bps': [0.0] * len(TENORS),
                }
                continue

            recovery = RECOVERY_RATES.get(name, 0.0)
            survival = []
            prs_spreads = []
            for tenor in TENORS:
                s = math.exp(-annual_prob * tenor)
                survival.append(round(s, 8))
                spread_bps = self._compute_prs_spread(
                    annual_prob, tenor, price_prs_func, recovery
                )
                prs_spreads.append(round(spread_bps, 2))

            term_structure[name] = {
                'survival': survival,
                'prs_spread_bps': prs_spreads,
            }

        # Compute basis vs nearest gauges
        nearest_gauges_data = pdata.get('nearest_gauges', [])
        nearest_basis = []
        for ng in nearest_gauges_data:
            gid = ng['gauge_id']
            gauge_hc = gauge_hazard.get(gid)
            if not gauge_hc:
                continue

            property_flood_count = len(flood_depths)
            prop_summary = pdata.get('summary', {})
            gauge_flood_count = prop_summary.get('floods_at_nearest_gauge', len(flood_events))

            transmission_rate = (
                property_flood_count / gauge_flood_count
                if gauge_flood_count > 0 else 0.0
            )

            basis_bps = {}
            for name in DEPTH_THRESHOLDS:
                prop_spreads = term_structure[name]['prs_spread_bps']
                gauge_trigger = self._map_threshold_to_gauge_trigger(name)
                gauge_spreads = self._get_gauge_prs_spreads(
                    gauge_hc, gauge_trigger, price_prs_func
                )
                basis_at_tenors = []
                for j, tenor in enumerate(TENORS):
                    g_spread = gauge_spreads[j] if j < len(gauge_spreads) else 0.0
                    p_spread = prop_spreads[j] if j < len(prop_spreads) else 0.0
                    basis_at_tenors.append(round(g_spread - p_spread, 2))
                basis_bps[name] = {
                    'tenors': TENORS,
                    'values': basis_at_tenors,
                }

            nearest_basis.append({
                'gauge_id': gid,
                'distance_km': round(ng.get('distance_m', 0) / 1000, 2),
                'gauge_elevation_m': round(ng.get('gauge_elevation_m', 0), 2),
                'gauge_flood_count': gauge_flood_count,
                'property_flood_count': property_flood_count,
                'event_basis': gauge_flood_count - property_flood_count,
                'flood_transmission_rate': round(transmission_rate, 4),
                'basis_bps': basis_bps,
            })

        # Summary
        avg_basis = 0.0
        if nearest_basis:
            five_yr_bases = []
            for nb in nearest_basis:
                any_flood_basis = nb['basis_bps'].get('any_flood', {}).get('values', [])
                if len(any_flood_basis) > 4:
                    five_yr_bases.append(any_flood_basis[4])
            avg_basis = np.mean(five_yr_bases) if five_yr_bases else 0.0

        avg_transmission = 0.0
        if nearest_basis:
            avg_transmission = np.mean([nb['flood_transmission_rate'] for nb in nearest_basis])

        # IDW-weighted gauge spread
        idw_gauge_spreads = {}
        if nearest_basis:
            distances = [nb.get('distance_km', 1.0) for nb in nearest_basis]
            weights = [1.0 / max(d, 0.1) for d in distances]
            w_total = sum(weights)
            weights = [w / w_total for w in weights]

            for name in DEPTH_THRESHOLDS:
                weighted_spreads = []
                for j in range(len(TENORS)):
                    gs = 0.0
                    for k, nb in enumerate(nearest_basis):
                        prop_s = term_structure[name]['prs_spread_bps'][j] if j < len(term_structure[name]['prs_spread_bps']) else 0
                        basis_v = nb['basis_bps'].get(name, {}).get('values', [])
                        b = basis_v[j] if j < len(basis_v) else 0
                        gs += weights[k] * (prop_s + b)
                    weighted_spreads.append(round(gs, 2))
                idw_gauge_spreads[name] = weighted_spreads

        pricing_method = 'gev' if has_gev else 'floor'

        from models.audit import log_model_usage
        five_yr_spread = term_structure.get('any_flood', {}).get('prs_spread_bps', [0]*5)
        log_model_usage("prs", "prs_spread", parameters={
            "property_id": prop_id,
            "pricing_method": pricing_method,
            "flood_count": len(flood_depths),
            "spread_5yr_any_bps": five_yr_spread[4] if len(five_yr_spread) > 4 else 0,
            "base_rate": round(base_rate, 6),
        }, context="Property PRS spread calculation")

        summary_data = {
            'avg_basis_bps': round(float(avg_basis), 2),
            'flood_transmission_rate': round(float(avg_transmission), 4),
        }
        if flood_depths:
            summary_data['max_depth_m'] = round(float(max(flood_depths)), 4)
            summary_data['mean_depth_m'] = round(float(np.mean(flood_depths)), 4)
        else:
            summary_data['max_depth_m'] = 0.0
            summary_data['mean_depth_m'] = 0.0

        return {
            'property_id': prop_id,
            'location': pdata.get('location', {}),
            'elevation_m': pdata.get('elevation_m', 0),
            'floor_level_m': pdata.get('floor_level_m', 0),
            'flood_zone': pdata.get('flood_zone', 'Zone 1'),
            'flood_count': len(flood_depths),
            'has_gev': has_gev,
            'pricing_method': pricing_method,
            'min_spread_bps': MIN_PRS_SPREAD_BPS,
            'gev_params': gev_params,
            'depth_thresholds': depth_thresholds,
            'term_structure': term_structure,
            'nearest_gauges': nearest_basis,
            'idw_gauge_spreads': idw_gauge_spreads,
            'summary': summary_data,
        }

    def _compute_prs_spread(self, annual_hazard_rate: float, tenor: int,
                            price_prs_func, recovery: float = 0.0) -> float:
        """Delegate to models.hazard.prs_analytical.compute_prs_spread."""
        return compute_prs_spread(
            annual_hazard_rate=annual_hazard_rate,
            tenor=tenor,
            recovery=recovery,
        )

    def _map_threshold_to_gauge_trigger(self, threshold_name: str) -> str:
        """Map property depth threshold to gauge trigger level."""
        mapping = {
            'any_flood': 'alert',
            'moderate': 'warning',
            'severe': 'severe',
        }
        return mapping.get(threshold_name, 'warning')

    def _get_gauge_prs_spreads(self, gauge_hc: Dict, trigger: str,
                               price_prs_func) -> List[float]:
        """Get gauge PRS spreads at each tenor for a given trigger level."""
        hazard_rate_key = f'annual_hazard_rate_{trigger}'
        annual_rate = gauge_hc.get(hazard_rate_key, 0)

        if annual_rate <= 0:
            return [0.0] * len(TENORS)

        spreads = []
        for tenor in TENORS:
            spread = self._compute_prs_spread(annual_rate, tenor, price_prs_func)
            spreads.append(round(spread, 2))

        return spreads
