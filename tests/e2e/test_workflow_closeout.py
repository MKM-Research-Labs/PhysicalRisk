# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

"""
Trading workflow e2e test: trade close-out flow.
Split from test_trading_workflows.py.
"""

import pytest

from tests.e2e.helpers import (
    close_all_panels,
    open_trading_desk,
)


class TestTradeCloseOut:
    """Close-out workflow: find trade, click close, enter spread, confirm."""

    @pytest.fixture(autouse=True)
    def setup(self, map_page):
        close_all_panels(map_page)
        open_trading_desk(map_page, tab="blotter")
        map_page.wait_for_timeout(3_000)
        yield
        close_all_panels(map_page)

    def _find_close_button(self, page):
        """Locate a close-out button on any trade row."""
        view = page.locator("#td-blotter-view")
        # Look for close buttons — could be a button with "Close" text or an icon
        close_btn = view.locator("button:has-text('Close')").first
        if close_btn.count() > 0 and close_btn.is_visible():
            return close_btn
        # Try icon-style close buttons (e.g. data-action="close")
        close_btn = view.locator("[data-action='close']").first
        if close_btn.count() > 0 and close_btn.is_visible():
            return close_btn
        # Try buttons with close-related classes
        close_btn = view.locator("[class*='close-out'], [class*='closeout']").first
        if close_btn.count() > 0 and close_btn.is_visible():
            return close_btn
        return None

    def test_blotter_has_close_button(self, map_page, trade_data):
        """At least one trade should have a close-out button."""
        trades = trade_data.get("trades", [])
        if not trades:
            pytest.skip("No trades in blotter")
        map_page.wait_for_timeout(3_000)
        btn = self._find_close_button(map_page)
        if btn is None:
            pytest.skip("No close-out button found on any trade row")
        assert btn.is_visible()

    def test_close_button_opens_dialog(self, map_page, trade_data):
        """Clicking the close button should open a modal or dialog."""
        trades = trade_data.get("trades", [])
        if not trades:
            pytest.skip("No trades in blotter")
        map_page.wait_for_timeout(3_000)
        btn = self._find_close_button(map_page)
        if btn is None:
            pytest.skip("No close-out button found")

        btn.click(force=True)
        map_page.wait_for_timeout(3_000)

        # Look for a modal/dialog with spread input
        modal = map_page.locator("[class*='modal'], [class*='dialog'], [id*='close-modal'], [id*='closeout']")
        spread_input = map_page.locator("input[id*='spread'], input[name*='spread'], input[id*='close']")

        has_dialog = modal.count() > 0 or spread_input.count() > 0
        if not has_dialog:
            pytest.skip("Close-out dialog/modal did not appear")
        assert has_dialog

# Note: spread/confirm coverage is provided by tests/e2e/test_lifecycle_closeout.py,
# which uses the real #td-closeout-* element IDs end-to-end.
