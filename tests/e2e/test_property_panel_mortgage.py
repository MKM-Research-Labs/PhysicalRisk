# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

"""
Property panel e2e tests — mortgage detail.
"""

import pytest


class TestMortgageDetail:
    """Mortgage detail panel tests."""

    def _open_mortgage_panel(self, map_page, prop_id):
        """Try to open mortgage detail via available functions."""
        # Try viewMortgageDetail
        has_fn = map_page.evaluate(
            "() => typeof window.viewMortgageDetail === 'function'"
        )
        if has_fn:
            map_page.evaluate(f"window.viewMortgageDetail('{prop_id}')")
            map_page.wait_for_timeout(3_000)
            return True

        # Try opening property storms first, then switching to mortgage tab
        has_storms = map_page.evaluate(
            "() => typeof window.viewPropertyStorms === 'function'"
        )
        if has_storms:
            map_page.evaluate(f"window.viewPropertyStorms('{prop_id}')")
            map_page.wait_for_timeout(3_000)
            # Click mortgage impact tab (idx 3)
            tab = map_page.locator(".prop-storm-tab[data-idx='3']")
            if tab.count() > 0:
                tab.click()
                map_page.wait_for_timeout(3_000)
                return True

        return False

    def test_mortgage_panel_opens(self, map_page, first_property_id):
        """Mortgage detail panel should open."""
        opened = self._open_mortgage_panel(map_page, first_property_id)
        if not opened:
            pytest.skip("No mortgage detail function available")

        # Check for dedicated mortgage panel or content within storm panel
        mortgage_panel = map_page.locator("#mortgage-detail-panel")
        storm_panel = map_page.locator("#prop-storm-panel")

        panel_visible = (
            (mortgage_panel.count() > 0 and mortgage_panel.is_visible())
            or (storm_panel.count() > 0 and storm_panel.is_visible())
        )
        assert panel_visible, "Neither mortgage panel nor storm panel is visible"

    def test_mortgage_content_shows_data(self, map_page, first_property_id):
        """Mortgage content should show LTV, amortisation, or loan data."""
        opened = self._open_mortgage_panel(map_page, first_property_id)
        if not opened:
            pytest.skip("No mortgage detail function available")

        # Check both possible containers
        mortgage_panel = map_page.locator("#mortgage-detail-panel")
        content_el = map_page.locator("#prop-storm-content")

        text = ""
        if mortgage_panel.count() > 0 and mortgage_panel.is_visible():
            text = mortgage_panel.inner_text()
        elif content_el.count() > 0:
            text = content_el.inner_text()

        has_mortgage_data = (
            "ltv" in text.lower()
            or "loan" in text.lower()
            or "amortis" in text.lower()
            or "mortgage" in text.lower()
            or "principal" in text.lower()
            or "balance" in text.lower()
        )
        assert has_mortgage_data, f"No mortgage data found in panel content: '{text[:200]}'"
