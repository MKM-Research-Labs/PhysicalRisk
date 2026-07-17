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

"""PRS (Physical Risk Swap) pricing via QuantLib CDS engine."""

import logging
from typing import Dict

import QuantLib as ql

from .curves import create_survival_curve_from_hazard, create_flat_hazard_curve

logger = logging.getLogger(__name__)


def price_prs(
    gauge_data: Dict,
    trigger_level: str = 'warning',
    notional: float = 10_000_000,
    tenor_years: int = 5,
    running_spread: float = 0.01,
    recovery_rate: float = 0.0,  # No recovery for flood - full loss
    risk_free_rate: float = 0.03,
    use_term_structure: bool = True
) -> Dict:
    """
    Price a Physical Risk Swap for a single gauge.

    Args:
        gauge_data: Gauge hazard curve data from hazard_curves.json
        trigger_level: 'alert', 'warning', or 'severe'
        notional: Notional amount
        tenor_years: Contract tenor in years
        running_spread: Annual premium rate
        recovery_rate: Recovery rate (typically 0 for flood)
        risk_free_rate: Risk-free discount rate
        use_term_structure: Use full term structure vs flat hazard

    Returns:
        Dictionary with pricing results
    """
    # Set evaluation date
    today = ql.Date.todaysDate()
    ql.Settings.instance().evaluationDate = today

    # Get the appropriate hazard rate and term structure
    hazard_rate_key = f"annual_hazard_rate_{trigger_level}"
    term_structure_key = f"term_structure_{trigger_level}"

    annual_hazard_rate = gauge_data[hazard_rate_key]
    term_structure = gauge_data[term_structure_key]

    # Create hazard/survival curve
    if use_term_structure:
        hazard_curve = create_survival_curve_from_hazard(today, term_structure)
        hazard_quote = None
    else:
        hazard_curve, hazard_quote = create_flat_hazard_curve(today, annual_hazard_rate)

    # Create risk-free curve
    risk_free_curve = ql.FlatForward(
        today,
        ql.QuoteHandle(ql.SimpleQuote(risk_free_rate)),
        ql.Actual365Fixed(),
        ql.Compounded,
        ql.Annual
    )

    # CDS parameters
    calendar = ql.TARGET()
    convention = ql.Following
    day_counter = ql.Actual360()

    protection_start = calendar.advance(today, 1, ql.Days)
    maturity_date = calendar.advance(today, tenor_years, ql.Years)
    upfront_date = calendar.advance(today, 3, ql.Days)

    # Create schedule
    schedule = ql.Schedule(
        protection_start,
        maturity_date,
        ql.Period(ql.Quarterly),
        calendar,
        convention,
        convention,
        ql.DateGeneration.TwentiethIMM,
        False
    )

    # Create CDS (PRS)
    cds = ql.CreditDefaultSwap(
        ql.Protection.Buyer,
        notional,
        0.0,  # No upfront
        running_spread,
        schedule,
        convention,
        day_counter,
        True,  # settles_accrual
        True,  # pays_at_default_time
        protection_start,
        upfront_date
    )

    # Create pricing engine
    engine = ql.IsdaCdsEngine(
        ql.DefaultProbabilityTermStructureHandle(hazard_curve),
        recovery_rate,
        ql.YieldTermStructureHandle(risk_free_curve),
        True  # includeSettlementDateFlows
    )
    cds.setPricingEngine(engine)

    # Calculate results
    npv = cds.NPV()
    fair_spread = cds.fairSpread()
    fair_upfront = cds.fairUpfront()
    premium_leg = cds.couponLegNPV()
    protection_leg = cds.defaultLegNPV()

    # Get survival probabilities at key dates
    survival_probs = {}
    for year in range(1, tenor_years + 1):
        date = today + ql.Period(year, ql.Years)
        survival_probs[f"{year}yr"] = hazard_curve.survivalProbability(date)

    # Get trigger threshold (different key format for severe)
    if trigger_level == 'severe':
        threshold_key = 'severe_flood_warning_m'
    else:
        threshold_key = f"flood_{trigger_level}_m"

    return {
        'gauge_id': gauge_data['gauge_id'],
        'gauge_name': gauge_data['gauge_name'],
        'trigger_level': trigger_level,
        'trigger_threshold_m': gauge_data[threshold_key],
        'annual_hazard_rate': annual_hazard_rate,
        'notional': notional,
        'tenor_years': tenor_years,
        'running_spread': running_spread,
        'running_spread_bps': running_spread * 10000,
        'recovery_rate': recovery_rate,
        'npv': npv,
        'fair_spread': fair_spread,
        'fair_spread_bps': fair_spread * 10000,
        'fair_upfront': fair_upfront,
        'premium_leg_npv': premium_leg,
        'protection_leg_npv': protection_leg,
        'survival_probabilities': survival_probs,
        'use_term_structure': use_term_structure
    }
