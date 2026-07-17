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

"""
Governance e2e tests: MRC CRUD sub-routes — part 3.

Covers participants CRUD and meeting detail UI.
"""

import pytest

from tests.e2e.conftest import get_first_meeting_id
from tests.e2e.helpers import (
    close_all_panels,
    open_governance,
    switch_governance_tab,
)


# ---------------------------------------------------------------------------
# Participants CRUD API
# ---------------------------------------------------------------------------


class TestMRCParticipantsCRUD:
    """Participants CRUD via API."""

    def test_add_participant(self, map_page):
        """POST participant should auto-generate ID and save."""
        meeting_id = get_first_meeting_id(map_page)
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
        meeting_id = get_first_meeting_id(map_page)
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
        # Wait for MRC content to load (async fetch from /api/v1/governance/mrc)
        try:
            map_page.wait_for_function(
                "() => {"
                "  var c = document.getElementById('mg-content');"
                "  return c && (c.textContent.indexOf('meeting') !== -1"
                "    || c.textContent.indexOf('Meeting') !== -1"
                "    || c.textContent.indexOf('MRC') !== -1"
                "    || c.querySelector('tr') !== null);"
                "}",
                timeout=8_000,
            )
        except Exception:
            pass
        map_page.wait_for_timeout(1_000)
        yield
        close_all_panels(map_page)

    def _click_first_meeting_row(self, map_page):
        """Click first meeting row, wait for detail tabs to render."""
        content = map_page.locator("#mg-content")
        rows = content.locator("tr")
        if rows.count() <= 1:
            return False
        rows.nth(1).click(force=True)
        # Wait for the async fetch + render to complete: meeting detail
        # renders tab buttons with id="mrc-mtab-agenda" into #mrc-sub-content
        try:
            map_page.wait_for_selector(
                "#mrc-mtab-agenda", state="attached", timeout=10_000
            )
        except Exception:
            # Fallback: the fetch may have failed or content is different
            map_page.wait_for_timeout(2_000)
        return True

    def test_meeting_list_has_rows(self, map_page):
        """Meeting list should have at least one row."""
        content = map_page.locator("#mg-content")
        text = content.inner_text(timeout=10_000).lower()
        has_meetings = (
            "mrc" in text or "meeting" in text
            or content.locator("tr").count() > 1
        )
        assert has_meetings, "No meetings visible in MRC tab"

    def test_meeting_row_clickable(self, map_page):
        """Clicking a meeting row should open detail or change content."""
        content = map_page.locator("#mg-content")
        before_text = content.inner_text(timeout=10_000)
        if not self._click_first_meeting_row(map_page):
            pytest.skip("No clickable meeting rows")
        # Allow extra time for async fetch + render of meeting detail
        map_page.wait_for_timeout(3_000)
        after_text = content.inner_text(timeout=10_000)
        assert after_text != before_text or len(after_text) > len(before_text), \
            "Content didn't change after clicking meeting row"

    def test_meeting_detail_has_tabs(self, map_page):
        """Meeting detail view should have sub-tabs (Agenda, Minutes, etc.)."""
        if not self._click_first_meeting_row(map_page):
            pytest.skip("No meetings to click")
        text = map_page.locator("#mg-content").inner_text(timeout=10_000).lower()
        tab_keywords = ["agenda", "minutes", "decisions", "actions",
                        "participants", "documents"]
        found = [kw for kw in tab_keywords if kw in text]
        assert len(found) >= 3, \
            f"Only {len(found)} tab keywords found: {found}"

    def test_meeting_detail_shows_metadata(self, map_page):
        """Meeting detail should show date, chair, or status."""
        if not self._click_first_meeting_row(map_page):
            pytest.skip("No meetings to click")
        text = map_page.locator("#mg-content").inner_text(timeout=10_000).lower()
        keywords = ["date", "chair", "status", "location", "scheduled",
                     "completed", "2026"]
        found = [kw for kw in keywords if kw in text]
        assert len(found) >= 2, \
            f"Meeting detail missing metadata. Found: {found}"
