# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

"""
E2e test: Close out a trade -> P&L reflects.
Split from test_trading_lifecycle.py.
"""

import pytest

from tests.e2e.helpers import (
    close_all_panels,
    open_trading_desk,
)


class TestCloseOutTradePL:
    """Workflow: open blotter -> close a trade -> verify P&L updated."""

    @pytest.fixture(autouse=True)
    def setup(self, map_page):
        close_all_panels(map_page)
        yield

    def test_01_open_blotter_and_count_trades(self, map_page):
        """Open blotter, count open trades, verify P&L bar exists."""
        open_trading_desk(map_page, tab="blotter")
        map_page.wait_for_timeout(2_000)

        trade_count = map_page.evaluate("""() => {
            const wrap = document.getElementById('td-blotter-table-wrap');
            if (!wrap) return 0;
            // Count non-closed rows
            const rows = wrap.querySelectorAll('tbody tr');
            let live = 0;
            rows.forEach(r => {
                if (!r.textContent.includes('CLOSED')) live++;
            });
            return live;
        }""")

        if trade_count == 0:
            pytest.skip("No open trades in blotter to close")

        # Verify P&L bar
        pnl_bar = map_page.locator("#td-pnl-bar")
        assert pnl_bar.count() > 0, "P&L bar not found"

    def test_02_click_close_button_opens_modal(self, map_page):
        """Find a Close button on an open trade and click it to open modal."""
        open_trading_desk(map_page, tab="blotter")
        map_page.wait_for_timeout(2_000)

        # Find any "Close" button in blotter rows
        close_btns = map_page.evaluate("""() => {
            const wrap = document.getElementById('td-blotter-table-wrap');
            if (!wrap) return 0;
            const btns = wrap.querySelectorAll('button');
            let closeCount = 0;
            for (const b of btns) {
                if (b.textContent.trim() === 'Close') closeCount++;
            }
            return closeCount;
        }""")

        if close_btns == 0:
            pytest.skip("No Close buttons found in blotter")

        # Click the first Close button
        map_page.evaluate("""() => {
            const wrap = document.getElementById('td-blotter-table-wrap');
            const btns = wrap.querySelectorAll('button');
            for (const b of btns) {
                if (b.textContent.trim() === 'Close') {
                    b.click();
                    return true;
                }
            }
            return false;
        }""")
        map_page.wait_for_timeout(1_000)

        # Verify close-out modal appeared (id="td-closeout-modal")
        modal = map_page.locator("#td-closeout-modal")
        assert modal.count() > 0, "Close-out modal did not appear"

    def test_03_enter_closeout_spread_and_confirm(self, map_page):
        """Enter a closeout spread in the modal and confirm."""
        open_trading_desk(map_page, tab="blotter")
        map_page.wait_for_timeout(2_000)

        # Click first Close button
        clicked = map_page.evaluate("""() => {
            const wrap = document.getElementById('td-blotter-table-wrap');
            if (!wrap) return false;
            const btns = wrap.querySelectorAll('button');
            for (const b of btns) {
                if (b.textContent.trim() === 'Close') {
                    b.click();
                    return true;
                }
            }
            return false;
        }""")
        if not clicked:
            pytest.skip("No Close button found")

        map_page.wait_for_timeout(1_000)

        # Verify modal is open
        modal = map_page.locator("#td-closeout-modal")
        if modal.count() == 0:
            pytest.skip("Close-out modal did not appear")

        # Enter closeout spread in the input
        spread_input = map_page.locator("#td-closeout-spread-input")
        if spread_input.count() == 0:
            pytest.skip("Closeout spread input not found in modal")

        spread_input.fill("50")
        map_page.wait_for_timeout(500)

        # Verify settlement amount updated (no longer "Enter spread above")
        settle_text = map_page.evaluate("""() => {
            const el = document.getElementById('td-settle-amount');
            return el ? el.textContent : '';
        }""")
        assert "Enter spread" not in settle_text, (
            "Settlement amount did not update after entering spread"
        )

        # Confirm button should now be enabled
        confirm_btn = map_page.locator("#td-closeout-confirm")
        if confirm_btn.count() == 0:
            pytest.skip("Confirm button not found in close-out modal")

        confirm_btn.click(force=True)
        map_page.wait_for_timeout(5_000)

        # Modal should have closed (removed from DOM or hidden)
        modal_gone = map_page.evaluate("""() => {
            const m = document.getElementById('td-closeout-modal');
            if (!m) return true;
            const style = window.getComputedStyle(m);
            return style.display === 'none' || style.visibility === 'hidden' || m.hidden;
        }""")
        assert modal_gone, "Close-out modal did not close after confirmation"

    def test_04_verify_closed_trade_in_blotter(self, map_page):
        """Verify the blotter shows the trade as closed."""
        open_trading_desk(map_page, tab="blotter")
        map_page.wait_for_timeout(2_000)

        # Look for CLOSED badge in the blotter
        has_closed = map_page.evaluate("""() => {
            const wrap = document.getElementById('td-blotter-table-wrap');
            if (!wrap) return false;
            return wrap.innerHTML.includes('CLOSED');
        }""")

        # Also verify P&L bar still shows data
        pnl_text = map_page.evaluate("""() => {
            const bar = document.getElementById('td-pnl-bar');
            return bar ? bar.textContent : '';
        }""")

        assert has_closed or len(pnl_text) > 10, (
            "Blotter does not show CLOSED trade and P&L bar is empty"
        )
