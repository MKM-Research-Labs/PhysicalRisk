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

"""Tests for routes/propertyts/risk.py — portfolio VaR/ES endpoint (part 1).

Error paths, happy-path structure, single-storm numerics.
"""

import pytest

from tests.routes.propertyts.conftest import (
    make_risk_client as _make_client,
    make_storm_sequences as _make_sequences,
    PORTFOLIO_VAR_URL as URL,
)


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
