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

"""Per-property processing, PRS spread, and gauge-basis calculation."""

from typing import Dict, Optional

import numpy as np

from models.floodrisk.depth_damage import is_prs_flood
from models.frequency import (
    annual_exceedance_probability,
    return_period_years,
)

from ..constants import TENORS
from ._basis import gauge_severe_count, nearest_gauge_basis
from ._loss import property_loss_block


class _ProcessMixin:
    """Property processing + PRS spread + gauge basis."""

    def _process_property(self, pdata: Dict, gauge_hazard: Dict,
                          price_prs_func, num_storms: int = 1000,
                          frame=None, lambda_per_year: float = 0.0,
                          freq_config=None, catchment: str = "",
                          loss_draws=None, value_lookup=None,
                          wind_lambda_per_year=None, wind_loss_draws=None,
                          **kwargs) -> Optional[Dict]:
        """Process a single asset's timeseries *pdata*: count severe floods that
        reach it, compute spread and basis.

        Takes the already-loaded per-asset timeseries record (the caller reads it
        through the ``database`` seam); a falsy *pdata* is skipped rather than
        aborting the whole hazard-curve generation."""
        if not pdata:
            return None

        prop_id = pdata['property_id']
        flood_events = pdata.get('flood_events', [])
        prs_floods = [e for e in flood_events if is_prs_flood(e)]
        flood_count = len(prs_floods)

        # Flood-only spread.
        #
        # Previously flood_count / num_storms: a per-STORM conditional with no
        # time dimension, priced as though one storm were one year. The storms
        # of a sequence are one hours-clause event, and an event is what
        # arrives at a rate, so the count is regrouped onto events and then
        # annualised through the frequency layer (MKM-EF-001).
        if frame is not None and lambda_per_year > 0:
            p_event = frame.conditional_probability(
                e.get('storm_id') for e in prs_floods)
            annual_prob = annual_exceedance_probability(lambda_per_year, p_event)
            spread_bps = round(annual_prob * 10000, 2)
            event_flood_count = int(frame.event_flags(
                e.get('storm_id') for e in prs_floods).sum())
        else:
            # No event frame supplied — fall back to the pre-frequency metric
            # in full, so a caller that has not been migrated prices exactly as
            # it did before rather than silently reporting zeros.
            p_event = (flood_count / num_storms) if num_storms > 0 else 0.0
            annual_prob = p_event
            event_flood_count = flood_count
            spread_bps = round(annual_prob * 10000, 2)

        # Stage 6 — peril outcomes. Wind is a pure intersect/union at the
        # property/BRI node (no gauge propagation). Returns None when the
        # catchment has no typhoon damage → flood-only fallback (no prs_perils
        # block, byte-identical output).
        #
        # Suppressed for the dedicated peril scenario modes (win/faw/fow and the
        # BRI-anchored bow/baw): those files already ARE the peril spread (the
        # flood_events were re-stamped by the peril timeseries generator so this
        # very count IS the peril count). Attaching a prs_perils block there
        # would double-count and confuse the basis/waterfall, so the headline
        # spread stands alone.
        if getattr(self, "mode", "normal") in ("win", "faw", "fow", "bow", "baw"):
            wind_info = None
        else:
            wind_info = self._wind_union(
                prop_id, flood_events, num_storms,
                frame=frame, lambda_per_year=lambda_per_year,
                catchment=catchment, wind_lambda_per_year=wind_lambda_per_year)

        # The four peril outcomes (Stage 6). flood_only is the flood spine
        # (unchanged); the others are derived from the 1:1-paired event set.
        prs_perils = None
        if wind_info is not None:
            prs_perils = {
                'flood_only':     {'count': flood_count,               'spread_bps': spread_bps},
                'wind_only':      {'count': wind_info['wind_count'],   'spread_bps': wind_info['wind_spread_bps']},
                'flood_or_wind':  {'count': wind_info['union_count'],  'spread_bps': wind_info['union_spread_bps']},
                'flood_and_wind': {'count': wind_info['joint_count'],  'spread_bps': wind_info['joint_spread_bps']},
            }

        # Term structure is flat — storms are independent. The severe leg is the
        # flood spine; the four peril outcomes (Stage 6) ride alongside it.
        term_structure = {
            'tenors': TENORS,
            'severe': {
                'prs_spread_bps': [spread_bps] * len(TENORS),
            },
        }
        if prs_perils is not None:
            term_structure['perils'] = {
                name: {'prs_spread_bps': [o['spread_bps']] * len(TENORS)}
                for name, o in prs_perils.items()
            }

        # Basis vs the nearest gauges, its summary, and the IDW gauge spread —
        # extracted to ``_basis.py`` to keep this file within the size limit.
        basis = nearest_gauge_basis(
            pdata, gauge_hazard, flood_events, spread_bps, num_storms)
        nearest_basis = basis['nearest_basis']
        avg_basis = basis['avg_basis']
        avg_transmission = basis['avg_transmission']
        idw_gauge_spreads = basis['idw_gauge_spreads']

        flood_depths = [e['flood_depth_m'] for e in flood_events if e.get('flooded', False)]
        summary_data = {
            'avg_basis_bps': round(float(avg_basis), 2),
            'flood_transmission_rate': round(float(avg_transmission), 4),
            'max_depth_m': round(float(max(flood_depths)), 4) if flood_depths else 0.0,
            'mean_depth_m': round(float(np.mean(flood_depths)), 4) if flood_depths else 0.0,
        }

        # Per-storm details for Basis Explorer visualisation
        storm_details = []
        for e in flood_events:
            storm_details.append({
                'storm_id': e.get('storm_id', ''),
                'gauge_peak_m': round(e.get('interpolated_wse_m', 0), 4),
                'flood_depth_m': round(e.get('flood_depth_m', 0), 4),
                'damage_ratio': round(e.get('damage_ratio', 0), 4),
                'flooded': e.get('flooded', False),
                'exceeded_severe': e.get('exceeded_severe', False),
                'retention_factor': round(e.get('retention_factor', 0), 4),
            })

        result = {
            'property_id': prop_id,
            'location': pdata.get('location', {}),
            'elevation_m': pdata.get('elevation_m', 0),
            'floor_level_m': pdata.get('floor_level_m', 0),
            'flood_zone': pdata.get('flood_zone', 'Zone 1'),
            'flood_count': flood_count,
            'has_gev': False,
            'pricing_method': 'event_frequency',
            'gev_params': None,
            'depth_thresholds': {
                'severe': {
                    'threshold_m': 0.0,
                    'annual_probability': round(annual_prob, 8),
                    'return_period_yrs': (
                        round(return_period_years(lambda_per_year or 1.0, p_event), 2)
                        if p_event > 0 else None),
                    'event_flood_count': event_flood_count,
                    'conditional_per_event': round(p_event, 8),
                },
            },
            'term_structure': term_structure,
            'nearest_gauges': nearest_basis,
            'idw_gauge_spreads': idw_gauge_spreads,
            'summary': summary_data,
            'storm_details': storm_details,
        }
        # Stage 6 peril outcomes — only present for catchments whose typhoon
        # stage ran (keeps flood-only output byte-identical).
        if prs_perils is not None:
            result['prs_perils'] = prs_perils

        # Loss-weighted view (MKM-EF-001 Stage 6c/6d, additive). Present only
        # when the frequency layer is active and its config was supplied — i.e.
        # the real generator path — so the unit-test callers that pass a frame
        # but no config, and the pre-frequency fallback, keep byte-identical
        # output. Does not touch the spread. With a value lookup the loss is a
        # currency amount (Stage 6d); without one it is the damage ratio at unit
        # exposure. A missing entry in the lookup means value zero, not
        # unit-exposure, so the whole book stays on one basis.
        if frame is not None and lambda_per_year > 0 and freq_config is not None:
            asset_value = (float(value_lookup.get(prop_id, 0.0))
                           if value_lookup is not None else None)
            result['loss_metrics'] = property_loss_block(
                frame, prs_floods, lambda_per_year, freq_config, prop_id,
                catchment, asset_value=asset_value, draws=loss_draws)
            # Wind peril loss (Stage 6e), on the same footing, when the typhoon
            # stage ran. Priced on the wind arrival rate (Stage 6f); this
            # defaults to the storm event rate, so the numbers are unchanged
            # unless a catchment carries a distinct wind lambda. The draws must
            # match that rate, hence a separate wind draw set rather than the
            # flood one.
            if wind_info is not None:
                w_lambda = (lambda_per_year if wind_lambda_per_year is None
                            else wind_lambda_per_year)
                w_draws = loss_draws if wind_loss_draws is None else wind_loss_draws
                result['loss_metrics_wind'] = property_loss_block(
                    frame, wind_info['wind_loss_records'], w_lambda,
                    freq_config, prop_id, catchment, asset_value=asset_value,
                    draws=w_draws)
        return result

    @staticmethod
    def _get_gauge_severe_count(gauge_hc: Dict, num_storms: int = 0) -> int:
        """Number of severe flood events at a gauge — delegates to ``_basis``.

        Kept as a method because callers (and tests) reach it through the
        generator; the logic lives in ``_basis.gauge_severe_count``.
        """
        return gauge_severe_count(gauge_hc, num_storms)
