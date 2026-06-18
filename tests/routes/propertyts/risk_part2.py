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

"""Tests for routes/propertyts/risk.py — portfolio VaR/ES endpoint (part 2).

Missing files, zero-depth, unknown property, mortgage impairment, multiple storms.
"""

import pytest

from tests.routes.propertyts.conftest import (
    make_risk_client as _make_client,
    make_storm_sequences as _make_sequences,
    make_prop_flood as _make_prop_flood,
    make_property_json as _make_property_json,
    make_mortgage_json as _make_mortgage_json,
    PORTFOLIO_VAR_URL as URL,
)


# ===========================================================================
# Missing supporting files — graceful degradation
# ===========================================================================

class TestPortfolioVarMissingFiles:

    def test_missing_property_json_returns_200(self, tmp_path, monkeypatch):
        client = _make_client(
            tmp_path, monkeypatch,
            sequences=_make_sequences("STORM-0001"),
        )
        assert client.get(URL).status_code == 200

    def test_missing_property_json_status_success(self, tmp_path, monkeypatch):
        client = _make_client(
            tmp_path, monkeypatch,
            sequences=_make_sequences("STORM-0001"),
        )
        assert client.get(URL).get_json()["status"] == "success"

    def test_missing_property_json_zero_portfolio_value(self, tmp_path, monkeypatch):
        client = _make_client(
            tmp_path, monkeypatch,
            sequences=_make_sequences("STORM-0001"),
        )
        assert client.get(URL).get_json()["total_portfolio_value"] == 0.0

    def test_missing_mortgage_json_returns_200(self, tmp_path, monkeypatch):
        client = _make_client(
            tmp_path, monkeypatch,
            sequences=_make_sequences("STORM-0001"),
            property_json=_make_property_json("PROP-001", 300000),
        )
        assert client.get(URL).status_code == 200

    def test_missing_mortgage_json_zero_portfolio_mortgages(self, tmp_path, monkeypatch):
        client = _make_client(
            tmp_path, monkeypatch,
            sequences=_make_sequences("STORM-0001"),
            property_json=_make_property_json("PROP-001", 300000),
        )
        assert client.get(URL).get_json()["total_portfolio_mortgages"] == 0.0


# ===========================================================================
# Zero-depth flood events are skipped
# ===========================================================================

class TestPortfolioVarZeroDepth:

    @pytest.fixture
    def client_zero_depth(self, tmp_path, monkeypatch):
        return _make_client(
            tmp_path, monkeypatch,
            sequences=_make_sequences("STORM-0001"),
            prop_floods={"PROP-001.json": _make_prop_flood("PROP-001", [
                {"storm_id": "STORM-0001", "flood_depth_m": 0.0, "damage_ratio": 0.1}
            ])},
            property_json=_make_property_json("PROP-001", 400000),
        )

    def test_zero_depth_storms_with_damage_is_zero(self, client_zero_depth):
        assert client_zero_depth.get(URL).get_json()["storms_with_damage"] == 0

    def test_zero_depth_property_damage_max_is_zero(self, client_zero_depth):
        assert client_zero_depth.get(URL).get_json()["property_damage"]["max"] == 0.0

    def test_zero_depth_prob_loss_is_zero(self, client_zero_depth):
        assert client_zero_depth.get(URL).get_json()["prob_loss_pct"] == 0.0

    def test_zero_depth_cond_mean_is_zero(self, client_zero_depth):
        assert client_zero_depth.get(URL).get_json()["property_damage"]["cond_mean"] == 0


# ===========================================================================
# Property ID not in property.json → skipped
# ===========================================================================

