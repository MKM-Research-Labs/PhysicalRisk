# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Property pricing and basis calculation mixin for PropertyHazardCurveGenerator.

v3.0: Replaced GEV/CDS pricing with simple severe event count.
Spread (bp) = N(severe floods) / N(total scenarios) × 10,000.
Term structure is flat (storms are independent).

Stage 6 (peril outcomes): the pricer emits a ``prs_perils`` block with all
four peril outcomes at the property/BRI node (coupling_spec.md §11.6):

* ``flood_only``    — severe flood triggers (the flood spine, unchanged)
* ``wind_only``     — binary ``is_prs_wind`` damage-onset triggers
* ``flood_or_wind`` — union over the 1:1-paired event set (one denominator)
* ``flood_and_wind``— intersection (inclusion-exclusion: F + W − union)

The wind leg is the binary ``is_prs_wind`` damage-onset trigger — NOT the
continuous wind damage amount. The flood-only ``prs_spread_bps`` /
``term_structure.severe`` (flood spine) is kept unchanged: it still drives the
gauge basis and the flood-vs-gauge spread decomposition. Wind has no gauge
intermediary — it is a pure intersect/union at the property node. Catchments
without a typhoon stage emit no ``prs_perils`` block and are byte-identical to
before (flood-only fallback).
"""

import json
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

from models.floodrisk.depth_damage import is_prs_flood
from models.winddamage.threshold import is_prs_wind

from .constants import TENORS


class PricingMixin:
    """Mixin providing property processing, PRS pricing, and basis methods."""

    def _process_property(self, prop_file: Path, gauge_hazard: Dict,
                          price_prs_func, num_storms: int = 1000,
                          **kwargs) -> Optional[Dict]:
        """Process a single property: count severe floods that reach property, compute spread and basis."""
        with open(prop_file, 'r') as f:
            pdata = json.load(f)

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

    # ------------------------------------------------------------------
    # Stage 6 — peril outcomes (flood ∪/∩ wind over the 1:1-paired event set)
    # ------------------------------------------------------------------

    def _wind_union(self, prop_id: str, flood_events: List[Dict],
                    num_storms: int) -> Optional[Dict]:
        """Count flood ∪ wind and flood ∩ wind PRS triggers for one property.

        Returns ``None`` when the catchment has no typhoon damage (flood-only
        fallback — the headline flood spread is unchanged). Otherwise returns
        the wind-leg, union and intersection counts/spreads, deduplicated on the
        shared 1:1 ``event_id`` so an event that triggers BOTH flood and wind
        counts once in the union and once in the intersection.

        The wind trigger is :func:`is_prs_wind` (binary damage-onset). Each
        storm sequence carries its paired typhoon's ``event_id`` (Stage 2), so
        the flood leg (keyed by ``storm_id`` == ``sequence_id``) and the wind
        leg (keyed by ``event_id``) meet in ``event_id`` space.
        """
        wind_index = self._wind_damage_index()
        if not wind_index:
            return None
        seq_to_event = self._seq_to_event_map()

        # Wind-triggered events for this property.
        wind_eids = {
            eid for eid, pmap in wind_index.items()
            if prop_id in pmap and is_prs_wind(pmap[prop_id])
        }

        # Flood-triggered events, mapped storm_id → event_id. A flood-triggered
        # storm with no paired event_id can't collide with a wind event, so it
        # is counted on its own (keeps flood-only totals exact).
        flood_eids = set()
        flood_unmapped = 0
        for e in flood_events:
            if is_prs_flood(e):
                eid = seq_to_event.get(e.get('storm_id', ''))
                if eid:
                    flood_eids.add(eid)
                else:
                    flood_unmapped += 1

        wind_count = len(wind_eids)
        union_count = len(flood_eids | wind_eids) + flood_unmapped
        # Intersection (flood AND wind) lives in event_id space only — a
        # flood-triggered storm with no event_id cannot also be a wind event.
        joint_count = len(flood_eids & wind_eids)
        bps = lambda c: round((c / num_storms) * 10000, 2) if num_storms > 0 else 0.0
        return {
            'wind_count': wind_count,
            'union_count': union_count,
            'joint_count': joint_count,
            'wind_spread_bps': bps(wind_count),
            'union_spread_bps': bps(union_count),
            'joint_spread_bps': bps(joint_count),
        }

    def _seq_to_event_map(self) -> Dict[str, str]:
        """``sequence_id → event_id`` from ``storm_sequences.json`` (cached).

        Only sequences carrying both ids are included; empty when the file is
        absent or pre-coupling (no ``event_id`` field).
        """
        cached = getattr(self, '_seq_to_event_cache', None)
        if cached is not None:
            return cached
        out: Dict[str, str] = {}
        seq_path = self.output_dir / 'storm_sequences.json'
        if seq_path.exists():
            try:
                with open(seq_path, 'r') as f:
                    data = json.load(f)
                for seq in data.get('sequences', []):
                    sid = seq.get('sequence_id')
                    eid = seq.get('event_id')
                    if sid and eid:
                        out[sid] = eid
            except (OSError, json.JSONDecodeError):
                pass
        self._seq_to_event_cache = out
        return out

    def _wind_damage_index(self) -> Dict[str, Dict[str, Dict]]:
        """``event_id → {property_id → {peak_sustained_ms, threshold_ms}}``.

        Walks ``typhoon/damage/EVT-*.json`` once and caches the result. Empty
        when the typhoon stage hasn't run for this catchment. Built once for
        the whole portfolio (not per-property) so pricing stays O(events) not
        O(events × properties).
        """
        cached = getattr(self, '_wind_damage_cache', None)
        if cached is not None:
            return cached
        out: Dict[str, Dict[str, Dict]] = {}
        damage_dir = self.output_dir / 'typhoon' / 'damage'
        if damage_dir.exists():
            for fp in sorted(damage_dir.glob('EVT-*.json')):
                try:
                    with open(fp, 'r') as f:
                        data = json.load(f)
                except (OSError, json.JSONDecodeError):
                    continue
                eid = data.get('event_id') or fp.stem
                pmap: Dict[str, Dict] = {}
                for d in data.get('damages', []):
                    pid = d.get('property_id')
                    if pid:
                        pmap[pid] = {
                            'peak_sustained_ms': d.get('peak_sustained_ms'),
                            'threshold_ms': d.get('threshold_ms'),
                        }
                if pmap:
                    out[eid] = pmap
        self._wind_damage_cache = out
        return out
