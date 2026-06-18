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

"""Unit tests for the src/routes/commercial/ package (part 1).

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
# _parse_commercial_request (via generate_report route)
# ---------------------------------------------------------------------------

def test_report_options_preflight(client):
    resp = client.options("/api/v1/commercial/report")
    assert resp.status_code == 204


def test_report_missing_property_id(client):
    resp = client.post("/api/v1/commercial/report", json={})
    assert resp.status_code == 400
    assert "propertyId is required" in resp.get_json()["message"]


def test_generate_report_success(client, cfg_tmp, monkeypatch):
    pdf = cfg_tmp / "rep.pdf"
    pdf.write_bytes(b"%PDF-1.4 fake")
    import reports.commercial as rc
    monkeypatch.setattr(rc, "generate_commercial_report",
                        lambda **k: str(pdf))
    resp = client.post("/api/v1/commercial/report", json={"propertyId": CPID})
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "success"
    assert resp.get_json()["pdf_base64"]


def test_generate_report_not_found(client, monkeypatch):
    import reports.commercial as rc
    monkeypatch.setattr(rc, "generate_commercial_report", lambda **k: None)
    resp = client.post("/api/v1/commercial/report", json={"propertyId": CPID})
    assert resp.status_code == 404


def test_generate_report_exception(client, monkeypatch):
    import reports.commercial as rc
    def boom(**k):
        raise RuntimeError("render failed")
    monkeypatch.setattr(rc, "generate_commercial_report", boom)
    resp = client.post("/api/v1/commercial/report", json={"propertyId": CPID})
    assert resp.status_code == 500


# ---------------------------------------------------------------------------
# generate_loan_report_route
# ---------------------------------------------------------------------------

def test_loan_report_success(client, cfg_tmp, monkeypatch):
    pdf = cfg_tmp / "loan.pdf"
    pdf.write_bytes(b"%PDF-1.4 loan")
    import reports.commercial as rc
    monkeypatch.setattr(rc, "generate_cloan_report", lambda **k: str(pdf))
    resp = client.post("/api/v1/commercial/loan-report", json={"propertyId": CPID})
    assert resp.status_code == 200


def test_loan_report_asset_missing(client, cfg_tmp, monkeypatch):
    import reports.commercial as rc
    monkeypatch.setattr(rc, "generate_cloan_report", lambda **k: None)
    import reports.commercial.commercial_report as cr
    monkeypatch.setattr(cr, "_load_commercial_record", lambda pid, d: None)
    resp = client.post("/api/v1/commercial/loan-report", json={"propertyId": CPID})
    assert resp.status_code == 404
    assert "not found" in resp.get_json()["message"]


def test_loan_report_no_loan(client, cfg_tmp, monkeypatch):
    import reports.commercial as rc
    monkeypatch.setattr(rc, "generate_cloan_report", lambda **k: None)
    import reports.commercial.commercial_report as cr
    monkeypatch.setattr(cr, "_load_commercial_record", lambda pid, d: {"x": 1})
    resp = client.post("/api/v1/commercial/loan-report", json={"propertyId": CPID})
    assert resp.status_code == 404
    assert "No loan linked" in resp.get_json()["message"]


def test_loan_report_exception(client, monkeypatch):
    import reports.commercial as rc
    def boom(**k):
        raise RuntimeError("x")
    monkeypatch.setattr(rc, "generate_cloan_report", boom)
    resp = client.post("/api/v1/commercial/loan-report", json={"propertyId": CPID})
    assert resp.status_code == 500


# ---------------------------------------------------------------------------
# loan-pricer route + _find_commercial_loan
# ---------------------------------------------------------------------------

def test_loan_pricer_options(client):
    resp = client.options(f"/api/v1/commercial/{CPID}/loan-pricer")
    assert resp.status_code == 200


def test_loan_pricer_no_loan(client, cfg_tmp):
    # no commercial_loan.json on disk
    resp = client.get(f"/api/v1/commercial/{CPID}/loan-pricer")
    assert resp.status_code == 404
    assert "No loan linked" in resp.get_json()["message"]


def test_loan_pricer_success(client, cfg_tmp, monkeypatch):
    _write_commercial_loan(cfg_tmp, ltv=0.6)
    import routes._loan_pricing as lp
    captured = {}
    def fake_price(cdm, overrides):
        captured["ltv"] = cdm["Mortgage"]["CurrentStatus"]["CurrentLTV"]
        captured["overrides"] = overrides
        return {"price": 99.5}
    monkeypatch.setattr(lp, "compute_loan_pricing", fake_price)
    resp = client.get(f"/api/v1/commercial/{CPID}/loan-pricer")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["price"] == 99.5
    assert body["property_id"] == CPID
    # decimal LTV 0.6 normalised to 60.0
    assert captured["ltv"] == 60.0


def test_loan_pricer_post_overrides(client, cfg_tmp, monkeypatch):
    _write_commercial_loan(cfg_tmp, ltv=0.6)
    import routes._loan_pricing as lp
    captured = {}
    def fake_price(cdm, overrides):
        captured["overrides"] = overrides
        return {"price": 1}
    monkeypatch.setattr(lp, "compute_loan_pricing", fake_price)
    resp = client.post(f"/api/v1/commercial/{CPID}/loan-pricer",
                       json={"overrides": {"rate": 0.05}})
    assert resp.status_code == 200
    assert captured["overrides"] == {"rate": 0.05}


def test_loan_pricer_value_error(client, cfg_tmp, monkeypatch):
    _write_commercial_loan(cfg_tmp)
    import routes._loan_pricing as lp
    def bad(cdm, overrides):
        raise ValueError("bad input")
    monkeypatch.setattr(lp, "compute_loan_pricing", bad)
    resp = client.get(f"/api/v1/commercial/{CPID}/loan-pricer")
    assert resp.status_code == 422
    assert "bad input" in resp.get_json()["message"]


def test_loan_pricer_exception(client, cfg_tmp, monkeypatch):
    _write_commercial_loan(cfg_tmp)
    import routes._loan_pricing as lp
    def boom(cdm, overrides):
        raise RuntimeError("x")
    monkeypatch.setattr(lp, "compute_loan_pricing", boom)
    resp = client.get(f"/api/v1/commercial/{CPID}/loan-pricer")
    assert resp.status_code == 500


# ---------------------------------------------------------------------------
# storms route
# ---------------------------------------------------------------------------

def test_storms_options(client):
    resp = client.options(f"/api/v1/commercial/{CPID}/storms")
    assert resp.status_code == 200


def test_storms_not_found(client, cfg_tmp):
    resp = client.get(f"/api/v1/commercial/{CPID}/storms")
    assert resp.status_code == 404


def test_storms_success_with_enrichment(client, cfg_tmp):
    _write_commercial(cfg_tmp)
    cts_dir = cfg_tmp / "commercialts"
    cts_dir.mkdir()
    (cts_dir / f"{CPID}.json").write_text(json.dumps({
        "elevation_m": 10, "floor_level_m": 0.3, "location": {"lat": 1, "lon": 2},
        "nearest_gauges": [{"gauge_id": "GAUGE-001", "distance_m": 100}],
        "summary": {},
        "flood_events": [{"storm_id": "SEQ-001", "flooded": True,
                          "exceeded_severe": True, "damage_ratio": 0.1}],
    }))
    # sequences + gauge + gaugehc enrichment data
    (cfg_tmp / "storm_sequences.json").write_text(json.dumps({
        "num_sequences": 10,
        "sequences": [{"sequence_id": "SEQ-001", "sequence_type": "isolated",
                       "intensity_category": "severe", "name": "Big",
                       "total_precipitation_mm": 80}],
    }))
    (cfg_tmp / "gauge.json").write_text(json.dumps({
        "flood_gauges": [{"FloodGauge": {
            "Header": {"GaugeID": "GAUGE-001"},
            "FloodStage": {"UK": {"FloodAlert": 4, "FloodWarning": 4.5,
                                  "SevereFloodWarning": 5}},
        }}]
    }))
    (cfg_tmp / "gaugehc.json").write_text(json.dumps({
        "hazard_curves": {"GAUGE-001": {"annual_flood_prob_severe": 0.2,
                                        "gauge_name": "Test Gauge"}}
    }))
    ss_dir = cfg_tmp / "stress_storms"
    ss_dir.mkdir()
    (ss_dir / "_index.json").write_text(json.dumps({
        "storms": [{"storm_id": "SEQ-001",
                    "trigger_summary": {"gauges_severe": 3}}]
    }))
    resp = client.get(f"/api/v1/commercial/{CPID}/storms")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["property_address"] == "Tower One"
    ev = body["flood_events"][0]
    assert ev["sequence_type"] == "isolated"
    assert ev["intensity_category"] == "severe"
    assert ev["gauges_severe"] == 3
    ng = body["nearest_gauges"][0]
    assert ng["flood_stages"]["severe"] == 5
    assert ng["severe_count"] == 2  # 0.2 * 10
    assert body["summary"]["severe_at_nearest_gauge"] == 2
