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

"""Tests for the CDM tool's RED-gated recompute glue + small data helpers.

Covers ``_maybe_recompute`` (every branch: non-priced asset, no-RED change,
RED-but-no-curve, RED-but-shortcut-declines, and the supported before/after),
plus ``_baseline_value``, ``_num_storms``, ``api_catchment-info`` and the
priced-store short-circuit in ``_hc_record``.
"""

import json

FLOOR = "PropertyHeader.Construction.FloorLevelMeters"
GROUND = "PropertyHeader.RiskAssessment.GroundLevelMeters"
TYPE = "PropertyHeader.Header.propertyType"


def _target(floor=1.0):
    return {"PropertyHeader": {"Header": {"PropertyID": "P1"},
                               "Construction": {"FloorLevelMeters": floor}}}


# --- _maybe_recompute -------------------------------------------------------
def test_maybe_recompute_non_priced_asset_none(app_mod):
    assert app_mod._maybe_recompute("mortgage", "L1", {}, {FLOOR: 1.0}) is None


def test_maybe_recompute_no_red_change_none(app_mod):
    # propertyType is GREEN -> the loop finds no RED field -> None
    assert app_mod._maybe_recompute("property", "P1", _target(), {TYPE: "x"}) is None


def test_maybe_recompute_red_but_no_hazard_curve(app_mod, monkeypatch):
    monkeypatch.setattr(app_mod, "_hc_record", lambda a, r: None)
    out = app_mod._maybe_recompute("property", "P1", _target(), {FLOOR: 1.0})
    assert out["supported"] is False and out["tier"] == "RED"
    assert "No hazard curve" in out["reason"]


def test_maybe_recompute_red_shortcut_declines(app_mod, monkeypatch):
    monkeypatch.setattr(app_mod, "_hc_record",
                        lambda a, r: {"spread_decomposition": {"x": 1}})
    monkeypatch.setattr(app_mod, "_num_storms", lambda a: 100)
    monkeypatch.setattr(app_mod, "_baseline_value", lambda a, r, p: 0.0)
    # ground-level edit -> recompute_decomposition returns None -> full re-run
    out = app_mod._maybe_recompute("property", "P1", _target(), {GROUND: 1.0})
    assert out["supported"] is False and "full portfolio re-run" in out["reason"]


def test_maybe_recompute_supported_before_after(app_mod, monkeypatch):
    before = {"property_spread_bps": 100.0}
    after = {"property_spread_bps": 0.0}
    monkeypatch.setattr(app_mod, "_hc_record",
                        lambda a, r: {"spread_decomposition": before})
    monkeypatch.setattr(app_mod, "_num_storms", lambda a: 100)
    monkeypatch.setattr(app_mod, "_baseline_value", lambda a, r, p: 0.0)
    monkeypatch.setattr(app_mod, "recompute_decomposition",
                        lambda *a, **k: after)
    out = app_mod._maybe_recompute("property", "P1", _target(5.0), {FLOOR: 5.0})
    assert out["supported"] is True and out["tier"] == "RED"
    assert out["before"] == before and out["after"] == after
    assert out["field"] == FLOOR


def test_update_endpoint_surfaces_recompute(client, seed, app_mod, monkeypatch):
    """An end-to-end PUT carries the recompute block in its response."""
    seed("property", {"properties": [_target(1.0)]})
    monkeypatch.setattr(app_mod, "_maybe_recompute",
                        lambda *a, **k: {"supported": True, "tier": "RED"})
    r = client.put("/api/property/items/P1", json={"changes": {FLOOR: 2.0}})
    assert r.get_json()["recompute"] == {"supported": True, "tier": "RED"}


# --- _baseline_value --------------------------------------------------------
def test_baseline_value_reads_seed_doc(app_mod, seam):
    seam.save_properties(app_mod.CATCHMENT, {"properties": [_target(3.0)]})
    assert app_mod._baseline_value("property", "P1", FLOOR) == 3.0
    # an unknown record id -> None
    assert app_mod._baseline_value("property", "ZZZ", FLOOR) is None


def test_baseline_value_no_seed_data_returns_none(app_mod, seam):
    # empty seam + no golden fixture for commercial -> _seed_doc raises -> None
    assert app_mod._baseline_value("commercial", "C1", FLOOR) is None


# --- _num_storms ------------------------------------------------------------
def test_num_storms_reads_metadata(app_mod, seam):
    seam.save_property_hazard_curves(
        app_mod.CATCHMENT, {"metadata": {"num_storms": 250}}, mode="flood")
    assert app_mod._num_storms("property") == 250


def test_num_storms_no_data_or_unsupported(app_mod, seam):
    assert app_mod._num_storms("property") is None       # empty seam, no metadata
    assert app_mod._num_storms("mortgage") is None        # not in _HC_GETTERS


# --- api_catchment_info -----------------------------------------------------
def test_catchment_info_with_center(client, app_mod, monkeypatch):
    import config.visual as vis
    monkeypatch.setattr(vis, "get_map_center", lambda: (51.5, -0.1))
    data = client.get("/api/catchment-info").get_json()
    assert data["catchment"] == app_mod.CATCHMENT
    assert data["lat"] == 51.5 and data["lon"] == -0.1


def test_catchment_info_handles_failure(client, app_mod, monkeypatch):
    import config.visual as vis
    def boom():
        raise RuntimeError("no center")
    monkeypatch.setattr(vis, "get_map_center", boom)
    data = client.get("/api/catchment-info").get_json()
    assert data["lat"] is None and data["lon"] is None


# --- _hc_record priced short-circuit ---------------------------------------
def test_hc_record_prefers_priced_store(app_mod, sandbox):
    app_mod._save_priced("property", "PROP-NEW", {"flood_zone": "X"})
    assert app_mod._hc_record("property", "PROP-NEW") == {"flood_zone": "X"}
