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

"""PRS CDM record construction and counterparty loading."""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import database
from config import config
from models.schedule.maturity import compute_maturity_date
from port.cdm.prs import PhysicalRiskSwapCDM

from ._constants import _REIT_PARTY_ID, DEFAULT_YIELD_CURVE, RECOVERY

logger = logging.getLogger(__name__)

# CDM validator (instantiated once)
_cdm = PhysicalRiskSwapCDM()


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
    property_set: Optional[Dict] = None,
) -> Dict:
    """Build a full PRS CDM record.

    Args:
        property_set: Optional dict with PropertySet fields (PropertyID,
            PropertyAddress, etc.).  When provided the trade is typed as
            ``PropertyPRS`` and the PropertySet section is attached.
    """
    trade_type = 'PropertyPRS' if property_set else 'PRS'
    start_date = trade_date + timedelta(days=2)
    end_date = compute_maturity_date(tenor, trade_date.date()
                                     if hasattr(trade_date, 'date')
                                     else trade_date)

    record = {
        'PhysicalSwap': {
            'Header': {
                'SwapID': swap_id,
                'CatchmentID': catchment_id,
                'TradeType': trade_type,
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
                'Currency': config.CURRENCY,
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
                'Currency': config.CURRENCY,
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

    if property_set:
        record['PhysicalSwap']['PropertySet'] = property_set

    # Validate against PRS CDM schema
    errors = _cdm.validate(record)
    if errors:
        logger.warning('CDM validation for %s: %s', swap_id, errors)

    return record


def _load_counterparties(catchment_id: str) -> List[Dict]:
    """Load counterparties for *catchment_id* via the database seam, excluding the REIT.

    Returns the random pool of external counterparties (banks, insurers,
    reinsurers, etc.) suitable for gauge-PRS assignment. The REIT is
    filtered because it is reserved for property-PRS trades only.
    """
    counterparties = []
    ctpy_data = database.get_counterparty_portfolio(catchment_id)
    if ctpy_data:
        for c in ctpy_data.get('counterparties', []):
            cs = c.get('CounterpartySet', {})
            party = cs.get('Party', {})
            party_id = party.get('PartyID', '')
            if party_id == _REIT_PARTY_ID:
                continue  # REIT reserved for property PRS
            platform = cs.get('_platform', {})
            counterparties.append({
                'id': party_id,
                'name': (f"{platform.get('ShortName', party.get('PartyName', ''))}"
                         f" ({platform.get('CreditRating', 'NR')})"),
            })

    if not counterparties:
        counterparties = [{'id': f'CTPY-{i:03d}', 'name': f'Counterparty {i}'}
                          for i in range(1, 22)]
    return counterparties
