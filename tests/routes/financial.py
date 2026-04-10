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

"""
Tests for routes.propertyts.financial — portfolio-impact endpoint.

Covers: OPTIONS, no propertyts dir → 404, storm not found → 404,
storm with flooding → 200 with portfolio summary, mortgage enrichment.
"""

import json
from pathlib import Path

import pytest


# ===========================================================================
# Fixtures
# ===========================================================================

@pytest.fixture
def fin_client_no_data(tmp_path, monkeypatch):
    """Flask client with no propertyts directory."""
    from config import config
    monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
    monkeypatch.setattr(config, "get_gaugets_dir", lambda: tmp_path / "gaugets")

    from server import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


@pytest.fixture
def fin_env(tmp_path, monkeypatch):
    """
    Flask client with full synthetic data for portfolio-impact.

    Creates:
      tmp_path/propertyts/PROP-001.json   — floods in STORM-001
      tmp_path/property.json              — valuation data
      tmp_path/mortgage.json              — mortgage data
    """
    from config import config

    pts_dir = tmp_path / "propertyts"
    pts_dir.mkdir()

    # Property flood file
    prop_flood = {
        "property_id": "PROP-001",
        "flood_events": [
            {
                "storm_id": "STORM-001",
                "flood_depth_m": 0.5,
                "damage_ratio": 0.15,
                "flooded": True,
                "exceeded_severe": True,
            }
        ]
    }
    (pts_dir / "PROP-001.json").write_text(json.dumps(prop_flood))

    # Property valuation
    property_data = {
        "properties": [
            {
                "PropertyHeader": {
                    "Header": {"PropertyID": "PROP-001"},
                    "Valuation": {"PropertyValue": 400_000},
                }
            }
        ]
    }
    (tmp_path / "property.json").write_text(json.dumps(property_data))

    # Mortgage data
    mortgage_data = {
        "mortgages": [
            {
                "Mortgage": {
                    "Header": {"MortgageID": "MORT-001", "PropertyID": "PROP-001"},
                    "CurrentStatus": {
                        "OutstandingBalance": 280_000,
                        "CurrentLTV": 0.70,
                        "RemainingTerm": 240,
                    }
                }
            }
        ]
    }
    (tmp_path / "mortgage.json").write_text(json.dumps(mortgage_data))

    monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
    monkeypatch.setattr(config, "get_input_path", lambda name: tmp_path / name)
    monkeypatch.setattr(config, "get_gaugets_dir", lambda: tmp_path / "gaugets")

    from server import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


# ===========================================================================
# OPTIONS /propertyts/<storm_id>/portfolio-impact
# ===========================================================================

class TestPortfolioImpactOptions:

    def test_options_returns_200(self, fin_client_no_data):
        r = fin_client_no_data.options("/api/v1/propertyts/STORM-001/portfolio-impact")
        assert r.status_code == 200


# ===========================================================================
# No propertyts directory
# ===========================================================================

class TestPortfolioImpactNoData:

    def test_no_pts_dir_returns_404(self, fin_client_no_data):
        r = fin_client_no_data.get("/api/v1/propertyts/STORM-001/portfolio-impact")
        assert r.status_code == 404
        data = json.loads(r.data)
        assert data["status"] == "error"


# ===========================================================================
# Storm not found / no flooding
# ===========================================================================

class TestPortfolioImpactStormNotFound:

    def test_unknown_storm_returns_404(self, fin_env):
        r = fin_env.get("/api/v1/propertyts/STORM-NONEXISTENT/portfolio-impact")
        assert r.status_code == 404
        data = json.loads(r.data)
        assert data["status"] == "error"


# ===========================================================================
# Happy path
# ===========================================================================

class TestPortfolioImpactSuccess:

    def test_valid_storm_returns_200(self, fin_env):
        r = fin_env.get("/api/v1/propertyts/STORM-001/portfolio-impact")
        assert r.status_code == 200
        data = json.loads(r.data)
        assert data["status"] == "success"

    def test_response_has_portfolio_key(self, fin_env):
        r = fin_env.get("/api/v1/propertyts/STORM-001/portfolio-impact")
        data = json.loads(r.data)
        assert "portfolio" in data
        portfolio = data["portfolio"]
        for key in ("total_properties", "properties_affected",
                    "total_damage", "mortgages_in_negative_equity"):
            assert key in portfolio

    def test_response_has_properties_list(self, fin_env):
        r = fin_env.get("/api/v1/propertyts/STORM-001/portfolio-impact")
        data = json.loads(r.data)
        assert "properties" in data
        props = data["properties"]
        assert len(props) >= 1

    def test_property_entry_has_damage_fields(self, fin_env):
        r = fin_env.get("/api/v1/propertyts/STORM-001/portfolio-impact")
        data = json.loads(r.data)
        entry = data["properties"][0]
        assert entry["property_id"] == "PROP-001"
        assert entry["flood_depth_m"] == pytest.approx(0.5)
        assert entry["damage_ratio"] == pytest.approx(0.15)
        assert entry["damage_amount"] == pytest.approx(400_000 * 0.15)

    def test_mortgage_enrichment_present(self, fin_env):
        r = fin_env.get("/api/v1/propertyts/STORM-001/portfolio-impact")
        data = json.loads(r.data)
        entry = data["properties"][0]
        assert entry["has_mortgage"] is True
        assert entry["outstanding_balance"] == pytest.approx(280_000)
        assert "post_damage_ltv" in entry
        assert "negative_equity" in entry

    def test_storm_id_in_response(self, fin_env):
        r = fin_env.get("/api/v1/propertyts/STORM-001/portfolio-impact")
        data = json.loads(r.data)
        assert data["storm_id"] == "STORM-001"
