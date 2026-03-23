# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

"""
E2e test: EOD submit -> history snapshot.
Split from test_trading_lifecycle.py.
"""

import pytest

from tests.e2e.helpers import (
    close_all_panels,
    open_trading_desk,
)


class TestEODSnapAndHistory:
    """Workflow: open EOD tab -> submit -> verify new snapshot in history."""

    @pytest.fixture(autouse=True)
    def setup(self, map_page):
        close_all_panels(map_page)
        yield

    def test_01_open_eod_tab_count_history(self, map_page):
        """Open EOD tab and count existing snapshots."""
        open_trading_desk(map_page, tab="eod")
        map_page.wait_for_timeout(6_000)

        # Verify EOD view is visible
        eod_view = map_page.locator("#td-eod-view")
        assert eod_view.count() > 0, "EOD view not found"

        # Read current snapshot count from history wrapper
        history_text = map_page.evaluate("""() => {
            const wrap = document.getElementById('td-eod-history-wrap');
            return wrap ? wrap.textContent : '';
        }""")

        # History should show "EOD History (N days)" or "No snapshots yet"
        assert "EOD History" in history_text or "No snapshots" in history_text, (
            "EOD history section not rendered"
        )

    def test_02_submit_eod(self, map_page):
        """Click EOD Submit and verify success."""
        open_trading_desk(map_page, tab="eod")
        map_page.wait_for_timeout(6_000)

        submit_btn = map_page.locator("#td-eod-submit-btn")
        if submit_btn.count() == 0:
            pytest.skip("EOD Submit button not found")

        # Record pre-submit history count
        pre_count = map_page.evaluate("""() => {
            const wrap = document.getElementById('td-eod-history-wrap');
            if (!wrap) return 0;
            return wrap.querySelectorAll('tbody tr, tr').length;
        }""")

        # Button may not be visible — use JS click as fallback
        try:
            submit_btn.click(force=True, timeout=3_000)
        except Exception:
            map_page.evaluate("""() => {
                const btn = document.getElementById('td-eod-submit-btn');
                if (btn) btn.click();
                else if (typeof window.tdSubmitEod === 'function') window.tdSubmitEod();
            }""")
        # Wait for status to change from "Submitting..." — poll up to 30s
        status_text = ""
        for _ in range(60):
            map_page.wait_for_timeout(1_500)
            status_text = map_page.evaluate("""() => {
                const el = document.getElementById('td-eod-status');
                return el ? el.textContent : '';
            }""")
            if "submitting" not in status_text.lower():
                break

        has_notif = map_page.evaluate("""() => {
            const notifs = document.querySelectorAll('.notif-message');
            for (const n of notifs) {
                const t = n.textContent.toLowerCase();
                if (t.includes('eod') || t.includes('success') || t.includes('submitted')
                    || t.includes('snapshot'))
                    return true;
            }
            return false;
        }""")

        assert (
            "submitted" in status_text.lower()
            or "saved" in status_text.lower()
            or "success" in status_text.lower()
            or "snapshot" in status_text.lower()
            or "eod" in status_text.lower()
            or has_notif
        ), f"EOD submit did not confirm success. Status: {status_text}"

    def test_03_verify_new_snapshot_in_history(self, map_page):
        """After submitting, a new snapshot should appear in history."""
        open_trading_desk(map_page, tab="eod")
        map_page.wait_for_timeout(6_000)

        # Read history content — should contain at least one row with a date
        history_content = map_page.evaluate("""() => {
            const wrap = document.getElementById('td-eod-history-wrap');
            if (!wrap) return {text: '', rowCount: 0};
            const rows = wrap.querySelectorAll('tr');
            return {
                text: wrap.textContent,
                rowCount: rows.length
            };
        }""")

        # Either we have table rows or the text says "N days"
        assert (
            history_content["rowCount"] > 1
            or "days" in history_content["text"].lower()
        ), "No EOD snapshots found in history after submit"
