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
Tests for MRC meeting CRUD — minutes items, malformed IDs, edge cases.

Split from mrc_crud.py.
"""

import copy
import json
import pathlib

import pytest


_BASE_MEETING = {
    "id": "MRC-2026-001",
    "title": "Q1 2026 MRC Meeting",
    "date": "2026-03-15",
    "agenda": [
        {"item": 1, "title": "Minutes of previous meeting",
         "description": "", "presenter": "Chair",
         "duration": "10m", "status": "Standing"},
    ],
    "minutes": [
        {"item": 1, "title": "Minutes approved", "text": "Approved.",
         "presenter": "Chair"},
    ],
    "decisions": [
        {"id": "D-001", "description": "Approve GEV model", "date": "2026-03-15"},
    ],
    "actions": [
        {"id": "A-001", "description": "Update docs", "owner": "Lead",
         "target_date": "2026-04-01", "status": "Open"},
    ],
    "participants": [
        {"id": "P-001", "name": "Alice", "role": "CRO",
         "organisation": "MKM", "status": "Confirmed"},
    ],
}


@pytest.fixture
def mrc_crud_client(tmp_path, monkeypatch):
    """Flask test client with MRC meeting JSON and governance monkeypatches."""
    import routes.governance._constants as gov_constants
    from config import config

    meetings_path = str(tmp_path / "mrc_meetings.json")
    inv_path = str(tmp_path / "model_inventory.json")
    audit_path = str(tmp_path / "model_audit_log.json")

    with open(meetings_path, "w") as f:
        json.dump([copy.deepcopy(_BASE_MEETING)], f)
    with open(inv_path, "w") as f:
        json.dump({"models": []}, f)
    with open(audit_path, "w") as f:
        json.dump([], f)

    monkeypatch.setattr(gov_constants, "MRC_MEETINGS_PATH", meetings_path)
    monkeypatch.setattr(gov_constants, "INVENTORY_PATH", inv_path)
    monkeypatch.setattr(gov_constants, "AUDIT_LOG_PATH", audit_path)
    monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)

    from server import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


BASE_URL = "/api/v1/governance/mrc/meetings/MRC-2026-001"


# ===========================================================================
# Minutes Items CRUD
# ===========================================================================

class TestMinutesItemsCrud:

    def test_add_minute_item_returns_200(self, mrc_crud_client):
        r = mrc_crud_client.post(
            f"{BASE_URL}/minutes-items",
            json={"title": "AOB", "text": "No other business.",
                  "presenter": "Chair"},
        )
        assert r.status_code == 200
        meeting = r.get_json()["meeting"]
        assert isinstance(meeting["minutes"], list)
        assert len(meeting["minutes"]) == 2

    def test_add_minute_item_missing_meeting_returns_404(self, mrc_crud_client):
        r = mrc_crud_client.post(
            "/api/v1/governance/mrc/meetings/GHOST/minutes-items",
            json={"title": "x"},
        )
        assert r.status_code == 404

    def test_update_minute_item_returns_200(self, mrc_crud_client):
        r = mrc_crud_client.post(
            f"{BASE_URL}/minutes-items/1/update",
            json={"text": "Updated text."},
        )
        assert r.status_code == 200
        item = r.get_json()["meeting"]["minutes"][0]
        assert item["text"] == "Updated text."

    def test_update_minute_item_not_found_returns_404(self, mrc_crud_client):
        r = mrc_crud_client.post(
            f"{BASE_URL}/minutes-items/999/update",
            json={"text": "x"},
        )
        assert r.status_code == 404

    def test_update_minute_item_legacy_format_returns_400(self, mrc_crud_client):
        """When minutes is a string (legacy), updating an item returns 400."""
        # First set minutes to a string via the update endpoint
        mrc_crud_client.post(f"{BASE_URL}/minutes/update",
                             json={"minutes": "legacy text"})
        r = mrc_crud_client.post(
            f"{BASE_URL}/minutes-items/1/update",
            json={"text": "x"},
        )
        assert r.status_code == 400

    def test_delete_minute_item_returns_200(self, mrc_crud_client):
        # Add another item first
        mrc_crud_client.post(f"{BASE_URL}/minutes-items",
                             json={"title": "Extra"})
        r = mrc_crud_client.post(f"{BASE_URL}/minutes-items/1/delete")
        assert r.status_code == 200
        meeting = r.get_json()["meeting"]
        assert len(meeting["minutes"]) == 1
        assert meeting["minutes"][0]["item"] == 1  # Renumbered

    def test_delete_minute_item_legacy_format_returns_400(self, mrc_crud_client):
        """When minutes is a string, deleting returns 400."""
        mrc_crud_client.post(f"{BASE_URL}/minutes/update",
                             json={"minutes": "legacy text"})
        r = mrc_crud_client.post(f"{BASE_URL}/minutes-items/1/delete")
        assert r.status_code == 400

    def test_delete_minute_item_missing_meeting_returns_404(self, mrc_crud_client):
        r = mrc_crud_client.post(
            "/api/v1/governance/mrc/meetings/GHOST/minutes-items/1/delete"
        )
        assert r.status_code == 404


# ===========================================================================
# Coverage expansion: malformed IDs (L129-130, L191-192, L255-256),
# missing meeting on update (L147, L211, L275, L333),
# minutes string→list conversion (L314)
# ===========================================================================

class TestMalformedDecisionId:
    """Lines 129-130: existing decision with malformed ID triggers except (IndexError, ValueError)."""

    @pytest.fixture
    def mrc_crud_malformed_decisions(self, tmp_path, monkeypatch):
        import routes.governance._constants as gov_constants
        from config import config

        meeting = copy.deepcopy(_BASE_MEETING)
        # Add a decision with a malformed ID that can't be parsed as "D-NNN"
        meeting["decisions"].append({"id": "BADID", "description": "Malformed", "date": "2026-01-01"})

        meetings_path = str(tmp_path / "mrc_meetings.json")
        inv_path = str(tmp_path / "model_inventory.json")
        audit_path = str(tmp_path / "model_audit_log.json")

        with open(meetings_path, "w") as f:
            json.dump([meeting], f)
        with open(inv_path, "w") as f:
            json.dump({"models": []}, f)
        with open(audit_path, "w") as f:
            json.dump([], f)

        monkeypatch.setattr(gov_constants, "MRC_MEETINGS_PATH", meetings_path)
        monkeypatch.setattr(gov_constants, "INVENTORY_PATH", inv_path)
        monkeypatch.setattr(gov_constants, "AUDIT_LOG_PATH", audit_path)
        monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)

        from server import create_app
        app = create_app()
        app.config["TESTING"] = True
        return app.test_client()

    def test_add_decision_with_malformed_existing_id(self, mrc_crud_malformed_decisions):
        """Malformed decision ID is skipped; new decision still gets a valid auto-ID."""
        r = mrc_crud_malformed_decisions.post(
            f"{BASE_URL}/decisions",
            json={"description": "New after malformed"},
        )
        assert r.status_code == 200
        decisions = r.get_json()["meeting"]["decisions"]
        ids = [d["id"] for d in decisions]
        # D-001 exists, BADID is malformed (skipped), new one should be D-002
        assert "D-002" in ids


class TestMalformedActionId:
    """Lines 191-192: existing action with malformed ID triggers except."""

    @pytest.fixture
    def mrc_crud_malformed_actions(self, tmp_path, monkeypatch):
        import routes.governance._constants as gov_constants
        from config import config

        meeting = copy.deepcopy(_BASE_MEETING)
        meeting["actions"].append({"id": "NOPE", "description": "Bad", "owner": "X",
                                   "target_date": "", "status": "Open"})

        meetings_path = str(tmp_path / "mrc_meetings.json")
        inv_path = str(tmp_path / "model_inventory.json")
        audit_path = str(tmp_path / "model_audit_log.json")

        with open(meetings_path, "w") as f:
            json.dump([meeting], f)
        with open(inv_path, "w") as f:
            json.dump({"models": []}, f)
        with open(audit_path, "w") as f:
            json.dump([], f)

        monkeypatch.setattr(gov_constants, "MRC_MEETINGS_PATH", meetings_path)
        monkeypatch.setattr(gov_constants, "INVENTORY_PATH", inv_path)
        monkeypatch.setattr(gov_constants, "AUDIT_LOG_PATH", audit_path)
        monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)

        from server import create_app
        app = create_app()
        app.config["TESTING"] = True
        return app.test_client()

    def test_add_action_with_malformed_existing_id(self, mrc_crud_malformed_actions):
        r = mrc_crud_malformed_actions.post(
            f"{BASE_URL}/actions",
            json={"description": "New action"},
        )
        assert r.status_code == 200
        actions = r.get_json()["meeting"]["actions"]
        ids = [a["id"] for a in actions]
        assert "A-002" in ids


class TestMalformedParticipantId:
    """Lines 255-256: existing participant with malformed ID triggers except."""

    @pytest.fixture
    def mrc_crud_malformed_participants(self, tmp_path, monkeypatch):
        import routes.governance._constants as gov_constants
        from config import config

        meeting = copy.deepcopy(_BASE_MEETING)
        meeting["participants"].append({"id": "WRONG", "name": "X", "role": "",
                                        "organisation": "", "status": "Invited"})

        meetings_path = str(tmp_path / "mrc_meetings.json")
        inv_path = str(tmp_path / "model_inventory.json")
        audit_path = str(tmp_path / "model_audit_log.json")

        with open(meetings_path, "w") as f:
            json.dump([meeting], f)
        with open(inv_path, "w") as f:
            json.dump({"models": []}, f)
        with open(audit_path, "w") as f:
            json.dump([], f)

        monkeypatch.setattr(gov_constants, "MRC_MEETINGS_PATH", meetings_path)
        monkeypatch.setattr(gov_constants, "INVENTORY_PATH", inv_path)
        monkeypatch.setattr(gov_constants, "AUDIT_LOG_PATH", audit_path)
        monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)

        from server import create_app
        app = create_app()
        app.config["TESTING"] = True
        return app.test_client()

    def test_add_participant_with_malformed_existing_id(self, mrc_crud_malformed_participants):
        r = mrc_crud_malformed_participants.post(
            f"{BASE_URL}/participants",
            json={"name": "New Person"},
        )
        assert r.status_code == 200
        participants = r.get_json()["meeting"]["participants"]
        ids = [p["id"] for p in participants]
        assert "P-002" in ids


class TestUpdateMissingMeeting:
    """Lines 147, 211, 275, 333: update endpoints with missing meeting → 404."""

    def test_update_decision_missing_meeting_returns_404(self, mrc_crud_client):
        """Line 147: update_decision with non-existent meeting."""
        r = mrc_crud_client.post(
            "/api/v1/governance/mrc/meetings/GHOST/decisions/D-001/update",
            json={"description": "x"},
        )
        assert r.status_code == 404

    def test_update_action_missing_meeting_returns_404(self, mrc_crud_client):
        """Line 211: update_action with non-existent meeting."""
        r = mrc_crud_client.post(
            "/api/v1/governance/mrc/meetings/GHOST/actions/A-001/update",
            json={"status": "Closed"},
        )
        assert r.status_code == 404

    def test_update_participant_missing_meeting_returns_404(self, mrc_crud_client):
        """Line 275: update_participant with non-existent meeting."""
        r = mrc_crud_client.post(
            "/api/v1/governance/mrc/meetings/GHOST/participants/P-001/update",
            json={"status": "Confirmed"},
        )
        assert r.status_code == 404

    def test_update_minute_item_missing_meeting_returns_404(self, mrc_crud_client):
        """Line 333: update_minute_item with non-existent meeting."""
        r = mrc_crud_client.post(
            "/api/v1/governance/mrc/meetings/GHOST/minutes-items/1/update",
            json={"text": "x"},
        )
        assert r.status_code == 404


class TestMinutesStringToListConversion:
    """Line 314: add_minute_item when minutes is a string (legacy) converts to empty list."""

    def test_add_minute_item_when_minutes_is_string(self, mrc_crud_client):
        """Set minutes to a string via update, then add a minutes-item."""
        # First set minutes to a string (legacy format)
        mrc_crud_client.post(f"{BASE_URL}/minutes/update",
                             json={"minutes": "legacy text"})
        # Now add a minutes item — this should convert the string to a list
        r = mrc_crud_client.post(
            f"{BASE_URL}/minutes-items",
            json={"title": "New Item", "text": "Some text", "presenter": "Chair"},
        )
        assert r.status_code == 200
        meeting = r.get_json()["meeting"]
        assert isinstance(meeting["minutes"], list)
        assert len(meeting["minutes"]) == 1
        assert meeting["minutes"][0]["title"] == "New Item"
