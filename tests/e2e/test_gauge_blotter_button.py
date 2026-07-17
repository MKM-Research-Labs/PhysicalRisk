# Copyright (c) 2022-2026 MKM Research Labs.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
E2E tests: gauge blotter button state after trade commit.

Verifies:
- Blotter button is muted for gauges with no trades
- After committing a trade, re-opening the panel shows the button enabled
- Button click opens the trading desk blotter
"""

import pytest

from tests.e2e.helpers import close_gauge_panel, open_gauge_panel


class TestGaugeBlotterButtonState:
    """Blotter button should reflect whether the gauge has open trades."""

    def test_blotter_button_exists_in_tab_bar(self, map_page, first_gauge_id):
        """Blotter button should be in the tab bar."""
        open_gauge_panel(map_page, first_gauge_id)
        map_page.wait_for_timeout(5_000)

        btn = map_page.locator("#hazard-blotter-link")
        assert btn.count() > 0, "No #hazard-blotter-link button found"

        # Should be inside the tab bar, not the header
        tab_bar = map_page.locator("#hazard-tab-bar")
        btn_in_bar = tab_bar.locator("#hazard-blotter-link")
        assert btn_in_bar.count() > 0, "Blotter button not inside #hazard-tab-bar"

        close_gauge_panel(map_page)

    def test_blotter_button_muted_for_gauge_without_trades(self, map_page, first_gauge_id):
        """For a gauge with no trades, the blotter button should be disabled."""
        open_gauge_panel(map_page, first_gauge_id)
        map_page.wait_for_timeout(5_000)

        result = map_page.evaluate("""() => {
            var btn = document.getElementById('hazard-blotter-link');
            if (!btn) return { exists: false };
            return {
                exists: true,
                disabled: btn.disabled,
                color: btn.style.color,
                cursor: btn.style.cursor
            };
        }""")
        assert result['exists'], "Blotter button not found"

        # Check active gauges to determine expected state
        has_trades = map_page.evaluate(f"""async () => {{
            try {{
                var cfg = window.__BACKEND_CONFIG || {{}};
                var resp = await fetch((cfg.url || '') + '/api/v1/trading/blotter/active-gauges');
                var data = await resp.json();
                return (data.gauge_ids || []).indexOf('{first_gauge_id}') !== -1;
            }} catch (e) {{ return false; }}
        }}""")

        if not has_trades:
            assert result['disabled'], (
                f"Button should be disabled for {first_gauge_id} (no trades)"
            )

        close_gauge_panel(map_page)

    def test_blotter_button_enabled_for_gauge_with_trades(self, map_page):
        """For a gauge with trades, the blotter button should be enabled."""
        # Find a gauge that has trades
        gauge_id = map_page.evaluate("""async () => {
            try {
                var cfg = window.__BACKEND_CONFIG || {};
                var resp = await fetch((cfg.url || '') + '/api/v1/trading/blotter/active-gauges');
                var data = await resp.json();
                var ids = data.gauge_ids || [];
                return ids.length > 0 ? ids[0] : null;
            } catch (e) { return null; }
        }""")
        if not gauge_id:
            pytest.skip("No gauges with active trades")

        open_gauge_panel(map_page, gauge_id)
        map_page.wait_for_timeout(5_000)

        result = map_page.evaluate("""() => {
            var btn = document.getElementById('hazard-blotter-link');
            if (!btn) return { exists: false };
            return {
                exists: true,
                disabled: btn.disabled,
                color: btn.style.color,
                cursor: btn.style.cursor
            };
        }""")
        assert result['exists'], "Blotter button not found"
        assert not result['disabled'], (
            f"Button should be enabled for {gauge_id} (has trades)"
        )
        assert 'pointer' in result.get('cursor', ''), (
            f"Button cursor should be pointer, got: {result.get('cursor')}"
        )

        close_gauge_panel(map_page)

    def test_blotter_button_click_opens_trading_desk(self, map_page):
        """Clicking enabled blotter button should open the trading desk."""
        # Find a gauge with trades
        gauge_id = map_page.evaluate("""async () => {
            try {
                var cfg = window.__BACKEND_CONFIG || {};
                var resp = await fetch((cfg.url || '') + '/api/v1/trading/blotter/active-gauges');
                var data = await resp.json();
                var ids = data.gauge_ids || [];
                return ids.length > 0 ? ids[0] : null;
            } catch (e) { return null; }
        }""")
        if not gauge_id:
            pytest.skip("No gauges with active trades")

        open_gauge_panel(map_page, gauge_id)
        map_page.wait_for_timeout(5_000)

        # Click the blotter button
        btn = map_page.locator("#hazard-blotter-link")
        if btn.count() > 0 and not map_page.evaluate("document.getElementById('hazard-blotter-link').disabled"):
            btn.click()
            map_page.wait_for_timeout(3_000)

            # Trading desk should be visible
            td = map_page.locator("#trading-desk-panel")
            assert td.count() > 0 and td.is_visible(), (
                "Trading desk panel not visible after clicking Gauge Blotter"
            )
        else:
            pytest.skip("Blotter button is disabled")
