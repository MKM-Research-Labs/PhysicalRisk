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

"""Unit tests for the src/routes/commercial/ package (part 3).

Catchment-agnostic: all commercial.json / commercial_loan.json /
commercialts / hazard files are synthesised inside tmp_path. Report PDF
generation is mocked — these tests exercise the HTTP layer, not the
report renderers.
"""

import json

import pytest


@pytest.fixture
def cfg_tmp(tmp_path, monkeypatch):
    from config import config
    monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
    monkeypatch.setattr(config, "get_input_path", lambda fname: tmp_path / fname)
    monkeypatch.setattr(config, "get_reports_dir", lambda *a, **k: tmp_path)
    return tmp_path


@pytest.fixture
def client(cfg_tmp):
    from server import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


CPID = "CPROP-0001"


def _write_commercial(tmp_path, **over):
    rec = {
        "CommercialAsset": {
            "Header": {"PropertyID": CPID},
            "Location": {"BuildingName": "Tower One", "BuildingNumber": "1",
                         "StreetName": "Market St", "Postcode": "AB1 2CD"},
            "Valuation": {"PropertyValue": 5_000_000},
            "CommercialAttributes": {"CommercialType": "Office"},
            "Tenancy": {"AnchorTenant": "BigCo"},
            "RiskAssessment": {"GroundLevelMeters": 10, "RiverDistanceMeters": 2000,
                               "EAFloodZone": "Zone 2"},
            "Construction": {"FloorLevelMeters": 0.3},
        }
    }
    rec["CommercialAsset"].update(over)
    (tmp_path / "commercial.json").write_text(
        json.dumps({"commercial_assets": [rec]}))


def _write_commercial_loan(tmp_path, ltv=0.6):
    (tmp_path / "commercial_loan.json").write_text(json.dumps({
        "commercial_loans": [{
            "Mortgage": {
                "Header": {"PropertyID": CPID},
                "CurrentStatus": {"OutstandingBalance": 3_000_000,
                                  "CurrentLTV": ltv, "RemainingTerm": 240},
            }
        }]
    }))


# ---------------------------------------------------------------------------
# blotter
# ---------------------------------------------------------------------------

def test_blotter_options(client):
    resp = client.options("/api/v1/commercial/blotter")
    assert resp.status_code == 200


def test_blotter_missing_file(client, cfg_tmp):
    resp = client.get("/api/v1/commercial/blotter")
    assert resp.status_code == 200
    assert resp.get_json()["summary"]["num_assets"] == 0


def test_blotter_success_with_loan_and_cts(client, cfg_tmp):
    _write_commercial(cfg_tmp)
    _write_commercial_loan(cfg_tmp, ltv=0.6)
    cts_dir = cfg_tmp / "commercialts"
    cts_dir.mkdir()
    (cts_dir / f"{CPID}.json").write_text(json.dumps({
        "nearest_gauges": [{"gauge_elevation_m": 8}]}))
    resp = client.get("/api/v1/commercial/blotter")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["summary"]["num_assets"] == 1
    a = body["assets"][0]
    assert a["property_id"] == CPID
    assert a["has_loan"] is True
    assert a["current_ltv"] == 60.0  # 0.6 normalised
    assert a["anchor_tenant"] == "BigCo"
    assert a["river_distance_km"] == 2.0


def test_blotter_loan_file_missing(client, cfg_tmp):
    """Asset present, commercial_loan.json absent → loan FileNotFoundError pass."""
    _write_commercial(cfg_tmp)
    resp = client.get("/api/v1/commercial/blotter")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["summary"]["num_assets"] == 1
    assert body["assets"][0]["has_loan"] is False


def test_blotter_skips_asset_without_property_id(client, cfg_tmp):
    """Asset record with no PropertyID is skipped via `continue`."""
    rec = {"CommercialAsset": {"Header": {}, "Location": {},
                               "Valuation": {}, "CommercialAttributes": {}}}
    (cfg_tmp / "commercial.json").write_text(
        json.dumps({"commercial_assets": [rec]}))
    resp = client.get("/api/v1/commercial/blotter")
    assert resp.status_code == 200
    assert resp.get_json()["summary"]["num_assets"] == 0


def test_blotter_malformed_cts_file_tolerated(client, cfg_tmp):
    """A corrupt commercialts/<id>.json is swallowed (except pass)."""
    _write_commercial(cfg_tmp)
    cts_dir = cfg_tmp / "commercialts"
    cts_dir.mkdir()
    (cts_dir / f"{CPID}.json").write_text("{not valid json")
    resp = client.get("/api/v1/commercial/blotter")
    assert resp.status_code == 200
    assert resp.get_json()["summary"]["num_assets"] == 1


