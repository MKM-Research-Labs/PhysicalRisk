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

"""Per-property processing, PRS spread, and gauge-basis calculation."""

from typing import Dict, Optional

import numpy as np

from models.floodrisk.depth_damage import is_prs_flood

from ..constants import TENORS


class _ProcessMixin:
    """Property processing + PRS spread + gauge basis."""

    def _process_property(self, pdata: Dict, gauge_hazard: Dict,
                          price_prs_func, num_storms: int = 1000,
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
        flood_count = len([e for e in flood_events if is_prs_flood(e)])

        # Flood-only spread = severe flood count / total scenarios (in bp).
        # Kept unchanged: it drives the gauge basis and the spread
        # decomposition, which stay flood-vs-gauge until Stage 6.
        spread_bps = round((flood_count / num_storms) * 10000, 2) if num_storms > 0 else 0.0

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
            wind_info = self._wind_union(prop_id, flood_events, num_storms)

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

        # Compute basis vs nearest gauges
        nearest_gauges_data = pdata.get('nearest_gauges', [])
        nearest_basis = []
        for ng in nearest_gauges_data:
            gid = ng['gauge_id']
            gauge_hc = gauge_hazard.get(gid)
            if not gauge_hc:
                continue

            # Gauge severe count from GEV probability in gaugehc
            gauge_severe_count = self._get_gauge_severe_count(gauge_hc, num_storms)
            # Count property floods that came from severe gauge events
            # (not alert-only) — this is the hedged subset
            severe_and_flooded = sum(1 for e in flood_events if is_prs_flood(e))
            gauge_flood_count = gauge_severe_count
            # Transmission rate: fraction of severe gauge events that reach
            # the property.  By definition <= 1 (gauge is on the river).
            transmission_rate = (
                severe_and_flooded / gauge_flood_count
                if gauge_flood_count > 0 else 0.0
            )

            gauge_spread_bps = round((gauge_severe_count / num_storms) * 10000, 2) if num_storms > 0 else 0.0

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

        from models.audit import log_model_usage
        audit_params = {
            "property_id": prop_id,
            "flood_count": flood_count,
            "num_storms": num_storms,
            "spread_bps": spread_bps,
        }
        if wind_info is not None:
            audit_params["wind_count"] = wind_info["wind_count"]
            audit_params["union_count"] = wind_info["union_count"]
            audit_params["joint_count"] = wind_info["joint_count"]
            audit_params["union_spread_bps"] = wind_info["union_spread_bps"]
            audit_params["joint_spread_bps"] = wind_info["joint_spread_bps"]
        log_model_usage("prs", "prs_spread", parameters=audit_params,
                        context="Property PRS spread (event count)")

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
            'storm_details': storm_details,
        }
        # Stage 6 peril outcomes — only present for catchments whose typhoon
        # stage ran (keeps flood-only output byte-identical).
        if prs_perils is not None:
            result['prs_perils'] = prs_perils
        return result

    @staticmethod
    def _get_gauge_severe_count(gauge_hc: Dict, num_storms: int = 0) -> int:
        """Get the number of severe flood events from a gauge.

        Uses the GEV-calibrated annual_flood_prob_severe from gaugehc,
        converted to a count via num_storms.  Falls back to the
        sequence_gauge enriched severe_event_count if GEV is unavailable.
        """
        prob = gauge_hc.get('annual_flood_prob_severe', 0)
        if prob > 0 and num_storms > 0:
            return round(prob * num_storms)
        return gauge_hc.get('severe_event_count', 0)
