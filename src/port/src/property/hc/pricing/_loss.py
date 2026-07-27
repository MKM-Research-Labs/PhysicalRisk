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

"""Per-asset loss block for the property and commercial legs (MKM-EF-001, 6c).

The PRS spread is a probability; this rides alongside it, additively, as the
loss-weighted view — average annual loss, AEP and OEP curves and an event loss
table — for the same severe-flood peril the spread is priced on.

Each severe flood the asset takes already carries a depth-damage ratio. Those
records are regrouped onto the hours-clause events (taking the worst within an
event, matching the occurrence rule) and run through the frequency model's loss
sampler.

The loss is a currency amount — the depth-damage ratio times the asset's own
value, the same ``value × damage_ratio`` the routes and reports use — when the
value is supplied. When it is not (``asset_value=None``) the block falls back to
*unit exposure*, the damage ratio itself, a severity per unit of value. A value
of zero is not the same as a missing value: it keeps the currency basis and
reports a zero loss, so a data gap in the portfolio surfaces as ``exposure_value
= 0`` rather than being silently rebased to a severity.
"""

from typing import Dict, List, Optional, Sequence

from config.frequency import FrequencyConfig, config_hash
from models.frequency import (
    compact_loss_block,
    loss_metrics,
    regrouped_event_losses,
)
from models.frequency.datastructures import EventDraws, ProvenanceClass


def property_loss_block(
    frame,
    prs_floods: Sequence[Dict],
    lambda_per_year: float,
    freq_config: FrequencyConfig,
    subject_id: str,
    catchment: str,
    asset_value: Optional[float] = None,
    draws: Optional[EventDraws] = None,
) -> Dict:
    """Return the additive loss block for one asset.

    Args:
        frame: the event frame the spread was priced on.
        prs_floods: the asset's severe flood events — the same set the spread
            counts — each carrying its ``storm_id`` and ``damage_ratio``.
        lambda_per_year: the catchment arrival rate.
        freq_config: the frequency configuration; supplies the simulation knobs,
            the return-period grid and the hash recorded in the export.
        subject_id: the property or commercial asset identifier.
        catchment: the catchment, recorded in the export metadata.
        asset_value: the asset's reinstatement value. When given (including
            zero), each event's loss is ``damage_ratio * asset_value`` and the
            block is a currency amount; when ``None`` the loss is the damage
            ratio at unit exposure.
        draws: shared run draws, so every asset is scored against the same
            simulated storms; omitting them samples the asset on its own.

    Returns:
        A compact, JSON-serialisable loss block carrying ``exposure_value`` and
        a ``basis`` of ``"currency"`` or ``"unit_exposure_damage_ratio"``.
    """
    if asset_value is None:
        multiplier, basis = 1.0, "unit_exposure_damage_ratio"
    else:
        multiplier, basis = float(asset_value), "currency"

    identifiers: List[str] = [event.get("storm_id") for event in prs_floods]
    per_record = [float(event.get("damage_ratio", 0.0)) * multiplier
                  for event in prs_floods]
    event_losses = regrouped_event_losses(frame, identifiers, per_record)

    metrics = loss_metrics(
        frame, event_losses, lambda_per_year, freq_config.simulation,
        subject_id, catchment, ProvenanceClass.GENERATOR_DERIVED.value,
        freq_config.rate.return_periods_years,
        config_hash=config_hash(freq_config), draws=draws)
    block = compact_loss_block(metrics, basis)
    block["exposure_value"] = multiplier
    return block
