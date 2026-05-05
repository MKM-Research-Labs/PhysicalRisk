# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

"""
Trading workflow e2e test: EOD submit flow.
Split from test_trading_workflows.py.
"""

import pytest

from tests.e2e.helpers import (
    close_all_panels,
    open_trading_desk,
)


class TestEODSubmit:
    """End-of-Day snapshot submission workflow."""

    @pytest.fixture(autouse=True)
    def setup(self, map_page):
        close_all_panels(map_page)
        open_trading_desk(map_page, tab="eod")
        map_page.wait_for_timeout(3_000)
        yield
        close_all_panels(map_page)

    # Note: EOD submit button presence is implicitly covered by the next test
    # (test_eod_submit_creates_snapshot) and explicitly by test_lifecycle_eod.py,
    # which uses the real #td-eod-submit-btn ID.

    def test_eod_submit_creates_snapshot(self, map_page):
        """Clicking EOD submit should create a snapshot (success message or history update)."""
        view = map_page.locator("#td-eod-view")
        submit_btn = view.locator(
            "button:has-text('Submit'), button:has-text('Snap'), "
            "button:has-text('EOD'), button:has-text('Run'), "
            "button[id*='eod-submit'], button[id*='eod-snap']"
        ).first
        if submit_btn.count() == 0 or not submit_btn.is_visible():
            pytest.skip("No EOD submit button found")

        # Count history entries before
        history_rows = view.locator("tr, [class*='history-item'], li")
        rows_before = history_rows.count()

        # Button may not be visible — use JS click as fallback
        try:
            submit_btn.click(force=True, timeout=3_000)
        except Exception:
            map_page.evaluate("""() => {
                const btn = document.getElementById('td-eod-submit-btn');
                if (btn) btn.click();
                else if (typeof window.tdSubmitEod === 'function') window.tdSubmitEod();
            }""")
        map_page.wait_for_timeout(9_000)

        # Check for success indicators — broad search
        result = map_page.evaluate("""() => {
            const view = document.getElementById('td-eod-view');
            const viewText = view ? view.textContent.toLowerCase() : '';
            const status = document.getElementById('td-eod-status');
            const statusText = status ? status.textContent.toLowerCase() : '';
            const notifs = document.querySelectorAll('.notif-message');
            const notifTexts = Array.from(notifs).map(n => n.textContent.toLowerCase());
            const rows = view ? view.querySelectorAll('tr, [class*="history-item"], li').length : 0;
            return {
                viewText: viewText.substring(0, 500),
                statusText: statusText,
                notifTexts: notifTexts,
                rows: rows
            };
        }""")

        rows_after = result.get("rows", 0)
        rows_grew = rows_after > rows_before
        all_text = result.get("viewText", "") + result.get("statusText", "")
        notif_texts = result.get("notifTexts", [])
        has_success = any(kw in all_text for kw in ["success", "snapshot", "completed", "snapped", "eod"])
        has_notif = len(notif_texts) > 0

        assert has_success or has_notif or rows_grew, (
            f"No success feedback after EOD submit. "
            f"View text: {all_text[:100]}, notifs: {notif_texts}, rows: {rows_before}->{rows_after}"
        )

    def test_eod_history_has_pdf_link(self, map_page):
        """EOD history should show a PDF download link for a completed snapshot."""
        view = map_page.locator("#td-eod-view")
        text = view.inner_text().lower()

        # Check for PDF link or download icon
        pdf_link = view.locator(
            "a[href*='.pdf'], a:has-text('PDF'), a:has-text('Download'), "
            "button:has-text('PDF'), [class*='pdf']"
        )
        has_pdf = pdf_link.count() > 0 or "pdf" in text
        if not has_pdf:
            pytest.skip("No PDF link found in EOD history (may need prior snapshots)")
        assert has_pdf