# ---------------------------------------------------------------------------
# portfolio-impact
# ---------------------------------------------------------------------------

def test_portfolio_impact_options(client):
    resp = client.options("/api/v1/commercial/STORM-0001/portfolio-impact")
    assert resp.status_code == 200


def test_portfolio_impact_dir_missing(client, cfg_tmp):
    resp = client.get("/api/v1/commercial/STORM-0001/portfolio-impact")
    assert resp.status_code == 404


def test_portfolio_impact_success(client, cfg_tmp):
    _write_commercial(cfg_tmp)
    _write_commercial_loan(cfg_tmp, ltv=0.6)
    cts_dir = cfg_tmp / "commercialts"
    cts_dir.mkdir()
    (cts_dir / f"{CPID}.json").write_text(json.dumps({
        "property_id": CPID,
        "flood_events": [{
            "storm_id": "STORM-0001", "flooded": True, "exceeded_severe": True,
            "damage_ratio": 0.2, "flood_depth_m": 1.5,
        }],
    }))
    resp = client.get("/api/v1/commercial/STORM-0001/portfolio-impact")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["portfolio"]["assets_affected"] == 1
    a = body["assets"][0]
    assert a["damage_amount"] == 1_000_000.0  # 5M * 0.2
    assert a["post_damage_value"] == 4_000_000.0
    assert a["has_loan"] is True
    # outstanding 3M < post 4M → not negative equity
    assert a["negative_equity"] is False


def test_portfolio_impact_skips_non_prs_and_other_storms(client, cfg_tmp):
    _write_commercial(cfg_tmp)
    cts_dir = cfg_tmp / "commercialts"
    cts_dir.mkdir()
    (cts_dir / f"{CPID}.json").write_text(json.dumps({
        "property_id": CPID,
        "flood_events": [
            {"storm_id": "OTHER", "flooded": True, "exceeded_severe": True,
             "damage_ratio": 0.2},
            {"storm_id": "STORM-0001", "flooded": False, "exceeded_severe": False,
             "damage_ratio": 0.2},
        ],
    }))
    resp = client.get("/api/v1/commercial/STORM-0001/portfolio-impact")
    assert resp.status_code == 200
    assert resp.get_json()["portfolio"]["assets_affected"] == 0


# ---------------------------------------------------------------------------
# Defensive branches — loan-report missing id, no-match loan, malformed files
# ---------------------------------------------------------------------------

def test_loan_report_missing_property_id(client):
    """reports.py: POST loan-report with no propertyId → 400."""
    resp = client.post("/api/v1/commercial/loan-report",
                       data=json.dumps({}), content_type="application/json")
    assert resp.status_code == 400


def test_loan_pricer_loan_file_present_but_no_match(client, cfg_tmp):
    """pricing.py _find_commercial_loan: loans exist but none match → 404.

    Distinct from the missing-file path: here the list is iterated to the
    end without a hit (the final ``return None``).
    """
    (cfg_tmp / "commercial_loan.json").write_text(json.dumps({
        "commercial_loans": [{
            "Mortgage": {"Header": {"PropertyID": "CPROP-9999"}}
        }]
    }))
    resp = client.get(f"/api/v1/commercial/{CPID}/loan-pricer")
    assert resp.status_code == 404


def test_portfolio_impact_commercial_json_missing(client, cfg_tmp):
    """portfolio.py: commercialts dir exists but commercial.json absent.

    asset_lookup stays empty (FileNotFoundError swallowed), so every
    CPROP-*.json is skipped (pid not in asset_lookup → continue).
    """
    cts_dir = cfg_tmp / "commercialts"
    cts_dir.mkdir()
    (cts_dir / f"{CPID}.json").write_text(json.dumps({
        "property_id": CPID,
        "flood_events": [{"storm_id": "STORM-0001", "flooded": True,
                          "exceeded_severe": True, "damage_ratio": 0.2}],
    }))
    resp = client.get("/api/v1/commercial/STORM-0001/portfolio-impact")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["portfolio"]["total_assets"] == 0
    assert data["portfolio"]["assets_affected"] == 0


def test_portfolio_impact_skips_asset_without_property_id(client, cfg_tmp):
    """portfolio.py: a commercial record with no PropertyID is skipped."""
    (cfg_tmp / "commercial.json").write_text(json.dumps({
        "commercial_assets": [{"CommercialAsset": {"Header": {}}}]
    }))
    cts_dir = cfg_tmp / "commercialts"
    cts_dir.mkdir()
    resp = client.get("/api/v1/commercial/STORM-0001/portfolio-impact")
    assert resp.status_code == 200
    assert resp.get_json()["portfolio"]["total_assets"] == 0
