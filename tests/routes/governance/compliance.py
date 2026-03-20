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
Tests for routes.governance.compliance — BCBS 239 self-assessment and
RACI matrix routes.

Covers: get_bcbs239 (no data / with data), update_bcbs239_principle
(not found / valid / score-to-status), get_bcbs239_pdf (→ 404),
update_raci_role (not found / valid / backup), update_raci_activity
(not found / valid / invalid role id), update_raci_escalation
(not found / valid).
"""

import copy
import json
from pathlib import Path

import pytest


# ===========================================================================
# BCBS 239 Fixtures
# ===========================================================================

_BASE_BCBS239 = {
    "assessment_date": "2026-01-01",
    "principles": [
        {
            "id": 1,
            "name": "Governance",
            "description": "Board oversight of data",
            "score": 3,
            "status": "Largely Compliant",
            "evidence": "Board minutes confirm oversight",
            "gaps": "",
            "remediation": "",
            "target_date": "",
        },
        {
            "id": 2,
            "name": "Data architecture",
            "description": "Data architecture and IT infrastructure",
            "score": 2,
            "status": "Materially Non-compliant",
            "evidence": "",
            "gaps": "Legacy systems",
            "remediation": "System upgrade planned",
            "target_date": "2027-01-01",
        },
    ],
}


@pytest.fixture
def bcbs_env(tmp_path, monkeypatch):
    """Isolated BCBS 239 environment."""
    import routes.governance._constants as gov_constants

    bcbs_path = str(tmp_path / "bcbs239_assessment.json")
    Path(bcbs_path).write_text(json.dumps(copy.deepcopy(_BASE_BCBS239)))
    monkeypatch.setattr(gov_constants, "BCBS239_PATH", bcbs_path)
    return {"bcbs_path": bcbs_path, "tmp_path": tmp_path}


@pytest.fixture
def bcbs_client(bcbs_env, monkeypatch):
    """Flask test client with isolated BCBS 239 data."""
    from config import config
    monkeypatch.setattr(config, "get_input_dir", lambda: bcbs_env["tmp_path"])

    from server import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client(), bcbs_env


@pytest.fixture
def bcbs_client_no_data(tmp_path, monkeypatch):
    """Flask test client where BCBS 239 file does not exist."""
    import routes.governance._constants as gov_constants
    from config import config

    monkeypatch.setattr(gov_constants, "BCBS239_PATH", str(tmp_path / "missing.json"))
    monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)

    from server import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


# ===========================================================================
# GET /governance/bcbs239
# ===========================================================================

class TestGetBcbs239:

    def test_no_data_returns_404(self, bcbs_client_no_data):
        r = bcbs_client_no_data.get("/api/v1/governance/bcbs239")
        assert r.status_code == 404
        assert r.get_json()["status"] == "error"

    def test_with_data_returns_200(self, bcbs_client):
        client, _ = bcbs_client
        r = client.get("/api/v1/governance/bcbs239")
        assert r.status_code == 200
        assert r.get_json()["status"] == "success"

    def test_response_has_assessment(self, bcbs_client):
        client, _ = bcbs_client
        r = client.get("/api/v1/governance/bcbs239")
        data = r.get_json()
        assert "assessment" in data
        assert "principles" in data["assessment"]

    def test_principles_count(self, bcbs_client):
        client, _ = bcbs_client
        r = client.get("/api/v1/governance/bcbs239")
        assert len(r.get_json()["assessment"]["principles"]) == 2


# ===========================================================================
# POST /governance/bcbs239/principles/<id>/update
# ===========================================================================

class TestUpdateBcbs239Principle:

    def test_no_data_file_returns_404(self, bcbs_client_no_data):
        r = bcbs_client_no_data.post(
            "/api/v1/governance/bcbs239/principles/1/update",
            json={"score": 4}
        )
        assert r.status_code == 404

    def test_principle_not_found_returns_404(self, bcbs_client):
        client, _ = bcbs_client
        r = client.post(
            "/api/v1/governance/bcbs239/principles/999/update",
            json={"score": 4}
        )
        assert r.status_code == 404

    def test_valid_update_returns_200(self, bcbs_client):
        client, _ = bcbs_client
        r = client.post(
            "/api/v1/governance/bcbs239/principles/1/update",
            json={"score": 4, "evidence": "Full board mandate"}
        )
        assert r.status_code == 200
        assert r.get_json()["status"] == "success"

    def test_score_1_derives_non_compliant_status(self, bcbs_client):
        client, _ = bcbs_client
        r = client.post(
            "/api/v1/governance/bcbs239/principles/1/update",
            json={"score": 1}
        )
        assert r.status_code == 200
        assessment = r.get_json()["assessment"]
        p = next(x for x in assessment["principles"] if x["id"] == 1)
        assert p["status"] == "Non-compliant"

    def test_score_4_derives_fully_compliant_status(self, bcbs_client):
        client, _ = bcbs_client
        r = client.post(
            "/api/v1/governance/bcbs239/principles/1/update",
            json={"score": 4}
        )
        p = next(x for x in r.get_json()["assessment"]["principles"] if x["id"] == 1)
        assert p["status"] == "Fully Compliant"

    def test_update_evidence_field(self, bcbs_client):
        client, _ = bcbs_client
        r = client.post(
            "/api/v1/governance/bcbs239/principles/2/update",
            json={"evidence": "New evidence gathered"}
        )
        assert r.status_code == 200
        p = next(x for x in r.get_json()["assessment"]["principles"] if x["id"] == 2)
        assert p["evidence"] == "New evidence gathered"

    def test_update_gaps_and_remediation(self, bcbs_client):
        client, _ = bcbs_client
        r = client.post(
            "/api/v1/governance/bcbs239/principles/1/update",
            json={"gaps": "Minor gap", "remediation": "Action plan created"}
        )
        p = next(x for x in r.get_json()["assessment"]["principles"] if x["id"] == 1)
        assert p["gaps"] == "Minor gap"
        assert p["remediation"] == "Action plan created"

    def test_assessment_date_updated(self, bcbs_client):
        client, _ = bcbs_client
        r = client.post(
            "/api/v1/governance/bcbs239/principles/1/update",
            json={"score": 3}
        )
        assert r.get_json()["assessment"]["assessment_date"] is not None


# ===========================================================================
# GET /governance/bcbs239/pdf
# ===========================================================================

class TestGetBcbs239Pdf:

    def test_bcbs239_pdf_responds(self, bcbs_client):
        """Returns 200 if PDF exists, 404 if not yet generated."""
        client, _ = bcbs_client
        r = client.get("/api/v1/governance/bcbs239/pdf")
        assert r.status_code in (200, 404)


# ===========================================================================
# RACI endpoint coverage gaps (using raci_client from conftest)
# ===========================================================================

class TestUpdateRaciRoleExtra:
    """Additional tests for update_raci_role to hit missing branches."""

    def test_no_raci_file_returns_404(self, bcbs_client_no_data, monkeypatch):
        import routes.governance._constants as gov_constants
        monkeypatch.setattr(gov_constants, "RACI_PATH", "/nonexistent/raci.json")
        r = bcbs_client_no_data.post(
            "/api/v1/governance/raci/roles/operations_lead/update",
            json={"assigned_to": "New Person"}
        )
        assert r.status_code == 404

    def test_role_not_found_returns_404(self, raci_client):
        r = raci_client.post(
            "/api/v1/governance/raci/roles/nonexistent_role/update",
            json={"assigned_to": "Someone"}
        )
        assert r.status_code == 404

    def test_valid_role_update_returns_success(self, raci_client):
        r = raci_client.post(
            "/api/v1/governance/raci/roles/operations_lead/update",
            json={"assigned_to": "New Lead", "backup": "Deputy"}
        )
        assert r.status_code == 200
        assert r.get_json()["status"] == "success"

    def test_backup_field_updated(self, raci_client):
        r = raci_client.post(
            "/api/v1/governance/raci/roles/model_owner/update",
            json={"assigned_to": "Owner A", "backup": "Owner B"}
        )
        roles = r.get_json()["raci"]["roles"]
        owner = next(x for x in roles if x["role_id"] == "model_owner")
        assert owner["backup"] == "Owner B"

    def test_response_has_audit_entry(self, raci_client):
        r = raci_client.post(
            "/api/v1/governance/raci/roles/operations_lead/update",
            json={"assigned_to": "X"}
        )
        assert "audit_entry" in r.get_json()


class TestUpdateRaciActivityExtra:
    """Additional tests for update_raci_activity to hit missing branches."""

    def test_activity_not_found_returns_404(self, raci_client):
        r = raci_client.post(
            "/api/v1/governance/raci/activities/ACT-GHOST/update",
            json={"R": "operations_lead"}
        )
        assert r.status_code == 404

    def test_invalid_role_id_returns_400(self, raci_client):
        r = raci_client.post(
            "/api/v1/governance/raci/activities/ACT-01/update",
            json={"R": "nonexistent_role"}
        )
        assert r.status_code == 400

    def test_valid_activity_update_returns_success(self, raci_client):
        r = raci_client.post(
            "/api/v1/governance/raci/activities/ACT-01/update",
            json={"R": "model_owner", "notes": "Updated"}
        )
        assert r.status_code == 200
        assert r.get_json()["status"] == "success"

    def test_notes_updated(self, raci_client):
        r = raci_client.post(
            "/api/v1/governance/raci/activities/ACT-01/update",
            json={"notes": "New note"}
        )
        activities = r.get_json()["raci"]["activities"]
        assert activities[0]["notes"] == "New note"

    def test_null_raci_code_allowed(self, raci_client):
        """Setting C or I to None (null) is valid."""
        r = raci_client.post(
            "/api/v1/governance/raci/activities/ACT-01/update",
            json={"C": None, "I": None}
        )
        assert r.status_code == 200


class TestUpdateRaciEscalationExtra:
    """Tests for update_raci_escalation."""

    def test_trigger_not_found_returns_404(self, raci_client):
        r = raci_client.post(
            "/api/v1/governance/raci/escalation-triggers/GHOST/update",
            json={"tier_threshold": {"1": "Immediate"}}
        )
        assert r.status_code == 404

    def test_valid_escalation_update_returns_success(self, raci_client):
        r = raci_client.post(
            "/api/v1/governance/raci/escalation-triggers/ESC-01/update",
            json={"tier_threshold": {"1": "Immediate", "2": "Within 4 hours"},
                  "response_required": "Full investigation"}
        )
        assert r.status_code == 200
        assert r.get_json()["status"] == "success"

    def test_escalation_tier_threshold_updated(self, raci_client):
        r = raci_client.post(
            "/api/v1/governance/raci/escalation-triggers/ESC-01/update",
            json={"tier_threshold": {"1": "Immediate"}}
        )
        triggers = r.get_json()["raci"]["escalation_triggers"]
        assert triggers[0]["tier_threshold"]["1"] == "Immediate"

    def test_response_has_audit_entry(self, raci_client):
        r = raci_client.post(
            "/api/v1/governance/raci/escalation-triggers/ESC-01/update",
            json={"response_required": "Updated response"}
        )
        assert "audit_entry" in r.get_json()
