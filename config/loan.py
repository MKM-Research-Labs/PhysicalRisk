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
Loan-pricing parameters: discount curve, credit-rating spreads, hazard spreads.

The loan coupon a borrower contractually pays is built up from components::

    coupon  =  risk-free discount rate          (DISCOUNT_CURVE, ~4.5%)
            +  credit spread                     (CREDIT_RATING_SPREADS, by rating)
            +  hazard spread                     (FLOOD_ + WIND_HAZARD_SPREADS)

A typical BBB borrower on a Medium flood / Medium wind asset at a ~3y tenor
therefore prices near 7.0%::

    0.045 (risk-free) + 0.015 (BBB) + 0.006 (flood) + 0.004 (wind) = 0.070

The expected-cashflow present values are discounted on the risk-free curve
(``discount_rate``), NOT on the coupon — so the contractual margin over
risk-free is what compensates for credit + hazard.
"""

from typing import Dict, List

# ===========================================================================
# Risk-free discount curve
# ===========================================================================
# Simple, gently-upward sloping curve centred on ~4.5%. Keyed by tenor in
# whole years. ``discount_rate(term)`` linearly interpolates / clamps to the
# curve endpoints, so any term resolves to a rate.
DISCOUNT_CURVE: Dict[int, float] = {
    1:  0.0420,   # 4.20%
    2:  0.0440,   # 4.40%
    3:  0.0450,   # 4.50%  ← reference point
    5:  0.0460,   # 4.60%
    7:  0.0460,   # 4.60%
    10: 0.0470,   # 4.70%
    20: 0.0475,   # 4.75%
    30: 0.0480,   # 4.80%
}

# ===========================================================================
# Credit-rating spreads (S&P-style letter grades → spread, decimal)
# ===========================================================================
# Added to the risk-free rate to reflect borrower credit quality. Calibrated
# so investment-grade names sit a little over risk-free and sub-investment /
# high-yield names carry materially more.
CREDIT_RATING_SPREADS: Dict[str, float] = {
    "AAA": 0.0050,   #  50 bps
    "AA":  0.0075,   #  75 bps
    "A":   0.0100,   # 100 bps
    "BBB": 0.0150,   # 150 bps  ← default / reference
    "BB":  0.0275,   # 275 bps
    "B":   0.0450,   # 450 bps
    "CCC": 0.0700,   # 700 bps
}

# Order best→worst, for dropdowns / iteration.
CREDIT_RATINGS: List[str] = ["AAA", "AA", "A", "BBB", "BB", "B", "CCC"]
DEFAULT_CREDIT_RATING: str = "BBB"

# ===========================================================================
# Hazard spreads (physical risk → spread, decimal)
# ===========================================================================
# Keyed lowercase; lookups normalise case/whitespace so "Very High",
# "very high" and " Very high " all resolve. Flood is weighted a little more
# heavily than wind for residential/commercial real estate.
FLOOD_HAZARD_SPREADS: Dict[str, float] = {
    "very low":  0.0010,
    "low":       0.0030,
    "medium":    0.0060,
    "high":      0.0120,
    "very high": 0.0220,
}

WIND_HAZARD_SPREADS: Dict[str, float] = {
    "very low":  0.0005,
    "low":       0.0020,
    "medium":    0.0040,
    "high":      0.0080,
    "very high": 0.0150,
}

# Category labels (display order), low→high risk.
RISK_CATEGORIES: List[str] = ["Very low", "Low", "Medium", "High", "Very high"]
DEFAULT_RISK_CATEGORY: str = "Medium"

# ===========================================================================
# Term caps
# ===========================================================================
# Commercial loans are capped at 7 years; residential is uncapped here (the
# pricer still bounds current_term to original_maturity).
COMMERCIAL_MAX_TERM_YEARS: int = 7


# ===========================================================================
# Helpers
# ===========================================================================
def _norm(category: str) -> str:
    """Normalise a risk-category label for case/space-insensitive lookup."""
    return (category or "").strip().lower()


def discount_rate(term_years: float) -> float:
    """Risk-free discount rate for a given term, interpolated off DISCOUNT_CURVE.

    Linearly interpolates between the two bracketing tenors; clamps to the
    first/last curve point for terms outside the curve's range.
    """
    tenors = sorted(DISCOUNT_CURVE)
    if term_years <= tenors[0]:
        return DISCOUNT_CURVE[tenors[0]]
    if term_years >= tenors[-1]:
        return DISCOUNT_CURVE[tenors[-1]]
    for lo, hi in zip(tenors, tenors[1:]):
        if lo <= term_years <= hi:
            frac = (term_years - lo) / (hi - lo)
            return DISCOUNT_CURVE[lo] + frac * (DISCOUNT_CURVE[hi] - DISCOUNT_CURVE[lo])
    return DISCOUNT_CURVE[tenors[-1]]


def credit_spread_for_rating(rating: str) -> float:
    """Credit spread (decimal) for a letter rating; falls back to the default."""
    if rating is None:
        return CREDIT_RATING_SPREADS[DEFAULT_CREDIT_RATING]
    return CREDIT_RATING_SPREADS.get(
        str(rating).strip().upper(),
        CREDIT_RATING_SPREADS[DEFAULT_CREDIT_RATING],
    )


def flood_hazard_spread(category: str) -> float:
    """Flood hazard spread (decimal) for a risk category."""
    return FLOOD_HAZARD_SPREADS.get(_norm(category),
                                    FLOOD_HAZARD_SPREADS[_norm(DEFAULT_RISK_CATEGORY)])


def wind_hazard_spread(category: str) -> float:
    """Wind hazard spread (decimal) for a risk category."""
    return WIND_HAZARD_SPREADS.get(_norm(category),
                                   WIND_HAZARD_SPREADS[_norm(DEFAULT_RISK_CATEGORY)])


def build_coupon(term_years: float,
                 credit_rating: str = DEFAULT_CREDIT_RATING,
                 flood_category: str = DEFAULT_RISK_CATEGORY,
                 wind_category: str = DEFAULT_RISK_CATEGORY) -> Dict[str, float]:
    """Assemble the contractual coupon from its components.

    Returns a dict with the total ``rate`` plus its decomposition into
    ``risk_free``, ``credit_spread``, ``flood_spread``, ``wind_spread`` and the
    combined ``hazard_spread`` — all decimals.
    """
    rf = discount_rate(term_years)
    cs = credit_spread_for_rating(credit_rating)
    fl = flood_hazard_spread(flood_category)
    wi = wind_hazard_spread(wind_category)
    return {
        "rate": rf + cs + fl + wi,
        "risk_free": rf,
        "credit_spread": cs,
        "flood_spread": fl,
        "wind_spread": wi,
        "hazard_spread": fl + wi,
        "credit_rating": (str(credit_rating).strip().upper()
                          if credit_rating else DEFAULT_CREDIT_RATING),
    }
