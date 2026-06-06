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

"""Tests for the standalone Loan Calculator endpoint + pricing helper (part 2).

The standalone calculator is launched from the asset right-click menu but is
asset-independent: the client supplies every pricing input and POSTs to
``/api/v1/loan-pricer`` (no property/loan id). It is backed by
``routes._loan_pricing.compute_standalone_pricing``.
"""

import pytest


class TestStandaloneLoanPricerRoutePart2:
    """Continuation of the standalone route tests (term cap, income yield,
    and validation) split out to keep each file within the line budget."""

    def test_income_yield_derives_borrower_income(self, prop_client):
        """A commercial marker forwards the asset's net initial yield; the
        borrower income is then the annual passing rent (yield x property
        value), not the fixed default."""
        client, _ = prop_client
        r = client.post("/api/v1/loan-pricer", json={"inputs": {
            "loan_amount": 200000, "property_value": 300000,
            "income_yield": 0.06,
        }})
        data = r.get_json()
        assert data["status"] == "success"
        assert data["inputs"]["gross_annual_income"] == pytest.approx(0.06 * 300000)
        # The yield itself is consumed, not echoed back as a pricing input.
        assert "income_yield" not in data["inputs"]

    def test_income_yield_tracks_property_value(self, prop_client):
        """Income = yield x value, so a larger property value lifts income."""
        client, _ = prop_client

        def income_for(value):
            r = client.post("/api/v1/loan-pricer", json={"inputs": {
                "loan_amount": 200000, "property_value": value,
                "income_yield": 0.05,
            }})
            return r.get_json()["inputs"]["gross_annual_income"]

        assert income_for(1_000_000) == pytest.approx(50_000)
        assert income_for(10_000_000) == pytest.approx(500_000)

    def test_commercial_caps_term_at_seven_years(self, prop_client):
        client, _ = prop_client
        r = client.post("/api/v1/loan-pricer", json={
            "asset_class": "commercial",
            "inputs": {
                "loan_amount": 200000, "property_value": 300000,
                "original_maturity": 30, "current_term": 30,
            }})
        data = r.get_json()
        assert data["asset_class"] == "commercial"
        assert data["inputs"]["current_term"] == 7
        assert data["inputs"]["original_maturity"] == 7

    def test_residential_term_not_capped(self, prop_client):
        client, _ = prop_client
        r = client.post("/api/v1/loan-pricer", json={"inputs": {
            "loan_amount": 200000, "property_value": 300000,
            "current_term": 25,
        }})
        assert r.get_json()["inputs"]["current_term"] == 25

    def test_missing_required_returns_422(self, prop_client):
        client, _ = prop_client
        r = client.post("/api/v1/loan-pricer",
                        json={"inputs": {"interest_rate": 0.04}})
        assert r.status_code == 422
        assert r.get_json()["status"] == "error"

    def test_empty_body_returns_422(self, prop_client):
        client, _ = prop_client
        r = client.post("/api/v1/loan-pricer", json={})
        assert r.status_code == 422


