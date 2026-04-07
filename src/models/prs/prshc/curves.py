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

"""Hazard and survival curve construction for PRS pricing."""

import logging
import math
from typing import Dict, List, Tuple

import QuantLib as ql

logger = logging.getLogger(__name__)


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

    # Calculate constant hazard rate from 5-year survival probability
    # S(t) = e^(-lambda*t) => lambda = -ln(S(t))/t
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

    For Poisson process, the hazard rate lambda gives:
    S(t) = e^(-lambda*t)

    Args:
        evaluation_date: QuantLib Date
        annual_hazard_rate: lambda = annual flood probability
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
