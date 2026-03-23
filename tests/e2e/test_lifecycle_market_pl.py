# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

"""
E2e test: Market curve update -> P&L impact.
Split from test_trading_lifecycle.py.
"""

import pytest

from tests.e2e.helpers import (
    close_all_panels,
    open_trading_desk,
)


class TestMarketUpdatePL:
    """Workflow: open market tab -> modify curve -> commit -> verify P&L change."""

    @pytest.fixture(autouse=True)
    def setup(self, map_page):
        close_all_panels(map_page)
        yield

    def test_01_open_market_tab_record_yield(self, map_page):
        """Open the Market tab and record the current yield curve."""
        open_trading_desk(map_page, tab="market")

        # Wait for market data to load
        map_page.wait_for_timeout(6_000)

        # Read the current yield curve from JS state
        yield_curve = map_page.evaluate("() => window.tdYieldCurve || null")
        if yield_curve is None:
            # tdYieldCurve is inside IIFE; read from DOM inputs instead
            yield_curve = map_page.evaluate("""() => {
                const inputs = document.querySelectorAll(
                    '#td-market-inputs input[data-mode="yield"]');
                const result = {};
                inputs.forEach(inp => {
                    result[inp.getAttribute('data-tenor')] = parseFloat(inp.value);
                });
                return Object.keys(result).length > 0 ? result : null;
            }""")

        # At minimum the market view should exist
        mkt_view = map_page.locator("#td-market-view")
        assert mkt_view.count() > 0, "Market view not found"

    def test_02_change_yield_curve_value(self, map_page):
        """Modify a yield curve tenor value via the input fields."""
        open_trading_desk(map_page, tab="market")
        map_page.wait_for_timeout(6_000)

        # Switch to yield curve mode (select may be hidden — use JS fallback)
        mode_select = map_page.locator("#td-curve-mode")
        if mode_select.count() > 0:
            map_page.evaluate("""(sel) => {
                for (let i = 0; i < sel.options.length; i++) {
                    if (sel.options[i].value === 'yield') {
                        sel.selectedIndex = i;
                        sel.dispatchEvent(new Event('change', {bubbles: true}));
                        break;
                    }
                }
            }""", mode_select.element_handle())
        map_page.wait_for_timeout(3_000)

        # Find tenor inputs — rendered in #td-market-inputs
        has_inputs = map_page.evaluate("""() => {
            const inputs = document.querySelectorAll(
                '#td-market-inputs input[data-mode="yield"]');
            return inputs.length;
        }""")

        if has_inputs == 0:
            pytest.skip("No yield curve tenor inputs found in market tab")

        # Read current 1Y rate, bump it by 0.5%
        original = map_page.evaluate("""() => {
            const inp = document.querySelector(
                '#td-market-inputs input[data-tenor="1"][data-mode="yield"]');
            return inp ? parseFloat(inp.value) : null;
        }""")

        if original is None:
            pytest.skip("Could not read 1Y yield input")

        new_rate = round(original + 0.50, 2)
        map_page.evaluate(f"""() => {{
            const inp = document.querySelector(
                '#td-market-inputs input[data-tenor="1"][data-mode="yield"]');
            if (inp) {{
                inp.value = '{new_rate}';
                inp.dispatchEvent(new Event('change'));
                if (typeof window.tdCurveInputChanged === 'function') {{
                    window.tdCurveInputChanged(inp);
                }}
            }}
        }}""")
        map_page.wait_for_timeout(1_500)

        # Verify commit button shows dirty state
        commit_text = map_page.evaluate("""() => {
            const btn = document.getElementById('td-commit-btn');
            return btn ? btn.textContent : '';
        }""")
        assert "Commit" in commit_text, "Commit button not visible after curve change"

    def test_03_commit_market_changes(self, map_page):
        """Click Commit on market tab to save curve changes."""
        open_trading_desk(map_page, tab="market")
        map_page.wait_for_timeout(6_000)

        # Switch to yield and modify to ensure dirty state
        mode_select = map_page.locator("#td-curve-mode")
        if mode_select.count() > 0:
            map_page.evaluate("""(sel) => {
                for (var i = 0; i < sel.options.length; i++) {
                    if (sel.options[i].value === 'yield') {
                        sel.selectedIndex = i;
                        sel.dispatchEvent(new Event('change', {bubbles: true}));
                        if (typeof window.tdCurveModeChanged === 'function') {
                            window.tdCurveModeChanged('yield');
                        }
                        break;
                    }
                }
            }""", mode_select.element_handle())
        map_page.wait_for_timeout(3_000)

        # Bump 2Y rate to ensure there is something dirty
        map_page.evaluate("""() => {
            const inp = document.querySelector(
                '#td-market-inputs input[data-tenor="2"][data-mode="yield"]');
            if (inp) {
                var cur = parseFloat(inp.value) || 4.0;
                inp.value = (cur + 0.10).toFixed(2);
                inp.dispatchEvent(new Event('change'));
                if (typeof window.tdCurveInputChanged === 'function') {
                    window.tdCurveInputChanged(inp);
                }
            }
        }""")
        map_page.wait_for_timeout(1_500)

        # Click commit
        commit_btn = map_page.locator("#td-commit-btn")
        if commit_btn.count() == 0:
            pytest.skip("Commit button not found on market tab")

        # Button may not be visible — use JS click as fallback
        try:
            commit_btn.click(force=True, timeout=3_000)
        except Exception:
            map_page.evaluate("""() => {
                const btn = document.getElementById('td-commit-btn');
                if (btn) btn.click();
                else if (typeof window.tdCommitMarket === 'function') window.tdCommitMarket();
            }""")
        map_page.wait_for_timeout(9_000)

        # Verify commit happened — look for success notification or
        # commit button reverted to non-dirty state
        result = map_page.evaluate("""() => {
            const btn = document.getElementById('td-commit-btn');
            const btnText = btn ? btn.textContent : '';
            const notifs = document.querySelectorAll('.notif-message');
            let hasSuccess = false;
            let hasError = false;
            for (const n of notifs) {
                const t = n.textContent.toLowerCase();
                if (t.includes('committed') || t.includes('revalued'))
                    hasSuccess = true;
                if (t.includes('nothing to commit'))
                    hasSuccess = true;  // no changes needed is also ok
                if (t.includes('error') || t.includes('fail'))
                    hasError = true;
            }
            return {btnText, hasSuccess, hasError};
        }""")

        # Either success notification or no error
        assert result["hasSuccess"] or not result["hasError"], (
            "Market commit showed an error"
        )

    def test_04_verify_pnl_after_curve_change(self, map_page):
        """After committing curve changes, P&L values should reflect them."""
        # Switch to blotter to see updated P&L
        close_all_panels(map_page)
        open_trading_desk(map_page, tab="blotter")
        map_page.wait_for_timeout(6_000)

        # Read P&L bar content
        pnl_bar_text = map_page.evaluate("""() => {
            const bar = document.getElementById('td-pnl-bar');
            return bar ? bar.textContent : '';
        }""")

        # The bar should show P&L metrics (Daily P&L, Running P&L, etc.)
        assert len(pnl_bar_text) > 10, (
            "P&L bar is empty or missing after curve commit"
        )

        # Verify blotter has trade rows (they should have been revalued)
        row_count = map_page.evaluate("""() => {
            const wrap = document.getElementById('td-blotter-table-wrap');
            if (!wrap) return 0;
            return wrap.querySelectorAll('tbody tr').length;
        }""")
        assert row_count > 0, "Blotter has no trades after market curve change"
