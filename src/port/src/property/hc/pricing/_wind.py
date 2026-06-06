# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Stage-6 peril outcomes: flood union/intersection wind over paired events."""

import json
from typing import Dict, List, Optional

from models.floodrisk.depth_damage import is_prs_flood
from models.winddamage.threshold import is_prs_wind


class _WindMixin:
    """Wind union/intersection peril counting and damage/seq index caches."""

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
        """``event_id → {property_id → {peak_sustained_ms, threshold_ms, v_50_eff_ms}}``.

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
                # Key on the filename stem (canonical 5-digit event id that
                # matches storm_sequences). The internal event_id field can be
                # mis-stamped by genesis, so do not trust it for the join.
                eid = fp.stem
                pmap: Dict[str, Dict] = {}
                for d in data.get('damages', []):
                    pid = d.get('property_id')
                    if pid:
                        pmap[pid] = {
                            'peak_sustained_ms': d.get('peak_sustained_ms'),
                            'threshold_ms': d.get('threshold_ms'),
                            'v_50_eff_ms': d.get('v_50_eff_ms'),
                        }
                if pmap:
                    out[eid] = pmap
        self._wind_damage_cache = out
        return out
