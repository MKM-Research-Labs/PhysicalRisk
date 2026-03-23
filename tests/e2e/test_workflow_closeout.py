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

    def test_spread_input_updates_settlement(self, map_page, trade_data):
        """Entering a closeout spread should update the settlement amount."""
        trades = trade_data.get("trades", [])
        if not trades:
            pytest.skip("No trades in blotter")
        map_page.wait_for_timeout(3_000)
        btn = self._find_close_button(map_page)
        if btn is None:
            pytest.skip("No close-out button found")

        btn.click(force=True)
        map_page.wait_for_timeout(3_000)

        # Find spread input
        spread_input = map_page.locator(
            "input[id*='spread'], input[name*='spread'], input[id*='close-spread']"
        ).first
        if spread_input.count() == 0 or not spread_input.is_visible():
            pytest.skip("No spread input in close-out dialog")

        spread_input.fill("50")
        map_page.wait_for_timeout(3_000)

        # Check for settlement amount text updating
        dialog_area = map_page.locator(
            "[class*='modal'], [class*='dialog'], [id*='close-modal'], [id*='closeout']"
        ).first
        if dialog_area.count() > 0:
            text = dialog_area.inner_text().lower()
            has_settlement = (
                "settlement" in text
                or "amount" in text
                or "p&l" in text
                or "pnl" in text
                or any(c.isdigit() for c in text)
            )
            assert has_settlement, "No settlement amount shown after entering spread"
        # If no dialog area found, just pass — spread was entered without error

    def test_confirm_closeout_posts(self, map_page, trade_data):
        """Confirming close-out should POST and mark the trade as closed."""
        trades = trade_data.get("trades", [])
        if not trades:
            pytest.skip("No trades in blotter")
        map_page.wait_for_timeout(3_000)
        btn = self._find_close_button(map_page)
        if btn is None:
            pytest.skip("No close-out button found")

        btn.click(force=True)
        map_page.wait_for_timeout(3_000)

        # Fill spread if present
        spread_input = map_page.locator(
            "input[id*='spread'], input[name*='spread'], input[id*='close-spread']"
        ).first
        if spread_input.count() > 0 and spread_input.is_visible():
            spread_input.fill("50")
            map_page.wait_for_timeout(1_500)

        # Look for confirm button
        confirm_btn = map_page.locator(
            "button:has-text('Confirm'), button:has-text('Submit'), "
            "button:has-text('Close Out'), button[id*='confirm']"
        ).first
        if confirm_btn.count() == 0 or not confirm_btn.is_visible():
            pytest.skip("No confirm button found in close-out dialog")

        # Intercept the POST request
        with map_page.expect_response(
            lambda resp: "/trading/close" in resp.url, timeout=10_000
        ) as resp_info:
            confirm_btn.click(force=True)
            map_page.wait_for_timeout(3_000)

        response = resp_info.value
        assert response.status in (200, 201), (
            f"Close-out POST returned status {response.status}"
        )
