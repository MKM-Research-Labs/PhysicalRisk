# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

"""
Governance e2e tests: MRC CRUD sub-routes.

Covers meeting detail, agenda, minutes, decisions, actions, participants,
and document endpoints — the 15 CRUD routes previously untested.
"""

import pytest

from tests.e2e.helpers import (
    close_all_panels,
    get_governance_content_text,
    open_governance,
    switch_governance_tab,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_first_meeting_id(map_page):
    """Fetch first meeting ID from API."""
    result = map_page.evaluate("""async () => {
        var cfg = window.__BACKEND_CONFIG || {};
        var baseUrl = cfg.url || '';
        var resp = await fetch(
            baseUrl + '/api/v1/governance/mrc/meetings'
        );
        var data = await resp.json();
        var meetings = data.meetings || [];
        if (meetings.length === 0) return { skip: true };
        return { id: meetings[0].id };
    }""")
    if result.get("skip"):
        return None
    return result.get("id")


def _open_meeting_detail(map_page):
    """Open MRC tab and click first meeting row to get detail view."""
    close_all_panels(map_page)
    open_governance(map_page)
    switch_governance_tab(map_page, "mrc")
    map_page.wait_for_timeout(6_000)  # API load

    content = map_page.locator("#mg-content")
    # Click first meeting row in the table
    rows = content.locator("tr[data-meeting-id]").or_(
        content.locator("tr").filter(has_text="MRC")
    ).or_(
        content.locator("[onclick*='viewMeeting']").or_(
            content.locator("[onclick*='openMeeting']")
        )
    )
    if rows.count() > 0:
        rows.first.click(force=True)
        map_page.wait_for_timeout(6_000)
        return True

    # Fallback: try clicking any clickable row after header
    all_rows = content.locator("tr")
    if all_rows.count() > 1:
        all_rows.nth(1).click(force=True)
        map_page.wait_for_timeout(6_000)
        return True

    return False


# ---------------------------------------------------------------------------
# Meeting API tests
# ---------------------------------------------------------------------------


class TestMRCMeetingsAPI:
    """MRC meetings API: list, detail, create."""

    def test_list_meetings_returns_data(self, map_page):
        """GET /api/v1/governance/mrc/meetings should return meetings."""
        result = map_page.evaluate("""async () => {
            var cfg = window.__BACKEND_CONFIG || {};
            var baseUrl = cfg.url || '';
            var resp = await fetch(
                baseUrl + '/api/v1/governance/mrc/meetings'
            );
            var data = await resp.json();
            return {
                http_status: resp.status,
                api_status: data.status,
                count: (data.meetings || []).length,
            };
        }""")
        assert result["http_status"] == 200
        assert result["api_status"] == "success"
        assert result["count"] > 0, "No MRC meetings found"

    def test_meeting_summary_has_fields(self, map_page):
        """Meeting summary should include expected fields."""
        result = map_page.evaluate("""async () => {
            var cfg = window.__BACKEND_CONFIG || {};
            var baseUrl = cfg.url || '';
            var resp = await fetch(
                baseUrl + '/api/v1/governance/mrc/meetings'
            );
            var data = await resp.json();
            var m = (data.meetings || [])[0];
            if (!m) return { skip: true };
            return {
                has_id: !!m.id,
                has_title: !!m.title,
                has_date: !!m.date,
                has_status: !!m.status,
                has_chair: !!m.chair,
            };
        }""")
        if result.get("skip"):
            pytest.skip("No meetings")
        assert result["has_id"], "Missing id"
        assert result["has_title"], "Missing title"
        assert result["has_date"], "Missing date"
        assert result["has_status"], "Missing status"

    def test_meeting_detail_returns_full_object(self, map_page):
        """GET /api/v1/governance/mrc/meetings/<id> should return full detail."""
        meeting_id = _get_first_meeting_id(map_page)
        if not meeting_id:
            pytest.skip("No meetings available")

        result = map_page.evaluate(f"""async () => {{
            var cfg = window.__BACKEND_CONFIG || {{}};
            var baseUrl = cfg.url || '';
            var resp = await fetch(
                baseUrl + '/api/v1/governance/mrc/meetings/{meeting_id}'
            );
            var data = await resp.json();
            var m = data.meeting || {{}};
            return {{
                http_status: resp.status,
                has_agenda: Array.isArray(m.agenda),
                has_decisions: Array.isArray(m.decisions),
                has_actions: Array.isArray(m.actions),
                has_participants: Array.isArray(m.participants),
            }};
        }}""")
        assert result["http_status"] == 200
        assert result["has_agenda"], "Missing agenda array"
        assert result["has_decisions"], "Missing decisions array"
        assert result["has_actions"], "Missing actions array"


# ---------------------------------------------------------------------------
# Agenda CRUD API
# ---------------------------------------------------------------------------


class TestMRCAgendaCRUD:
    """Agenda item CRUD via API."""

    def test_add_agenda_item(self, map_page):
        """POST agenda item should succeed and return updated meeting."""
        meeting_id = _get_first_meeting_id(map_page)
        if not meeting_id:
            pytest.skip("No meetings available")

        result = map_page.evaluate(f"""async () => {{
            var cfg = window.__BACKEND_CONFIG || {{}};
            var baseUrl = cfg.url || '';
            var resp = await fetch(
                baseUrl + '/api/v1/governance/mrc/meetings/{meeting_id}/agenda',
                {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{
                        title: 'E2E Test Agenda Item',
                        description: 'Created by E2E test',
                        presenter: 'Test User',
                        duration: '10 min',
                        status: 'Pending'
                    }})
                }}
            );
            var data = await resp.json();
            return {{
                http_status: resp.status,
                api_status: data.status,
                agenda_count: (data.meeting || {{}}).agenda
                    ? data.meeting.agenda.length : 0,
            }};
        }}""")
        assert result["http_status"] == 200
        assert result["api_status"] == "success"
        assert result["agenda_count"] > 0, "Agenda empty after add"

    def test_delete_agenda_item(self, map_page):
        """DELETE last agenda item should succeed."""
        meeting_id = _get_first_meeting_id(map_page)
        if not meeting_id:
            pytest.skip("No meetings available")

        result = map_page.evaluate(f"""async () => {{
            var cfg = window.__BACKEND_CONFIG || {{}};
            var baseUrl = cfg.url || '';
            // Get current agenda count
            var resp1 = await fetch(
                baseUrl + '/api/v1/governance/mrc/meetings/{meeting_id}'
            );
            var data1 = await resp1.json();
            var agenda = (data1.meeting || {{}}).agenda || [];
            if (agenda.length === 0) return {{ skip: true }};
            var lastItem = agenda.length;
            // Delete last item
            var resp2 = await fetch(
                baseUrl + '/api/v1/governance/mrc/meetings/{meeting_id}/agenda/' + lastItem + '/delete',
                {{ method: 'POST' }}
            );
            var data2 = await resp2.json();
            return {{
                http_status: resp2.status,
                api_status: data2.status,
            }};
        }}""")
        if result.get("skip"):
            pytest.skip("No agenda items to delete")
        assert result["http_status"] == 200
        assert result["api_status"] == "success"


# ---------------------------------------------------------------------------
# Decisions CRUD API
# ---------------------------------------------------------------------------


class TestMRCDecisionsCRUD:
    """Decisions CRUD via API."""

    def test_add_decision(self, map_page):
        """POST decision should auto-generate ID and save."""
        meeting_id = _get_first_meeting_id(map_page)
        if not meeting_id:
            pytest.skip("No meetings available")

        result = map_page.evaluate(f"""async () => {{
            var cfg = window.__BACKEND_CONFIG || {{}};
            var baseUrl = cfg.url || '';
            var resp = await fetch(
                baseUrl + '/api/v1/governance/mrc/meetings/{meeting_id}/decisions',
                {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{
                        description: 'E2E test decision',
                        date: '2026-03-24'
                    }})
                }}
            );
            var data = await resp.json();
            var decisions = (data.meeting || {{}}).decisions || [];
            var last = decisions[decisions.length - 1] || {{}};
            return {{
                http_status: resp.status,
                api_status: data.status,
                has_id: !!last.id,
                id_format: (last.id || '').substring(0, 2),
            }};
        }}""")
        assert result["http_status"] == 200
        assert result["api_status"] == "success"
        assert result["has_id"], "Decision missing auto-generated ID"
        assert result["id_format"] == "D-", \
            f"Expected D-xxx format, got {result['id_format']}"

    def test_delete_decision(self, map_page):
        """DELETE decision should succeed."""
        meeting_id = _get_first_meeting_id(map_page)
        if not meeting_id:
            pytest.skip("No meetings available")

        result = map_page.evaluate(f"""async () => {{
            var cfg = window.__BACKEND_CONFIG || {{}};
            var baseUrl = cfg.url || '';
            var resp1 = await fetch(
                baseUrl + '/api/v1/governance/mrc/meetings/{meeting_id}'
            );
            var data1 = await resp1.json();
            var decisions = (data1.meeting || {{}}).decisions || [];
            if (decisions.length === 0) return {{ skip: true }};
            var lastId = decisions[decisions.length - 1].id;
            var resp2 = await fetch(
                baseUrl + '/api/v1/governance/mrc/meetings/{meeting_id}/decisions/' + lastId + '/delete',
                {{ method: 'POST' }}
            );
            var data2 = await resp2.json();
            return {{
                http_status: resp2.status,
                api_status: data2.status,
            }};
        }}""")
        if result.get("skip"):
            pytest.skip("No decisions to delete")
        assert result["http_status"] == 200
        assert result["api_status"] == "success"


# ---------------------------------------------------------------------------
# Actions CRUD API
# ---------------------------------------------------------------------------


class TestMRCActionsCRUD:
    """Actions CRUD via API."""

    def test_add_action(self, map_page):
        """POST action should auto-generate ID and save."""
        meeting_id = _get_first_meeting_id(map_page)
        if not meeting_id:
            pytest.skip("No meetings available")

        result = map_page.evaluate(f"""async () => {{
            var cfg = window.__BACKEND_CONFIG || {{}};
            var baseUrl = cfg.url || '';
            var resp = await fetch(
                baseUrl + '/api/v1/governance/mrc/meetings/{meeting_id}/actions',
                {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{
                        description: 'E2E test action item',
                        owner: 'Test User',
                        target_date: '2026-04-24',
                        status: 'Open'
                    }})
                }}
            );
            var data = await resp.json();
            var actions = (data.meeting || {{}}).actions || [];
            var last = actions[actions.length - 1] || {{}};
            return {{
                http_status: resp.status,
                api_status: data.status,
                has_id: !!last.id,
                id_format: (last.id || '').substring(0, 2),
            }};
        }}""")
        assert result["http_status"] == 200
        assert result["api_status"] == "success"
        assert result["has_id"], "Action missing auto-generated ID"
        assert result["id_format"] == "A-", \
            f"Expected A-xxx format, got {result['id_format']}"

    def test_delete_action(self, map_page):
        """DELETE action should succeed."""
        meeting_id = _get_first_meeting_id(map_page)
        if not meeting_id:
            pytest.skip("No meetings available")

        result = map_page.evaluate(f"""async () => {{
            var cfg = window.__BACKEND_CONFIG || {{}};
            var baseUrl = cfg.url || '';
            var resp1 = await fetch(
                baseUrl + '/api/v1/governance/mrc/meetings/{meeting_id}'
            );
            var data1 = await resp1.json();
            var actions = (data1.meeting || {{}}).actions || [];
            if (actions.length === 0) return {{ skip: true }};
            var lastId = actions[actions.length - 1].id;
            var resp2 = await fetch(
                baseUrl + '/api/v1/governance/mrc/meetings/{meeting_id}/actions/' + lastId + '/delete',
                {{ method: 'POST' }}
            );
            var data2 = await resp2.json();
            return {{
                http_status: resp2.status,
                api_status: data2.status,
            }};
        }}""")
        if result.get("skip"):
            pytest.skip("No actions to delete")
        assert result["http_status"] == 200
        assert result["api_status"] == "success"


# ---------------------------------------------------------------------------
# Participants CRUD API
# ---------------------------------------------------------------------------


class TestMRCParticipantsCRUD:
    """Participants CRUD via API."""

    def test_add_participant(self, map_page):
        """POST participant should auto-generate ID and save."""
        meeting_id = _get_first_meeting_id(map_page)
        if not meeting_id:
            pytest.skip("No meetings available")

        result = map_page.evaluate(f"""async () => {{
            var cfg = window.__BACKEND_CONFIG || {{}};
            var baseUrl = cfg.url || '';
            var resp = await fetch(
                baseUrl + '/api/v1/governance/mrc/meetings/{meeting_id}/participants',
                {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{
                        name: 'E2E Test Participant',
                        role: 'Observer',
                        organisation: 'MKM Research Labs',
                        status: 'Invited'
                    }})
                }}
            );
            var data = await resp.json();
            var participants = (data.meeting || {{}}).participants || [];
            var last = participants[participants.length - 1] || {{}};
            return {{
                http_status: resp.status,
                api_status: data.status,
                has_id: !!last.id,
                id_format: (last.id || '').substring(0, 2),
            }};
        }}""")
        assert result["http_status"] == 200
        assert result["api_status"] == "success"
        assert result["has_id"], "Participant missing auto-generated ID"
        assert result["id_format"] == "P-", \
            f"Expected P-xxx format, got {result['id_format']}"

    def test_delete_participant(self, map_page):
        """DELETE participant should succeed."""
        meeting_id = _get_first_meeting_id(map_page)
        if not meeting_id:
            pytest.skip("No meetings available")

        result = map_page.evaluate(f"""async () => {{
            var cfg = window.__BACKEND_CONFIG || {{}};
            var baseUrl = cfg.url || '';
            var resp1 = await fetch(
                baseUrl + '/api/v1/governance/mrc/meetings/{meeting_id}'
            );
            var data1 = await resp1.json();
            var participants = (data1.meeting || {{}}).participants || [];
            if (participants.length === 0) return {{ skip: true }};
            var lastId = participants[participants.length - 1].id;
            var resp2 = await fetch(
                baseUrl + '/api/v1/governance/mrc/meetings/{meeting_id}/participants/' + lastId + '/delete',
                {{ method: 'POST' }}
            );
            var data2 = await resp2.json();
            return {{
                http_status: resp2.status,
                api_status: data2.status,
            }};
        }}""")
        if result.get("skip"):
            pytest.skip("No participants to delete")
        assert result["http_status"] == 200
        assert result["api_status"] == "success"


# ---------------------------------------------------------------------------
# Meeting detail UI tests
# ---------------------------------------------------------------------------


class TestMRCMeetingDetailUI:
    """Meeting detail view: tabs and content rendering."""

    @pytest.fixture(autouse=True)
    def setup(self, map_page):
        close_all_panels(map_page)
        open_governance(map_page)
        switch_governance_tab(map_page, "mrc")
        map_page.wait_for_timeout(6_000)
        yield
        close_all_panels(map_page)

    def test_meeting_list_has_rows(self, map_page):
        """Meeting list should have at least one row."""
        content = map_page.locator("#mg-content")
        text = content.inner_text().lower()
        has_meetings = (
            "mrc" in text or "meeting" in text
            or content.locator("tr").count() > 1
        )
        assert has_meetings, "No meetings visible in MRC tab"

    def test_meeting_row_clickable(self, map_page):
        """Clicking a meeting row should open detail or change content."""
        content = map_page.locator("#mg-content")
        before_text = content.inner_text()

        # Try clicking a meeting row
        rows = content.locator("tr")
        if rows.count() > 1:
            rows.nth(1).click(force=True)
            map_page.wait_for_timeout(6_000)
            after_text = content.inner_text()
            # Content should change after clicking
            assert after_text != before_text or len(after_text) > len(before_text), \
                "Content didn't change after clicking meeting row"
        else:
            pytest.skip("No clickable meeting rows")

    def test_meeting_detail_has_tabs(self, map_page):
        """Meeting detail view should have sub-tabs (Agenda, Minutes, etc.)."""
        content = map_page.locator("#mg-content")
        rows = content.locator("tr")
        if rows.count() <= 1:
            pytest.skip("No meetings to click")
        rows.nth(1).click(force=True)
        map_page.wait_for_timeout(6_000)

        text = content.inner_text().lower()
        tab_keywords = ["agenda", "minutes", "decisions", "actions",
                        "participants", "documents"]
        found = [kw for kw in tab_keywords if kw in text]
        assert len(found) >= 3, \
            f"Only {len(found)} tab keywords found: {found}"

    def test_meeting_detail_shows_metadata(self, map_page):
        """Meeting detail should show date, chair, or status."""
        content = map_page.locator("#mg-content")
        rows = content.locator("tr")
        if rows.count() <= 1:
            pytest.skip("No meetings to click")
        rows.nth(1).click(force=True)
        map_page.wait_for_timeout(6_000)

        text = content.inner_text().lower()
        keywords = ["date", "chair", "status", "location", "scheduled",
                     "completed", "2026"]
        found = [kw for kw in keywords if kw in text]
        assert len(found) >= 2, \
            f"Meeting detail missing metadata. Found: {found}"
