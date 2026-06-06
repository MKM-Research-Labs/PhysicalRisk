# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.
#
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""Shared loan-pricer bridge used by the property and commercial routes.

Wraps ``LoanCDM.to_pricer_inputs`` + ``LoanPricer.price_loan`` and
returns a JSON-serialisable ``{inputs, pricing}`` payload. The same helper
backs the initial (GET) load of the Loan Pricer panel and every live
re-price (POST with user overrides), so the editable form and the read-only
derivation share one code path.
"""

from typing import Any, Dict, Optional

from config.loan import COMMERCIAL_MAX_TERM_YEARS
from port.cdm import LoanCDM

from routes._loan_pricing._constants import (
    OVERRIDE_KEYS,
    _INPUT_DEFAULTS,
    _PRICING_KEYS,
    _STANDALONE_DEFAULTS,
    _STRING_OVERRIDE_KEYS,
)
from routes._loan_pricing._helpers import (
    _apply_overrides,
    _coerce_number,
    _price_effective,
)
from routes._loan_pricing._coupon import _build_coupon

__all__ = [
    "compute_loan_pricing",
    "compute_standalone_pricing",
]


def compute_loan_pricing(mortgage_cdm: Dict[str, Any],
                         overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Price a CDM loan record, optionally with user overrides.

    Args:
        mortgage_cdm: Nested CDM mortgage dict (with top-level ``Mortgage`` key).
        overrides: Optional pricing-input overrides from the editable panel.

    Returns:
        ``{"mortgage_id", "property_id", "inputs", "pricing"}`` — all
        JSON-serialisable. Raises ``ValueError`` if loan amount or property
        value can't be resolved (nothing meaningful to price).
    """
    cdm = LoanCDM()
    base = cdm.to_pricer_inputs(mortgage_cdm)

    mortgage_id = base.pop("mortgage_id", None)
    property_id = base.pop("property_id", None)

    effective: Dict[str, Any] = {**_INPUT_DEFAULTS, **base}
    effective = _apply_overrides(effective, overrides)

    priced = _price_effective(effective)
    return {
        "mortgage_id": mortgage_id,
        "property_id": property_id,
        **priced,
    }


def compute_standalone_pricing(inputs: Optional[Dict[str, Any]] = None,
                               asset_class: str = "residential") -> Dict[str, Any]:
    """Price a loan from user-supplied inputs alone — no CDM record.

    Backs the standalone Loan Calculator launched from the main screen, which
    is not tied to any property/loan. The caller supplies all pricing inputs
    (loan amount and property value are mandatory); anything omitted falls back
    to ``_INPUT_DEFAULTS`` / ``_STANDALONE_DEFAULTS``.

    The contractual coupon is *built up* from components rather than supplied::

        coupon = risk-free (discount curve) + credit spread (rating)
                 + flood hazard spread + wind hazard spread

    Expected cashflows are then discounted on the risk-free rate, so the
    coupon's margin over risk-free is what pays for credit + hazard. Any
    ``interest_rate`` in the inputs is ignored (the coupon is derived).

    Args:
        inputs: Pricing inputs keyed by ``OVERRIDE_KEYS``. ``loan_amount`` and
            ``property_value`` are required.
        asset_class: ``"residential"`` or ``"commercial"``. Commercial loans
            cap the term at ``COMMERCIAL_MAX_TERM_YEARS`` (7 years).

    Returns:
        ``{"mortgage_id": None, "property_id": None, "asset_class",
        "inputs", "pricing", "coupon"}`` — all JSON-serialisable. Raises
        ``ValueError`` if loan amount or property value is missing.
    """
    effective: Dict[str, Any] = {**_INPUT_DEFAULTS, **_STANDALONE_DEFAULTS}
    effective = _apply_overrides(effective, inputs)

    # Commercial loans max out at 7 years.
    if asset_class == "commercial":
        cap = COMMERCIAL_MAX_TERM_YEARS
        effective["original_maturity"] = min(effective["original_maturity"], cap)
        effective["current_term"] = min(effective["current_term"], cap)

    # Derive the borrower income from the asset's net initial yield, if the
    # calculator forwarded one (commercial markers). Annual passing rent =
    # net initial yield x capital value, so the income tracks the property
    # value and the asset's real yield rather than a fixed default. The yield
    # itself is not a price_loan kwarg, so it's consumed here.
    income_yield = effective.pop("income_yield", None)
    if income_yield is not None and float(income_yield) > 0:
        effective["gross_annual_income"] = round(
            float(income_yield) * float(effective["property_value"]), 2)

    # Build the contractual coupon from its components and use it as the rate
    # the borrower pays; discount expected cashflows on the risk-free rate.
    coupon = _build_coupon(
        term_years=effective["current_term"],
        credit_rating=effective.get("credit_rating"),
        flood_category=effective.get("flood_risk_category"),
        wind_category=effective.get("wind_risk_category"),
        flood_spread_bps=effective.get("flood_spread_bps"),
        union_spread_bps=effective.get("union_spread_bps"),
        prs_spread_bps=effective.get("prs_spread_bps"),
        prs_scenario=effective.get("prs_scenario"),
    )
    # A user-supplied contractual coupon (left panel) overrides the model-derived
    # rate the borrower pays; the model coupon stays in ``coupon`` for display as
    # the "Original Contractual Coupon". Cashflows still discount on the risk-free
    # curve, so the override only moves the contractual leg.
    user_coupon = effective.pop("contractual_coupon", None)
    if user_coupon is not None and float(user_coupon) > 0:
        effective["interest_rate"] = float(user_coupon)
    else:
        effective["interest_rate"] = coupon["rate"]

    priced = _price_effective(effective, discount_rate=coupon["risk_free"])
    return {
        "mortgage_id": None,
        "property_id": None,
        "asset_class": asset_class,
        "coupon": coupon,
        **priced,
    }
