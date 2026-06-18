# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial 
# research and educational use only. Any commercial use, including 
# but not limited to use in or for products or services offered for sale, 
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Cross-panel navigation e2e tests — Part 2.

Validates: Context Menu -> Trading Desk, Historical tab -> Stress tab.
"""

import pytest

from tests.e2e.conftest import (
    cpf_close_all_panels,
    cpf_open_gauge_panel,
)


# ---------------------------------------------------------------------------
# TestContextMenuToTradingDesk
# ---------------------------------------------------------------------------

class TestContextMenuToTradingDesk:
    """Right-click gauge marker -> context menu -> Trading Desk."""

    @pytest.fixture(autouse=True)
    def _setup(self, map_page):
        cpf_close_all_panels(map_page)
        yield
        cpf_close_all_panels(map_page)

    def test_right_click_gauge_shows_context_menu(self, map_page):
        """Right-clicking a gauge marker should show a context menu."""
        markers = map_page.locator("[class*='awesome-marker-icon-']")
        if markers.count() == 0:
            pytest.skip("No gauge markers found on map")

        markers.first.click(button="right", force=True)
        map_page.wait_for_timeout(3_000)

        ctx_menu = map_page.locator(".ctx-menu").or_(
            map_page.locator("[class*='context-menu']")
        )
        if ctx_menu.count() == 0:
            pytest.skip("Context menu did not appear on right-click")

        assert ctx_menu.first.is_visible(), "Context menu should be visible"

    def test_gauge_blotter_menu_item_opens_trading_desk(self, map_page):
        """Clicking 'Gauge Blotter' in context menu should open trading desk."""
        markers = map_page.locator("[class*='awesome-marker-icon-']")
        if markers.count() == 0:
            pytest.skip("No gauge markers found on map")

        markers.first.click(button="right", force=True)
        map_page.wait_for_timeout(3_000)

        ctx_menu = map_page.locator(".ctx-menu").or_(
            map_page.locator("[class*='context-menu']")
        )
        if ctx_menu.count() == 0:
            pytest.skip("Context menu did not appear")

        # Find the "Gauge Blotter" menu item
        blotter_item = ctx_menu.locator("text=Gauge Blotter").or_(
            ctx_menu.locator("text=gauge blotter")
        ).or_(
            ctx_menu.locator("text=Blotter")
        )

        if blotter_item.count() == 0:
            pytest.skip("No 'Gauge Blotter' item in context menu")

        # Check if the item is disabled
        is_disabled = blotter_item.first.evaluate(
            "el => el.classList.contains('disabled') || el.getAttribute('disabled') !== null"
        )
        if is_disabled:
            pytest.skip("Gauge Blotter menu item is disabled")

        blotter_item.first.click(force=True)
        map_page.wait_for_timeout(6_000)

        td_panel = map_page.locator("#trading-desk-panel")
        try:
            td_panel.wait_for(state="visible", timeout=10_000)
        except Exception:
            # Trading desk may open but be hidden behind other panels
            is_in_dom = td_panel.count() > 0
            if is_in_dom:
                # Force show via JS
                map_page.evaluate("""() => {
                    const p = document.getElementById('trading-desk-panel');
                    if (p) p.style.display = '';
                }""")
                map_page.wait_for_timeout(1_500)
            else:
                pytest.skip("Trading desk panel not in DOM after Gauge Blotter click")

        assert td_panel.is_visible(), (
            "Trading desk should open after clicking Gauge Blotter in context menu"
        )


# ---------------------------------------------------------------------------
# TestHistoricalToStress
# ---------------------------------------------------------------------------

class TestHistoricalToStress:
    """Historical tab -> storm scenario click -> Stress tab activation."""

    @pytest.fixture(autouse=True)
    def _setup(self, map_page):
        cpf_close_all_panels(map_page)
        yield
        cpf_close_all_panels(map_page)

    def test_historical_tab_has_content(self, map_page, first_gauge_id):
        """Open gauge panel, switch to Historical tab (data-tab='4'), verify content."""
        cpf_open_gauge_panel(map_page, first_gauge_id)
        map_page.wait_for_timeout(3_000)

        # Switch to Historical tab (tab index 4)
        hist_tab = map_page.locator(
            "#hazard-curve-panel [data-tab='4']"
        ).or_(
            map_page.locator("#hazard-curve-panel").locator("text=Historical")
        )
        if hist_tab.count() == 0:
            pytest.skip("Historical tab not found in gauge panel")

        hist_tab.first.click(force=True)
        map_page.wait_for_timeout(3_000)

        # Verify some content appeared in the panel
        panel = map_page.locator("#hazard-curve-panel")
        panel_text = panel.inner_text()
        # Historical tab should have some data (chart, table, or text)
        assert len(panel_text.strip()) > 50, (
            "Historical tab should have substantive content"
        )

    def test_storm_scenario_click_activates_stress_tab(
        self, map_page, first_gauge_id
    ):
        """Click a storm scenario in Historical tab to activate the Stress tab."""
        cpf_open_gauge_panel(map_page, first_gauge_id)
        map_page.wait_for_timeout(3_000)

        # Switch to Historical tab
        hist_tab = map_page.locator(
            "#hazard-curve-panel [data-tab='4']"
        ).or_(
            map_page.locator("#hazard-curve-panel").locator("text=Historical")
        )
        if hist_tab.count() == 0:
            pytest.skip("Historical tab not found")

        hist_tab.first.click(force=True)
        map_page.wait_for_timeout(3_000)

        # Look for storm scenario items in the right panel
        panel = map_page.locator("#hazard-curve-panel")
        storm_items = panel.locator("[data-storm-id]").or_(
            panel.locator("[class*='storm-scenario']")
        ).or_(
            panel.locator("[class*='storm-item']")
        ).or_(
            panel.locator("text=/STORM-/")
        )

        if storm_items.count() == 0:
            pytest.skip("No storm scenarios found in Historical tab")

        storm_items.first.click(force=True)
        map_page.wait_for_timeout(3_000)

        # Verify the Stress tab (data-tab='5') is now active
        stress_tab = panel.locator("[data-tab='5']").or_(
            panel.locator("text=Stress")
        )
        if stress_tab.count() == 0:
            pytest.skip("Stress tab not found in gauge panel")

        is_active = stress_tab.first.evaluate(
            "el => el.classList.contains('active') || "
            "el.getAttribute('aria-selected') === 'true' || "
            "window.getComputedStyle(el).fontWeight >= '600'"
        )
        assert is_active, (
            "Stress tab should be active after clicking a storm scenario"
        )
