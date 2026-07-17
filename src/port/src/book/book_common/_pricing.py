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

"""Leg PV computation and single-trade pricing/saving."""

import logging
import math
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import database
from models.hazard.prs_analytical import compute_prs_spread, interpolate_yield_rate

from ._constants import (
    DEFAULT_YIELD_CURVE,
    RECOVERY,
    SPREAD_OFFSET_MAX,
    SPREAD_OFFSET_MIN,
)
from ._records import _build_cdm_record

logger = logging.getLogger(__name__)


def _compute_leg_pvs(hazard_rate: float, trade_spread_bps: float,
                     tenor: int, notional: float,
                     yield_curve: Optional[Dict] = None) -> Dict:
    """Compute premium and protection leg present values using yield curve."""
    if hazard_rate <= 0:
        return {
            'premium_leg_pv': 0.0,
            'protection_leg_pv': 0.0,
            'risky_annuity': float(tenor),
        }

    yc = yield_curve or DEFAULT_YIELD_CURVE
    hazard_lambda = -math.log(1.0 - min(hazard_rate, 0.999))
    dt = 0.25
    n_periods = tenor * 4

    annuity = 0.0
    protection_pv = 0.0

    for i in range(1, n_periods + 1):
        t = i * dt
        t_prev = (i - 1) * dt
        survival = math.exp(-hazard_lambda * t)
        surv_prev = math.exp(-hazard_lambda * t_prev)
        rf = interpolate_yield_rate(yc, t)
        discount = math.exp(-rf * t)
        rf_mid = interpolate_yield_rate(yc, t - dt / 2)
        discount_mid = math.exp(-rf_mid * (t - dt / 2))

        annuity += dt * survival * discount
        protection_pv += (1.0 - RECOVERY) * (surv_prev - survival) * discount_mid

    premium_pv = (trade_spread_bps / 10000) * annuity * notional
    prot_pv_scaled = protection_pv * notional

    return {
        'premium_leg_pv': round(premium_pv, 2),
        'protection_leg_pv': round(prot_pv_scaled, 2),
        'risky_annuity': round(annuity, 6),
    }


def _price_and_save_trade(
    gauge_id: str,
    gauge_name: str,
    catchment_id: str,
    is_payer: bool,
    tenor: int,
    notional: float,
    trigger: str,
    hazard_rate: float,
    counterparties: List[Dict],
    ctpy_idx: int,
    base_date: datetime,
    output_dir: Path,
    property_set: Optional[Dict] = None,
    fair_spread_override: Optional[float] = None,
) -> tuple:
    """Price a single trade, build CDM, save JSON, return (record, new_ctpy_idx).

    Args:
        property_set: Optional PropertySet dict for property PRS trades.
        fair_spread_override: Optional fair spread in bps (skips hazard-rate
            computation).  Used by property trades where spread comes from
            propertyhc.json event-count model rather than the analytical pricer.
    """
    import random
    import uuid

    if fair_spread_override is not None:
        fair_spread = fair_spread_override
    else:
        fair_spread = compute_prs_spread(hazard_rate, tenor, RECOVERY,
                                          yield_curve=DEFAULT_YIELD_CURVE)
    prefix = 'PRS-P' if property_set else 'PRS-'
    swap_id = f'{prefix}{uuid.uuid4().hex[:8].upper()}'
    offset = random.uniform(SPREAD_OFFSET_MIN, SPREAD_OFFSET_MAX)
    if property_set:
        # PropertyPRS: REIT (payer) buys protection above fair value;
        # desk (receiver) sells above fair — client always pays the ask.
        trade_spread = fair_spread + offset
    else:
        # Gauge PRS: desk perspective — payer pays below fair, receiver
        # receives above fair (desk always gets the favourable side).
        trade_spread = fair_spread - offset if is_payer else fair_spread + offset

    pvs = _compute_leg_pvs(hazard_rate, trade_spread, tenor, notional)
    direction = 1.0 if is_payer else -1.0
    npv = (pvs['protection_leg_pv'] - pvs['premium_leg_pv']) * direction

    ctpy = counterparties[ctpy_idx % len(counterparties)]
    td = base_date + timedelta(days=random.randint(0, 20))

    record = _build_cdm_record(
        swap_id=swap_id,
        gauge_id=gauge_id,
        gauge_name=gauge_name,
        catchment_id=catchment_id,
        counterparty_id=ctpy['id'],
        counterparty_name=ctpy['name'],
        is_payer=is_payer,
        notional=notional,
        tenor=tenor,
        trigger=trigger,
        trade_spread_bps=trade_spread,
        fair_spread_bps=fair_spread,
        npv=npv,
        premium_leg_pv=pvs['premium_leg_pv'],
        protection_leg_pv=pvs['protection_leg_pv'],
        risky_annuity=pvs['risky_annuity'],
        trade_date=td,
        property_set=property_set,
    )

    # Persist through the prs_trade seam — the blotter/client/routes read these
    # back via database.iter_prs_trade_ids / get_prs_trade (output_dir is kept
    # for call-site compatibility).
    database.save_prs_trade(catchment_id, swap_id, record)

    dir_label = 'PAY' if is_payer else 'RCV'
    logger.info(
        '%s %s %s %s %dY %.1f/%.1f bps MTM=%.0f',
        swap_id, dir_label, gauge_id[:16], trigger,
        tenor, trade_spread, fair_spread, npv
    )

    return record, ctpy_idx + 1
