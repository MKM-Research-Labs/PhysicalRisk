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
Tests for routes.governance.audit — audit trail, validation questions,
risk rating, and PDF doc serving.

Covers: log_model_usage (model not found, valid), get_audit_trail (empty,
with data, filters), update_validation_question (not found, invalid status,
valid), get_risk_rating, override_risk_rating (invalid, no reason, set, clear),
and all PDF endpoints (all return 404 without generated files).
"""

import json
import pytest


# All tests reuse the gov_client fixture from conftest.py.


# ===========================================================================
# POST /governance/models/<model_id>/audit
# ===========================================================================

class TestLogModelUsage:

    def test_model_not_found_returns_404(self, gov_client):
        r = gov_client.post("/api/v1/governance/models/DOES-NOT-EXIST/audit",
                            json={"event_type": "usage"})
        assert r.status_code == 404
        assert r.get_json()["status"] == "error"

    def test_valid_model_returns_200(self, gov_client):
        r = gov_client.post("/api/v1/governance/models/MKM-TEST-001/audit",
                            json={"event_type": "usage", "user": "tester"})
        assert r.status_code == 200
        assert r.get_json()["status"] == "success"

    def test_entry_has_expected_fields(self, gov_client):
        r = gov_client.post("/api/v1/governance/models/MKM-TEST-001/audit",
                            json={"event_type": "calibration", "user": "alice",
                                  "action": "ran calibration"})
        entry = r.get_json()["entry"]
        assert entry["model_id"] == "MKM-TEST-001"
        assert entry["event_type"] == "calibration"
        assert entry["user"] == "alice"
        assert "timestamp" in entry

    def test_defaults_applied_when_no_json(self, gov_client):
        r = gov_client.post("/api/v1/governance/models/MKM-TEST-001/audit")
        assert r.status_code == 200
        entry = r.get_json()["entry"]
        assert entry["event_type"] == "usage"
        assert entry["user"] == "system"

    def test_parameters_stored(self, gov_client):
        r = gov_client.post("/api/v1/governance/models/MKM-TEST-001/audit",
                            json={"parameters": {"key": "value"}})
        assert r.get_json()["entry"]["parameters"] == {"key": "value"}


# ===========================================================================
# GET /governance/audit-trail
# ===========================================================================

class TestGetAuditTrail:

    def test_empty_trail_returns_200(self, gov_client):
        r = gov_client.get("/api/v1/governance/audit-trail")
        assert r.status_code == 200
        data = r.get_json()
        assert data["status"] == "success"
        assert data["entries"] == []

    def test_after_log_entry_appears(self, gov_client):
        gov_client.post("/api/v1/governance/models/MKM-TEST-001/audit",
                        json={"event_type": "usage"})
        r = gov_client.get("/api/v1/governance/audit-trail")
        data = r.get_json()
        assert data["total_entries"] == 1
        assert len(data["entries"]) == 1

    def test_filter_by_model_id(self, gov_client):
        gov_client.post("/api/v1/governance/models/MKM-TEST-001/audit",
                        json={"event_type": "usage"})
        r = gov_client.get("/api/v1/governance/audit-trail?model_id=MKM-TEST-001")
        assert r.get_json()["total_entries"] == 1

    def test_filter_by_model_id_no_match(self, gov_client):
        gov_client.post("/api/v1/governance/models/MKM-TEST-001/audit",
                        json={"event_type": "usage"})
        r = gov_client.get("/api/v1/governance/audit-trail?model_id=OTHER-001")
        assert r.get_json()["total_entries"] == 0

    def test_filter_by_event_type(self, gov_client):
        gov_client.post("/api/v1/governance/models/MKM-TEST-001/audit",
                        json={"event_type": "calibration"})
        gov_client.post("/api/v1/governance/models/MKM-TEST-001/audit",
                        json={"event_type": "usage"})
        r = gov_client.get("/api/v1/governance/audit-trail?event_type=calibration")
        entries = r.get_json()["entries"]
        assert all(e["event_type"] == "calibration" for e in entries)

    def test_limit_parameter(self, gov_client):
        for _ in range(5):
            gov_client.post("/api/v1/governance/models/MKM-TEST-001/audit",
                            json={"event_type": "usage"})
        r = gov_client.get("/api/v1/governance/audit-trail?limit=2")
        assert r.get_json()["returned"] == 2

    def test_has_returned_field(self, gov_client):
        r = gov_client.get("/api/v1/governance/audit-trail")
        assert "returned" in r.get_json()


# ===========================================================================
# POST /governance/models/<model_id>/validation-questions/<id>/update
# ===========================================================================

class TestUpdateValidationQuestion:

    _URL = "/api/v1/governance/models/MKM-TEST-001/validation-questions/{qid}/update"

    def test_model_not_found_returns_404(self, gov_client):
        r = gov_client.post(
            "/api/v1/governance/models/GHOST/validation-questions/1/update",
            json={"status": "Compliant", "evidence": "ok"}
        )
        assert r.status_code == 404

    def test_question_not_found_returns_404(self, gov_client):
        r = gov_client.post(
            self._URL.format(qid=999),
            json={"status": "Compliant", "evidence": "ok"}
        )
        assert r.status_code == 404

    def test_invalid_status_returns_400(self, gov_client):
        r = gov_client.post(
            self._URL.format(qid=1),
            json={"status": "BOGUS_STATUS"}
        )
        assert r.status_code == 400
        assert r.get_json()["status"] == "error"

    def test_valid_update_returns_success(self, gov_client):
        r = gov_client.post(
            self._URL.format(qid=1),
            json={"status": "Addressed", "evidence": "Test evidence",
                  "reviewed_by": "QA Team"}
        )
        assert r.status_code == 200
        assert r.get_json()["status"] == "success"

    def test_valid_update_has_model_and_audit_entry(self, gov_client):
        r = gov_client.post(
            self._URL.format(qid=1),
            json={"status": "Addressed", "evidence": "ok"}
        )
        data = r.get_json()
        assert "model" in data
        assert "audit_entry" in data

    def test_risk_rating_recalculated(self, gov_client):
        r = gov_client.post(
            self._URL.format(qid=1),
            json={"status": "Addressed", "evidence": "ok"}
        )
        model = r.get_json()["model"]
        rr = model["overall_risk_rating"]
        assert rr["last_calculated"] is not None

    def test_all_valid_statuses(self, gov_client):
        for status in ("Addressed", "Partially Addressed", "Not Addressed", "Not Applicable"):
            r = gov_client.post(
                self._URL.format(qid=1),
                json={"status": status, "evidence": "ok"}
            )
            assert r.status_code == 200


# ===========================================================================
# GET /governance/models/<model_id>/risk-rating
# ===========================================================================

class TestGetRiskRating:

    def test_model_not_found_returns_404(self, gov_client):
        r = gov_client.get("/api/v1/governance/models/GHOST/risk-rating")
        assert r.status_code == 404

    def test_valid_model_returns_success(self, gov_client):
        r = gov_client.get("/api/v1/governance/models/MKM-TEST-001/risk-rating")
        assert r.status_code == 200
        data = r.get_json()
        assert data["status"] == "success"
        assert data["model_id"] == "MKM-TEST-001"

    def test_response_has_risk_rating(self, gov_client):
        r = gov_client.get("/api/v1/governance/models/MKM-TEST-001/risk-rating")
        data = r.get_json()
        assert "risk_rating" in data
        rr = data["risk_rating"]
        assert "calculated_rating" in rr
        assert "effective_rating" in rr

    def test_risk_rating_has_component_scores(self, gov_client):
        r = gov_client.get("/api/v1/governance/models/MKM-TEST-001/risk-rating")
        rr = r.get_json()["risk_rating"]
        assert "component_scores" in rr


# ===========================================================================
# POST /governance/models/<model_id>/risk-rating/override
# ===========================================================================

class TestOverrideRiskRating:

    _URL = "/api/v1/governance/models/MKM-TEST-001/risk-rating/override"

    def test_model_not_found_returns_404(self, gov_client):
        r = gov_client.post(
            "/api/v1/governance/models/GHOST/risk-rating/override",
            json={"rating": "Low", "reason": "MRC decision"}
        )
        assert r.status_code == 404

    def test_invalid_rating_returns_400(self, gov_client):
        r = gov_client.post(self._URL,
                            json={"rating": "BOGUS", "reason": "test"})
        assert r.status_code == 400
        assert r.get_json()["status"] == "error"

    def test_no_reason_returns_400(self, gov_client):
        r = gov_client.post(self._URL,
                            json={"rating": "Low", "reason": ""})
        assert r.status_code == 400

    def test_no_reason_field_returns_400(self, gov_client):
        r = gov_client.post(self._URL, json={"rating": "Low"})
        # reason defaults to "" → stripped = "" → 400
        assert r.status_code == 400

    def test_valid_override_returns_success(self, gov_client):
        r = gov_client.post(self._URL,
                            json={"rating": "Acceptable", "reason": "MRC annual review",
                                  "user": "mrc_chair"})
        assert r.status_code == 200
        assert r.get_json()["status"] == "success"

    def test_override_stored_in_model(self, gov_client):
        gov_client.post(self._URL,
                        json={"rating": "Conditional", "reason": "Override applied"})
        r = gov_client.get("/api/v1/governance/models/MKM-TEST-001/risk-rating")
        rr = r.get_json()["risk_rating"]
        assert rr["mrc_override"] == "Conditional"
        assert rr["effective_rating"] == "Conditional"

    def test_clear_override_with_null(self, gov_client):
        # First set an override
        gov_client.post(self._URL,
                        json={"rating": "Acceptable", "reason": "Set override"})
        # Clear it
        r = gov_client.post(self._URL,
                            json={"rating": None, "reason": "Clearing override"})
        assert r.status_code == 200
        assert r.get_json()["status"] == "success"

    def test_response_has_audit_entry(self, gov_client):
        r = gov_client.post(self._URL,
                            json={"rating": "Unacceptable", "reason": "Stress scenario"})
        data = r.get_json()
        assert "audit_entry" in data
        assert data["audit_entry"]["event_type"] == "risk_rating_override"


# ===========================================================================
# PDF endpoints — model not in _MODEL_DOC_DIRS returns 404
# ===========================================================================

class TestPdfEndpoints:

    def test_documentation_pdf_unknown_model_404(self, gov_client):
        r = gov_client.get("/api/v1/governance/models/UNKNOWN/documentation/pdf")
        assert r.status_code == 404

    def test_documentation_pdf_known_model_no_file_404(self, gov_client):
        # MKM-TEST-001 is not in _MODEL_DOC_DIRS → 404 (no doc dir registered)
        r = gov_client.get("/api/v1/governance/models/MKM-TEST-001/documentation/pdf")
        assert r.status_code == 404

    def test_test_results_pdf_unknown_model_404(self, gov_client):
        r = gov_client.get("/api/v1/governance/models/UNKNOWN/test-results/pdf")
        assert r.status_code == 404

    def test_test_results_pdf_known_model_no_file_404(self, gov_client):
        # MKM-TEST-001 not in _MODEL_DOC_DIRS
        r = gov_client.get("/api/v1/governance/models/MKM-TEST-001/test-results/pdf")
        assert r.status_code == 404

    def test_parameter_inventory_pdf_responds(self, gov_client):
        r = gov_client.get("/api/v1/governance/parameter-inventory/pdf")
        # Returns 200 if PDF exists, 404 if not yet generated
        assert r.status_code in (200, 404)

    def test_mrc_tor_pdf_responds(self, gov_client):
        r = gov_client.get("/api/v1/governance/mrc/terms-of-reference/pdf")
        assert r.status_code in (200, 404)
