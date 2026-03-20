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

"""Tests for routes/propertyts/risk.py — portfolio VaR/ES endpoint."""

import json

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_sequences(*storm_ids):
    """Build storm_sequences.json data.

    In the current model, storm_id in propertyts IS the sequence_id,
    so sequence_id must match the storm_id used in flood events.
    """
    return {
        "sequences": [
            {"sequence_id": sid, "storms": [{"storm_id": f"{sid}-pulse0"}]}
            for sid in storm_ids
        ]
    }


def _make_prop_flood(property_id, flood_events):
    return {"property_id": property_id, "flood_events": flood_events}


def _make_property_json(property_id, value):
    return {"properties": [{"PropertyHeader": {
        "Header": {"PropertyID": property_id},
        "Valuation": {"PropertyValue": value},
    }}]}


def _make_mortgage_json(property_id, outstanding):
    return {"mortgages": [{"Mortgage": {
        "Header": {"MortgageID": "MORT-001", "PropertyID": property_id},
        "FinancialTerms": {"OriginalBalance": outstanding},
        "CurrentStatus": {"OutstandingBalance": outstanding},
    }}]}


def _make_client(tmp_path, monkeypatch, *, pts_dir=True, sequences=None,
                 prop_floods=None, property_json=None, mortgage_json=None):
    """Generic factory for propertyts test clients."""
    from config import config

    if pts_dir:
        (tmp_path / "propertyts").mkdir(exist_ok=True)

    if sequences is not None:
        (tmp_path / "storm_sequences.json").write_text(json.dumps(sequences))

    for fname, data in (prop_floods or {}).items():
        (tmp_path / "propertyts" / fname).write_text(json.dumps(data))

    if property_json is not None:
        (tmp_path / "property.json").write_text(json.dumps(property_json))

    if mortgage_json is not None:
        (tmp_path / "mortgage.json").write_text(json.dumps(mortgage_json))

    monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
    monkeypatch.setattr(config, "get_input_path", lambda f: tmp_path / f)

    from server import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


URL = "/api/v1/propertyts/portfolio-var"


# ===========================================================================
# Error paths
# ===========================================================================

class TestPortfolioVarErrors:

    def test_no_pts_dir_returns_404(self, pts_client_no_data):
        r = pts_client_no_data.get(URL)
        assert r.status_code == 404

    def test_no_pts_dir_status_error(self, pts_client_no_data):
        assert pts_client_no_data.get(URL).get_json()["status"] == "error"

    def test_options_returns_ok(self, pts_client_no_data):
        r = pts_client_no_data.options(URL)
        assert r.status_code == 200

    def test_missing_sequences_returns_404(self, tmp_path, monkeypatch):
        client = _make_client(tmp_path, monkeypatch, pts_dir=True)  # no sequences file
        r = client.get(URL)
        assert r.status_code == 404

    def test_missing_sequences_message_mentions_doublet(self, tmp_path, monkeypatch):
        client = _make_client(tmp_path, monkeypatch, pts_dir=True)
        msg = client.get(URL).get_json()["message"].lower()
        assert "storm_sequences" in msg or "not found" in msg


# ===========================================================================
# Happy path — basic structure
# ===========================================================================

