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

"""What-if sensitivity for the deferred wind decoupling (MKM-EF-001, Stage 6j).

The companion to ``models.frequency.sensitivity`` for the wind peril. Opting a
catchment into ``DECOUPLED_WIND_CATCHMENTS`` reprices its wind, union and
intersection legs, and that decision is gated on real typhoon data. This
quantifies the reprice before it is made: for one asset it runs both the coupled
(production) and decoupled legs off the same inputs and reports the deltas and
the number of unpaired typhoons the coupled model is dropping.

It changes nothing priced — it calls the same ``coupled_wind_legs`` and
``decoupled_wind_legs`` the pricing path would use, side by side, as a
diagnostic for the model-risk decision.
"""

from typing import Dict

from ._wind import coupled_wind_legs, decoupled_wind_legs


def wind_decoupling_sensitivity(
    wind_eids: set,
    event_to_seq: Dict[str, str],
    flood_seqs: set,
    n_wind_events: int,
    frame,
    lambda_flood: float,
    lambda_wind: float,
) -> Dict:
    """Compare coupled vs decoupled wind pricing for one asset.

    Args:
        wind_eids: the wind events (paired and unpaired) that trigger the asset.
        event_to_seq: the ``event_id -> sequence_id`` pairing.
        flood_seqs: the flood-triggering sequences for the asset.
        n_wind_events: the size of the wind (typhoon) catalogue.
        frame: the flood event frame.
        lambda_flood: the storm event arrival rate.
        lambda_wind: the wind event arrival rate.

    Returns:
        Both leg sets, the count of unpaired typhoons the coupled model drops,
        and the wind and union spread deltas the decoupling would introduce.
    """
    paired_wind_seqs = {event_to_seq[eid] for eid in wind_eids
                        if eid in event_to_seq}

    coupled = coupled_wind_legs(paired_wind_seqs, flood_seqs, frame, lambda_flood)
    decoupled = decoupled_wind_legs(
        wind_eids, n_wind_events, flood_seqs, paired_wind_seqs, frame,
        lambda_flood, lambda_wind)

    return {
        "coupled": coupled,
        "decoupled": decoupled,
        "dropped_unpaired_events": len(wind_eids) - len(paired_wind_seqs),
        "wind_spread_delta_bps": round(
            decoupled["wind_spread_bps"] - coupled["wind_spread_bps"], 2),
        "union_spread_delta_bps": round(
            decoupled["union_spread_bps"] - coupled["union_spread_bps"], 2),
    }
