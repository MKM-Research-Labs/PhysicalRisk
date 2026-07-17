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
Trading Desk — remaining 6 tabs e2e tests (part 1).

Covers: Market State, FS01 Risk, Aggregate Map.
"""

import pytest

from tests.e2e.conftest import td_close_all_panels, td_open_trading_desk, td_close_trading_desk


# ---------------------------------------------------------------------------
# Market State tab
# ---------------------------------------------------------------------------


class TestMarketTab:
    """Market State tab content checks."""

    @pytest.fixture(autouse=True)
    def open_market_tab(self, map_page):
        td_close_all_panels(map_page)
        td_open_trading_desk(map_page)
        map_page.locator("#td-tab-market").click(force=True)
        map_page.wait_for_timeout(1_500)
        yield
        td_close_trading_desk(map_page)

    def test_market_view_visible(self, map_page):
        """Market content area should be visible after clicking the tab."""
        view = map_page.locator("#td-market-view")
        assert view.count() > 0, "No #td-market-view element found"
        assert view.is_visible(), "#td-market-view is not visible"

    def test_has_yield_curve_content(self, map_page):
        """Market tab should mention yield, curve, or tenor."""
        text = map_page.locator("#td-market-view").inner_text().lower()
        assert any(kw in text for kw in ("yield", "curve", "tenor")), (
            f"Expected yield/curve/tenor keywords in market view, got: {text[:200]}"
        )

    def test_has_hazard_term_structure(self, map_page):
        """Market tab should have hazard term structure selector or content."""
        view = map_page.locator("#td-market-view")
        text = view.inner_text().lower()
        selects = view.locator("select")
        has_keyword = any(kw in text for kw in ("hazard", "alert", "warning", "severe"))
        has_select = selects.count() > 0
        assert has_keyword or has_select, (
            "No hazard term structure selector or keywords found"
        )

    def test_has_charts_or_inputs(self, map_page):
        """Market tab should contain chart canvases or input fields."""
        view = map_page.locator("#td-market-view")
        canvases = view.locator("canvas")
        inputs = view.locator("input")
        assert canvases.count() > 0 or inputs.count() > 0, (
            "No canvas or input elements found in market view"
        )


# ---------------------------------------------------------------------------
# FS01 Risk tab
# ---------------------------------------------------------------------------


class TestFS01Tab:
    """FS01 Risk tab content checks."""

    @pytest.fixture(autouse=True)
    def open_risk_tab(self, map_page):
        td_close_all_panels(map_page)
        td_open_trading_desk(map_page)
        map_page.locator("#td-tab-risk").click(force=True)
        map_page.wait_for_timeout(1_500)
        yield
        td_close_trading_desk(map_page)

    def test_risk_view_visible(self, map_page):
        """Risk content area should be visible."""
        view = map_page.locator("#td-risk-view")
        assert view.count() > 0, "No #td-risk-view element found"
        assert view.is_visible(), "#td-risk-view is not visible"

    def test_has_risk_grid(self, map_page):
        """Risk tab should contain a table or grid."""
        view = map_page.locator("#td-risk-view")
        tables = view.locator("table")
        grids = view.locator("[class*='grid']")
        assert tables.count() > 0 or grids.count() > 0, (
            "No table or grid element found in risk view"
        )

    def test_content_mentions_risk_keywords(self, map_page):
        """Risk tab should mention FS01, risk, or gauge."""
        text = map_page.locator("#td-risk-view").inner_text().lower()
        assert any(kw in text for kw in ("fs01", "risk", "gauge")), (
            f"Expected fs01/risk/gauge keywords, got: {text[:200]}"
        )


# ---------------------------------------------------------------------------
# Aggregate Map tab
# ---------------------------------------------------------------------------


class TestAggregateTab:
    """Aggregate Map tab content checks."""

    @pytest.fixture(autouse=True)
    def open_map_tab(self, map_page):
        td_close_all_panels(map_page)
        td_open_trading_desk(map_page)
        map_page.locator("#td-tab-map").click(force=True)
        map_page.wait_for_timeout(1_500)
        yield
        td_close_trading_desk(map_page)

    def test_map_view_visible(self, map_page):
        """Aggregate map content area should be visible."""
        view = map_page.locator("#td-map-view")
        assert view.count() > 0, "No #td-map-view element found"
        assert view.is_visible(), "#td-map-view is not visible"

    def test_has_leaflet_or_svg(self, map_page):
        """Aggregate tab should contain a Leaflet map or SVG circles."""
        view = map_page.locator("#td-map-view")
        leaflet = view.locator(".leaflet-container")
        svgs = view.locator("svg")
        circles = view.locator("circle")
        canvas = view.locator("canvas")
        assert (
            leaflet.count() > 0
            or svgs.count() > 0
            or circles.count() > 0
            or canvas.count() > 0
        ), "No Leaflet map, SVG, circle, or canvas found in aggregate view"
