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
Trading Desk — Port Stress tab e2e tests — Part 1.

Covers: panel structure, storm selector, P(flood) sub-tab.
"""

import pytest

from tests.e2e.conftest import (
    ps_close_all_panels,
    ps_open_trading_desk,
    ps_close_trading_desk,
)


# ---------------------------------------------------------------------------
# Port Stress tab — structure
# ---------------------------------------------------------------------------


class TestPortStressTab:
    """Port Stress tab: storm selector, sub-tabs, charts."""

    @pytest.fixture(autouse=True)
    def open_port_stress_tab(self, map_page):
        ps_close_all_panels(map_page)
        ps_open_trading_desk(map_page)
        map_page.locator("#td-tab-portstress").click(force=True)
        map_page.wait_for_timeout(4_000)  # storm load
        yield
        ps_close_trading_desk(map_page)

    def test_portstress_view_visible(self, map_page):
        """Port Stress content area should be visible."""
        view = map_page.locator("#td-portstress-view")
        assert view.count() > 0, "No #td-portstress-view element"
        assert view.is_visible(), "#td-portstress-view is not visible"

    def test_has_storm_selector(self, map_page):
        """Storm selector dropdown should exist."""
        select = map_page.locator("#ps-storm-sel")
        assert select.count() > 0, "No #ps-storm-sel found"

    def test_storm_selector_has_options(self, map_page):
        """Storm selector should have at least one storm option."""
        select = map_page.locator("#ps-storm-sel")
        assert select.count() > 0, "No storm selector"
        options = select.locator("option")
        assert options.count() > 0, "Storm selector has no options"

    def test_has_sub_tab_buttons(self, map_page):
        """All 4 sub-tab buttons should exist."""
        view = map_page.locator("#td-portstress-view")
        if view.count() == 0:
            pytest.skip("Port stress view not found")
        for tab_id in ["ps-tab-pflood", "ps-tab-portpnl",
                        "ps-tab-gaugepnl", "ps-tab-severity"]:
            btn = map_page.locator(f"#{tab_id}")
            assert btn.count() > 0, f"Sub-tab #{tab_id} not found"

    def test_has_stats_bar(self, map_page):
        """Stats bar should exist."""
        bar = map_page.locator("#ps-stats-bar")
        assert bar.count() > 0, "No stats bar"

    def test_has_content_area(self, map_page):
        """Main content div should exist."""
        content = map_page.locator("#ps-content")
        assert content.count() > 0, "No #ps-content element"


# ---------------------------------------------------------------------------
# P(flood) sub-tab
# ---------------------------------------------------------------------------


class TestPortStressPFlood:
    """P(flood) sub-tab: bar chart of flood probabilities per gauge."""

    @pytest.fixture(autouse=True)
    def open_pflood(self, map_page):
        ps_close_all_panels(map_page)
        ps_open_trading_desk(map_page)
        map_page.locator("#td-tab-portstress").click(force=True)
        map_page.wait_for_timeout(4_000)

        btn = map_page.locator("#ps-tab-pflood")
        if btn.count() == 0:
            pytest.skip("P(flood) sub-tab not found")
        btn.click(force=True)
        map_page.wait_for_timeout(3_000)
        yield
        ps_close_trading_desk(map_page)

    def test_pflood_has_content(self, map_page):
        """P(flood) tab should render content (chart or text)."""
        content = map_page.locator("#ps-content")
        text = content.inner_text()
        has_content = (
            len(text.strip()) > 0
            or content.locator("canvas").count() > 0
        )
        assert has_content, "P(flood) tab is empty"

    def test_pflood_has_chart_or_data(self, map_page):
        """Should show a bar chart or flood probability data."""
        content = map_page.locator("#ps-content")
        canvas = content.locator("canvas")
        text = content.inner_text().lower()
        has_data = (
            canvas.count() > 0
            or "flood" in text
            or "p(" in text
            or "%" in text
        )
        assert has_data, "No chart or flood data in P(flood) tab"
