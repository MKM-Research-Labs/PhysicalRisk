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

"""Override coercion / application and the JSON-safe pricing runner."""

from typing import Any, Dict, Optional

from models.loan import LoanPricer

from routes._loan_pricing._constants import (
    OVERRIDE_KEYS,
    _PRICING_KEYS,
    _STRING_OVERRIDE_KEYS,
)


def _coerce_number(value: Any) -> Any:
    """Cast numeric-looking override values to float; leave others untouched."""
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return value
    return value


def _apply_overrides(effective: Dict[str, Any],
                     overrides: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Overlay user-supplied overrides onto the effective input set.

    Only keys in ``OVERRIDE_KEYS`` are honoured; blank/None values are
    ignored so the form can clear nothing accidentally.
    """
    if not overrides:
        return effective
    for key in OVERRIDE_KEYS:
        if key in overrides and overrides[key] is not None and overrides[key] != "":
            if key in _STRING_OVERRIDE_KEYS:
                effective[key] = overrides[key]
            else:
                effective[key] = _coerce_number(overrides[key])
    return effective


def _price_effective(effective: Dict[str, Any],
                     discount_rate: Optional[float] = None) -> Dict[str, Any]:
    """Run the pricer over a resolved input set and return JSON-safe payload.

    Raises ``ValueError`` if loan amount or property value is missing
    (nothing meaningful to price).

    ``discount_rate`` (risk-free) is forwarded to the pricer; when None the
    engine discounts at the contractual coupon (legacy behaviour).
    """
    if not effective.get("loan_amount") or not effective.get("property_value"):
        raise ValueError("Cannot price loan: missing loan amount or property value")

    pricer = LoanPricer()
    result = pricer.price_loan(
        loan_amount=effective["loan_amount"],
        property_value=effective["property_value"],
        gross_annual_income=effective["gross_annual_income"],
        interest_rate=effective["interest_rate"],
        insurance_rate=effective["insurance_rate"],
        original_maturity=effective["original_maturity"],
        current_term=effective["current_term"],
        recovery_haircut=effective["recovery_haircut"],
        flood_risk_category=effective.get("flood_risk_category"),
        discount_rate=discount_rate,
    )

    pricing = {k: float(result[k]) for k in _PRICING_KEYS}
    inputs = {
        k: (float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else v)
        for k, v in effective.items()
    }
    return {"inputs": inputs, "pricing": pricing}
