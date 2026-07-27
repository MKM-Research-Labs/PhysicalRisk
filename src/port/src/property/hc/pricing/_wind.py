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

"""Stage-6 peril outcomes: flood union/intersection wind over paired events."""

from typing import Dict, List, Optional

from models.floodrisk.depth_damage import is_prs_flood
from models.frequency import annual_exceedance_probability
from models.winddamage.threshold import is_prs_wind
from port.src._typhoon_join import load_seq_to_event_map, load_wind_damage_index


class _WindMixin:
    """Wind union/intersection peril counting and damage/seq index caches."""

    # ------------------------------------------------------------------
    # Stage 6 — peril outcomes (flood ∪/∩ wind over the 1:1-paired event set)
    # ------------------------------------------------------------------

    def _wind_union(self, prop_id: str, flood_events: List[Dict],
                    num_storms: int, frame=None,
                    lambda_per_year: float = 0.0) -> Optional[Dict]:
        """Count flood ∪ wind and flood ∩ wind PRS triggers for one property.

        Returns ``None`` when the catchment has no typhoon damage (flood-only
        fallback — the headline flood spread is unchanged). Otherwise returns
        the wind-leg, union and intersection counts/spreads, deduplicated on the
        shared 1:1 ``event_id`` so an event that triggers BOTH flood and wind
        counts once in the union and once in the intersection.

        The wind trigger is :func:`is_prs_wind` (binary damage-onset). Each
        storm sequence carries its paired typhoon's ``event_id`` (Stage 2), so
        the flood leg (keyed by ``storm_id`` == ``sequence_id``) and the wind
        leg (keyed by ``event_id``) meet in *sequence* space: the wind side is
        mapped back through the 1:1 pairing rather than the flood side being
        mapped forward. Working in sequence space is what lets both legs be
        annualised on the same event frame, and it removes the need to treat a
        flood-triggered sequence with no paired typhoon as a special case —
        it is simply a sequence that no wind event coincides with.

        When *frame* and *lambda_per_year* are supplied, all three legs are
        annualised through the frequency layer (MKM-EF-001). Without them the
        pre-frequency count ratio is returned, so an unmigrated caller prices
        exactly as before. Leaving flood annualised and wind not would make the
        union and intersection legs internally inconsistent, which is why they
        move together.
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

        # Everything is expressed in sequence space. The wind side is mapped
        # back through the 1:1 pairing; a wind event with no paired sequence is
        # dropped, because it cannot be placed on the flood timeline at all.
        event_to_seq = {eid: sid for sid, eid in seq_to_event.items()}
        wind_seqs = {event_to_seq[eid] for eid in wind_eids if eid in event_to_seq}
        flood_seqs = {e.get('storm_id', '') for e in flood_events if is_prs_flood(e)}
        flood_seqs.discard('')

        union_seqs = flood_seqs | wind_seqs
        joint_seqs = flood_seqs & wind_seqs

        if frame is not None and lambda_per_year > 0:
            def bps(seqs):
                conditional = frame.conditional_probability(seqs)
                return round(annual_exceedance_probability(
                    lambda_per_year, conditional) * 10000, 2)
        else:
            def bps(seqs):
                return (round((len(seqs) / num_storms) * 10000, 2)
                        if num_storms > 0 else 0.0)

        # Sequence-space wind-loss records for the additive loss leg (Stage 6e).
        # One pseudo-record per wind-triggered event, carrying the authoritative
        # per-event damage ratio, keyed by sequence so the loss assembly regroups
        # it onto the same event frame the flood leg uses. Shaped like a flood
        # record (storm_id + damage_ratio) so the one loss builder serves both.
        wind_loss_records = [
            {'storm_id': event_to_seq[eid],
             'damage_ratio': wind_index[eid][prop_id].get('damage_ratio') or 0.0}
            for eid in wind_eids if eid in event_to_seq
        ]

        return {
            'wind_count': len(wind_seqs),
            'union_count': len(union_seqs),
            'joint_count': len(joint_seqs),
            'wind_spread_bps': bps(wind_seqs),
            'union_spread_bps': bps(union_seqs),
            'joint_spread_bps': bps(joint_seqs),
            'wind_loss_records': wind_loss_records,
        }

    def _seq_to_event_map(self) -> Dict[str, str]:
        """``sequence_id → event_id`` from ``storm_sequences.json`` (cached).

        Only sequences carrying both ids are included; empty when the file is
        absent or pre-coupling (no ``event_id`` field).
        """
        cached = getattr(self, '_seq_to_event_cache', None)
        if cached is None:
            cached = load_seq_to_event_map()
            self._seq_to_event_cache = cached
        return cached

    def _wind_damage_index(self) -> Dict[str, Dict[str, Dict]]:
        """``event_id → {property_id → {peak_sustained_ms, threshold_ms, v_50_eff_ms}}``.

        Walks ``typhoon/damage/EVT-*.json`` once and caches the result. Empty
        when the typhoon stage hasn't run for this catchment. Built once for
        the whole portfolio (not per-property) so pricing stays O(events) not
        O(events × properties). Loading lives in ``port.src._typhoon_join``.
        """
        cached = getattr(self, '_wind_damage_cache', None)
        if cached is None:
            cached = load_wind_damage_index()
            self._wind_damage_cache = cached
        return cached
