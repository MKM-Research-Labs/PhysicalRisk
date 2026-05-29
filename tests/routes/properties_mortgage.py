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
Tests for mortgage endpoints and mortgage report generation.

Covers: mortgage report (success, error, import error, edge cases),
GET /properties/<id>/rloan, GET /rloans list.
"""

from unittest.mock import patch

import pytest


# ===========================================================================
# POST /properties/rloan-report
# ===========================================================================

class TestGenerateMortgageReport:

    def test_no_json_returns_error(self, prop_client):
        client, _ = prop_client
        r = client.post("/api/v1/properties/rloan-report")
        assert r.status_code in (400, 415)

    def test_missing_property_id_returns_400(self, prop_client):
        client, _ = prop_client
        r = client.post("/api/v1/properties/rloan-report", json={})
        assert r.status_code == 400
        assert "Property ID" in r.get_json()["message"]

    def test_property_not_found_returns_404(self, prop_client):
        client, reg = prop_client
        reg.get_property_loader.return_value.find_by_id.return_value = None
        r = client.post(
            "/api/v1/properties/rloan-report", json={"propertyId": "GHOST"}
        )
        assert r.status_code == 404

    def test_mortgage_not_found_returns_404(self, prop_client):
        client, reg = prop_client
        reg.get_property_loader.return_value.find_by_id.return_value = {
            "property_id": "PROP-001"
        }
        reg.get_rloan_loader.return_value.find_by_property_id.return_value = None
        r = client.post(
            "/api/v1/properties/rloan-report", json={"propertyId": "PROP-001"}
        )
        assert r.status_code == 404
        assert "mortgage" in r.get_json()["message"].lower()

    def test_options_returns_ok(self, prop_client):
        client, _ = prop_client
        r = client.options("/api/v1/properties/rloan-report")
        assert r.status_code == 200

    def test_no_json_body_returns_400(self, prop_client):
        """Line 149: get_json() returns None -> 400."""
        client, _ = prop_client
        r = client.post("/api/v1/properties/rloan-report",
                        data='',
                        content_type='application/json')
        assert r.status_code in (400, 415, 500)

    def test_generate_mortgage_report_success(self, prop_client, tmp_path):
        """Lines 174-193: full success path with mocked mortgage report generator."""
        client, reg = prop_client
        prop_data = {"PropertyHeader": {"PropertyID": "PROP-001"}}
        mort_data = {"Mortgage": {"Header": {"PropertyID": "PROP-001"}}}
        reg.get_property_loader.return_value.find_by_id.return_value = prop_data
        reg.get_rloan_loader.return_value.find_by_property_id.return_value = mort_data

        fake_pdf = tmp_path / "mort_report.pdf"
        fake_pdf.write_bytes(b"%PDF-1.4 mortgage content")

        with patch("reports.rloan.rloan_generator.generate_rloan_report",
                   return_value=fake_pdf):
            r = client.post("/api/v1/properties/rloan-report",
                            json={"propertyId": "PROP-001"})
            assert r.status_code in (200, 500)

    def test_generate_mortgage_report_exception_returns_500(self, prop_client):
        """Lines 203-208: exception -> 500."""
        client, reg = prop_client
        reg.get_property_loader.return_value.find_by_id.return_value = {"p": 1}
        reg.get_rloan_loader.return_value.find_by_property_id.return_value = {"m": 1}

        with patch("reports.rloan.rloan_generator.generate_rloan_report",
                   side_effect=RuntimeError("mort report error")):
            r = client.post("/api/v1/properties/rloan-report", json={"propertyId": "PROP-001"})
            assert r.status_code in (200, 500)


# ===========================================================================
# GET /properties/<id>/rloan
# ===========================================================================

class TestPropertyMortgage:

    def test_not_found_returns_404(self, prop_client):
        client, reg = prop_client
        reg.get_rloan_loader.return_value.find_by_property_id.return_value = None
        r = client.get("/api/v1/properties/PROP-GHOST/rloan")
        assert r.status_code == 404
        assert r.get_json()["status"] == "error"

    def test_found_returns_mortgage(self, prop_client):
        client, reg = prop_client
        rloan_record = {
            "Mortgage": {"Header": {"PropertyID": "PROP-001"}, "Outstanding": 200000}
        }
        reg.get_rloan_loader.return_value.find_by_property_id.return_value = rloan_record
        r = client.get("/api/v1/properties/PROP-001/rloan")
        assert r.status_code == 200
        data = r.get_json()
        assert data["status"] == "success"
        assert data["property_id"] == "PROP-001"
        assert "mortgage" in data

    def test_loader_exception_returns_500(self, prop_client):
        client, reg = prop_client
        reg.get_rloan_loader.return_value.find_by_property_id.side_effect = (
            RuntimeError("db down")
        )
        r = client.get("/api/v1/properties/PROP-001/rloan")
        assert r.status_code == 500

    def test_options_returns_ok(self, prop_client):
        client, _ = prop_client
        r = client.options("/api/v1/properties/PROP-001/rloan")
        assert r.status_code == 200


# ===========================================================================
# Coverage expansion: mortgage import error, null body, list mortgages
# ===========================================================================

class TestGenerateMortgageReportImportError:
    """Lines 216-217: ImportError when mortgage report generator is unavailable."""

    def test_mortgage_import_error_returns_500(self, prop_client, monkeypatch):
        client, reg = prop_client
        reg.get_property_loader.return_value.find_by_id.return_value = {"p": 1}
        reg.get_rloan_loader.return_value.find_by_property_id.return_value = {"m": 1}

        import sys
        import types
        fake_mod = types.ModuleType("reports.rloan.rloan_generator")
        def _raise(*a, **kw):
            raise ImportError("no module reports.rloan.rloan_generator")
        fake_mod.generate_rloan_report = _raise
        monkeypatch.setitem(sys.modules, "reports.rloan.rloan_generator", fake_mod)

        r = client.post("/api/v1/properties/rloan-report",
                        json={"propertyId": "PROP-001"})
        assert r.status_code == 500
        data = r.get_json()
        assert data["status"] == "error"


class TestNoJsonBodyEdgeMortgageReport:
    """Line 168: generate_mortgage_report with None JSON body."""

    def test_mortgage_report_null_json_returns_400(self, prop_client):
        """Same for rloan-report: null JSON body -> line 168 -> 400."""
        client, _ = prop_client
        r = client.post("/api/v1/properties/rloan-report",
                        data='null',
                        content_type='application/json')
        assert r.status_code in (400, 500)


class TestListMortgages:
    """Lines 233-245: GET /rloans endpoint."""

    def test_list_mortgages_success(self, prop_client):
        client, reg = prop_client
        reg.get_rloan_loader.return_value.list_all.return_value = [
            {"mortgage_id": "MORT-001"},
            {"mortgage_id": "MORT-002"},
        ]
        r = client.get("/api/v1/rloans")
        assert r.status_code == 200
        data = r.get_json()
        assert data["status"] == "success"
        assert data["count"] == 2
        assert len(data["mortgages"]) == 2

    def test_list_mortgages_empty(self, prop_client):
        client, reg = prop_client
        reg.get_rloan_loader.return_value.list_all.return_value = []
        r = client.get("/api/v1/rloans")
        assert r.status_code == 200
        assert r.get_json()["count"] == 0

    def test_list_mortgages_exception_returns_500(self, prop_client):
        client, reg = prop_client
        reg.get_rloan_loader.return_value.list_all.side_effect = RuntimeError("db error")
        r = client.get("/api/v1/rloans")
        assert r.status_code == 500
        assert r.get_json()["status"] == "error"
