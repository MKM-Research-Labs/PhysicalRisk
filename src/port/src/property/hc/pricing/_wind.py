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

from config.frequency import is_wind_decoupled
from models.floodrisk.depth_damage import is_prs_flood
from models.frequency import annual_exceedance_probability
from models.winddamage.threshold import is_prs_wind
from port.src._typhoon_join import load_seq_to_event_map, load_wind_damage_index


def decoupled_wind_legs(
    wind_eids: set,
    n_wind_events: int,
    flood_seqs: set,
    paired_wind_seqs: set,
    frame,
    lambda_flood: float,
    lambda_wind: float,
) -> Dict:
    """Price wind as an INDEPENDENT arrival process (MKM-EF-001, Stage 6i).

    The opt-in alternative to the coupled 1:1 model. Flood and wind are treated
    as independent Poisson processes, so the union and intersection follow from
    the two marginal annual probabilities — ``1-(1-P_f)(1-P_w)`` and
    ``P_f·P_w`` — rather than from set operations in a shared event space.

    This counts the unpaired typhoons the coupled model drops: the wind
    conditional is ``triggering wind events / all wind events`` over the whole
    typhoon catalogue, not just the paired subset. Two assumptions are baked in
    and documented as the mode's limitations: independence (it trades the coupled
    model's pairing correlation for coverage of unpaired events), and uniform
    weights over the damage-bearing typhoon population (a coverage/weighting
    refinement is a follow-on, as it was for the flood catalogue). The counts use
    inclusion-exclusion so ``union = flood + wind - joint`` still holds for
    display, while the spreads use the independent-probability model.

    Args:
        wind_eids: the wind events (paired and unpaired) that trigger the asset.
        n_wind_events: the size of the wind (typhoon) catalogue — the denominator.
        flood_seqs: the flood-triggering sequences for the asset.
        paired_wind_seqs: the paired subset of ``wind_eids`` mapped to sequences,
            the only wind events that can intersect a flood sequence.
        frame: the flood event frame, for the flood conditional.
        lambda_flood: the storm event arrival rate.
        lambda_wind: the wind event arrival rate.

    Returns:
        The wind/union/joint counts and spreads, as ``_wind_union`` returns them.
    """
    p_flood = frame.conditional_probability(flood_seqs)
    p_wind = (len(wind_eids) / n_wind_events) if n_wind_events else 0.0
    prob_flood = annual_exceedance_probability(lambda_flood, p_flood)
    prob_wind = annual_exceedance_probability(lambda_wind, p_wind)
    prob_union = 1.0 - (1.0 - prob_flood) * (1.0 - prob_wind)
    prob_joint = prob_flood * prob_wind

    wind_count = len(wind_eids)
    joint_count = len(flood_seqs & paired_wind_seqs)
    union_count = len(flood_seqs) + wind_count - joint_count
    return {
        'wind_count': wind_count,
        'union_count': union_count,
        'joint_count': joint_count,
        'wind_spread_bps': round(prob_wind * 10000, 2),
        'union_spread_bps': round(prob_union * 10000, 2),
        'joint_spread_bps': round(prob_joint * 10000, 2),
    }


class _WindMixin:
    """Wind union/intersection peril counting and damage/seq index caches."""

    # ------------------------------------------------------------------
    # Stage 6 — peril outcomes (flood ∪/∩ wind over the 1:1-paired event set)
    # ------------------------------------------------------------------

    def _wind_union(self, prop_id: str, flood_events: List[Dict],
                    num_storms: int, frame=None,
                    lambda_per_year: float = 0.0, catchment: str = "",
                    wind_lambda_per_year=None) -> Optional[Dict]:
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

        # Sequence-space wind-loss records for the additive loss leg (Stage 6e).
        # One pseudo-record per PAIRED wind-triggered event, carrying the
        # authoritative per-event damage ratio, keyed by sequence so the loss
        # assembly regroups it onto the same event frame the flood leg uses.
        # Shaped like a flood record (storm_id + damage_ratio) so the one loss
        # builder serves both. Unchanged by the decoupling below — the additive
        # wind-loss view stays sequence-space.
        wind_loss_records = [
            {'storm_id': event_to_seq[eid],
             'damage_ratio': wind_index[eid][prop_id].get('damage_ratio') or 0.0}
            for eid in wind_eids if eid in event_to_seq
        ]

        # Decoupled (Stage 6i, opt-in): wind is an independent arrival process
        # counting unpaired typhoons. Otherwise the coupled 1:1 model in shared
        # sequence space — the default, byte-identical to prior stages.
        if frame is not None and lambda_per_year > 0 and is_wind_decoupled(catchment):
            wind_lambda = (lambda_per_year if wind_lambda_per_year is None
                           else wind_lambda_per_year)
            legs = decoupled_wind_legs(
                wind_eids, len(wind_index), flood_seqs, wind_seqs, frame,
                lambda_per_year, wind_lambda)
            legs['wind_loss_records'] = wind_loss_records
            return legs

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
