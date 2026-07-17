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

"""Unit tests for the src/routes/commercial/ package (part 2).

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
# hazard / she / shd / bri
# ---------------------------------------------------------------------------

_PERIL_FILES = [
    ("hazard", "commercialhc.json"),
    ("she", "commercialshe.json"),
    ("shd", "commercialshd.json"),
    ("bri", "commercialbri.json"),
    ("win", "commercialwin.json"),
    ("faw", "commercialfaw.json"),
    ("fow", "commercialfow.json"),
    ("bow", "commercialbow.json"),
    ("baw", "commercialbaw.json"),
]


@pytest.mark.parametrize("suffix,filename", _PERIL_FILES)
def test_hazard_file_missing(client, cfg_tmp, suffix, filename):
    resp = client.get(f"/api/v1/commercial/{CPID}/{suffix}")
    assert resp.status_code == 404
    assert "not yet generated" in resp.get_json()["message"]


@pytest.mark.parametrize("suffix,filename", _PERIL_FILES)
def test_hazard_asset_missing(client, cfg_tmp, suffix, filename):
    (cfg_tmp / filename).write_text(json.dumps({"property_hazard_curves": {}}))
    resp = client.get(f"/api/v1/commercial/{CPID}/{suffix}")
    assert resp.status_code == 404
    assert "not" in resp.get_json()["message"].lower()


def test_hazard_options(client):
    resp = client.options(f"/api/v1/commercial/{CPID}/hazard")
    assert resp.status_code == 200


def test_hazard_success_with_metadata(client, cfg_tmp):
    (cfg_tmp / "commercialhc.json").write_text(json.dumps({
        "property_hazard_curves": {CPID: {"flood_count": 5}},
        "metadata": {"terrain_grid": {"a": 1}, "num_storms": 20000},
    }))
    resp = client.get(f"/api/v1/commercial/{CPID}/hazard")
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert data["_metadata"]["num_storms"] == 20000
    assert data["_metadata"]["terrain_grid"] == {"a": 1}


@pytest.mark.parametrize("suffix,filename", [
    p for p in _PERIL_FILES if p[0] != "hazard"
])
def test_hazard_variants_success(client, cfg_tmp, suffix, filename):
    (cfg_tmp / filename).write_text(json.dumps({
        "property_hazard_curves": {CPID: {"flood_count": 3}}}))
    resp = client.get(f"/api/v1/commercial/{CPID}/{suffix}")
    assert resp.status_code == 200
    assert resp.get_json()["data"]["flood_count"] == 3


# ---------------------------------------------------------------------------
# commercial_record
# ---------------------------------------------------------------------------

def test_record_options(client):
    resp = client.options(f"/api/v1/commercial/{CPID}")
    assert resp.status_code == 200


def test_record_file_missing(client, cfg_tmp):
    resp = client.get(f"/api/v1/commercial/{CPID}")
    assert resp.status_code == 404
    assert "commercial.json not found" in resp.get_json()["message"]


def test_record_not_found(client, cfg_tmp):
    (cfg_tmp / "commercial.json").write_text(json.dumps({"commercial_assets": []}))
    resp = client.get(f"/api/v1/commercial/{CPID}")
    assert resp.status_code == 404
    assert "not found" in resp.get_json()["message"]


def test_record_success(client, cfg_tmp):
    _write_commercial(cfg_tmp)
    resp = client.get(f"/api/v1/commercial/{CPID}")
    assert resp.status_code == 200
    assert resp.get_json()["property"]["CommercialAsset"]["Header"]["PropertyID"] == CPID


# ---------------------------------------------------------------------------
# list_commercial / list_commercial_loans
# ---------------------------------------------------------------------------

def test_list_commercial_missing_file(client, cfg_tmp):
    resp = client.get("/api/v1/commercial")
    assert resp.status_code == 200
    assert resp.get_json()["count"] == 0


def test_list_commercial_success(client, cfg_tmp):
    _write_commercial(cfg_tmp)
    resp = client.get("/api/v1/commercial")
    assert resp.get_json()["count"] == 1


def test_list_commercial_loans_missing_file(client, cfg_tmp):
    resp = client.get("/api/v1/commercial-loans")
    assert resp.status_code == 200
    assert resp.get_json()["count"] == 0


def test_list_commercial_loans_success(client, cfg_tmp):
    _write_commercial_loan(cfg_tmp)
    resp = client.get("/api/v1/commercial-loans")
    assert resp.get_json()["count"] == 1


# ---------------------------------------------------------------------------
# storms.py enrichment helpers — direct unit tests of the except branches
# ---------------------------------------------------------------------------

def test_lookup_address_swallows_malformed_json(cfg_tmp):
    """storms.py _lookup_commercial_address: corrupt commercial.json → ''."""
    from routes.commercial.storms import _lookup_commercial_address
    (cfg_tmp / "commercial.json").write_text("{not valid json")
    assert _lookup_commercial_address(CPID) == ""


def test_enrich_flood_events_swallows_malformed_sequences(cfg_tmp):
    """storms.py _enrich_flood_events: corrupt storm_sequences.json is tolerated."""
    from routes.commercial.storms import _enrich_flood_events
    (cfg_tmp / "storm_sequences.json").write_text("{bad json")
    pdata = {"flood_events": [{"storm_id": "S1"}]}
    _enrich_flood_events(pdata)  # must not raise
    ev = pdata["flood_events"][0]
    assert ev["sequence_type"] == "isolated"
    assert ev["gauges_severe"] == 0


def test_enrich_flood_events_reads_storms_metadata(cfg_tmp):
    """storms.py _enrich_flood_events: a storm_sequences doc with the 'storms' key
    supplies per-storm name/category metadata (build_storm_lookups line 68 branch)."""
    import database
    from db_helpers import tmp_catchment
    from config import config
    from routes.commercial.storms import _enrich_flood_events
    with tmp_catchment(cfg_tmp, catchment=config.catchment_id):
        database.save_storm_sequences(database.active_catchment(), {
            "storms": [{"storm_id": "S1", "name": "Bertha",
                        "intensity_category": "severe",
                        "effective_precipitation_mm": 42}]
        })
        pdata = {"flood_events": [{"storm_id": "S1"}]}
        _enrich_flood_events(pdata)
    ev = pdata["flood_events"][0]
    assert ev["name"] == "Bertha"
    assert ev["intensity_category"] == "severe"
    assert ev["effective_precipitation_mm"] == 42


def test_enrich_flood_events_swallows_malformed_stress_storms(cfg_tmp):
    """storms.py _enrich_flood_events: corrupt stress_storms.json is tolerated."""
    from routes.commercial.storms import _enrich_flood_events
    (cfg_tmp / "stress_storms.json").write_text("{bad json")
    pdata = {"flood_events": [{"storm_id": "S1"}]}
    _enrich_flood_events(pdata)  # must not raise
    assert pdata["flood_events"][0]["gauges_severe"] == 0


def test_enrich_nearest_gauges_swallows_malformed_gauge_json(cfg_tmp):
    """storms.py _enrich_nearest_gauges: corrupt gauge.json → empty stages."""
    from routes._storm_enrich import enrich_nearest_gauges as _enrich_nearest_gauges
    (cfg_tmp / "gauge.json").write_text("{bad json")
    pdata = {"nearest_gauges": [{"gauge_id": "G1"}]}
    severe = _enrich_nearest_gauges(pdata)
    assert severe == 0
    assert pdata["nearest_gauges"][0]["flood_stages"] == {}


def test_enrich_nearest_gauges_swallows_malformed_hc_json(cfg_tmp):
    """storms.py _enrich_nearest_gauges: corrupt gaugehc.json is tolerated."""
    from routes._storm_enrich import enrich_nearest_gauges as _enrich_nearest_gauges
    (cfg_tmp / "gaugehc.json").write_text("{bad json")
    (cfg_tmp / "storm_sequences.json").write_text(json.dumps({"num_sequences": 100}))
    pdata = {"nearest_gauges": [{"gauge_id": "G1"}]}
    severe = _enrich_nearest_gauges(pdata)
    assert severe == 0
