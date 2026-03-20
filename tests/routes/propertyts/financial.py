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

"""Tests for routes/propertyts/financial.py.

Covers:
  GET /propertyts/<storm_id>/portfolio-impact
  GET /propertyts/sequence/<sequence_id>/portfolio-impact
"""

import pytest


# ===========================================================================
# /propertyts/<storm_id>/portfolio-impact
# ===========================================================================

class TestPortfolioImpact:

    def test_no_pts_dir_returns_404(self, pts_client_no_data):
        r = pts_client_no_data.get("/api/v1/propertyts/STORM-0001/portfolio-impact")
        assert r.status_code == 404
        assert r.get_json()["status"] == "error"

    def test_options_returns_ok(self, pts_client_no_data):
        r = pts_client_no_data.options("/api/v1/propertyts/STORM-0001/portfolio-impact")
        assert r.status_code == 200

    def test_unknown_storm_returns_404(self, pts_env):
        r = pts_env["client"].get("/api/v1/propertyts/STORM-GHOST/portfolio-impact")
        assert r.status_code == 404
        assert r.get_json()["status"] == "error"

    def test_known_storm_returns_success(self, pts_env):
        r = pts_env["client"].get(f"/api/v1/propertyts/{pts_env['storm_id']}/portfolio-impact")
        assert r.status_code == 200
        assert r.get_json()["status"] == "success"

    def test_response_has_storm_id(self, pts_env):
        sid = pts_env["storm_id"]
        r = pts_env["client"].get(f"/api/v1/propertyts/{sid}/portfolio-impact")
        assert r.get_json()["storm_id"] == sid

    def test_response_has_portfolio(self, pts_env):
        r = pts_env["client"].get(f"/api/v1/propertyts/{pts_env['storm_id']}/portfolio-impact")
        data = r.get_json()
        assert "portfolio" in data
        port = data["portfolio"]
        assert "total_properties" in port
        assert "properties_affected" in port
        assert "total_damage" in port

    def test_response_has_properties_list(self, pts_env):
        r = pts_env["client"].get(f"/api/v1/propertyts/{pts_env['storm_id']}/portfolio-impact")
        data = r.get_json()
        assert "properties" in data
        assert len(data["properties"]) >= 1

    def test_property_entry_has_financial_fields(self, pts_env):
        r = pts_env["client"].get(f"/api/v1/propertyts/{pts_env['storm_id']}/portfolio-impact")
        prop = r.get_json()["properties"][0]
        assert "property_id" in prop
        assert "property_value" in prop
        assert "flood_depth_m" in prop
        assert "damage_ratio" in prop
        assert "damage_amount" in prop
        assert "post_damage_value" in prop
        assert "has_mortgage" in prop

    def test_mortgaged_property_has_ltv_fields(self, pts_env):
        r = pts_env["client"].get(f"/api/v1/propertyts/{pts_env['storm_id']}/portfolio-impact")
        props = r.get_json()["properties"]
        mortgaged = [p for p in props if p["has_mortgage"]]
        assert len(mortgaged) >= 1
        p = mortgaged[0]
        assert "outstanding_balance" in p
        assert "current_ltv" in p
        assert "post_damage_ltv" in p
        assert "negative_equity" in p

    def test_properties_sorted_by_damage_descending(self, pts_env):
        r = pts_env["client"].get(f"/api/v1/propertyts/{pts_env['storm_id']}/portfolio-impact")
        props = r.get_json()["properties"]
        amounts = [p["damage_amount"] for p in props]
        assert amounts == sorted(amounts, reverse=True)

    def test_portfolio_damage_pct_non_negative(self, pts_env):
        r = pts_env["client"].get(f"/api/v1/propertyts/{pts_env['storm_id']}/portfolio-impact")
        pct = r.get_json()["portfolio"]["damage_pct"]
        assert pct >= 0

    def test_portfolio_totals_count(self, pts_env):
        r = pts_env["client"].get(f"/api/v1/propertyts/{pts_env['storm_id']}/portfolio-impact")
        port = r.get_json()["portfolio"]
        assert port["properties_affected"] == len(r.get_json()["properties"])


