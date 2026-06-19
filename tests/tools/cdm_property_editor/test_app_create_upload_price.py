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

"""Endpoint tests for the CDM tool's add / bulk-upload / price-new flows.

Drives ``POST /items`` (create), ``POST /upload`` (xlsx bulk add) and
``POST /items/<id>/price`` (scoped-batch pricing, with ``price_new.price_asset``
stubbed) through the Flask test client, covering the validation, minting,
auditing, rejection and not-supported branches plus the sandbox priced-store
helpers.
"""

import io
import json

from openpyxl import Workbook


def _upload_xlsx(sheet_title, headers, rows):
    """An in-memory .xlsx with one sheet of CDM-path headers + data rows."""
    wb = Workbook()
    wb.remove(wb.active)
    ws = wb.create_sheet(sheet_title)
    ws.append(headers)
    for r in rows:
        ws.append(r)
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf


# --- create -----------------------------------------------------------------
def test_create_unknown_asset_404(client):
    assert client.post("/api/nope/items", json={"changes": {}}).status_code == 404


def test_create_unsupported_asset_400(client):
    # gauge / counterparty are not in NEW_ASSET
    r = client.post("/api/gauge/items", json={"changes": {}})
    assert r.status_code == 400 and "not supported" in r.get_json()["error"]


def test_create_validation_error_400(client, seed):
    seed("property", {"properties": []})
    r = client.post("/api/property/items", json={
        "changes": {"PropertyHeader.Header.propertyType": "castle"}})
    assert r.status_code == 400
    assert "PropertyHeader.Header.propertyType" in r.get_json()["errors"]


def test_create_unknown_field_400(client, seed):
    seed("property", {"properties": []})
    r = client.post("/api/property/items", json={
        "changes": {"PropertyHeader.Header.NotAField": 1}})
    assert r.get_json()["errors"]["PropertyHeader.Header.NotAField"] == \
        "not an editable schema field"


def test_create_mints_id_and_audits(client, seed, app_mod):
    seed("property", {"properties": []})
    r = client.post("/api/property/items", json={"changes": {
        "PropertyHeader.Header.propertyType": "residential",
        "PropertyHeader.Valuation.PropertyValue": 300000,
        "PropertyHeader.Location.StreetName": "",  # blank -> skipped
    }})
    assert r.status_code == 200
    body = r.get_json()
    assert body["status"] == "success" and body["id"].startswith("PROP-")
    rec = body["record"]
    assert rec["PropertyHeader"]["Header"]["CatchmentID"] == app_mod.CATCHMENT
    assert rec["PropertyHeader"]["Valuation"]["PropertyValue"] == 300000
    assert "StreetName" not in rec["PropertyHeader"].get("Location", {})
    # persisted + audited as a record creation
    saved = json.loads((app_mod.SANDBOX_DIR / "property_sandbox.json").read_text())
    assert saved["properties"][-1]["PropertyHeader"]["Header"]["PropertyID"] == body["id"]
    audit = client.get("/api/audit").get_json()
    assert audit[0]["field"] == "(record)" and audit[0]["new"] == body["id"]


def test_create_appends_to_list_shaped_doc(client, seed, app_mod):
    seed("property", [])  # bare-list sandbox document
    r = client.post("/api/property/items", json={"changes": {
        "PropertyHeader.Header.propertyType": "residential"}})
    assert r.status_code == 200
    saved = json.loads((app_mod.SANDBOX_DIR / "property_sandbox.json").read_text())
    assert isinstance(saved, list) and len(saved) == 1


# --- upload -----------------------------------------------------------------
def test_upload_unsupported_asset_400(client):
    r = client.post("/api/gauge/upload", data={})
    assert r.status_code == 400 and "not supported" in r.get_json()["error"]


def test_upload_no_file_400(client):
    r = client.post("/api/property/upload", data={})
    assert r.status_code == 400 and "No file" in r.get_json()["error"]


def test_upload_bad_workbook_400(client):
    bad = io.BytesIO(b"not a real xlsx")
    r = client.post("/api/property/upload",
                    data={"file": (bad, "x.xlsx")},
                    content_type="multipart/form-data")
    assert r.status_code == 400 and "Could not read workbook" in r.get_json()["error"]


def test_upload_header_only_note(client, seed):
    seed("property", {"properties": []})
    buf = _upload_xlsx("Portfolio (Template)",
                       ["PropertyHeader.Header.PropertyID"], [])
    r = client.post("/api/property/upload",
                    data={"file": (buf, "wb.xlsx")},
                    content_type="multipart/form-data")
    body = r.get_json()
    assert body["created"] == 0 and "No data rows" in body["note"]


