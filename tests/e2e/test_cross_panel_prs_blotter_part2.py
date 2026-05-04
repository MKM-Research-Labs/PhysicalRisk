# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

"""
Cross-panel e2e tests: PRS pricer ↔ blotter ↔ storm scenarios.

Tests the connected user journeys that a client demo would follow:
- Gauge PRS commit → blotter shows trade → blotter button active
- Property storm scenarios → PRS Pricing tab → gauge PRS opens
- Nav menu → gauge PRS → commit → nav menu → blotter shows trade
- Storm scenarios tabs remain consistent when flipping between them
"""

import pytest

from tests.e2e.helpers import (
    close_all_panels,
    close_gauge_panel,
    open_gauge_panel,
    switch_gauge_tab,
)


CLOSE_ALL_JS = """() => {
    ['trading-desk-panel', 'hazard-curve-panel', 'property-hc-panel',
     'prop-storm-panel', 'mortgage-detail-panel'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.style.display = 'none';
    });
}"""


class TestPropertyStormToPRS:
    """Property storm scenarios → PRS Pricing tab → PRS pricer opens."""

    def _open_storm_panel(self, map_page, prop_id):
        has_fn = map_page.evaluate(
            "() => typeof window.viewPropertyStorms === 'function'"
        )
        if not has_fn:
            pytest.skip("viewPropertyStorms not available")
        map_page.evaluate(f"window.viewPropertyStorms('{prop_id}')")
        map_page.wait_for_timeout(4_000)

    def test_01_storm_panel_has_prs_tab(self, map_page, first_property_id):
        """Storm panel should have PRS Pricing action tab."""
        self._open_storm_panel(map_page, first_property_id)
        tab = map_page.locator(".prop-storm-tab[data-idx='6']")
        assert tab.count() > 0, "PRS Pricing tab (idx 6) not found"
        text = tab.inner_text().lower()
        assert "prs" in text, f"Tab doesn't mention PRS: '{text}'"
        map_page.evaluate(CLOSE_ALL_JS)

    def test_02_prs_tab_opens_property_hazard_panel(self, map_page, first_property_id):
        """Clicking PRS Pricing tab should open the property hazard panel."""
        self._open_storm_panel(map_page, first_property_id)

        tab = map_page.locator(".prop-storm-tab[data-idx='6']")
        if tab.count() == 0:
            pytest.skip("PRS Pricing tab not found")
        tab.click()
        map_page.wait_for_timeout(5_000)

        phc = map_page.locator("#property-hc-panel")
        assert phc.count() > 0 and phc.is_visible(), (
            "Property hazard panel not visible after clicking PRS Pricing tab"
        )
        map_page.evaluate(CLOSE_ALL_JS)

    def test_03_storm_flood_history_click_opens_timeline(self, map_page, first_property_id):
        """Clicking a storm in Flood History should open Flood Timeline."""
        self._open_storm_panel(map_page, first_property_id)

        # Switch to Flood History tab (idx 3)
        hist_tab = map_page.locator(".prop-storm-tab[data-idx='3']")
        if hist_tab.count() == 0:
            pytest.skip("Flood History tab not found")
        hist_tab.click()
        map_page.wait_for_timeout(3_000)

        # Click first table row
        row = map_page.locator("#prop-storm-content table tr").nth(1)
        if row.count() == 0:
            pytest.skip("No flood history rows")
        row.click()
        map_page.wait_for_timeout(3_000)

        # Should now be on Flood Timeline (idx 1)
        timeline_chart = map_page.locator("#prop-timeline-chart")
        timeline_select = map_page.locator("#prop-timeline-select")
        has_timeline = timeline_chart.count() > 0 or timeline_select.count() > 0
        assert has_timeline, "Flood Timeline not shown after clicking storm row"

        map_page.evaluate(CLOSE_ALL_JS)


