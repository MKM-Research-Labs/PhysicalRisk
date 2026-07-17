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

"""Tests for the standalone Loan Calculator endpoint + pricing helper (part 1).

The standalone calculator is launched from the asset right-click menu but is
asset-independent: the client supplies every pricing input and POSTs to
``/api/v1/loan-pricer`` (no property/loan id). It is backed by
``routes._loan_pricing.compute_standalone_pricing``.
"""

import pytest


# ===========================================================================
# POST /api/v1/loan-pricer  (standalone — no asset id)
# ===========================================================================

class TestStandaloneLoanPricerRoute:

    def test_options_returns_ok(self, prop_client):
        client, _ = prop_client
        r = client.options("/api/v1/loan-pricer")
        assert r.status_code == 200

    def test_prices_from_inputs_key(self, prop_client):
        client, _ = prop_client
        r = client.post("/api/v1/loan-pricer", json={"inputs": {
            "loan_amount": 200000,
            "property_value": 300000,
            "interest_rate": 0.035,
            "flood_risk_category": "Medium",
        }})
        assert r.status_code == 200
        data = r.get_json()
        assert data["status"] == "success"
        # Standalone: not tied to any record.
        assert data["property_id"] is None
        assert data["mortgage_id"] is None
        assert "mortgage_value" in data["pricing"]
        assert data["inputs"]["loan_amount"] == 200000

    def test_bare_body_accepted(self, prop_client):
        """A bare {...} of fields (no inputs/overrides wrapper) prices too."""
        client, _ = prop_client
        r = client.post("/api/v1/loan-pricer", json={
            "loan_amount": 150000,
            "property_value": 250000,
        })
        assert r.status_code == 200
        assert r.get_json()["status"] == "success"

    def test_defaults_fill_missing_inputs(self, prop_client):
        client, _ = prop_client
        r = client.post("/api/v1/loan-pricer", json={"inputs": {
            "loan_amount": 200000,
            "property_value": 300000,
        }})
        data = r.get_json()
        # Coupon is derived from defaults (BBB / Medium flood / Medium wind),
        # not typed in: it should land in a sensible band around 7%.
        coupon = data["coupon"]
        assert coupon["credit_rating"] == "BBB"
        assert 0.06 <= coupon["rate"] <= 0.08
        # The derived coupon is used as the contractual interest rate.
        assert data["inputs"]["interest_rate"] == coupon["rate"]
        # Discount is the risk-free curve point, well below the coupon.
        assert data["pricing"]["discount_rate"] == coupon["risk_free"]
        assert coupon["risk_free"] < coupon["rate"]

    def test_user_contractual_coupon_overrides_model_rate(self, prop_client):
        """A user-supplied contractual coupon becomes the rate the borrower
        pays, while the returned ``coupon`` still reports the model-derived rate
        (the "Original Contractual Coupon"). The risk-free discount is unchanged."""
        client, _ = prop_client
        r = client.post("/api/v1/loan-pricer", json={"inputs": {
            "loan_amount": 200000,
            "property_value": 300000,
            "credit_rating": "BBB",
            "contractual_coupon": 0.09,
        }})
        data = r.get_json()
        coupon = data["coupon"]
        # The model coupon is preserved for display, distinct from the override.
        assert coupon["rate"] != pytest.approx(0.09)
        # The borrower pays the user-defined coupon.
        assert data["inputs"]["interest_rate"] == pytest.approx(0.09)
        # Discounting still happens on the risk-free curve, not the override.
        assert data["pricing"]["discount_rate"] == coupon["risk_free"]
        # The override is consumed, not echoed back as a pricing input.
        assert "contractual_coupon" not in data["inputs"]

    def test_blank_contractual_coupon_uses_model_rate(self, prop_client):
        """Without a user coupon, the borrower pays the model-derived rate."""
        client, _ = prop_client
        r = client.post("/api/v1/loan-pricer", json={"inputs": {
            "loan_amount": 200000, "property_value": 300000, "credit_rating": "BBB",
        }})
        data = r.get_json()
        assert data["inputs"]["interest_rate"] == data["coupon"]["rate"]

    def test_coupon_decomposes_to_components(self, prop_client):
        client, _ = prop_client
        r = client.post("/api/v1/loan-pricer", json={"inputs": {
            "loan_amount": 200000,
            "property_value": 300000,
            "credit_rating": "BBB",
            "flood_risk_category": "Medium",
            "wind_risk_category": "Medium",
        }})
        c = r.get_json()["coupon"]
        assert c["rate"] == pytest.approx(
            c["risk_free"] + c["credit_spread"] + c["flood_spread"] + c["wind_spread"])
        assert c["hazard_spread"] == pytest.approx(c["flood_spread"] + c["wind_spread"])

    def test_flood_leg_is_prs_priced(self, prop_client):
        """The flood spread must come from the analytical PRS pricer, not a
        flat lookup: it equals compute_prs_spread() for the category's annual
        hazard at the loan tenor, on the risk-free curve."""
        from config.loan import flood_annual_hazard, PRS_FLOOD_RECOVERY
        from models.hazard.prs_analytical import compute_prs_spread

        client, _ = prop_client
        r = client.post("/api/v1/loan-pricer", json={"inputs": {
            "loan_amount": 200000, "property_value": 300000,
            "credit_rating": "BBB", "flood_risk_category": "High",
            "wind_risk_category": "Medium", "current_term": 30,
        }})
        c = r.get_json()["coupon"]
        assert c["flood_priced_by"] == "PRS (category)"
        assert c["wind_priced_by"] == "static"
        assert c["flood_annual_hazard"] == pytest.approx(flood_annual_hazard("High"))

        expected_bps = compute_prs_spread(
            annual_hazard_rate=flood_annual_hazard("High"),
            tenor=30, recovery=PRS_FLOOD_RECOVERY,
            risk_free_rate=c["risk_free"])
        assert c["flood_spread"] == pytest.approx(expected_bps / 10000.0)

    def test_asset_flood_spread_overrides_category(self, prop_client):
        """When the calculator passes the asset's own modelled flood spread
        (flood_spread_bps, read from its hazard curve), it drives the flood
        leg verbatim instead of the coarse flood-category lookup — so the leg
        matches the property PRS pricer (e.g. 390 bp -> 3.9%)."""
        client, _ = prop_client
        r = client.post("/api/v1/loan-pricer", json={"inputs": {
            "loan_amount": 200000, "property_value": 300000,
            "flood_risk_category": "Medium",   # would be ~1% via the lookup
            "flood_spread_bps": 390,           # asset curve says 3.9%
        }})
        c = r.get_json()["coupon"]
        assert c["flood_priced_by"] == "PRS (asset curve)"
        assert c["flood_spread"] == pytest.approx(0.039)
        assert c["flood_annual_hazard"] == pytest.approx(0.039)

    def test_union_spread_prices_wind_leg_incrementally(self, prop_client):
        """When the calculator passes the asset's modelled flood-OR-wind union
        (union_spread_bps) alongside the asset flood spread, the wind leg is the
        incremental hazard union - flood (inclusion-exclusion), so flood + wind
        equals the union exactly and the joint events are not double-counted."""
        client, _ = prop_client
        r = client.post("/api/v1/loan-pricer", json={"inputs": {
            "loan_amount": 200000, "property_value": 300000,
            "flood_risk_category": "Medium",
            "flood_spread_bps": 300,    # flood marginal 3.0%
            "union_spread_bps": 500,    # flood OR wind 5.0%
        }})
        c = r.get_json()["coupon"]
        assert c["flood_priced_by"] == "PRS (asset curve)"
        assert c["wind_priced_by"] == "PRS (asset curve, union)"
        assert c["flood_spread"] == pytest.approx(0.030)
        # Wind leg is the incremental union - flood = 5.0% - 3.0% = 2.0%.
        assert c["wind_spread"] == pytest.approx(0.020)
        # Total hazard leg equals the union — no double-count of joint events.
        assert c["hazard_spread"] == pytest.approx(0.050)

    def test_union_below_flood_clamps_wind_to_zero(self, prop_client):
        """Defensive: union >= flood always holds in the model, but a union at
        or below the flood spread must clamp the incremental wind leg to 0
        rather than go negative."""
        client, _ = prop_client
        r = client.post("/api/v1/loan-pricer", json={"inputs": {
            "loan_amount": 200000, "property_value": 300000,
            "flood_spread_bps": 400,
            "union_spread_bps": 400,    # equal -> no incremental wind
        }})
        c = r.get_json()["coupon"]
        assert c["wind_spread"] == pytest.approx(0.0)
        assert c["hazard_spread"] == pytest.approx(0.040)

    def test_union_ignored_without_asset_flood(self, prop_client):
        """A union spread without an asset flood leg must NOT PRS-price wind:
        mixing an asset union against a coarse flood-category leg would compare
        incompatible scales, so the wind leg stays on the static category."""
        client, _ = prop_client
        r = client.post("/api/v1/loan-pricer", json={"inputs": {
            "loan_amount": 200000, "property_value": 300000,
            "flood_risk_category": "Medium", "wind_risk_category": "Medium",
            "union_spread_bps": 500,    # no flood_spread_bps -> ignored for wind
        }})
        c = r.get_json()["coupon"]
        assert c["wind_priced_by"] == "static"

    def test_larger_union_raises_wind_leg(self, prop_client):
        """Holding the flood leg fixed, a larger union (more wind-driven events)
        must price a larger incremental wind leg and thus a larger coupon."""
        client, _ = prop_client
        base = {"loan_amount": 200000, "property_value": 300000,
                "flood_spread_bps": 300}

        def coupon_for(union_bps):
            r = client.post("/api/v1/loan-pricer",
                            json={"inputs": {**base, "union_spread_bps": union_bps}})
            return r.get_json()["coupon"]

        low, high = coupon_for(400), coupon_for(600)
        assert high["wind_spread"] > low["wind_spread"]
        assert high["rate"] > low["rate"]

    def test_higher_flood_category_raises_coupon(self, prop_client):
        """A worse flood category must price a larger flood leg (PRS-driven)."""
        client, _ = prop_client

        def flood_spread_for(category):
            r = client.post("/api/v1/loan-pricer", json={"inputs": {
                "loan_amount": 200000, "property_value": 300000,
                "flood_risk_category": category,
            }})
            return r.get_json()["coupon"]["flood_spread"]

        assert (flood_spread_for("Very low") < flood_spread_for("Medium")
                < flood_spread_for("Very high"))

    def test_worse_rating_raises_coupon(self, prop_client):
        client, _ = prop_client

        def coupon_for(rating):
            r = client.post("/api/v1/loan-pricer", json={"inputs": {
                "loan_amount": 200000, "property_value": 300000,
                "credit_rating": rating,
            }})
            return r.get_json()["coupon"]["rate"]

        assert coupon_for("CCC") > coupon_for("BBB") > coupon_for("AAA")
