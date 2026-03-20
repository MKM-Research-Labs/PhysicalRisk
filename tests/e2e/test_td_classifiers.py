# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

"""
Trading Desk — Classifiers tab (Tab 9) e2e tests.

Verifies that the tab opens, summary table loads, and UI elements render.
Does NOT trigger actual classifier training (takes minutes per gauge).
"""

import pytest


# ---------------------------------------------------------------------------
# Helpers (same pattern as test_td_tabs.py)
# ---------------------------------------------------------------------------

PANEL_IDS_TO_CLOSE = [
    "trading-desk-panel",
    "hazard-curve-panel",
    "property-hc-panel",
    "prop-storm-panel",
    "mortgage-detail-panel",
    "mg-panel",
]

CLOSE_PANELS_JS = """() => {
    %s.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.style.display = 'none';
    });
    document.querySelectorAll('.ctx-menu').forEach(m => m.remove());
}""" % str(PANEL_IDS_TO_CLOSE).replace("'", '"')


def _close_all_panels(page):
    page.evaluate(CLOSE_PANELS_JS)


def _open_trading_desk(page):
    pi_btn = page.locator("text=\u03a0").first
    pi_btn.click()
    page.locator("#trading-desk-panel").wait_for(
        state="visible", timeout=5_000
    )


def _close_trading_desk(page):
    panel = page.locator("#trading-desk-panel")
    if panel.is_visible():
        close_btn = panel.locator("text=\u00d7").first
        if close_btn.is_visible():
            close_btn.click()


# ---------------------------------------------------------------------------
# Classifiers tab
# ---------------------------------------------------------------------------


class TestClassifiersTab:
    """Classifiers tab (Tab 9) renders and loads data."""

    @pytest.fixture(autouse=True)
    def open_classifiers_tab(self, map_page):
        _close_all_panels(map_page)
        _open_trading_desk(map_page)
        map_page.locator("#td-tab-classifiers").click(force=True)
        map_page.wait_for_timeout(1000)
        yield
        _close_trading_desk(map_page)

    def test_classifiers_view_visible(self, map_page):
        """Classifiers content area should be visible after clicking the tab."""
        view = map_page.locator("#td-classifiers-view")
        assert view.count() > 0, "No #td-classifiers-view element found"
        assert view.is_visible(), "#td-classifiers-view is not visible"

    def test_has_train_all_button(self, map_page):
        """Top bar should contain the Train All button."""
        btn = map_page.locator("#cl-train-all-btn")
        assert btn.count() > 0, "No #cl-train-all-btn found"
        assert btn.is_visible(), "Train All button is not visible"

    def test_has_summary_stats(self, map_page):
        """Top bar should show summary stats (X/Y trained)."""
        stats = map_page.locator("#cl-summary-stats")
        assert stats.count() > 0, "No #cl-summary-stats found"
        text = stats.inner_text()
        assert "trained" in text.lower(), (
            f"Expected 'trained' in stats, got: {text}"
        )

    def test_has_table_pane(self, map_page):
        """Left pane should contain the summary table."""
        pane = map_page.locator("#cl-table-pane")
        assert pane.count() > 0, "No #cl-table-pane found"
        # Should have a table with gauge rows (or a loading message)
        tables = pane.locator("table")
        text = pane.inner_text().lower()
        assert tables.count() > 0 or "gauge" in text or "no gauges" in text, (
            "No table or gauge content in table pane"
        )

    def test_has_detail_pane(self, map_page):
        """Right pane should exist (shows placeholder until gauge selected)."""
        pane = map_page.locator("#cl-detail-pane")
        assert pane.count() > 0, "No #cl-detail-pane found"

    def test_summary_table_has_rows(self, map_page):
        """Summary table should have at least one gauge row."""
        pane = map_page.locator("#cl-table-pane")
        rows = pane.locator("tr[data-gauge-id]")
        # Wait a bit for data to load
        map_page.wait_for_timeout(2000)
        rows = pane.locator("tr[data-gauge-id]")
        assert rows.count() > 0, "No gauge rows in summary table"

    def test_table_has_action_buttons(self, map_page):
        """Each gauge row should have a Train/Retrain button."""
        map_page.wait_for_timeout(2000)
        pane = map_page.locator("#cl-table-pane")
        btns = pane.locator("button[data-train-gauge]")
        assert btns.count() > 0, "No train/retrain buttons found"

    def test_row_click_populates_detail(self, map_page):
        """Clicking a gauge row should populate the detail panel."""
        map_page.wait_for_timeout(2000)
        pane = map_page.locator("#cl-table-pane")
        rows = pane.locator("tr[data-gauge-id]")
        if rows.count() > 0:
            rows.first.click()
            map_page.wait_for_timeout(500)
            detail = map_page.locator("#cl-detail-pane")
            text = detail.inner_text()
            # Should show gauge name or "Train Now" or metrics
            assert len(text.strip()) > 30, (
                f"Detail pane still empty after row click: {text[:100]}"
            )

    def test_progress_bar_hidden_initially(self, map_page):
        """Progress bar should be hidden when no batch training is running."""
        wrap = map_page.locator("#cl-progress-wrap")
        assert wrap.count() > 0, "No #cl-progress-wrap found"
        assert not wrap.is_visible(), "Progress bar should be hidden initially"