def test_upload_creates_and_rejects_and_skips_blanks(client, seed, app_mod):
    seed("property", {"properties": []})
    headers = ["PropertyHeader.Header.PropertyID",
               "PropertyHeader.Header.propertyType",
               "PropertyHeader.Valuation.PropertyValue"]
    rows = [
        ["MYPROP-1", "residential", 250000],   # ok, id kept as-is
        ["MYPROP-2", "castle", 100],           # rejected (bad menu value)
        ["", "", ""],                          # blank -> skipped
    ]
    buf = _upload_xlsx("Portfolio (Template)", headers, rows)
    r = client.post("/api/property/upload",
                    data={"file": (buf, "wb.xlsx")},
                    content_type="multipart/form-data")
    body = r.get_json()
    assert body["created"] == 1 and body["ids"] == ["MYPROP-1"]
    assert body["sheet"] == "Portfolio (Template)"
    assert len(body["rejected"]) == 1 and body["rejected"][0]["row"] == 3
    # the created record is persisted with the catchment tag
    saved = json.loads((app_mod.SANDBOX_DIR / "property_sandbox.json").read_text())
    assert saved["properties"][0]["PropertyHeader"]["Header"]["CatchmentID"] == \
        app_mod.CATCHMENT


def test_upload_unknown_field_rejects_row(client, seed):
    seed("property", {"properties": []})
    buf = _upload_xlsx("Portfolio (Template)",
                       ["PropertyHeader.Header.NopeField"], [["v"]])
    r = client.post("/api/property/upload",
                    data={"file": (buf, "wb.xlsx")},
                    content_type="multipart/form-data")
    body = r.get_json()
    assert body["created"] == 0 and body["rejected"][0]["errors"][
        "PropertyHeader.Header.NopeField"] == "unknown field"


def test_upload_skips_blank_cells_in_populated_row(client, seed, app_mod):
    seed("property", {"properties": []})
    headers = ["PropertyHeader.Header.PropertyID",
               "PropertyHeader.Header.propertyType",
               "PropertyHeader.Valuation.PropertyValue"]
    # middle cell blank (None) but the row is not empty -> cell skipped, row kept
    buf = _upload_xlsx("Portfolio (Template)", headers,
                       [["MYPROP-3", None, 300000]])
    r = client.post("/api/property/upload",
                    data={"file": (buf, "wb.xlsx")},
                    content_type="multipart/form-data")
    body = r.get_json()
    assert body["created"] == 1 and body["ids"] == ["MYPROP-3"]
    saved = json.loads((app_mod.SANDBOX_DIR / "property_sandbox.json").read_text())
    hdr = saved["properties"][0]["PropertyHeader"]["Header"]
    assert "propertyType" not in hdr  # the blank cell was not written


def test_upload_falls_back_to_first_sheet(client, seed):
    seed("property", {"properties": []})
    # sheet not named "<asset> (Template)" -> first sheet is used
    buf = _upload_xlsx("Some Other Sheet",
                       ["PropertyHeader.Header.propertyType"],
                       [["residential"]])
    r = client.post("/api/property/upload",
                    data={"file": (buf, "wb.xlsx")},
                    content_type="multipart/form-data")
    body = r.get_json()
    assert body["created"] == 1 and body["sheet"] == "Some Other Sheet"


# --- price ------------------------------------------------------------------
def test_price_unsupported_asset_400(client):
    r = client.post("/api/mortgage/items/RLOAN-1/price")
    assert r.status_code == 400 and "not supported" in r.get_json()["error"]


def test_price_record_not_found_404(client, seed):
    seed("property", {"properties": []})
    r = client.post("/api/property/items/ZZZ/price")
    assert r.status_code == 404


def test_price_returns_error_payload_on_failure(client, seed, app_mod, monkeypatch):
    seed("property", {"properties": [{"PropertyHeader": {
        "Header": {"PropertyID": "PROP-NEW"}}}]})
    monkeypatch.setattr(app_mod.price_new, "price_asset",
                        lambda *a, **k: {"ok": False, "curve": None,
                                         "error": "no flood events"})
    r = client.post("/api/property/items/PROP-NEW/price")
    assert r.status_code == 200
    assert r.get_json() == {"ok": False, "error": "no flood events"}


def test_price_happy_path_saves_and_returns_decomposition(client, seed, app_mod, monkeypatch):
    seed("property", {"properties": [{"PropertyHeader": {
        "Header": {"PropertyID": "PROP-NEW"}}}]})
    curve = {"flood_count": 4, "flood_zone": "3",
             "spread_decomposition": {"property_spread_bps": 77.0}}
    monkeypatch.setattr(app_mod.price_new, "price_asset",
                        lambda *a, **k: {"ok": True, "curve": curve, "error": None})
    r = client.post("/api/property/items/PROP-NEW/price")
    body = r.get_json()
    assert body["ok"] is True and body["property_spread_bps"] == 77.0
    assert body["flood_count"] == 4 and body["flood_zone"] == "3"
    # stored in the sandbox priced store and now served as the hc record
    assert app_mod._hc_record("property", "PROP-NEW") == curve


# --- priced-store helpers ---------------------------------------------------
def test_load_priced_missing_and_corrupt(app_mod, sandbox):
    assert app_mod._load_priced("property") == {}
    app_mod._priced_file("property").write_text("{ not json")
    assert app_mod._load_priced("property") == {}


def test_save_then_load_priced_roundtrip(app_mod, sandbox):
    app_mod._save_priced("property", "P1", {"flood_zone": "2"})
    app_mod._save_priced("property", "P2", {"flood_zone": "3"})
    store = app_mod._load_priced("property")
    assert store["P1"]["flood_zone"] == "2" and store["P2"]["flood_zone"] == "3"