# ===========================================================================
# /propertyts/sequence/<sequence_id>/portfolio-impact
# ===========================================================================

class TestSequencePortfolioImpact:

    def test_no_pts_dir_returns_404(self, pts_client_no_data):
        r = pts_client_no_data.get("/api/v1/propertyts/sequence/SEQ-0001/portfolio-impact")
        assert r.status_code == 404
        assert r.get_json()["status"] == "error"

    def test_options_returns_ok(self, pts_client_no_data):
        r = pts_client_no_data.options("/api/v1/propertyts/sequence/SEQ-0001/portfolio-impact")
        assert r.status_code == 200

    def test_unknown_sequence_returns_404(self, pts_env):
        r = pts_env["client"].get("/api/v1/propertyts/sequence/SEQ-GHOST/portfolio-impact")
        assert r.status_code == 404
        assert r.get_json()["status"] == "error"

    def test_known_sequence_returns_success(self, pts_env):
        seq_id = pts_env["seq_id"]
        r = pts_env["client"].get(f"/api/v1/propertyts/sequence/{seq_id}/portfolio-impact")
        assert r.status_code == 200
        assert r.get_json()["status"] == "success"

    def test_response_has_sequence_id(self, pts_env):
        seq_id = pts_env["seq_id"]
        r = pts_env["client"].get(f"/api/v1/propertyts/sequence/{seq_id}/portfolio-impact")
        assert r.get_json()["sequence_id"] == seq_id

    def test_response_has_damage_model(self, pts_env):
        seq_id = pts_env["seq_id"]
        r = pts_env["client"].get(f"/api/v1/propertyts/sequence/{seq_id}/portfolio-impact")
        assert r.get_json()["damage_model"] == "max_depth"

    def test_response_has_num_storms(self, pts_env):
        seq_id = pts_env["seq_id"]
        r = pts_env["client"].get(f"/api/v1/propertyts/sequence/{seq_id}/portfolio-impact")
        assert "num_storms_in_sequence" in r.get_json()
        assert r.get_json()["num_storms_in_sequence"] >= 1

    def test_response_has_portfolio(self, pts_env):
        seq_id = pts_env["seq_id"]
        r = pts_env["client"].get(f"/api/v1/propertyts/sequence/{seq_id}/portfolio-impact")
        data = r.get_json()
        assert "portfolio" in data
        assert "total_damage" in data["portfolio"]

    def test_response_has_properties_list(self, pts_env):
        seq_id = pts_env["seq_id"]
        r = pts_env["client"].get(f"/api/v1/propertyts/sequence/{seq_id}/portfolio-impact")
        assert "properties" in r.get_json()
        assert len(r.get_json()["properties"]) >= 1

    def test_property_entry_has_worst_storm_id(self, pts_env):
        seq_id = pts_env["seq_id"]
        r = pts_env["client"].get(f"/api/v1/propertyts/sequence/{seq_id}/portfolio-impact")
        prop = r.get_json()["properties"][0]
        assert "worst_storm_id" in prop

    def test_property_entry_has_num_sequence_floods(self, pts_env):
        seq_id = pts_env["seq_id"]
        r = pts_env["client"].get(f"/api/v1/propertyts/sequence/{seq_id}/portfolio-impact")
        prop = r.get_json()["properties"][0]
        assert "num_sequence_floods" in prop
        assert prop["num_sequence_floods"] >= 1

    def test_properties_sorted_by_damage_descending(self, pts_env):
        seq_id = pts_env["seq_id"]
        r = pts_env["client"].get(f"/api/v1/propertyts/sequence/{seq_id}/portfolio-impact")
        props = r.get_json()["properties"]
        amounts = [p["damage_amount"] for p in props]
        assert amounts == sorted(amounts, reverse=True)

    def test_property_entry_has_financial_fields(self, pts_env):
        seq_id = pts_env["seq_id"]
        r = pts_env["client"].get(f"/api/v1/propertyts/sequence/{seq_id}/portfolio-impact")
        prop = r.get_json()["properties"][0]
        assert "property_value" in prop
        assert "damage_amount" in prop
        assert "post_damage_value" in prop
        assert "has_mortgage" in prop