class TestPortfolioVarSuccess:

    def test_returns_200(self, pts_env):
        assert pts_env["client"].get(URL).status_code == 200

    def test_status_success(self, pts_env):
        assert pts_env["client"].get(URL).get_json()["status"] == "success"

    def test_top_level_keys_present(self, pts_env):
        data = pts_env["client"].get(URL).get_json()
        for key in [
            "storm_count", "storms_with_damage", "storms_zero_damage",
            "prob_loss_pct", "total_portfolio_value", "total_portfolio_mortgages",
            "property_damage", "mortgage_impairment",
            "prop_histogram", "mort_histogram", "tail_storms",
        ]:
            assert key in data, f"Missing key: {key}"

    def test_property_damage_sub_keys(self, pts_env):
        pd = pts_env["client"].get(URL).get_json()["property_damage"]
        for key in ["mean", "std", "var_95", "var_999", "es_95", "es_999",
                    "max", "cond_mean", "cond_var_95", "cond_var_999",
                    "cond_es_95", "cond_es_999"]:
            assert key in pd, f"Missing key in property_damage: {key}"

    def test_mortgage_impairment_sub_keys(self, pts_env):
        mi = pts_env["client"].get(URL).get_json()["mortgage_impairment"]
        for key in ["mean", "std", "var_95", "var_999", "es_95", "es_999",
                    "max", "cond_mean", "cond_var_95", "cond_var_999",
                    "cond_es_95", "cond_es_999"]:
            assert key in mi, f"Missing key in mortgage_impairment: {key}"

    def test_prop_histogram_has_50_bins(self, pts_env):
        assert len(pts_env["client"].get(URL).get_json()["prop_histogram"]) == 50

    def test_mort_histogram_has_50_bins(self, pts_env):
        assert len(pts_env["client"].get(URL).get_json()["mort_histogram"]) == 50

    def test_histogram_bin_has_lo_hi_count(self, pts_env):
        bin0 = pts_env["client"].get(URL).get_json()["prop_histogram"][0]
        assert "lo" in bin0 and "hi" in bin0 and "count" in bin0

    def test_tail_storms_is_list(self, pts_env):
        assert isinstance(pts_env["client"].get(URL).get_json()["tail_storms"], list)

    def test_tail_storms_sorted_descending(self, pts_env):
        storms = pts_env["client"].get(URL).get_json()["tail_storms"]
        damages = [s["property_damage"] for s in storms]
        assert damages == sorted(damages, reverse=True)

    def test_tail_storm_has_required_fields(self, pts_env):
        storms = pts_env["client"].get(URL).get_json()["tail_storms"]
        assert len(storms) >= 1
        s = storms[0]
        for f in ["storm_id", "property_damage", "mortgage_impairment", "n_affected"]:
            assert f in s, f"Missing field in tail_storm: {f}"


# ===========================================================================
# Single-storm numerics (pts_env has 1 storm, property_value=400000, damage_ratio=0.1)
# ===========================================================================

class TestPortfolioVarNumerics:

    def test_storm_count_is_one(self, pts_env):
        assert pts_env["client"].get(URL).get_json()["storm_count"] == 1

    def test_storms_with_damage_is_one(self, pts_env):
        assert pts_env["client"].get(URL).get_json()["storms_with_damage"] == 1

    def test_storms_zero_plus_with_damage_equals_total(self, pts_env):
        data = pts_env["client"].get(URL).get_json()
        assert data["storms_with_damage"] + data["storms_zero_damage"] == data["storm_count"]

    def test_prob_loss_pct_is_100(self, pts_env):
        assert pts_env["client"].get(URL).get_json()["prob_loss_pct"] == 100.0

    def test_total_portfolio_value(self, pts_env):
        assert pts_env["client"].get(URL).get_json()["total_portfolio_value"] == 400000.0

    def test_total_portfolio_mortgages(self, pts_env):
        assert pts_env["client"].get(URL).get_json()["total_portfolio_mortgages"] == 280000.0

    def test_property_damage_max_is_positive(self, pts_env):
        assert pts_env["client"].get(URL).get_json()["property_damage"]["max"] > 0

    def test_property_damage_cond_mean_positive(self, pts_env):
        assert pts_env["client"].get(URL).get_json()["property_damage"]["cond_mean"] > 0

    def test_no_mortgage_impairment_when_above_water(self, pts_env):
        # post_value = 400000 * 0.9 = 360000 > outstanding 280000 → impairment = 0
        mi = pts_env["client"].get(URL).get_json()["mortgage_impairment"]
        assert mi["max"] == 0.0


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
