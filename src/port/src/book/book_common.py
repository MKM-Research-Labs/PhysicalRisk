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

"""
Book generator — shared constants and pricing helpers.

Constants, yield curve, CDM record builder, leg PV computation,
and counterparty loading used by both market-making and Thames Central styles.
"""

import json
import logging
import math
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from models.hazard.prs_analytical import compute_prs_spread, interpolate_yield_rate
from models.schedule.maturity import compute_maturity_date
from port.cdm.prs import PhysicalRiskSwapCDM

logger = logging.getLogger(__name__)

from config.port import (
    DEFAULT_YIELD_CURVE,
    NOTIONALS,
    RECOVERY,
    SPREAD_OFFSET_MAX,
    SPREAD_OFFSET_MIN,
    TENORS,
    TRIGGER_RATE_KEY,
    TRIGGERS,
)

# CDM validator (instantiated once)
_cdm = PhysicalRiskSwapCDM()


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


def _build_cdm_record(
    swap_id: str,
    gauge_id: str,
    gauge_name: str,
    catchment_id: str,
    counterparty_id: str,
    counterparty_name: str,
    is_payer: bool,
    notional: float,
    tenor: int,
    trigger: str,
    trade_spread_bps: float,
    fair_spread_bps: float,
    npv: float,
    premium_leg_pv: float,
    protection_leg_pv: float,
    risky_annuity: float,
    trade_date: datetime,
) -> Dict:
    """Build a full PRS CDM record."""
    start_date = trade_date + timedelta(days=2)
    end_date = compute_maturity_date(tenor, trade_date.date()
                                     if hasattr(trade_date, 'date')
                                     else trade_date)

    record = {
        'PhysicalSwap': {
            'Header': {
                'SwapID': swap_id,
                'CatchmentID': catchment_id,
                'TradeType': 'PRS',
                'CounterParty': counterparty_id,
                'CounterPartyName': counterparty_name,
                'PartyId': 'MKM-RESEARCH-001',
                'ValuationDate': trade_date.strftime('%Y-%m-%d'),
                'ProtectionStart': start_date.strftime('%Y-%m-%d'),
                'TradeStatus': 'Committed',
            },
            'LegData': {
                'LegType': 'Fixed',
                'Payer': is_payer,
                'Currency': 'GBP',
                'Notional': notional,
                'DayCounter': 'ACT/360',
                'FixedLegRate': trade_spread_bps / 10000,
            },
            'ScheduleData': {
                'StartDate': start_date.strftime('%Y-%m-%d'),
                'EndDate': end_date.strftime('%Y-%m-%d'),
                'Tenor': '6M',
                'Calendar': 'London',
            },
            'GaugeSet': {
                'GaugeSetID': f'GSET-{gauge_id}',
                'CatchmentID': catchment_id,
                'GaugeCount': 1,
                'GaugeBasket': [{
                    'GaugeID': gauge_id,
                    'GaugeName': gauge_name,
                    'Weight': 1.0,
                    'TriggerLevel': trigger,
                }],
            },
            'Triggers': {
                'TriggerType': 'Any',
                'TriggerThreshold': 1,
            },
            'Payouts': {
                'Currency': 'GBP',
                'MaxPayout': notional,
            },
            'Pricing': {
                'SpreadBps': round(trade_spread_bps),
                'FairSpreadBps': round(fair_spread_bps, 2),
                'NPV': round(npv, 2),
                'PremiumLegPV': round(premium_leg_pv, 2),
                'ProtectionLegPV': round(protection_leg_pv, 2),
                'RiskyAnnuity': round(risky_annuity, 6),
                'YieldCurve': DEFAULT_YIELD_CURVE,
                'Recovery': RECOVERY,
                'TriggerLevel': trigger,
            },
        }
    }

    # Validate against PRS CDM schema
    errors = _cdm.validate(record)
    if errors:
        logger.warning('CDM validation for %s: %s', swap_id, errors)

    return record


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
) -> tuple:
    """Price a single trade, build CDM, save JSON, return (record, new_ctpy_idx)."""
    import random
    import uuid

    fair_spread = compute_prs_spread(hazard_rate, tenor, RECOVERY,
                                      yield_curve=DEFAULT_YIELD_CURVE)
    swap_id = f'PRS-{uuid.uuid4().hex[:8].upper()}'
    offset = random.uniform(SPREAD_OFFSET_MIN, SPREAD_OFFSET_MAX)
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
    )

    json_path = output_dir / f'{swap_id}.json'
    with open(json_path, 'w') as f:
        json.dump(record, f, indent=2)

    dir_label = 'PAY' if is_payer else 'RCV'
    logger.info(
        '%s %s %s %s %dY %.1f/%.1f bps MTM=%.0f',
        swap_id, dir_label, gauge_id[:16], trigger,
        tenor, trade_spread, fair_spread, npv
    )

    return record, ctpy_idx + 1


def _load_counterparties(counterparty_path: Path) -> List[Dict]:
    """Load counterparties from JSON file."""
    counterparties = []
    if counterparty_path.exists():
        with open(counterparty_path) as f:
            ctpy_data = json.load(f)
        for c in ctpy_data.get('counterparties', []):
            cs = c.get('CounterpartySet', {})
            party = cs.get('Party', {})
            platform = cs.get('_platform', {})
            counterparties.append({
                'id': party.get('PartyID', ''),
                'name': (f"{platform.get('ShortName', party.get('PartyName', ''))}"
                         f" ({platform.get('CreditRating', 'NR')})"),
            })

    if not counterparties:
        counterparties = [{'id': f'CTPY-{i:03d}', 'name': f'Counterparty {i}'}
                          for i in range(1, 22)]
    return counterparties
