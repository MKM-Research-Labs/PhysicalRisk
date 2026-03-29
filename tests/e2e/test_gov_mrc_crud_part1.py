# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

"""
Governance e2e tests: MRC CRUD sub-routes — part 1.

Covers meetings API (list, detail) and agenda CRUD.
"""

import pytest

from tests.e2e.conftest import get_first_meeting_id


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
        meeting_id = get_first_meeting_id(map_page)
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
        meeting_id = get_first_meeting_id(map_page)
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
        meeting_id = get_first_meeting_id(map_page)
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
