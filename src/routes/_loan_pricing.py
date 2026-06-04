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

from config.loan import (
    COMMERCIAL_MAX_TERM_YEARS,
    DEFAULT_CREDIT_RATING,
    DEFAULT_RISK_CATEGORY,
    PRS_FLOOD_RECOVERY,
    credit_spread_for_rating,
    discount_rate,
    flood_annual_hazard,
    wind_hazard_spread,
)
from models.hazard.prs_analytical import compute_prs_spread
from models.loan import LoanPricer
from port.cdm import LoanCDM

# Keys the panel is allowed to override. Anything else in the request body is
# ignored so the form can't smuggle in unexpected price_loan kwargs.
OVERRIDE_KEYS = (
    "loan_amount",
    "property_value",
    "gross_annual_income",
    "interest_rate",
    "insurance_rate",
    "original_maturity",
    "current_term",
    "recovery_haircut",
    "flood_risk_category",
    "wind_risk_category",
    "credit_rating",
    # The asset's own modelled flood PRS spread (bps), read from its hazard
    # curve by the calculator when launched from a property/commercial marker.
    # When present it supersedes the coarse flood-category lookup so the flood
    # leg matches the property PRS pricer exactly.
    "flood_spread_bps",
    # The asset's modelled combined flood-OR-wind PRS spread (the union, bps),
    # read from the same hazard curve when the catchment has a coupled typhoon
    # stage. When present the wind leg is PRS-priced as the *incremental* hazard
    # on top of flood (union - flood), so flood + wind == union exactly and the
    # joint flood-and-wind events are not double-counted. Absent for flood-only
    # catchments, in which case the wind leg falls back to the static category.
    "union_spread_bps",
    # The PRS hazard scenario the user picked in the calculator's dropdown
    # (flo | bri | win | faw | fow) and that scenario's modelled spread (bps),
    # read from the asset's hazard-curve peril fan. When present, this single
    # spread becomes the coupon's entire hazard leg, superseding the
    # flood_spread_bps / union_spread_bps split — so the borrower's coupon can
    # be priced against any one of the five peril scenarios, not just the
    # combined flood-OR-wind union.
    "prs_scenario",
    "prs_spread_bps",
    # The asset's net initial yield (passing rent / capital value), forwarded
    # by the calculator when launched from a commercial marker. Applied to the
    # property value it gives the annual passing rent, which becomes the
    # borrower income — so commercial income reflects the asset's real yield
    # instead of the fixed residential default.
    "income_yield",
)

# Override keys whose values are free-text categories, not numbers — kept
# verbatim instead of coerced to float.
_STRING_OVERRIDE_KEYS = frozenset({
    "flood_risk_category",
    "wind_risk_category",
    "credit_rating",
    "prs_scenario",
})

# Defaults for any pricing input the CDM record doesn't supply. Mirrors the
# fallbacks in LoanPricer.batch_price_loans so a sparse loan still
# prices instead of raising a TypeError on a missing kwarg.
_INPUT_DEFAULTS = {
    "gross_annual_income": 50000,
    "interest_rate": 0.035,
    "insurance_rate": 0.002,
    "original_maturity": 30,
    "current_term": 30,
    "recovery_haircut": 0.2,
}