class TestPortfolioVarUnknownPropertyId:

    @pytest.fixture
    def client_unknown_prop(self, tmp_path, monkeypatch):
        return _make_client(
            tmp_path, monkeypatch,
            sequences=_make_sequences("STORM-0001"),
            prop_floods={"PROP-999.json": _make_prop_flood("PROP-999", [
                {"storm_id": "STORM-0001", "flood_depth_m": 0.5, "damage_ratio": 0.2}
            ])},
            # property.json has PROP-001, not PROP-999
            property_json=_make_property_json("PROP-001", 400000),
        )

    def test_unknown_prop_id_is_skipped(self, client_unknown_prop):
        data = client_unknown_prop.get(URL).get_json()
        assert data["storms_with_damage"] == 0

    def test_portfolio_value_from_known_property(self, client_unknown_prop):
        assert client_unknown_prop.get(URL).get_json()["total_portfolio_value"] == 400000.0


# ===========================================================================
# Mortgage impairment: property value < outstanding mortgage after damage
# ===========================================================================

class TestPortfolioVarMortgageImpairment:

    @pytest.fixture
    def client_underwater(self, tmp_path, monkeypatch):
        # damage_ratio=0.8: post_value = 200000 * 0.2 = 40000 < mortgage 180000
        # expected impairment = 180000 - 40000 = 140000
        return _make_client(
            tmp_path, monkeypatch,
            sequences=_make_sequences("STORM-0001"),
            prop_floods={"PROP-001.json": _make_prop_flood("PROP-001", [
                {"storm_id": "STORM-0001", "flood_depth_m": 1.5, "damage_ratio": 0.8}
            ])},
            property_json=_make_property_json("PROP-001", 200000),
            mortgage_json=_make_mortgage_json("PROP-001", 180000),
        )

    def test_mortgage_impairment_max_is_positive(self, client_underwater):
        mi = client_underwater.get(URL).get_json()["mortgage_impairment"]
        assert mi["max"] > 0

    def test_mortgage_impairment_value(self, client_underwater):
        # post_value = 200000 * (1 - 0.8) = 40000; impairment = 180000 - 40000 = 140000
        mi = client_underwater.get(URL).get_json()["mortgage_impairment"]
        assert mi["max"] == pytest.approx(140000.0, rel=1e-3)

    def test_tail_storm_has_mortgage_impairment(self, client_underwater):
        tail = client_underwater.get(URL).get_json()["tail_storms"]
        assert len(tail) >= 1
        assert tail[0]["mortgage_impairment"] > 0


# ===========================================================================
# Multiple storms: VaR/ES distribution shape
# ===========================================================================

class TestPortfolioVarMultipleStorms:

    @pytest.fixture
    def client_two_storms(self, tmp_path, monkeypatch):
        # STORM-0001 floods, STORM-0002 does not
        return _make_client(
            tmp_path, monkeypatch,
            sequences=_make_sequences("STORM-0001", "STORM-0002"),
            prop_floods={"PROP-001.json": _make_prop_flood("PROP-001", [
                {"storm_id": "STORM-0001", "flood_depth_m": 0.5, "damage_ratio": 0.1}
            ])},
            property_json=_make_property_json("PROP-001", 500000),
        )

    def test_storm_count_is_two(self, client_two_storms):
        assert client_two_storms.get(URL).get_json()["storm_count"] == 2

    def test_storms_with_damage_is_one(self, client_two_storms):
        assert client_two_storms.get(URL).get_json()["storms_with_damage"] == 1

    def test_storms_zero_damage_is_one(self, client_two_storms):
        assert client_two_storms.get(URL).get_json()["storms_zero_damage"] == 1

    def test_prob_loss_pct_is_50(self, client_two_storms):
        assert client_two_storms.get(URL).get_json()["prob_loss_pct"] == pytest.approx(50.0, rel=1e-3)

    def test_tail_storms_limited_to_50(self, client_two_storms):
        assert len(client_two_storms.get(URL).get_json()["tail_storms"]) <= 50

    def test_tail_storms_contains_the_damaged_storm(self, client_two_storms):
        storm_ids = [s["storm_id"] for s in client_two_storms.get(URL).get_json()["tail_storms"]]
        assert "STORM-0001" in storm_ids
