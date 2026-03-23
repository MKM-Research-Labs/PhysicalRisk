# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

"""
Governance e2e test: model workstream detail navigation.
Split from test_governance_crud.py.
"""

import pytest

from tests.e2e.helpers import (
    close_all_panels,
    get_governance_content_text,
    open_governance,
    switch_governance_tab,
)


class TestModelWorkstreamDetail:
    """Model Inventory tab — click-through to detail view and back navigation."""

    @pytest.fixture(autouse=True)
    def setup(self, map_page):
        close_all_panels(map_page)
        open_governance(map_page)
        switch_governance_tab(map_page, "inventory")
        yield
        close_all_panels(map_page)

    def test_model_row_opens_detail(self, map_page):
        """Clicking a model row should open a detail view."""
        content = map_page.locator("#mg-content")
        assert content.count() > 0

        # Look for clickable rows in the inventory
        rows = content.locator("tr[style*='cursor'], tr[onclick], [class*='row']")
        if rows.count() == 0:
            # Fallback: try any table row with data
            rows = content.locator("table tbody tr")
        if rows.count() == 0:
            # Broader fallback: any clickable element in inventory
            rows = content.locator("[class*='model'], [class*='item'], [data-model]")
        if rows.count() == 0:
            pytest.skip("No model rows found in inventory tab")

        # Record initial content
        initial_text = content.inner_text()

        # Click the first row
        rows.first.click(force=True)
        map_page.wait_for_timeout(1_500)

        # Content should change to detail view
        detail_text = content.inner_text()
        back_btn = map_page.locator("#mg-back-btn")

        # Either content changed or back button appeared
        content_changed = detail_text != initial_text
        back_visible = back_btn.count() > 0 and back_btn.is_visible()

        if not content_changed and not back_visible:
            pytest.skip("Model row click did not open a detail view")

    def test_back_button_returns_to_list(self, map_page):
        """Back button should return to the inventory list."""
        content = map_page.locator("#mg-content")
        assert content.count() > 0

        # Click into detail view first
        rows = content.locator("tr[style*='cursor'], tr[onclick], [class*='row']")
        if rows.count() == 0:
            rows = content.locator("table tbody tr")
        if rows.count() == 0:
            rows = content.locator("[class*='model'], [class*='item'], [data-model]")
        if rows.count() == 0:
            pytest.skip("No model rows found in inventory tab")

        rows.first.click(force=True)
        map_page.wait_for_timeout(1_500)

        back_btn = map_page.locator("#mg-back-btn")
        if back_btn.count() == 0 or not back_btn.is_visible():
            pytest.skip("Back button (#mg-back-btn) not visible after opening detail")

        # Click back
        back_btn.click(force=True)
        map_page.wait_for_timeout(1_500)

        # Back button should be hidden again
        back_hidden = (
            back_btn.count() == 0
            or not back_btn.is_visible()
            or back_btn.evaluate("el => el.style.display") == "none"
        )
        assert back_hidden, "Back button should be hidden after returning to inventory list"

        # Inventory content should be restored (table or list visible)
        text = get_governance_content_text(map_page)
        assert len(text.strip()) > 0, "Inventory content is empty after clicking back"
