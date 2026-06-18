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

"""Tests for the peril and PRS-waterfall payload builders + their endpoints.

Covers ``_flood_payload``/``_wind_payload``/``_fire_payload``/``_seismic_payload``
and the ``/perils`` and ``/waterfall`` routes, stubbing the data loaders
(``_hc_record``/``_model_assets``/``_storm_type_index``) so the shaping logic is
tested deterministically without the data tree.
"""


# --- flood ------------------------------------------------------------------
def test_flood_unsupported_for_non_hc_asset(app_mod):
    out = app_mod._flood_payload("gauge", "G1")
    assert out["supported"] is False


def test_flood_no_record_zero_events(app_mod, monkeypatch):
    monkeypatch.setattr(app_mod, "_hc_record", lambda a, r: None)
    out = app_mod._flood_payload("property", "P1")
    assert out == {"supported": True, "count": 0, "events": []}


def test_flood_filters_sorts_and_caps(app_mod, monkeypatch):
    details = [{"storm_id": "S0", "flooded": False, "damage_ratio": 0}]  # dropped
    details += [{"storm_id": f"S{i}", "flooded": True, "damage_ratio": i / 100,
                 "flood_depth_m": 1.0, "gauge_peak_m": 2.0,
                 "exceeded_severe": (i % 2 == 0)} for i in range(1, 16)]
    monkeypatch.setattr(app_mod, "_hc_record", lambda a, r: {
        "flood_zone": "3", "storm_details": details})
    monkeypatch.setattr(app_mod, "_storm_type_index",
                        lambda: {"S15": {"type": "cluster", "intensity": "sev"}})
    out = app_mod._flood_payload("property", "P1")
    assert out["supported"] is True
    assert out["count"] == 15          # 15 real events (S0 filtered out)
    assert len(out["events"]) == 12    # capped at 12
    # highest damage first
    assert out["events"][0]["damage_pct"] == 15.0
    assert out["events"][0]["type"] == "cluster"   # storm-type index applied
    # an event with no type entry falls back to em-dash
    assert out["events"][1]["type"] == "—"


def test_flood_keeps_severe_with_zero_damage(app_mod, monkeypatch):
    monkeypatch.setattr(app_mod, "_hc_record", lambda a, r: {
        "storm_details": [{"storm_id": "S1", "exceeded_severe": True,
                           "damage_ratio": 0}]})
    monkeypatch.setattr(app_mod, "_storm_type_index", lambda: {})
    out = app_mod._flood_payload("property", "P1")
    assert out["count"] == 1 and out["events"][0]["severe"] is True


# --- wind -------------------------------------------------------------------
def test_wind_unsupported_for_non_hc_asset(app_mod):
    assert app_mod._wind_payload("gauge", "G1")["supported"] is False


def test_wind_zero_event_placeholder(app_mod):
    out = app_mod._wind_payload("property", "P1")
    assert out["supported"] is True and out["count"] == 0 and "note" in out


# --- fire -------------------------------------------------------------------
def test_fire_supported(app_mod, monkeypatch):
    monkeypatch.setattr(app_mod, "_model_assets", lambda k, p: ("MKM-FIRE-001", {
        "C1": {"n_sim": 100, "lambda_annual": 0.1, "n_fires": 5,
               "n_contained": 3, "n_partial": 1, "n_total": 1,
               "n_point_of_no_return": 0, "loss_frequency": 0.02,
               "containment_rate": 0.6}}))
    out = app_mod._fire_payload("commercial", "C1")
    assert out["supported"] is True and out["model"] == "MKM-FIRE-001"
    labels = [o["label"] for o in out["outcomes"]]
    assert labels == ["Contained", "Partial loss", "Total loss",
                      "Point of no return"]
    assert any(s["label"] == "Containment rate" for s in out["stats"])


def test_fire_unsupported_when_asset_absent(app_mod, monkeypatch):
    monkeypatch.setattr(app_mod, "_model_assets", lambda k, p: ("m", {}))
    assert app_mod._fire_payload("commercial", "ZZZ")["supported"] is False


# --- seismic ----------------------------------------------------------------
def test_seismic_supported_has_four_damage_states(app_mod, monkeypatch):
    monkeypatch.setattr(app_mod, "_model_assets", lambda k, p: ("SEIS", {
        "C1": {"n_sim": 100, "n_events": 7, "zone": "Z2", "site_class": "C",
               "construction_type": "RC", "rating": "B",
               "damage_state_counts": {"0": 50, "1": 30, "2": 15, "3": 5},
               "no_collapse_rate": 0.95, "loss_frequency": 0.01,
               "pml_475": 0.1, "pml_2475": 0.3}}))
    out = app_mod._seismic_payload("commercial", "C1")
    assert out["supported"] is True
    assert [d["label"] for d in out["damage_states"]] == \
        app_mod.SEISMIC_DS_LABELS
    assert out["damage_states"][3]["count"] == 5  # collapse state


def test_seismic_unsupported_when_asset_absent(app_mod, monkeypatch):
    monkeypatch.setattr(app_mod, "_model_assets", lambda k, p: ("m", {}))
    assert app_mod._seismic_payload("commercial", "ZZZ")["supported"] is False


# --- /perils endpoint -------------------------------------------------------
def test_perils_endpoint_returns_all_four(client, app_mod, monkeypatch):
    monkeypatch.setattr(app_mod, "_hc_record", lambda a, r: None)
    monkeypatch.setattr(app_mod, "_model_assets", lambda k, p: (None, {}))
    out = client.get("/api/property/items/P1/perils").get_json()
    assert set(out) == {"flood", "wind", "fire", "seismic"}


def test_perils_unknown_asset_404(client):
    assert client.get("/api/nope/items/x/perils").status_code == 404


# --- /waterfall endpoint ----------------------------------------------------
def test_waterfall_unknown_asset_404(client):
    assert client.get("/api/nope/items/x/waterfall").status_code == 404


def test_waterfall_unsupported_for_non_hc_asset(client):
    out = client.get("/api/gauge/items/G1/waterfall").get_json()
    assert out["supported"] is False


def test_waterfall_no_hc_record(client, app_mod, monkeypatch):
    monkeypatch.setattr(app_mod, "_hc_record", lambda a, r: None)
    out = client.get("/api/property/items/P1/waterfall").get_json()
    assert out["supported"] is True and out["spread_decomposition"] is None


def test_waterfall_with_decomposition(client, app_mod, monkeypatch):
    monkeypatch.setattr(app_mod, "_hc_record", lambda a, r: {
        "flood_zone": "3",
        "spread_decomposition": {"property_spread_bps": 84.5, "she_bps": 10}})
    out = client.get("/api/property/items/P1/waterfall").get_json()
    assert out["supported"] is True
    assert out["property_spread_bps"] == 84.5
    assert out["spread_decomposition"]["she_bps"] == 10
