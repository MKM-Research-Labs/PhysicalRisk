# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Covers the typhoon-linkage branch of /properties/<id>/storms and the
per-property typhoon damage loader in core_storms.py.

Catchment-agnostic: synthesises propertyts/, typhoon/damage/,
storm_sequences.json inside tmp_path and rebuilds the linkage cache.
"""

import json

import pytest

from routes.propertyts import core_storms as cs
from port import typhoon_storm_link as tsl


PROP_ID = "PROP-0001"


@pytest.fixture
def cfg_tmp(tmp_path, monkeypatch):
    from config import config
    monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
    monkeypatch.setattr(config, "get_input_path", lambda fname: tmp_path / fname)
    tsl.invalidate_cache()
    yield tmp_path
    tsl.invalidate_cache()


@pytest.fixture
def client(cfg_tmp):
    from server import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


# ---------------------------------------------------------------------------
# _load_typhoon_damage_for_property
# ---------------------------------------------------------------------------

def test_damage_loader_missing_dir(cfg_tmp):
    assert cs._load_typhoon_damage_for_property(PROP_ID) == {}


def test_damage_loader_bad_json_skipped(cfg_tmp):
    d = cfg_tmp / "typhoon" / "damage"
    d.mkdir(parents=True)
    (d / "EVT-0001.json").write_text("{bad")
    assert cs._load_typhoon_damage_for_property(PROP_ID) == {}


def test_damage_loader_indexes_property(cfg_tmp):
    d = cfg_tmp / "typhoon" / "damage"
    d.mkdir(parents=True)
    (d / "EVT-0001.json").write_text(json.dumps({
        "event_id": "EVT-0001",
        "damages": [
            {"property_id": "PROP-OTHER", "damage_ratio": 0.1},
            {"property_id": PROP_ID, "peak_sustained_ms": 55,
             "threshold_ms": 30, "v_50_eff_ms": 60, "damage_ratio": 0.3},
        ],
    }))
    out = cs._load_typhoon_damage_for_property(PROP_ID)
    assert out["EVT-0001"]["peak_sustained_ms"] == 55
    assert out["EVT-0001"]["damage_ratio"] == 0.3


def test_damage_loader_event_id_from_stem(cfg_tmp):
    d = cfg_tmp / "typhoon" / "damage"
    d.mkdir(parents=True)
    (d / "EVT-0002.json").write_text(json.dumps({
        "damages": [{"property_id": PROP_ID, "damage_ratio": 0.2}]}))
    out = cs._load_typhoon_damage_for_property(PROP_ID)
    assert "EVT-0002" in out


# ---------------------------------------------------------------------------
# Route: typhoon block + wind-only synthetic event
# ---------------------------------------------------------------------------

def _setup_catchment(tmp_path, flood_events):
    pts = tmp_path / "propertyts"
    pts.mkdir()
    (pts / f"{PROP_ID}.json").write_text(json.dumps({
        "elevation_m": 5, "floor_level_m": 5.2, "location": {},
        "nearest_gauges": [],
        "summary": {},
        "flood_events": flood_events,
    }))
    (tmp_path / "storm_sequences.json").write_text(json.dumps({
        "num_sequences": 2,
        "sequences": [
            {"sequence_id": "SEQ-CAT", "intensity_category": "catastrophic",
             "sequence_type": "isolated", "name": "Cat", "total_precipitation_mm": 200},
            {"sequence_id": "SEQ-EXT", "intensity_category": "extreme",
             "sequence_type": "isolated", "name": "Ext", "total_precipitation_mm": 150},
        ],
    }))
    dmg = tmp_path / "typhoon" / "damage"
    dmg.mkdir(parents=True)
    # EVT-0001 (extreme family) → pairs with catastrophic flood SEQ-CAT
    (dmg / "EVT-0001.json").write_text(json.dumps({
        "event_id": "EVT-0001", "scenario_family": "extreme",
        "damages": [{"property_id": PROP_ID, "peak_sustained_ms": 70,
                     "threshold_ms": 30, "v_50_eff_ms": 65, "damage_ratio": 0.5}],
    }))
    # EVT-0002 (severe family) → pairs with extreme flood SEQ-EXT
    (dmg / "EVT-0002.json").write_text(json.dumps({
        "event_id": "EVT-0002", "scenario_family": "severe",
        "damages": [{"property_id": PROP_ID, "peak_sustained_ms": 40,
                     "threshold_ms": 30, "v_50_eff_ms": 45, "damage_ratio": 0.2}],
    }))


def test_storms_attaches_typhoon_block(client, cfg_tmp):
    # property flooded in SEQ-CAT (which pairs with EVT-0001)
    _setup_catchment(cfg_tmp, [{
        "storm_id": "SEQ-CAT", "flooded": True, "exceeded_severe": True,
        "damage_ratio": 0.1, "flood_depth_m": 0.5,
    }])
    resp = client.get(f"/api/v1/properties/{PROP_ID}/storms")
    assert resp.status_code == 200
    events = {e["storm_id"]: e for e in resp.get_json()["flood_events"]}
    cat = events["SEQ-CAT"]
    assert cat["typhoon"] is not None
    assert cat["typhoon"]["event_id"] == "EVT-0001"
    assert cat["typhoon"]["peak_wind_ms"] == 70
    assert cat["typhoon"]["wind_damage_ratio"] == 0.5


def test_storms_appends_wind_only_event(client, cfg_tmp):
    # property flooded only in SEQ-CAT; SEQ-EXT (paired with EVT-0002) is
    # NOT in flood_events but the property is in EVT-0002 damage file →
    # a synthetic wind-only flood_event row must be appended.
    _setup_catchment(cfg_tmp, [{
        "storm_id": "SEQ-CAT", "flooded": True, "exceeded_severe": True,
        "damage_ratio": 0.1, "flood_depth_m": 0.5,
    }])
    resp = client.get(f"/api/v1/properties/{PROP_ID}/storms")
    assert resp.status_code == 200
    events = {e["storm_id"]: e for e in resp.get_json()["flood_events"]}
    assert "SEQ-EXT" in events
    synth = events["SEQ-EXT"]
    assert synth["flooded"] is False
    assert synth["flood_depth_m"] == 0.0
    assert synth["typhoon"]["event_id"] == "EVT-0002"
    assert synth["typhoon"]["peak_wind_ms"] == 40