class TestPrsScenarioCoupon:
    """The calculator's PRS Hazard Scenario dropdown sends a single chosen
    spread (prs_spread_bps) + its tag (prs_scenario); that spread becomes the
    coupon's entire hazard leg and supersedes the flood/union split."""

    def _coupon(self, client, **inputs):
        base = {"loan_amount": 200000, "property_value": 300000}
        r = client.post("/api/v1/loan-pricer", json={"inputs": {**base, **inputs}})
        assert r.status_code == 200
        return r.get_json()

    def test_win_scenario_is_all_wind(self, prop_client):
        client, _ = prop_client
        c = self._coupon(client, prs_scenario="win", prs_spread_bps=250)["coupon"]
        assert c["prs_scenario"] == "win"
        assert c["hazard_spread"] == pytest.approx(0.025)
        assert c["wind_spread"] == pytest.approx(0.025)
        assert c["flood_spread"] == pytest.approx(0.0)
        assert "scenario: win" in c["flood_priced_by"]

    @pytest.mark.parametrize("scenario", ["flo", "bri", "faw"])
    def test_flood_side_scenarios_are_all_flood(self, prop_client, scenario):
        client, _ = prop_client
        c = self._coupon(client, prs_scenario=scenario, prs_spread_bps=180)["coupon"]
        assert c["prs_scenario"] == scenario
        assert c["flood_spread"] == pytest.approx(0.018)
        assert c["wind_spread"] == pytest.approx(0.0)
        assert c["hazard_spread"] == pytest.approx(0.018)

    def test_fow_splits_into_flood_plus_incremental_wind(self, prop_client):
        client, _ = prop_client
        c = self._coupon(client, prs_scenario="fow", prs_spread_bps=500,
                         flood_spread_bps=300)["coupon"]
        assert c["flood_spread"] == pytest.approx(0.030)
        assert c["wind_spread"] == pytest.approx(0.020)
        assert c["hazard_spread"] == pytest.approx(0.050)

    def test_fow_without_base_flood_is_all_flood(self, prop_client):
        client, _ = prop_client
        c = self._coupon(client, prs_scenario="fow", prs_spread_bps=500)["coupon"]
        assert c["flood_spread"] == pytest.approx(0.050)
        assert c["wind_spread"] == pytest.approx(0.0)

    def test_scenario_supersedes_union_split(self, prop_client):
        """When a scenario spread is present it wins over flood/union, so the
        hazard leg is the scenario spread, not union - flood."""
        client, _ = prop_client
        c = self._coupon(client, prs_scenario="win", prs_spread_bps=250,
                         flood_spread_bps=300, union_spread_bps=900)["coupon"]
        assert c["hazard_spread"] == pytest.approx(0.025)
        assert c["wind_spread"] == pytest.approx(0.025)

    def test_coupon_decomposes_with_scenario(self, prop_client):
        client, _ = prop_client
        c = self._coupon(client, prs_scenario="faw", prs_spread_bps=120)["coupon"]
        assert c["rate"] == pytest.approx(
            c["risk_free"] + c["credit_spread"] + c["hazard_spread"])
        assert c["hazard_spread"] == pytest.approx(c["flood_spread"] + c["wind_spread"])

    def test_scenario_echoed_in_inputs(self, prop_client):
        """prs_scenario round-trips so the dropdown re-selects after a price."""
        client, _ = prop_client
        data = self._coupon(client, prs_scenario="win", prs_spread_bps=250)
        assert data["inputs"]["prs_scenario"] == "win"

    def test_no_scenario_keeps_legacy_two_leg(self, prop_client):
        """Without a scenario spread the coupon keeps the flood/wind split and
        carries no prs_scenario tag (backward compatible)."""
        client, _ = prop_client
        c = self._coupon(client, flood_spread_bps=300, union_spread_bps=500)["coupon"]
        assert "prs_scenario" not in c
        assert c["flood_spread"] == pytest.approx(0.030)
        assert c["wind_spread"] == pytest.approx(0.020)


# ===========================================================================
# compute_standalone_pricing helper
# ===========================================================================

class TestComputeStandalonePricing:

    def test_returns_unbound_pricing(self):
        from routes._loan_pricing import compute_standalone_pricing
        res = compute_standalone_pricing({
            "loan_amount": 200000,
            "property_value": 300000,
        })
        assert res["mortgage_id"] is None
        assert res["property_id"] is None
        assert res["asset_class"] == "residential"
        assert "mortgage_value" in res["pricing"]
        # Defaults filled in for omitted inputs.
        assert res["inputs"]["current_term"] == 30
        # Coupon derived from defaults; interest_rate tracks it.
        assert res["inputs"]["interest_rate"] == res["coupon"]["rate"]
        assert res["pricing"]["discount_rate"] == res["coupon"]["risk_free"]

    def test_commercial_term_cap_helper(self):
        from routes._loan_pricing import compute_standalone_pricing
        res = compute_standalone_pricing(
            {"loan_amount": 200000, "property_value": 300000, "current_term": 30},
            asset_class="commercial")
        assert res["inputs"]["current_term"] == 7

    def test_income_yield_helper(self):
        from routes._loan_pricing import compute_standalone_pricing
        res = compute_standalone_pricing({
            "loan_amount": 200000, "property_value": 400000,
            "income_yield": 0.07,
        })
        assert res["inputs"]["gross_annual_income"] == pytest.approx(0.07 * 400000)
        assert "income_yield" not in res["inputs"]

    def test_missing_property_value_raises(self):
        from routes._loan_pricing import compute_standalone_pricing
        with pytest.raises(ValueError):
            compute_standalone_pricing({"loan_amount": 200000})

    def test_none_inputs_raises(self):
        from routes._loan_pricing import compute_standalone_pricing
        with pytest.raises(ValueError):
            compute_standalone_pricing(None)
