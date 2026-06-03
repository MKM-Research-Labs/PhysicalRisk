# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Unit tests for the flood-storm ↔ typhoon-event linkage.

Catchment-agnostic: builds a synthetic typhoon/damage/ tree and a
storm_sequences.json inside tmp_path. No on-disk catchment data assumed.
"""

import json

import pytest

from port import typhoon_storm_link as tsl


@pytest.fixture
def cfg_tmp(tmp_path, monkeypatch):
    from config import config
    monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
    monkeypatch.setattr(config, "get_input_path", lambda fname: tmp_path / fname)
    tsl.invalidate_cache()
    yield tmp_path
    tsl.invalidate_cache()


def _write_damage(tmp_path, event_id, family, damages):
    dmg_dir = tmp_path / "typhoon" / "damage"
    dmg_dir.mkdir(parents=True, exist_ok=True)
    (dmg_dir / f"{event_id}.json").write_text(json.dumps({
        "event_id": event_id,
        "scenario_family": family,
        "damages": damages,
    }))


def _write_sequences(tmp_path, sequences):
    (tmp_path / "storm_sequences.json").write_text(
        json.dumps({"sequences": sequences}))


# ---------------------------------------------------------------------------
# _typhoon_dir
# ---------------------------------------------------------------------------

def test_typhoon_dir(cfg_tmp):
    assert tsl._typhoon_dir() == cfg_tmp / "typhoon"


# ---------------------------------------------------------------------------
# _load_typhoon_index
# ---------------------------------------------------------------------------

def test_load_typhoon_index_missing_dir(cfg_tmp):
    assert tsl._load_typhoon_index() == []


def test_load_typhoon_index_bad_json_skipped(cfg_tmp):
    dmg_dir = cfg_tmp / "typhoon" / "damage"
    dmg_dir.mkdir(parents=True)
    (dmg_dir / "EVT-0001.json").write_text("{not json")
    assert tsl._load_typhoon_index() == []


def test_load_typhoon_index_empty_damages_skipped(cfg_tmp):
    _write_damage(cfg_tmp, "EVT-0001", "extreme", [])
    assert tsl._load_typhoon_index() == []


def test_load_typhoon_index_parses(cfg_tmp):
    _write_damage(cfg_tmp, "EVT-0001", "extreme", [
        {"peak_sustained_ms": 40.0, "damage_ratio": 0.2},
        {"peak_sustained_ms": 60.0, "damage_ratio": 0.4},
    ])
    idx = tsl._load_typhoon_index()
    assert len(idx) == 1
    assert idx[0]["event_id"] == "EVT-0001"
    assert idx[0]["scenario_family"] == "extreme"
    assert idx[0]["peak_wind_ms"] == 60.0
    assert idx[0]["mean_damage_ratio"] == pytest.approx(0.3)


def test_load_typhoon_index_event_id_falls_back_to_stem(cfg_tmp):
    dmg_dir = cfg_tmp / "typhoon" / "damage"
    dmg_dir.mkdir(parents=True)
    (dmg_dir / "EVT-0007.json").write_text(json.dumps({
        "scenario_family": "severe",
        "damages": [{"peak_sustained_ms": 10.0, "damage_ratio": 0.1}],
    }))
    idx = tsl._load_typhoon_index()
    assert idx[0]["event_id"] == "EVT-0007"


# ---------------------------------------------------------------------------
# _load_flood_index
# ---------------------------------------------------------------------------

def test_load_flood_index_missing_file(cfg_tmp):
    assert tsl._load_flood_index() == []


def test_load_flood_index_bad_json(cfg_tmp):
    (cfg_tmp / "storm_sequences.json").write_text("{bad")
    assert tsl._load_flood_index() == []


def test_load_flood_index_skips_idless_and_sorts(cfg_tmp):
    _write_sequences(cfg_tmp, [
        {"sequence_id": "STORM-A", "intensity_category": "moderate",
         "total_precipitation_mm": 30.0},
        {"intensity_category": "severe", "total_precipitation_mm": 99.0},  # no id
        {"sequence_id": "STORM-B", "intensity_category": "extreme",
         "total_precipitation_mm": 80.0},
    ])
    idx = tsl._load_flood_index()
    assert [s["sequence_id"] for s in idx] == ["STORM-B", "STORM-A"]  # sorted desc


# ---------------------------------------------------------------------------
# build_linkage
# ---------------------------------------------------------------------------

def test_build_linkage_empty_when_no_typhoons(cfg_tmp):
    _write_sequences(cfg_tmp, [
        {"sequence_id": "STORM-A", "intensity_category": "moderate",
         "total_precipitation_mm": 30.0}])
    result = tsl.build_linkage()
    assert result["storm_to_typhoon"] == {}
    assert result["typhoon_to_storm"] == {}


def test_build_linkage_empty_when_no_floods(cfg_tmp):
    _write_damage(cfg_tmp, "EVT-0001", "extreme",
                  [{"peak_sustained_ms": 50.0, "damage_ratio": 0.3}])
    result = tsl.build_linkage()
    assert result["storm_to_typhoon"] == {}


def test_build_linkage_pairs_by_bucket(cfg_tmp):
    # catastrophic floods -> extreme typhoons
    _write_sequences(cfg_tmp, [
        {"sequence_id": "STORM-CAT1", "intensity_category": "catastrophic",
         "total_precipitation_mm": 200.0},
        {"sequence_id": "STORM-MOD1", "intensity_category": "moderate",
         "total_precipitation_mm": 20.0},
    ])
    _write_damage(cfg_tmp, "EVT-0001", "extreme",
                  [{"peak_sustained_ms": 70.0, "damage_ratio": 0.5}])
    _write_damage(cfg_tmp, "EVT-0002", "baseline",
                  [{"peak_sustained_ms": 25.0, "damage_ratio": 0.05}])
    result = tsl.build_linkage()
    s2t = result["storm_to_typhoon"]
    assert s2t["STORM-CAT1"]["event_id"] == "EVT-0001"
    assert s2t["STORM-MOD1"]["event_id"] == "EVT-0002"
    assert result["typhoon_to_storm"]["EVT-0001"] == "STORM-CAT1"
    assert result["diagnostics"]["linked_storms"] == 2
    assert result["diagnostics"]["unmatched_typhoons"] == []


def test_build_linkage_surplus_typhoons_unmatched(cfg_tmp):
    # one catastrophic flood, two extreme typhoons → one surplus typhoon
    _write_sequences(cfg_tmp, [
        {"sequence_id": "STORM-CAT1", "intensity_category": "catastrophic",
         "total_precipitation_mm": 200.0}])
    _write_damage(cfg_tmp, "EVT-0001", "extreme",
                  [{"peak_sustained_ms": 70.0, "damage_ratio": 0.5}])
    _write_damage(cfg_tmp, "EVT-0002", "extreme",
                  [{"peak_sustained_ms": 60.0, "damage_ratio": 0.4}])
    result = tsl.build_linkage()
    # strongest typhoon (EVT-0001, 70 m/s) pairs with the flood
    assert result["storm_to_typhoon"]["STORM-CAT1"]["event_id"] == "EVT-0001"
    assert result["diagnostics"]["unmatched_typhoons"] == ["EVT-0002"]


# ---------------------------------------------------------------------------
# Caching + public lookups
# ---------------------------------------------------------------------------

def test_get_linkage_caches(cfg_tmp):
    _write_sequences(cfg_tmp, [
        {"sequence_id": "STORM-CAT1", "intensity_category": "catastrophic",
         "total_precipitation_mm": 200.0}])
    _write_damage(cfg_tmp, "EVT-0001", "extreme",
                  [{"peak_sustained_ms": 70.0, "damage_ratio": 0.5}])
    first = tsl.get_linkage()
    second = tsl.get_linkage()
    assert first is second  # cached identity


def test_invalidate_cache_forces_rebuild(cfg_tmp):
    _write_sequences(cfg_tmp, [
        {"sequence_id": "STORM-CAT1", "intensity_category": "catastrophic",
         "total_precipitation_mm": 200.0}])
    _write_damage(cfg_tmp, "EVT-0001", "extreme",
                  [{"peak_sustained_ms": 70.0, "damage_ratio": 0.5}])
    first = tsl.get_linkage()
    tsl.invalidate_cache()
    second = tsl.get_linkage()
    assert first is not second


def test_link_for_storm(cfg_tmp):
    _write_sequences(cfg_tmp, [
        {"sequence_id": "STORM-CAT1", "intensity_category": "catastrophic",
         "total_precipitation_mm": 200.0}])
    _write_damage(cfg_tmp, "EVT-0001", "extreme",
                  [{"peak_sustained_ms": 70.0, "damage_ratio": 0.5}])
    assert tsl.link_for_storm("STORM-CAT1")["event_id"] == "EVT-0001"
    assert tsl.link_for_storm("STORM-MISSING") is None
    assert tsl.link_for_storm("") is None


def test_storm_for_typhoon(cfg_tmp):
    _write_sequences(cfg_tmp, [
        {"sequence_id": "STORM-CAT1", "intensity_category": "catastrophic",
         "total_precipitation_mm": 200.0}])
    _write_damage(cfg_tmp, "EVT-0001", "extreme",
                  [{"peak_sustained_ms": 70.0, "damage_ratio": 0.5}])
    assert tsl.storm_for_typhoon("EVT-0001") == "STORM-CAT1"
    assert tsl.storm_for_typhoon("EVT-MISSING") is None
    assert tsl.storm_for_typhoon("") is None
