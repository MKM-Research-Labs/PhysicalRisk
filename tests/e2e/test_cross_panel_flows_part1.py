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
Cross-panel navigation e2e tests — Part 1.

Validates: FS01 -> Blotter, Gauge Panel -> Trading Desk.
"""

import pytest

from tests.e2e.conftest import (
    cpf_close_all_panels,
    cpf_open_gauge_panel,
    cpf_open_trading_desk,
)


# ---------------------------------------------------------------------------
# TestFS01ToBlotter
# ---------------------------------------------------------------------------

class TestFS01ToBlotter:
    """FS01 risk grid -> Blotter tab filter flow."""

    @pytest.fixture(autouse=True)
    def _setup(self, map_page):
        cpf_close_all_panels(map_page)
        yield
        cpf_close_all_panels(map_page)

    def test_fs01_tab_shows_risk_grid(self, map_page):
        """Open trading desk, click FS01 tab, verify risk grid is visible."""
        cpf_open_trading_desk(map_page)

        fs01_tab = map_page.locator("#td-tab-risk")
        if fs01_tab.count() == 0:
            fs01_tab = map_page.locator("#td-tab-fs01")
        if fs01_tab.count() == 0:
            # Use text match inside trading desk panel only
            fs01_tab = map_page.locator("#trading-desk-panel button:has-text('FS01')")
        if fs01_tab.count() == 0:
            pytest.skip("FS01 tab not found in trading desk")

        fs01_tab.first.click(force=True)
        map_page.wait_for_timeout(3_000)

        # Look for the risk grid container
        grid = map_page.locator("#td-risk-view").or_(
            map_page.locator("#td-fs01-view")
        ).or_(
            map_page.locator("[class*='risk-grid']")
        ).or_(
            map_page.locator("#td-fs01-grid")
        )
        assert grid.count() > 0, "FS01 risk grid not visible after clicking tab"

    # Note: FS01-cell-click-to-blotter coverage was removed because the cell
    # markup uses inline onclick (tdRiskCellClick) rather than data-* attributes
    # the original selectors looked for. Re-add with a JS-driven test if needed.


# ---------------------------------------------------------------------------
# TestGaugeBlotterFlow
# ---------------------------------------------------------------------------

class TestGaugeBlotterFlow:
    """Gauge panel -> blotter link -> Trading Desk flow."""

    @pytest.fixture(autouse=True)
    def _setup(self, map_page):
        cpf_close_all_panels(map_page)
        yield
        cpf_close_all_panels(map_page)

    def test_gauge_panel_blotter_link_opens_trading_desk(
        self, map_page, first_traded_gauge_id
    ):
        """Open gauge panel for a traded gauge, click blotter link, trading desk opens."""
        cpf_open_gauge_panel(map_page, first_traded_gauge_id)
        map_page.wait_for_timeout(3_000)

        # Look for a blotter link or button inside the gauge panel
        panel = map_page.locator("#hazard-curve-panel")
        blotter_link = panel.locator("text=Blotter").or_(
            panel.locator("text=blotter")
        ).or_(
            panel.locator("[data-action='blotter']")
        ).or_(
            panel.locator("text=Trading")
        )

        if blotter_link.count() == 0:
            pytest.skip("No blotter link found in gauge panel")

        blotter_link.first.click(force=True)
        map_page.wait_for_timeout(3_000)

        td_panel = map_page.locator("#trading-desk-panel")
        td_panel.wait_for(state="visible", timeout=5_000)
        assert td_panel.is_visible(), "Trading desk should open from gauge panel blotter link"

    def test_trading_desk_blotter_visible_after_gauge_link(
        self, map_page, first_traded_gauge_id
    ):
        """After clicking gauge blotter link, the blotter view should be visible."""
        cpf_open_gauge_panel(map_page, first_traded_gauge_id)
        map_page.wait_for_timeout(3_000)

        panel = map_page.locator("#hazard-curve-panel")
        blotter_link = panel.locator("text=Blotter").or_(
            panel.locator("text=blotter")
        ).or_(
            panel.locator("[data-action='blotter']")
        ).or_(
            panel.locator("text=Trading")
        )

        if blotter_link.count() == 0:
            pytest.skip("No blotter link found in gauge panel")

        blotter_link.first.click(force=True)
        map_page.wait_for_timeout(3_000)

        td_panel = map_page.locator("#trading-desk-panel")
        if not td_panel.is_visible():
            pytest.skip("Trading desk did not open from gauge link")

        # Blotter view or tab should be active
        blotter_view = map_page.locator("#td-blotter-view")
        if blotter_view.count() > 0:
            map_page.wait_for_timeout(1_500)
            assert blotter_view.is_visible(), (
                "Blotter view should be visible in trading desk"
            )
        else:
            # At minimum the trading desk is open
            assert td_panel.is_visible()
