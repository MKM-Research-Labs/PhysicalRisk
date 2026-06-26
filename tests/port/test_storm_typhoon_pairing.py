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

"""Unit tests for the true 1:1 storm ↔ typhoon pairing (shared event_id).

Catchment-agnostic: seeds synthetic typhoon damage events and storm sequences
(carrying event_id per sequence) into the ``database`` seam via a scratch
``tmp_catchment`` backend. No on-disk catchment data assumed."""

import pytest
from db_helpers import tmp_catchment

import database
from port import storm_typhoon_pairing as stp

_CATCHMENT = "thames"


@pytest.fixture
def seam_tmp(tmp_path):
    """Bind a scratch seam backend and reset the pairing cache around the test."""
    with tmp_catchment(tmp_path, _CATCHMENT):
        stp.invalidate_cache()
        yield
        stp.invalidate_cache()


def _write_damage(event_id, family, damages, *, with_event_id=True):
    """Seed one typhoon damage event into the seam (keyed on event_id)."""
    payload = {"scenario_family": family, "damages": damages}
    if with_event_id:
        payload["event_id"] = event_id
    database.save_typhoon_event(_CATCHMENT, event_id, payload)


def _write_sequences(sequences):
    """Seed the storm sequences document into the seam."""
    database.save_storm_sequences(_CATCHMENT, {"sequences": sequences})


def _raise_value_error(*_a, **_k):
    raise ValueError("corrupt record")


# ---------------------------------------------------------------------------
# _load_typhoon_index
# ---------------------------------------------------------------------------

def test_load_typhoon_index_no_events(seam_tmp):
    assert stp._load_typhoon_index() == []


def test_load_typhoon_index_corrupt_event_skipped(seam_tmp, monkeypatch):
    _write_damage("EVT-0001", "extreme",
                  [{"peak_sustained_ms": 10.0, "damage_ratio": 0.1}])
    monkeypatch.setattr(database, "get_typhoon_event", _raise_value_error)
    assert stp._load_typhoon_index() == []


def test_load_typhoon_index_empty_damages_skipped(seam_tmp):
    _write_damage("EVT-0001", "extreme", [])
    assert stp._load_typhoon_index() == []


def test_load_typhoon_index_parses(seam_tmp):
    _write_damage("EVT-0001", "extreme", [
        {"peak_sustained_ms": 40.0, "damage_ratio": 0.2},
        {"peak_sustained_ms": 60.0, "damage_ratio": 0.4},
    ])
    idx = stp._load_typhoon_index()
    assert len(idx) == 1
    assert idx[0]["event_id"] == "EVT-0001"
    assert idx[0]["scenario_family"] == "extreme"
    assert idx[0]["peak_wind_ms"] == 60.0
    assert idx[0]["mean_damage_ratio"] == pytest.approx(0.3)


def test_load_typhoon_index_event_id_falls_back_to_key(seam_tmp):
    _write_damage("EVT-0007", "severe",
                  [{"peak_sustained_ms": 10.0, "damage_ratio": 0.1}],
                  with_event_id=False)
    idx = stp._load_typhoon_index()
    assert idx[0]["event_id"] == "EVT-0007"


# ---------------------------------------------------------------------------
# _load_storm_event_map
# ---------------------------------------------------------------------------

def test_load_storm_event_map_missing(seam_tmp):
    assert stp._load_storm_event_map() == []


def test_load_storm_event_map_corrupt(seam_tmp, monkeypatch):
    monkeypatch.setattr(database, "get_storm_sequences", _raise_value_error)
    assert stp._load_storm_event_map() == []


def test_load_storm_event_map_skips_idless_and_eventless(seam_tmp):
    _write_sequences([
        {"sequence_id": "SEQ-A", "event_id": "EVT-00000"},
        {"event_id": "EVT-00001"},                 # no sequence_id
        {"sequence_id": "SEQ-C"},                   # no event_id (pre-coupling)
        {"sequence_id": "SEQ-D", "event_id": "EVT-00003"},
    ])
    out = stp._load_storm_event_map()
    assert out == [
        {"sequence_id": "SEQ-A", "event_id": "EVT-00000"},
        {"sequence_id": "SEQ-D", "event_id": "EVT-00003"},
    ]


# ---------------------------------------------------------------------------
# build_pairing — direct 1:1 join on event_id
# ---------------------------------------------------------------------------

