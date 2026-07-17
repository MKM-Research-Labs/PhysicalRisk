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

"""
Loan-pricing parameters: discount curve, credit-rating spreads, hazard spreads.

The loan coupon a borrower contractually pays is built up from components::

    coupon  =  risk-free discount rate          (DISCOUNT_CURVE, ~4.5%)
            +  credit spread                     (CREDIT_RATING_SPREADS, by rating)
            +  flood hazard spread               (PRS flood pricer — see below)
            +  wind hazard spread                (WIND_HAZARD_SPREADS, static)

The flood component is priced by the platform's analytical Physical Risk Swap
(PRS) pricer rather than a flat lookup: each flood-risk category maps to an
annual flood probability (``FLOOD_CATEGORY_ANNUAL_HAZARD``, EA flood-zone
aligned), which ``models.hazard.prs_analytical.compute_prs_spread`` converts to
a fair CDS-equivalent spread. That call lives in the pricing layer
(``routes._loan_pricing``) because ``config`` must not import ``models``.

Wind has no PRS pricer yet, so it keeps the static ``WIND_HAZARD_SPREADS``
lookup as a placeholder.

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
# Flood hazard → annual flood probability (PRS pricer input)
# ===========================================================================
# Each flood-risk category maps to a representative annual flood probability,
# aligned with the EA flood-zone midpoints in config.models.EA_FLOOD_ZONE_RATES
# (Zone 1 ≈ 0.001, Zone 2 ≈ 0.005, Zone 3a ≈ 0.020, Zone 3b ≈ 0.050). The
# pricing layer feeds this probability to the PRS analytical pricer
# (compute_prs_spread) to obtain the fair flood spread — so the flood component
# of the coupon is genuinely PRS-priced rather than a flat assumption.
FLOOD_CATEGORY_ANNUAL_HAZARD: Dict[str, float] = {
    "very low":  0.001,   # ~1 in 1000  (EA Zone 1)
    "low":       0.005,   # ~1 in 200   (EA Zone 2)
    "medium":    0.010,   # ~1 in 100   (EA Zone 3 boundary)
    "high":      0.020,   # ~1 in 50    (EA Zone 3a)
    "very high": 0.050,   # ~1 in 20    (EA Zone 3b, functional floodplain)
}

# Recovery rate used when PRS-pricing the flood leg. 0% = full loss given a
# flood trigger, matching config.models.RECOVERY_RATES['any_flood'].
PRS_FLOOD_RECOVERY: float = 0.0

# ---------------------------------------------------------------------------
# Wind hazard spreads (static placeholder — no PRS wind pricer yet)
# ---------------------------------------------------------------------------
# Keyed lowercase; lookups normalise case/whitespace. These remain a flat
# lookup until a PRS wind pricer exists to price them like flood.
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


def flood_annual_hazard(category: str) -> float:
    """Annual flood probability for a risk category (PRS pricer input)."""
    return FLOOD_CATEGORY_ANNUAL_HAZARD.get(
        _norm(category),
        FLOOD_CATEGORY_ANNUAL_HAZARD[_norm(DEFAULT_RISK_CATEGORY)])


def wind_hazard_spread(category: str) -> float:
    """Wind hazard spread (decimal) for a risk category (static placeholder)."""
    return WIND_HAZARD_SPREADS.get(_norm(category),
                                   WIND_HAZARD_SPREADS[_norm(DEFAULT_RISK_CATEGORY)])


# Defaults for any pricing input a CDM loan record doesn't supply, so a sparse
# loan still prices instead of raising on a missing kwarg. Mirrors the fallbacks
# in LoanPricer.batch_price_loans.
LOAN_PRICING_INPUT_DEFAULTS: Dict[str, float] = {
    "gross_annual_income": 50000,
    "interest_rate": 0.035,
    "insurance_rate": 0.002,
    "original_maturity": 30,
    "current_term": 30,
    "recovery_haircut": 0.2,
}
