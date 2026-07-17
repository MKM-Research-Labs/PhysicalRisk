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

"""I/O utilities for PRS hazard curve loading and result formatting."""

import json
import logging
from typing import Dict

logger = logging.getLogger(__name__)


def load_hazard_curves(filepath: str) -> Dict:
    """Load hazard curves from JSON file."""
    with open(filepath) as f:
        return json.load(f)


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
