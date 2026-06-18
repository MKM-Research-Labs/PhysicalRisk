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

"""Flask endpoint tests for the CDM Asset Review tool.

Drives the real Flask app via its test client with the sandbox redirected
under ``tmp_path`` (see conftest), covering the list/detail/schema/edit-spec
endpoints, the validated PUT-edit + audit-trail flow, and the static helpers
(index template, shared waterfall JS).
"""

import json

PROP = {"PropertyHeader": {
    "Header": {"PropertyID": "P1", "propertyType": "residential"},
    "Location": {"StreetName": "High St", "TownCity": "London"},
    "Valuation": {"PropertyValue": 250000}}}


def test_index_renders(client):
    r = client.get("/")
    assert r.status_code == 200


def test_api_assets_lists_tabs_in_order(client, app_mod):
    data = client.get("/api/assets").get_json()
    keys = [d["key"] for d in data]
    assert keys == list(app_mod.ASSETS)
    assert {"key": "property", "label": "Properties"} in data


def test_api_lineage_shape(client):
    data = client.get("/api/lineage").get_json()
    assert set(data) == {"tiers", "exact", "amberPrefixes"}
    assert isinstance(data["amberPrefixes"], list)


def test_api_schema_ok(client):
    data = client.get("/api/property/schema").get_json()
    assert "PropertyHeader" in data["sections"]
    assert "PropertyHeader" in data["schema"]


def test_api_schema_unknown_asset_404(client):
    r = client.get("/api/nope/schema")
    assert r.status_code == 404 and "Unknown asset" in r.get_json()["error"]


def test_api_edit_spec_ok(client):
    specs = client.get("/api/property/edit-spec").get_json()
    assert "PropertyHeader.Valuation.PropertyValue" in specs


def test_api_edit_spec_unknown_asset_404(client):
    assert client.get("/api/nope/edit-spec").status_code == 404


def test_api_items_lists_summaries(client, seed):
    seed("property", {"properties": [PROP]})
    items = client.get("/api/property/items").get_json()
    assert len(items) == 1 and items[0]["id"] == "P1"


def test_api_items_unknown_asset_404(client):
    assert client.get("/api/nope/items").status_code == 404


def test_api_item_found(client, seed):
    seed("property", {"properties": [PROP]})
    rec = client.get("/api/property/items/P1").get_json()
    assert rec["PropertyHeader"]["Header"]["PropertyID"] == "P1"


def test_api_item_not_found_404(client, seed):
    seed("property", {"properties": [PROP]})
    r = client.get("/api/property/items/ZZZ")
    assert r.status_code == 404 and "not found" in r.get_json()["error"]


def test_api_item_unknown_asset_404(client):
    assert client.get("/api/nope/items/x").status_code == 404


# --- the PUT edit + audit flow ---------------------------------------------
def test_update_commits_and_audits(client, seed, app_mod):
    seed("property", {"properties": [PROP]})
    r = client.put("/api/property/items/P1", json={
        "changes": {"PropertyHeader.Header.propertyType": "commercial"}})
    assert r.status_code == 200
    body = r.get_json()
    assert body["status"] == "success" and body["updated"] == 1
    assert body["record"]["PropertyHeader"]["Header"]["propertyType"] == "commercial"
    # persisted to the sandbox
    saved = json.loads((app_mod.SANDBOX_DIR / "property_sandbox.json").read_text())
    assert saved["properties"][0]["PropertyHeader"]["Header"]["propertyType"] == "commercial"
    # audit trail records the change (newest first via /api/audit)
    audit = client.get("/api/audit").get_json()
    assert audit[0]["field"] == "PropertyHeader.Header.propertyType"
    assert audit[0]["old"] == "residential" and audit[0]["new"] == "commercial"
    assert audit[0]["record_id"] == "P1" and audit[0]["asset"] == "property"


def test_update_noop_change_not_audited(client, seed):
    seed("property", {"properties": [PROP]})
    r = client.put("/api/property/items/P1", json={
        "changes": {"PropertyHeader.Header.propertyType": "residential"}})
    assert r.status_code == 200 and r.get_json()["updated"] == 0
    assert client.get("/api/audit").get_json() == []


def test_update_validation_error_writes_nothing(client, seed):
    seed("property", {"properties": [PROP]})
    r = client.put("/api/property/items/P1", json={
        "changes": {"PropertyHeader.Header.propertyType": "castle"}})
    assert r.status_code == 400
    body = r.get_json()
    assert body["status"] == "error"
    assert "PropertyHeader.Header.propertyType" in body["errors"]
    assert client.get("/api/audit").get_json() == []


def test_update_unknown_field_rejected(client, seed):
    seed("property", {"properties": [PROP]})
    r = client.put("/api/property/items/P1", json={
        "changes": {"PropertyHeader.Header.NotAField": 1}})
    assert r.status_code == 400
    assert r.get_json()["errors"]["PropertyHeader.Header.NotAField"] == \
        "not an editable schema field"


def test_update_changes_must_be_object(client, seed):
    seed("property", {"properties": [PROP]})
    r = client.put("/api/property/items/P1", json={"changes": [1, 2]})
    assert r.status_code == 400 and "object" in r.get_json()["error"]


def test_update_unknown_asset_404(client):
    assert client.put("/api/nope/items/x", json={"changes": {}}).status_code == 404


def test_update_record_not_found_404(client, seed):
    seed("property", {"properties": [PROP]})
    r = client.put("/api/property/items/ZZZ", json={
        "changes": {"PropertyHeader.Header.propertyType": "commercial"}})
    assert r.status_code == 404


# --- sandbox seeding from a (fake) input dir -------------------------------
def test_records_seed_from_input_dir_when_no_sandbox(client, app_mod, monkeypatch, tmp_path):
    """First access copies the simulated portfolio into the sandbox."""
    src = tmp_path / "input"
    src.mkdir()
    (src / "property.json").write_text(json.dumps({"properties": [PROP]}),
                                       encoding="utf-8")
    monkeypatch.setattr(app_mod, "INPUT_DIR", src)
    # sandbox dir (app_mod.SANDBOX_DIR) is empty -> _ensure_sandbox seeds it
    items = client.get("/api/property/items").get_json()
    assert items[0]["id"] == "P1"
    assert (app_mod.SANDBOX_DIR / "property_sandbox.json").exists()


def test_seed_source_missing_raises(app_mod, monkeypatch, tmp_path):
    monkeypatch.setattr(app_mod, "INPUT_DIR", tmp_path / "missing")
    import pytest
    with pytest.raises(FileNotFoundError):
        app_mod._seed_source("gauge")


# --- static helpers ---------------------------------------------------------
def test_shared_waterfall_js_served(client):
    r = client.get("/shared/phc_basis_waterfall.js")
    assert r.status_code == 200
    assert r.headers["Content-Type"] == "application/javascript"
    assert len(r.get_data()) > 0