# Scalar pricing outputs returned to the client. The rest of price_loan's
# result is numpy time-series (outstanding_balance, hazard_rates, …) which is
# neither JSON-serialisable nor needed by the panel.
_PRICING_KEYS = (
    "mortgage_value",
    "credit_spread",
    "discount_rate",
    "ltv_factor",
    "flood_risk_factor",
    "annual_payment",
    "monthly_payment",
    "pv_cashflows",
    "pv_losses",
    "discount_to_par",
    "discount_percentage",
    "ltv_ratio",
    "affordability_ratio",
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


# Extra defaults for the standalone calculator: the contractual coupon is
# built up from a credit rating + flood/wind hazard rather than typed in, so
# the calculator seeds a rating and a wind category alongside the flood one.
_STANDALONE_DEFAULTS = {
    "credit_rating": DEFAULT_CREDIT_RATING,
    "flood_risk_category": DEFAULT_RISK_CATEGORY,
    "wind_risk_category": DEFAULT_RISK_CATEGORY,
}


def _build_coupon(term_years: float,
                  credit_rating: str,
                  flood_category: str,
                  wind_category: str,
                  flood_spread_bps: Optional[float] = None,
                  union_spread_bps: Optional[float] = None,
                  prs_spread_bps: Optional[float] = None,
                  prs_scenario: Optional[str] = None) -> Dict[str, Any]:
    """Assemble the contractual coupon from its components.

    ``coupon = risk-free + credit spread + flood spread + wind spread``

    **PRS scenario override.** When ``prs_spread_bps`` is supplied (the user
    picked a hazard scenario in the calculator's dropdown), that single
    modelled spread *is* the coupon's entire hazard leg and supersedes the
    flood/union split below. ``prs_scenario`` (flo | bri | win | faw | fow)
    only labels the leg and controls how it is shown back as a flood/wind
    decomposition (e.g. ``win`` is all wind; ``fow`` splits into flood plus the
    incremental wind). The total hazard always equals the chosen spread.

    The flood spread is *PRS-priced*. There are two sources, in priority order:

    1. **Asset curve** — when ``flood_spread_bps`` is supplied (the calculator
       was launched from a property/commercial asset and read that asset's own
       modelled flood spread from its hazard curve), it is used verbatim. This
       is the property's simulated flood frequency, so the flood leg matches
       the property PRS pricer exactly (no coarse category bucket).
    2. **Category lookup** — otherwise the flood-risk category maps to an annual
       flood probability which the analytical PRS pricer (``compute_prs_spread``)
       converts to a fair CDS-equivalent spread on the risk-free rate. This is
       the fallback for a truly standalone calculator (no asset) or an asset
       with too few flood events to have a hazard curve.

    The wind spread has two sources, in priority order:

    1. **Asset curve (union)** — when ``union_spread_bps`` (the modelled
       flood-OR-wind PRS spread) is supplied alongside an asset flood spread,
       the wind leg is the *incremental* hazard on top of flood. By
       inclusion-exclusion ``union = flood + wind - joint``, so the incremental
       ``wind = union - flood`` is exactly the genuinely-wind-driven frequency
       (the joint flood-and-wind events are already in the flood leg and are not
       double-counted). The total hazard leg then equals the union spread.
    2. **Category lookup** — otherwise wind has no PRS curve, so it falls back
       to the static wind-category spread (flood-only catchments, or a truly
       standalone calculator).

    Returns the total ``rate`` plus the full decomposition (all decimals).
    """
    rf = discount_rate(term_years)
    credit = credit_spread_for_rating(credit_rating)

    # PRS scenario override: one modelled spread drives the whole hazard leg.
    if prs_spread_bps is not None and float(prs_spread_bps) >= 0:
        scenario = (str(prs_scenario).strip().lower() if prs_scenario else "fow")
        total_bps = float(prs_spread_bps)
        total = total_bps / 10000.0
        if scenario == "win":
            # Pure wind frequency — no flood component.
            flood_leg, wind_leg = 0.0, total
        elif scenario == "fow":
            # Union splits into flood + incremental wind so the legs still read
            # naturally; the asset flood spread (BRI-preferred) is the base when
            # available, else the whole leg is flood.
            base_bps = (float(flood_spread_bps)
                        if (flood_spread_bps is not None and flood_spread_bps >= 0)
                        else total_bps)
            base_bps = min(base_bps, total_bps)
            flood_leg, wind_leg = base_bps / 10000.0, (total_bps - base_bps) / 10000.0
        else:
            # flo / bri / faw are flood-side scenarios — shown as a flood leg.
            flood_leg, wind_leg = total, 0.0
        return {
            "rate": rf + credit + total,
            "risk_free": rf,
            "credit_spread": credit,
            "flood_spread": flood_leg,
            "wind_spread": wind_leg,
            "hazard_spread": total,
            "flood_annual_hazard": total,
            "flood_priced_by": "PRS (scenario: %s)" % scenario,
            "wind_priced_by": "PRS (scenario: %s)" % scenario,
            "prs_scenario": scenario,
            "prs_spread_bps": total_bps,
            "credit_rating": (str(credit_rating).strip().upper()
                              if credit_rating else DEFAULT_CREDIT_RATING),
        }

    asset_flood = flood_spread_bps is not None and flood_spread_bps >= 0
    if asset_flood:
        # Asset's own modelled flood spread — recovery is 0 for flood, so the
        # spread is, to first order, the annual flood probability itself.
        flood_bps = float(flood_spread_bps)
        annual_hazard = flood_bps / 10000.0
        flood_source = "PRS (asset curve)"
    else:
        annual_hazard = flood_annual_hazard(flood_category)
        flood_bps = compute_prs_spread(
            annual_hazard_rate=annual_hazard,
            tenor=max(int(round(term_years)), 1),
            recovery=PRS_FLOOD_RECOVERY,
            risk_free_rate=rf,
        )
        flood_source = "PRS (category)"
    flood = flood_bps / 10000.0

    # Wind leg. Only PRS-price it from the union when the flood leg is *also*
    # asset-priced — mixing an asset union against a coarse flood-category leg
    # would compare incompatible scales. union >= flood always holds (the union
    # count >= the flood count), but clamp at 0 defensively.
    if union_spread_bps is not None and union_spread_bps >= 0 and asset_flood:
        wind_bps = max(0.0, float(union_spread_bps) - flood_bps)
        wind = wind_bps / 10000.0
        wind_source = "PRS (asset curve, union)"
    else:
        wind = wind_hazard_spread(wind_category)
        wind_source = "static"

    return {
        "rate": rf + credit + flood + wind,
        "risk_free": rf,
        "credit_spread": credit,
        "flood_spread": flood,
        "wind_spread": wind,
        "hazard_spread": flood + wind,
        "flood_annual_hazard": annual_hazard,
        "flood_priced_by": flood_source,
        "wind_priced_by": wind_source,
        "credit_rating": (str(credit_rating).strip().upper()
                          if credit_rating else DEFAULT_CREDIT_RATING),
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
    effective["interest_rate"] = coupon["rate"]

    priced = _price_effective(effective, discount_rate=coupon["risk_free"])
    return {
        "mortgage_id": None,
        "property_id": None,
        "asset_class": asset_class,
        "coupon": coupon,
        **priced,
    }
