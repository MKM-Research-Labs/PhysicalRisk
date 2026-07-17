# Copyright (c) 2022-2026 MKM Research Labs.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Tests for RACI matrix API endpoints."""

import json


class TestRACIMatrix:
    """Test RACI matrix API endpoints."""

    def test_get_raci_matrix(self, raci_client, raci_env):
        response = raci_client.get("/api/v1/governance/raci")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "success"

        raci = data["raci"]
        assert len(raci["roles"]) == 2
        assert len(raci["activities"]) == 1
        assert len(raci["escalation_triggers"]) == 1

    def test_get_raci_matrix_file_missing(self, gov_client, governance_env, monkeypatch):
        import routes.governance._constants as gov_constants
        monkeypatch.setattr(gov_constants, "RACI_PATH", "/nonexistent/raci.json")

        response = gov_client.get("/api/v1/governance/raci")
        assert response.status_code == 404

    def test_update_raci_role(self, raci_client, raci_env):
        response = raci_client.post(
            "/api/v1/governance/raci/roles/operations_lead/update",
            json={"assigned_to": "Jane Smith", "backup": "John Doe", "user": "Admin"},
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "success"

        role = next(r for r in data["raci"]["roles"] if r["role_id"] == "operations_lead")
        assert role["assigned_to"] == "Jane Smith"
        assert role["backup"] == "John Doe"
        assert data["audit_entry"]["event_type"] == "raci_role_update"

    def test_update_raci_role_not_found(self, raci_client, raci_env):
        response = raci_client.post(
            "/api/v1/governance/raci/roles/nonexistent_role/update",
            json={"assigned_to": "Someone", "user": "Admin"},
        )
        assert response.status_code == 404

    def test_update_raci_activity(self, raci_client, raci_env):
        response = raci_client.post(
            "/api/v1/governance/raci/activities/ACT-01/update",
            json={"R": "model_owner", "A": "model_owner", "notes": "Updated notes", "user": "Admin"},
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "success"

        act = data["raci"]["activities"][0]
        assert act["R"] == "model_owner"
        assert act["notes"] == "Updated notes"
        assert data["audit_entry"]["event_type"] == "raci_activity_update"

    def test_update_raci_activity_invalid_role(self, raci_client, raci_env):
        response = raci_client.post(
            "/api/v1/governance/raci/activities/ACT-01/update",
            json={"R": "invalid_role_id", "user": "Admin"},
        )
        assert response.status_code == 400

    def test_update_raci_escalation(self, raci_client, raci_env):
        response = raci_client.post(
            "/api/v1/governance/raci/escalation-triggers/ESC-01/update",
            json={
                "tier_threshold": {"1": "Immediate", "2": "Within 4h", "3": "Within 24h"},
                "response_required": "Full investigation report",
                "user": "Admin",
            },
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "success"

        trig = data["raci"]["escalation_triggers"][0]
        assert trig["tier_threshold"]["2"] == "Within 4h"
        assert trig["response_required"] == "Full investigation report"
        assert data["audit_entry"]["event_type"] == "raci_escalation_update"
