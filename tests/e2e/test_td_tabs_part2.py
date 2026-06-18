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
Trading Desk — remaining 6 tabs e2e tests (part 2).

Covers: EOD, Curves, Stress Test.
"""

import pytest

from tests.e2e.conftest import td_close_all_panels, td_open_trading_desk, td_close_trading_desk


# ---------------------------------------------------------------------------
# EOD tab
# ---------------------------------------------------------------------------


class TestEODTab:
    """EOD tab content checks."""

    @pytest.fixture(autouse=True)
    def open_eod_tab(self, map_page):
        td_close_all_panels(map_page)
        td_open_trading_desk(map_page)
        map_page.locator("#td-tab-eod").click(force=True)
        map_page.wait_for_timeout(1_500)
        yield
        td_close_trading_desk(map_page)

    def test_eod_view_visible(self, map_page):
        """EOD content area should be visible."""
        view = map_page.locator("#td-eod-view")
        assert view.count() > 0, "No #td-eod-view element found"
        assert view.is_visible(), "#td-eod-view is not visible"

    def test_has_history_list_or_table(self, map_page):
        """EOD tab should have a history list, table, or button."""
        view = map_page.locator("#td-eod-view")
        tables = view.locator("table")
        lists = view.locator("ul, ol")
        buttons = view.locator("button")
        assert (
            tables.count() > 0
            or lists.count() > 0
            or buttons.count() > 0
        ), "No table, list, or button found in EOD view"

    def test_content_mentions_eod_keywords(self, map_page):
        """EOD tab should mention EOD, P&L, or snapshot."""
        text = map_page.locator("#td-eod-view").inner_text().lower()
        assert any(kw in text for kw in ("eod", "p&l", "pnl", "snapshot", "end of day")), (
            f"Expected eod/p&l/snapshot keywords, got: {text[:200]}"
        )


# ---------------------------------------------------------------------------
# Curves tab
# ---------------------------------------------------------------------------


class TestCurvesTab:
    """Curves tab content checks."""

    @pytest.fixture(autouse=True)
    def open_curves_tab(self, map_page):
        td_close_all_panels(map_page)
        td_open_trading_desk(map_page)
        map_page.locator("#td-tab-curves").click(force=True)
        map_page.wait_for_timeout(1_500)
        yield
        td_close_trading_desk(map_page)

    def test_curves_view_visible(self, map_page):
        """Curves content area should be visible."""
        view = map_page.locator("#td-curves-view")
        assert view.count() > 0, "No #td-curves-view element found"
        assert view.is_visible(), "#td-curves-view is not visible"

    def test_has_chart_or_curve_content(self, map_page):
        """Curves tab should contain a chart canvas or curve keywords."""
        view = map_page.locator("#td-curves-view")
        canvases = view.locator("canvas")
        text = view.inner_text().lower()
        has_canvas = canvases.count() > 0
        has_keywords = any(kw in text for kw in ("curve", "hazard", "gauge", "trigger"))
        assert has_canvas or has_keywords, (
            "No canvas or curve keywords found in curves view"
        )


# ---------------------------------------------------------------------------
# Stress Test tab
# ---------------------------------------------------------------------------


class TestStressTab:
    """Stress Test tab content checks."""

    @pytest.fixture(autouse=True)
    def open_stress_tab(self, map_page):
        td_close_all_panels(map_page)
        td_open_trading_desk(map_page)
        map_page.locator("#td-tab-stress").click(force=True)
        map_page.wait_for_timeout(1_500)
        yield
        td_close_trading_desk(map_page)

    def test_stress_view_visible(self, map_page):
        """Stress content area should be visible."""
        view = map_page.locator("#td-stress-view")
        assert view.count() > 0, "No #td-stress-view element found"
        assert view.is_visible(), "#td-stress-view is not visible"

    def test_has_gauge_dropdown(self, map_page):
        """Stress tab should have a gauge dropdown selector."""
        view = map_page.locator("#td-stress-view")
        selects = view.locator("select")
        text = view.inner_text().lower()
        has_gauge_select = False
        for i in range(selects.count()):
            options_text = selects.nth(i).inner_text().lower()
            if "gauge" in options_text:
                has_gauge_select = True
                break
        has_gauge_keyword = "gauge" in text
        assert selects.count() > 0 and (has_gauge_select or has_gauge_keyword), (
            "No gauge dropdown found in stress view"
        )

    def test_has_storm_dropdown(self, map_page):
        """Stress tab should have a storm dropdown selector."""
        view = map_page.locator("#td-stress-view")
        selects = view.locator("select")
        text = view.inner_text().lower()
        has_storm_keyword = "storm" in text
        # Expect at least 2 selects (gauge + storm)
        assert selects.count() >= 2 or has_storm_keyword, (
            "No storm dropdown found in stress view"
        )
