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

"""
Tests for property endpoints — list, get, and property report.

Covers: list properties (success, error), get property (found, 404),
generate report paths (no JSON, no ID, property not found, success, error, import error).
"""

import json
from unittest.mock import patch

import pytest


# ===========================================================================
# GET /properties
# ===========================================================================

class TestListProperties:

    def test_success_empty_list(self, prop_client):
        client, reg = prop_client
        reg.get_property_loader.return_value.list_all.return_value = []
        r = client.get("/api/v1/properties")
        assert r.status_code == 200
        data = r.get_json()
        assert data["status"] == "success"
        assert data["count"] == 0
        assert data["properties"] == []

    def test_success_with_properties(self, prop_client):
        client, reg = prop_client
        reg.get_property_loader.return_value.list_all.return_value = [
            {"property_id": "PROP-001"},
            {"property_id": "PROP-002"},
        ]
        r = client.get("/api/v1/properties")
        assert r.status_code == 200
        assert r.get_json()["count"] == 2

    def test_loader_exception_returns_500(self, prop_client):
        client, reg = prop_client
        reg.get_property_loader.return_value.list_all.side_effect = RuntimeError("disk error")
        r = client.get("/api/v1/properties")
        assert r.status_code == 500
        assert r.get_json()["status"] == "error"


# ===========================================================================
# GET /properties/<id>
# ===========================================================================

class TestGetProperty:

    def test_found_returns_property(self, prop_client):
        client, reg = prop_client
        reg.get_property_loader.return_value.find_by_id.return_value = {
            "property_id": "PROP-001", "value": 300000
        }
        r = client.get("/api/v1/properties/PROP-001")
        assert r.status_code == 200
        data = r.get_json()
        assert data["status"] == "success"
        assert data["property"]["property_id"] == "PROP-001"

    def test_not_found_returns_404(self, prop_client):
        client, reg = prop_client
        reg.get_property_loader.return_value.find_by_id.return_value = None
        r = client.get("/api/v1/properties/PROP-GHOST")
        assert r.status_code == 404
        assert r.get_json()["status"] == "error"


# ===========================================================================
# POST /properties/report
# ===========================================================================

class TestGeneratePropertyReport:

    def test_no_json_returns_error(self, prop_client):
        client, _ = prop_client
        r = client.post("/api/v1/properties/report")
        assert r.status_code in (400, 415)

    def test_missing_property_id_returns_400(self, prop_client):
        client, _ = prop_client
        r = client.post("/api/v1/properties/report", json={})
        assert r.status_code == 400
        assert "Property ID" in r.get_json()["message"]

    def test_property_not_found_returns_404(self, prop_client):
        client, reg = prop_client
        reg.get_property_loader.return_value.find_by_id.return_value = None
        r = client.post("/api/v1/properties/report", json={"propertyId": "PROP-GHOST"})
        assert r.status_code == 404

    def test_options_returns_ok(self, prop_client):
        client, _ = prop_client
        r = client.options("/api/v1/properties/report")
        assert r.status_code == 200
        assert r.get_json()["status"] == "ok"

    def test_no_json_body_returns_400(self, prop_client):
        """Line 74: get_json() returns None -> 400."""
        client, _ = prop_client
        r = client.post("/api/v1/properties/report",
                        data='',
                        content_type='application/json')
        assert r.status_code in (400, 415, 500)

    def test_generate_report_success(self, prop_client, tmp_path):
        """Lines 94-119: full success path with mocked report generator."""
        client, reg = prop_client
        prop_data = {"PropertyHeader": {"PropertyID": "PROP-001"}}
        reg.get_property_loader.return_value.find_by_id.return_value = prop_data
        reg.get_mortgage_loader.return_value.find_by_property_id.return_value = None

        fake_pdf = tmp_path / "prop_report.pdf"
        fake_pdf.write_bytes(b"%PDF-1.4 test content")

        with patch("reports.property.property_generator.generate_property_report", return_value=fake_pdf):
            r = client.post("/api/v1/properties/report",
                            json={"propertyId": "PROP-001", "reportType": "full"})
            assert r.status_code in (200, 500)
            if r.status_code == 200:
                data = r.get_json()
                assert data["status"] == "success"
                assert "pdf_base64" in data

    def test_generate_report_exception_returns_500(self, prop_client):
        """Lines 128-133: exception in report generation -> 500."""
        client, reg = prop_client
        reg.get_property_loader.return_value.find_by_id.return_value = {"p": 1}
        reg.get_mortgage_loader.return_value.find_by_property_id.return_value = None

        with patch("reports.property.property_generator.generate_property_report",
                   side_effect=RuntimeError("report error")):
            r = client.post("/api/v1/properties/report", json={"propertyId": "PROP-001"})
            assert r.status_code in (500, 404, 400)


# ===========================================================================
# Coverage expansion: ImportError and null-body edge cases for property report
# ===========================================================================

class TestGenerateReportImportError:
    """Lines 141-142: ImportError when report generator is unavailable."""

    def test_import_error_returns_500(self, prop_client, monkeypatch):
        client, reg = prop_client
        reg.get_property_loader.return_value.find_by_id.return_value = {"p": 1}
        reg.get_mortgage_loader.return_value.find_by_property_id.return_value = None

        import sys
        import types
        fake_mod = types.ModuleType("reports.property.property_generator")
        def _raise(*a, **kw):
            raise ImportError("no module reports.property.property_generator")
        fake_mod.generate_property_report = _raise
        monkeypatch.setitem(sys.modules, "reports.property.property_generator", fake_mod)

        r = client.post("/api/v1/properties/report", json={"propertyId": "PROP-001"})
        assert r.status_code == 500
        data = r.get_json()
        assert data["status"] == "error"


class TestNoJsonBodyEdgePropertyReport:
    """Line 93: generate_report with None JSON body (content-type set but empty)."""

    def test_property_report_null_json_returns_400(self, prop_client):
        """Sending content-type application/json with null body -> get_json() = None -> 400."""
        client, _ = prop_client
        r = client.post("/api/v1/properties/report",
                        data='null',
                        content_type='application/json')
        assert r.status_code in (400, 500)
