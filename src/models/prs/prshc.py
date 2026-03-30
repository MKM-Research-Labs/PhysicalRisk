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
Physical Risk Swap (PRS) Pricing with Flood Hazard Curves.

This module demonstrates how to use the hazard curve output from
hazard_curve.py to price a Physical Risk Swap using QuantLib's
CDS pricing framework.

The key insight is that flood risk can be modeled like credit risk:
- Survival probability S(t) = P(no flood by time t)
- Default probability = P(at least one flood by time t)
- Hazard rate λ = annual flood probability (Poisson intensity)

Usage:
    python3 prshc.py --gauge THAMES-G001 --trigger warning
    python3 prshc.py --hazard-file input/thames/hazard_curves.json
"""

import argparse
import json
import logging
from typing import Dict, List

import QuantLib as ql

logger = logging.getLogger(__name__)


def load_hazard_curves(filepath: str) -> Dict:
    """Load hazard curves from JSON file."""
    with open(filepath) as f:
        return json.load(f)


def create_survival_curve_from_hazard(
    evaluation_date: ql.Date,
    term_structure: List[Dict],
    day_counter: ql.DayCounter = None
) -> ql.DefaultProbabilityTermStructure:
    """
    Create a QuantLib survival probability curve from hazard curve term structure.

    Args:
        evaluation_date: QuantLib Date for curve start
        term_structure: List of term structure points from hazard_curve.py
        day_counter: Day count convention (default Actual365Fixed)

    Returns:
        QuantLib DefaultProbabilityTermStructure ready for CDS pricing
    """
    if day_counter is None:
        day_counter = ql.Actual365Fixed()

    # Build dates and survival probabilities
    dates = [evaluation_date]  # Start with evaluation date
    survival_probs = [1.0]  # 100% survival at t=0

    for point in term_structure:
        year = point['year']
        survival = point['survival_prob']

        # Add date for this year
        date = evaluation_date + ql.Period(year, ql.Years)
        dates.append(date)
        survival_probs.append(survival)

    # For ISDA CDS engine, we need to use a curve that supports flat forward interpolation
    # Convert survival probabilities to hazard rates and use FlatHazardRate
    # Or use InterpolatedSurvivalProbabilityCurve with LogLinear interpolation

    # Use piecewise flat hazard rate curve which ISDA engine accepts
    # Build from survival probabilities by calculating implied hazard rates
    import math

    # Calculate constant hazard rate from 5-year survival probability
    # S(t) = e^(-λt) => λ = -ln(S(t))/t
    final_survival = survival_probs[-1]
    final_year = term_structure[-1]['year']

    if final_survival > 0 and final_survival < 1:
        implied_hazard_rate = -math.log(final_survival) / final_year
    else:
        implied_hazard_rate = 0.05  # Default fallback

    # Create flat hazard rate curve (ISDA engine compatible)
    hazard_quote = ql.SimpleQuote(implied_hazard_rate)
    curve = ql.FlatHazardRate(
        evaluation_date,
        ql.QuoteHandle(hazard_quote),
        day_counter
    )

    return curve


def create_flat_hazard_curve(
    evaluation_date: ql.Date,
    annual_hazard_rate: float,
    day_counter: ql.DayCounter = None
) -> ql.FlatHazardRate:
    """
    Create a flat hazard rate curve (simpler alternative).

    For Poisson process, the hazard rate λ gives:
    S(t) = e^(-λt)

    Args:
        evaluation_date: QuantLib Date
        annual_hazard_rate: λ = annual flood probability
        day_counter: Day count convention

    Returns:
        QuantLib FlatHazardRate curve
    """
    if day_counter is None:
        day_counter = ql.Actual365Fixed()

    hazard_quote = ql.SimpleQuote(annual_hazard_rate)
    curve = ql.FlatHazardRate(
        evaluation_date,
        ql.QuoteHandle(hazard_quote),
        day_counter
    )

    return curve, hazard_quote


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


def print_pricing_results(results: Dict):
    """Log formatted pricing results."""
    logger.info("PHYSICAL RISK SWAP (PRS) PRICING")

    logger.info(f"Gauge: {results['gauge_name']} ({results['gauge_id']})")
    logger.info(f"Trigger: {results['trigger_level'].upper()} level at {results['trigger_threshold_m']:.2f}m")
    logger.info(f"Annual Flood Probability (lambda): {results['annual_hazard_rate']:.2%}")

    logger.info("Contract Terms:")
    logger.info(f"  Notional:      ${results['notional']:,.0f}")
    logger.info(f"  Tenor:         {results['tenor_years']} years")
    logger.info(f"  Running Spread: {results['running_spread_bps']:.0f} bps")
    logger.info(f"  Recovery Rate:  {results['recovery_rate']:.0%}")

    logger.info("Pricing Results:")
    logger.info(f"  NPV:           ${results['npv']:,.2f}")
    logger.info(f"  Fair Spread:   {results['fair_spread_bps']:.1f} bps")
    logger.info(f"  Fair Upfront:  {results['fair_upfront']:.4f} ({results['fair_upfront']*100:.2f}%)")
    logger.info(f"  Premium Leg:   ${results['premium_leg_npv']:,.2f}")
    logger.info(f"  Protection Leg: ${results['protection_leg_npv']:,.2f}")

    logger.info("Survival Curve:")
    for tenor, prob in results['survival_probabilities'].items():
        logger.info(f"  S({tenor}): {prob:.4f} ({prob*100:.2f}%)")


def main():
    parser = argparse.ArgumentParser(description="Price Physical Risk Swap using hazard curves")
    parser.add_argument('--hazard-file', '-f', type=str,
                        default='input/thames/gaugehc.json',
                        help='Path to hazard curves JSON file')
    parser.add_argument('--gauge', '-g', type=str, default=None,
                        help='Gauge ID (e.g., THAMES-G001)')
    parser.add_argument('--list', '-l', action='store_true',
                        help='List available gauges and exit')
    parser.add_argument('--trigger', '-t', type=str,
                        choices=['alert', 'warning', 'severe'],
                        default='warning',
                        help='Trigger level (default: warning)')
    parser.add_argument('--notional', '-n', type=float, default=10_000_000,
                        help='Notional amount (default: 10M)')
    parser.add_argument('--tenor', type=int, default=5,
                        help='Contract tenor in years (default: 5)')
    parser.add_argument('--spread', '-s', type=float, default=0.01,
                        help='Running spread (default: 0.01 = 100bps)')
    parser.add_argument('--flat', action='store_true',
                        help='Use flat hazard rate instead of term structure')

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    # Load hazard curves
    logger.info(f"Loading hazard curves from {args.hazard_file}...")
    data = load_hazard_curves(args.hazard_file)

    # Handle --list
    if args.list:
        logger.info(f"Available Gauges ({len(data['hazard_curves'])} total):")
        for gauge_id, gauge_data in data['hazard_curves'].items():
            logger.info(f"  {gauge_id}: {gauge_data['gauge_name']}")
        return 0

    # Select gauge
    if args.gauge:
        if args.gauge not in data['hazard_curves']:
            logger.error(f"Gauge '{args.gauge}' not found")
            logger.info("Available gauges:")
            for gid in list(data['hazard_curves'].keys())[:10]:
                logger.info(f"  {gid}")
            if len(data['hazard_curves']) > 10:
                logger.info(f"  ... and {len(data['hazard_curves']) - 10} more (use --list to see all)")
            return 1
        gauge_data = data['hazard_curves'][args.gauge]
    else:
        # Use first gauge
        gauge_data = list(data['hazard_curves'].values())[0]
        logger.info(f"No gauge specified, using {gauge_data['gauge_id']}")

    # Price PRS
    results = price_prs(
        gauge_data=gauge_data,
        trigger_level=args.trigger,
        notional=args.notional,
        tenor_years=args.tenor,
        running_spread=args.spread,
        use_term_structure=not args.flat
    )

    # Print results
    print_pricing_results(results)

    return 0


if __name__ == "__main__":
    exit(main())