def test_build_pairing_empty_when_no_typhoons(seam_tmp):
    _write_sequences([{"sequence_id": "SEQ-A", "event_id": "EVT-00000"}])
    result = stp.build_pairing()
    assert result["storm_to_typhoon"] == {}
    assert result["typhoon_to_storm"] == {}
    # event_id present but no damage roll -> counted as flood-only.
    assert result["diagnostics"]["flood_only_storms"] == 1


def test_build_pairing_empty_when_no_floods(seam_tmp):
    _write_damage("EVT-00000", "extreme",
                  [{"peak_sustained_ms": 50.0, "damage_ratio": 0.3}])
    result = stp.build_pairing()
    assert result["storm_to_typhoon"] == {}
    assert result["diagnostics"]["unmatched_typhoons"] == ["EVT-00000"]


def test_build_pairing_joins_on_shared_event_id(seam_tmp):
    # The pairing is purely the shared event_id — NOT precipitation/wind rank.
    _write_sequences([
        {"sequence_id": "SEQ-A", "event_id": "EVT-00000"},
        {"sequence_id": "SEQ-B", "event_id": "EVT-00001"},
    ])
    _write_damage("EVT-00000", "extreme",
                  [{"peak_sustained_ms": 70.0, "damage_ratio": 0.5}])
    _write_damage("EVT-00001", "baseline",
                  [{"peak_sustained_ms": 25.0, "damage_ratio": 0.05}])
    result = stp.build_pairing()
    s2t = result["storm_to_typhoon"]
    assert s2t["SEQ-A"]["event_id"] == "EVT-00000"
    assert s2t["SEQ-A"]["scenario_family"] == "extreme"
    assert s2t["SEQ-A"]["peak_wind_ms"] == 70.0
    assert s2t["SEQ-B"]["event_id"] == "EVT-00001"
    assert result["typhoon_to_storm"]["EVT-00000"] == "SEQ-A"
    assert result["diagnostics"]["paired_storms"] == 2
    assert result["diagnostics"]["unmatched_typhoons"] == []


def test_build_pairing_flood_only_when_event_has_no_damage(seam_tmp):
    # SEQ-A's typhoon ran; SEQ-B's event_id has no damage roll (flood-only).
    _write_sequences([
        {"sequence_id": "SEQ-A", "event_id": "EVT-00000"},
        {"sequence_id": "SEQ-B", "event_id": "EVT-00001"},
    ])
    _write_damage("EVT-00000", "severe",
                  [{"peak_sustained_ms": 45.0, "damage_ratio": 0.2}])
    result = stp.build_pairing()
    assert set(result["storm_to_typhoon"]) == {"SEQ-A"}
    assert result["diagnostics"]["flood_only_storms"] == 1


# ---------------------------------------------------------------------------
# Caching + public lookups
# ---------------------------------------------------------------------------

def test_get_pairing_caches(seam_tmp):
    _write_sequences([{"sequence_id": "SEQ-A", "event_id": "EVT-00000"}])
    _write_damage("EVT-00000", "extreme",
                  [{"peak_sustained_ms": 70.0, "damage_ratio": 0.5}])
    assert stp.get_pairing() is stp.get_pairing()


def test_invalidate_cache_forces_rebuild(seam_tmp):
    _write_sequences([{"sequence_id": "SEQ-A", "event_id": "EVT-00000"}])
    _write_damage("EVT-00000", "extreme",
                  [{"peak_sustained_ms": 70.0, "damage_ratio": 0.5}])
    first = stp.get_pairing()
    stp.invalidate_cache()
    assert stp.get_pairing() is not first


def test_typhoon_for_storm(seam_tmp):
    _write_sequences([{"sequence_id": "SEQ-A", "event_id": "EVT-00000"}])
    _write_damage("EVT-00000", "extreme",
                  [{"peak_sustained_ms": 70.0, "damage_ratio": 0.5}])
    assert stp.typhoon_for_storm("SEQ-A")["event_id"] == "EVT-00000"
    assert stp.typhoon_for_storm("SEQ-MISSING") is None
    assert stp.typhoon_for_storm("") is None


def test_storm_for_typhoon(seam_tmp):
    _write_sequences([{"sequence_id": "SEQ-A", "event_id": "EVT-00000"}])
    _write_damage("EVT-00000", "extreme",
                  [{"peak_sustained_ms": 70.0, "damage_ratio": 0.5}])
    assert stp.storm_for_typhoon("EVT-00000") == "SEQ-A"
    assert stp.storm_for_typhoon("EVT-MISSING") is None
    assert stp.storm_for_typhoon("") is None