class TestStormScenarioTabConsistency:
    """Storm scenario tabs should show consistent data when switching."""

    def _open_storm_panel(self, map_page, prop_id):
        has_fn = map_page.evaluate(
            "() => typeof window.viewPropertyStorms === 'function'"
        )
        if not has_fn:
            pytest.skip("viewPropertyStorms not available")
        map_page.evaluate(f"window.viewPropertyStorms('{prop_id}')")
        map_page.wait_for_timeout(4_000)

    def test_distribution_and_history_show_same_flood_count(self, map_page, first_property_id):
        """Distribution and Flood History must show the same number of floods."""
        self._open_storm_panel(map_page, first_property_id)

        # Distribution tab (idx 0) — count events
        map_page.locator(".prop-storm-tab[data-idx='0']").click()
        map_page.wait_for_timeout(2_000)
        dist_count = map_page.evaluate("""() => {
            var stats = document.getElementById('prop-dist-stats');
            if (!stats) return null;
            var match = stats.textContent.match(/Events:\\s*(\\d+)/);
            return match ? parseInt(match[1]) : null;
        }""")

        # Flood History tab (idx 3) — count rows
        map_page.locator(".prop-storm-tab[data-idx='3']").click()
        map_page.wait_for_timeout(2_000)
        hist_count = map_page.evaluate("""() => {
            var stats = document.getElementById('prop-history-stats');
            if (!stats) return null;
            var match = stats.textContent.match(/Floods:\\s*(\\d+)/);
            return match ? parseInt(match[1]) : null;
        }""")

        if dist_count is None or hist_count is None:
            pytest.skip("Could not extract flood counts from stats")

        assert dist_count == hist_count, (
            f"Distribution shows {dist_count} events but "
            f"Flood History shows {hist_count} floods"
        )

        map_page.evaluate(CLOSE_ALL_JS)

    def test_header_flood_count_matches_history(self, map_page, first_property_id):
        """Header 'N property floods' must match Flood History event count."""
        self._open_storm_panel(map_page, first_property_id)

        header_count = map_page.evaluate("""() => {
            var status = document.getElementById('prop-storm-status');
            if (!status) return null;
            var match = status.textContent.match(/(\\d+)\\s*property flood/);
            return match ? parseInt(match[1]) : null;
        }""")

        # Flood History count
        map_page.locator(".prop-storm-tab[data-idx='3']").click()
        map_page.wait_for_timeout(2_000)
        hist_count = map_page.evaluate("""() => {
            var stats = document.getElementById('prop-history-stats');
            if (!stats) return null;
            var match = stats.textContent.match(/Floods:\\s*(\\d+)/);
            return match ? parseInt(match[1]) : null;
        }""")

        if header_count is None or hist_count is None:
            pytest.skip("Could not extract counts")

        assert header_count == hist_count, (
            f"Header says {header_count} property floods but "
            f"Flood History shows {hist_count}"
        )

        map_page.evaluate(CLOSE_ALL_JS)

    def test_worst_storms_are_subset_of_history(self, map_page, first_property_id):
        """Worst Storms top bars should all appear in Flood History."""
        self._open_storm_panel(map_page, first_property_id)

        # Get Worst Storms storm IDs (idx 2)
        map_page.locator(".prop-storm-tab[data-idx='2']").click()
        map_page.wait_for_timeout(2_000)
        worst_ids = map_page.evaluate("""() => {
            var chart = window.currentChart;
            if (!chart || !chart.data) return [];
            return chart.data.labels || [];
        }""")

        # Get Flood History storm IDs (idx 3)
        map_page.locator(".prop-storm-tab[data-idx='3']").click()
        map_page.wait_for_timeout(2_000)
        hist_ids = map_page.evaluate("""() => {
            var rows = document.querySelectorAll('#prop-storm-content table tr td:first-child');
            return Array.from(rows).map(td => td.textContent.trim());
        }""")

        if not worst_ids or not hist_ids:
            pytest.skip("Could not extract storm IDs")

        # Worst storms labels may be truncated — check prefix match
        for ws_id in worst_ids[:5]:
            found = any(h.startswith(ws_id) or ws_id.startswith(h) for h in hist_ids)
            assert found, (
                f"Worst storm '{ws_id}' not found in Flood History. "
                f"History has {len(hist_ids)} entries."
            )

        map_page.evaluate(CLOSE_ALL_JS)


