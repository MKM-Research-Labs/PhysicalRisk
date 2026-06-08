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

"""Constant tables for the loan-pricer bridge (override keys, defaults)."""

from config.loan import DEFAULT_CREDIT_RATING, DEFAULT_RISK_CATEGORY


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
    # (flo | bri | win | faw | fow | bow | baw) and that scenario's modelled
    # spread (bps), read from the asset's hazard-curve peril fan. When present,
    # this single spread becomes the coupon's entire hazard leg, superseding the
    # flood_spread_bps / union_spread_bps split — so the borrower's coupon can
    # be priced against any one of the peril scenarios, not just the combined
    # flood-OR-wind union.
    "prs_scenario",
    "prs_spread_bps",
    # The asset's modelled independent-peril legs (bps), read from the same
    # hazard curve (spread_decomposition.{fire,seismic}_spread_bps, written by
    # the commercial hazard route's fire/seismic read-time joins), plus the two
    # binary on/off toggles from the calculator's peril buttons. When a toggle
    # is on and its leg is present, that leg is folded into the all-in coupon by
    # root-sum-of-squares alongside the flood/wind basis; off legs are excluded.
    "fire_spread_bps",
    "seismic_spread_bps",
    "include_fire",
    "include_seismic",
    # The asset's net initial yield (passing rent / capital value), forwarded
    # by the calculator when launched from a commercial marker. Applied to the
    # property value it gives the annual passing rent, which becomes the
    # borrower income — so commercial income reflects the asset's real yield
    # instead of the fixed residential default.
    "income_yield",
    # User-defined contractual coupon (decimal) from the standalone calculator's
    # left panel. When supplied it overrides the model-derived coupon as the rate
    # the borrower pays; the model coupon is still returned (as ``coupon``) for
    # display as the "Original Contractual Coupon". Blank -> use the model coupon.
    "contractual_coupon",
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


# Extra defaults for the standalone calculator: the contractual coupon is
# built up from a credit rating + flood/wind hazard rather than typed in, so
# the calculator seeds a rating and a wind category alongside the flood one.
_STANDALONE_DEFAULTS = {
    "credit_rating": DEFAULT_CREDIT_RATING,
    "flood_risk_category": DEFAULT_RISK_CATEGORY,
    "wind_risk_category": DEFAULT_RISK_CATEGORY,
}
