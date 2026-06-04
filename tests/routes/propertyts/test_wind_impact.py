# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Unit tests for the storm-level wind-impact endpoint and its helpers.

Catchment-agnostic: all data (properties, commercials, loans, typhoon
damage rolls) is constructed inline in tmp_path. No geographic constants
or on-disk fixtures are assumed.
"""

import json

import pytest

from routes.propertyts import wind_impact as wi


# ---------------------------------------------------------------------------
# Helpers: monkeypatch config to a tmp catchment dir
# ---------------------------------------------------------------------------

@pytest.fixture
def cfg_tmp(tmp_path, monkeypatch):
    from config import config
    monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
    monkeypatch.setattr(config, "get_input_path", lambda fname: tmp_path / fname)
    return tmp_path


# ---------------------------------------------------------------------------
# _typhoon_damage_path
# ---------------------------------------------------------------------------

def test_typhoon_damage_path(cfg_tmp):
    p = wi._typhoon_damage_path("EVT-0001")
    assert p == cfg_tmp / "typhoon" / "damage" / "EVT-0001.json"


# ---------------------------------------------------------------------------
# _load_commercial_lookup
# ---------------------------------------------------------------------------

def test_load_commercial_lookup_missing_file(cfg_tmp):
    assert wi._load_commercial_lookup() == {}


def test_load_commercial_lookup_bad_json(cfg_tmp):
    (cfg_tmp / "commercial.json").write_text("{not valid json")
    assert wi._load_commercial_lookup() == {}


def test_load_commercial_lookup_parses_entries(cfg_tmp):
    data = {"commercials": [{
        "CommercialAsset": {
            "Header": {"PropertyID": "CPROP-001"},
            "Location": {"BuildingNumber": "10", "StreetName": "High St"},
            "CommercialAttributes": {"CommercialType": "Retail"},
            "Valuation": {"PropertyValue": 1_000_000},
        }
    }]}
    (cfg_tmp / "commercial.json").write_text(json.dumps(data))
    out = wi._load_commercial_lookup()
    assert out["CPROP-001"]["value"] == 1_000_000
    assert out["CPROP-001"]["address"] == "10 High St"
    assert out["CPROP-001"]["commercial_type"] == "Retail"


def test_load_commercial_lookup_skips_missing_id(cfg_tmp):
    data = {"commercials": [{"CommercialAsset": {"Header": {}}}]}
    (cfg_tmp / "commercial.json").write_text(json.dumps(data))
    assert wi._load_commercial_lookup() == {}


def test_load_commercial_lookup_properties_key_and_flat(cfg_tmp):
    """Falls back to 'properties' key and to a flat (non-CommercialAsset) record."""
    data = {"properties": [{
        "Header": {"PropertyID": "CPROP-002"},
        "Location": {"BuildingNumber": "", "StreetName": "Main"},
        "CommercialAttributes": {},
        "Valuation": {"PropertyValue": 500},
    }]}
    (cfg_tmp / "commercial.json").write_text(json.dumps(data))
    out = wi._load_commercial_lookup()
    assert out["CPROP-002"]["value"] == 500
    assert out["CPROP-002"]["address"] == "Main"
    assert out["CPROP-002"]["commercial_type"] == "Commercial"  # default


# ---------------------------------------------------------------------------
# _load_property_address_lookup
# ---------------------------------------------------------------------------

def test_load_property_address_lookup_missing_file(cfg_tmp):
    assert wi._load_property_address_lookup() == {}


def test_load_property_address_lookup_bad_json(cfg_tmp):
    (cfg_tmp / "property.json").write_text("garbage")
    assert wi._load_property_address_lookup() == {}


def test_load_property_address_lookup_parses(cfg_tmp):
    data = {"properties": [
        {"PropertyHeader": {
            "Header": {"PropertyID": "PROP-001"},
            "Location": {"BuildingNumber": "5", "StreetName": "Oak Rd"},
            "PropertyAttributes": {"PropertyType": "Detached"},
        }},
        {"PropertyHeader": {"Header": {}}},  # skipped (no id)
    ]}
    (cfg_tmp / "property.json").write_text(json.dumps(data))
    out = wi._load_property_address_lookup()
    assert list(out) == ["PROP-001"]
    assert out["PROP-001"]["address"] == "5 Oak Rd"
    assert out["PROP-001"]["type"] == "Detached"


# ---------------------------------------------------------------------------
# _build_wind_entry
# ---------------------------------------------------------------------------

def test_build_wind_entry_without_loan():
    entry = wi._build_wind_entry(
        asset_id="PROP-001", asset_class="residential", asset_value=200_000,
        damage={"damage_ratio": 0.25, "peak_sustained_ms": 50,
                "threshold_ms": 30, "v_50_eff_ms": 60},
        address="1 A St", asset_type="Residential", rloan_lookup={},
    )
    assert entry["damage_amount"] == 50_000.0
    assert entry["post_damage_value"] == 150_000.0
    assert entry["has_rloan"] is False
    assert "outstanding_balance" not in entry
    assert entry["peak_wind_ms"] == 50


def test_build_wind_entry_with_loan():
    rloan = {"PROP-001": {"outstanding_balance": 120_000,
                          "current_ltv": 60.0, "remaining_term_months": 200}}
    entry = wi._build_wind_entry(
        asset_id="PROP-001", asset_class="residential", asset_value=200_000,
        damage={"damage_ratio": 0.25}, address="", asset_type="Residential",
        rloan_lookup=rloan,
    )
    assert entry["has_rloan"] is True
    assert entry["outstanding_balance"] == 120_000
    # post_damage_value = 150000 → ltv = 120000/150000*100 = 80.0
    assert entry["post_damage_ltv"] == 80.0


def test_build_wind_entry_total_loss_ltv_capped():
    """post_damage_value <= 0 → LTV sentinel 999."""
    rloan = {"P": {"outstanding_balance": 100}}
    entry = wi._build_wind_entry(
        asset_id="P", asset_class="residential", asset_value=100,
        damage={"damage_ratio": 1.0}, address="", asset_type="X",
        rloan_lookup=rloan,
    )
    assert entry["post_damage_value"] == 0.0
    assert entry["post_damage_ltv"] == 999


def test_build_wind_entry_handles_none_ratio():
    entry = wi._build_wind_entry(
        asset_id="P", asset_class="residential", asset_value=100,
        damage={"damage_ratio": None}, address="", asset_type="X",
        rloan_lookup={},
    )
    assert entry["damage_ratio"] == 0.0
    assert entry["damage_amount"] == 0.0


# ---------------------------------------------------------------------------
# Route: wind_impact
# ---------------------------------------------------------------------------

@pytest.fixture
def client(cfg_tmp):
    from server import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


def test_wind_impact_options(client):
    resp = client.options("/api/v1/propertyts/STORM-0001/wind-impact")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "ok"


def test_wind_impact_no_typhoon_link(client, monkeypatch):
    monkeypatch.setattr(wi, "typhoon_for_storm", lambda sid: None)
    resp = client.get("/api/v1/propertyts/STORM-0001/wind-impact")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["typhoon"] is None
    assert body["rows"] == []
    assert body["summary"]["properties_in_scope"] == 0


def test_wind_impact_damage_file_missing(client, monkeypatch):
    monkeypatch.setattr(wi, "typhoon_for_storm", lambda sid: {"event_id": "EVT-9999"})
    resp = client.get("/api/v1/propertyts/STORM-0001/wind-impact")
    assert resp.status_code == 404
    assert "missing" in resp.get_json()["message"].lower()


def test_wind_impact_damage_file_unreadable(client, cfg_tmp, monkeypatch):
    monkeypatch.setattr(wi, "typhoon_for_storm", lambda sid: {"event_id": "EVT-0001"})
    dmg_dir = cfg_tmp / "typhoon" / "damage"
    dmg_dir.mkdir(parents=True)
    (dmg_dir / "EVT-0001.json").write_text("{bad json")
    resp = client.get("/api/v1/propertyts/STORM-0001/wind-impact")
    assert resp.status_code == 500
    assert "could not read" in resp.get_json()["message"].lower()


def test_wind_impact_full_rows(client, cfg_tmp, monkeypatch):
    # property.json + valuation
    (cfg_tmp / "property.json").write_text(json.dumps({"properties": [{
        "PropertyHeader": {
            "Header": {"PropertyID": "PROP-001"},
            "Location": {"BuildingNumber": "1", "StreetName": "A St"},
            "PropertyAttributes": {"PropertyType": "Detached"},
            "Valuation": {"PropertyValue": 200_000},
        }
    }]}))
    # commercial.json
    (cfg_tmp / "commercial.json").write_text(json.dumps({"commercials": [{
        "CommercialAsset": {
            "Header": {"PropertyID": "CPROP-001"},
            "Location": {"BuildingNumber": "2", "StreetName": "B St"},
            "CommercialAttributes": {"CommercialType": "Office"},
            "Valuation": {"PropertyValue": 1_000_000},
        }
    }]}))
    # loan.json (residential)
    (cfg_tmp / "loan.json").write_text(json.dumps({"loans": [{
        "RLoan": {
            "Header": {"PropertyID": "PROP-001"},
            "CurrentStatus": {"OutstandingBalance": 100_000,
                              "CurrentLTV": 50.0, "RemainingTerm": 180},
        }
    }]}))
    # typhoon damage roll
    dmg_dir = cfg_tmp / "typhoon" / "damage"
    dmg_dir.mkdir(parents=True)
    (dmg_dir / "EVT-0001.json").write_text(json.dumps({
        "horizon_hours": 48,
        "damages": [
            {"property_id": "PROP-001", "damage_ratio": 0.10},
            {"property_id": "CPROP-001", "damage_ratio": 0.20},
            {"property_id": "PROP-UNKNOWN", "damage_ratio": 0.5},  # no value → skip
            {"property_id": "CPROP-UNKNOWN", "damage_ratio": 0.5},  # not in lookup → skip
            {"damage_ratio": 0.9},  # no id → skip
        ],
    }))
    monkeypatch.setattr(wi, "typhoon_for_storm", lambda sid: {
        "event_id": "EVT-0001", "scenario_family": "fam",
        "peak_wind_ms": 55, "mean_damage_ratio": 0.15,
    })

    resp = client.get("/api/v1/propertyts/STORM-0001/wind-impact")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["typhoon"]["event_id"] == "EVT-0001"
    assert body["typhoon"]["horizon_hours"] == 48
    assert body["summary"]["properties_in_scope"] == 1
    assert body["summary"]["commercials_in_scope"] == 1
    # commercial damage 200k vs residential 20k → sorted desc, commercial first
    assert body["rows"][0]["asset_class"] == "commercial"
    assert body["summary"]["total_wind_damage"] == 220_000
    assert body["summary"]["max_damage_ratio"] == 0.20
    # residential row has loan enrichment
    res_row = next(r for r in body["rows"] if r["asset_class"] == "residential")
    assert res_row["has_rloan"] is True