class TestNavMenuToPanel:
    """Nav menu select → panel opens → correct gauge/property."""

    def _is_any_panel_visible(self, map_page, panel_ids):
        """Check if any of the given panel IDs is visible using computed style.

        Note: offsetParent is null for position:fixed elements, so we check
        offsetWidth/offsetHeight > 0 instead.
        """
        return map_page.evaluate("""(panelIds) => {
            return panelIds.some(id => {
                var el = document.getElementById(id);
                if (!el) return false;
                var cs = window.getComputedStyle(el);
                return cs.display !== 'none' && cs.visibility !== 'hidden'
                    && (el.offsetWidth > 0 || el.offsetHeight > 0);
            });
        }""", panel_ids)

    def test_nav_gauge_select_opens_panel(self, map_page):
        """Selecting a gauge from nav dropdown and clicking action opens panel."""
        map_page.wait_for_timeout(3_000)

        sel = map_page.locator("#nav-gauge-select")
        if sel.count() == 0:
            pytest.skip("No gauge select")
        options = sel.locator("option")
        if options.count() < 2:
            pytest.skip("No gauge options loaded")

        # Wait for backend handler AND panel module to be registered
        map_page.wait_for_function(
            "() => typeof window.viewHazardCurve === 'function'"
            " && window.GaugeHazardCurve"
            " && typeof window.GaugeHazardCurve.show === 'function'",
            timeout=10_000
        )

        # Select first real gauge
        sel.select_option(index=1)
        map_page.wait_for_timeout(1_000)

        buttons = map_page.locator("#nav-action-bar button")
        if buttons.count() == 0:
            pytest.skip("No action buttons appeared")
        # Click "Physical Risk Swap" (index 2) — opens hazard-curve-panel
        btn_idx = min(2, buttons.count() - 1)
        buttons.nth(btn_idx).click()
        map_page.wait_for_timeout(8_000)

        panels = ['hazard-curve-panel', 'prop-storm-panel',
                   'property-hc-panel', 'trading-desk-panel',
                   'gauge-pdf-panel', 'gauge-graph-panel']
        assert self._is_any_panel_visible(map_page, panels), \
            "No panel opened after nav menu action"

        map_page.evaluate(CLOSE_ALL_JS)

    def test_nav_property_select_opens_panel(self, map_page):
        """Selecting a property from nav dropdown and clicking action opens panel."""
        map_page.wait_for_timeout(3_000)

        sel = map_page.locator("#nav-prop-select")
        if sel.count() == 0:
            pytest.skip("No property select")
        options = sel.locator("option")
        if options.count() < 2:
            pytest.skip("No property options loaded")

        # Wait for backend handler functions to be registered
        map_page.wait_for_function(
            "() => typeof window.viewPropertyDetails === 'function'",
            timeout=10_000
        )

        sel.select_option(index=1)
        map_page.wait_for_timeout(500)

        buttons = map_page.locator("#nav-action-bar button")
        if buttons.count() == 0:
            pytest.skip("No action buttons appeared")
        # Click "Property Details" (index 0) — viewPropertyDetails
        buttons.first.click()
        map_page.wait_for_timeout(8_000)

        panels = ['hazard-curve-panel', 'prop-storm-panel',
                   'property-hc-panel', 'mortgage-detail-panel',
                   'gauge-pdf-panel', 'property-pdf-panel']
        # viewPropertyDetails opens a popup, not a panel — check for
        # info notification as an alternative success signal.
        popup_visible = map_page.evaluate("""() => {
            var popups = document.querySelectorAll('.leaflet-popup-content');
            return popups.length > 0;
        }""")
        panel_visible = self._is_any_panel_visible(map_page, panels)
        assert panel_visible or popup_visible, \
            "No panel or popup opened after nav menu action"

        map_page.evaluate(CLOSE_ALL_JS)
