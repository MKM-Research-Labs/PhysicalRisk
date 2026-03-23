# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

"""
Trading Desk — remaining 6 tabs e2e tests.

Covers: Market State, FS01 Risk, Aggregate Map, EOD, Curves, Stress Test.
Each test class opens the trading desk, activates the relevant tab, and
verifies that the expected content renders.
"""

import pytest


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

PANEL_IDS_TO_CLOSE = [
    "trading-desk-panel",
    "hazard-curve-panel",
    "property-hc-panel",
    "prop-storm-panel",
    "mortgage-detail-panel",
    "mg-panel",
    "property-pdf-panel",
    "storm-portfolio-panel",
    "gauge-pdf-panel",
]

CLOSE_PANELS_JS = """() => {
    %s.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.style.display = 'none';
    });
    document.querySelectorAll('.ctx-menu').forEach(m => m.remove());
}""" % str(PANEL_IDS_TO_CLOSE).replace("'", '"')


def _close_all_panels(page):
    """Hide every known panel and remove context menus."""
    page.evaluate(CLOSE_PANELS_JS)


def _open_trading_desk(page):
    """Click the Pi button and wait for the trading desk panel."""
    pi_btn = page.locator("text=\u03a0").first
    pi_btn.click()
    page.locator("#trading-desk-panel").wait_for(
        state="visible", timeout=5_000
    )


def _close_trading_desk(page):
    """Close the trading desk panel if visible."""
    panel = page.locator("#trading-desk-panel")
    if panel.is_visible():
        close_btn = panel.locator("text=\u00d7").first
        if close_btn.is_visible():
            close_btn.click()


# ---------------------------------------------------------------------------
# Market State tab
# ---------------------------------------------------------------------------


class TestMarketTab:
    """Market State tab content checks."""

    @pytest.fixture(autouse=True)
    def open_market_tab(self, map_page):
        _close_all_panels(map_page)
        _open_trading_desk(map_page)
        map_page.locator("#td-tab-market").click(force=True)
        map_page.wait_for_timeout(1_500)
        yield
        _close_trading_desk(map_page)

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
        _close_all_panels(map_page)
        _open_trading_desk(map_page)
        map_page.locator("#td-tab-risk").click(force=True)
        map_page.wait_for_timeout(1_500)
        yield
        _close_trading_desk(map_page)

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
        _close_all_panels(map_page)
        _open_trading_desk(map_page)
        map_page.locator("#td-tab-map").click(force=True)
        map_page.wait_for_timeout(1_500)
        yield
        _close_trading_desk(map_page)

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


# ---------------------------------------------------------------------------
# EOD tab
# ---------------------------------------------------------------------------


class TestEODTab:
    """EOD tab content checks."""

    @pytest.fixture(autouse=True)
    def open_eod_tab(self, map_page):
        _close_all_panels(map_page)
        _open_trading_desk(map_page)
        map_page.locator("#td-tab-eod").click(force=True)
        map_page.wait_for_timeout(1_500)
        yield
        _close_trading_desk(map_page)

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
        _close_all_panels(map_page)
        _open_trading_desk(map_page)
        map_page.locator("#td-tab-curves").click(force=True)
        map_page.wait_for_timeout(1_500)
        yield
        _close_trading_desk(map_page)

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
        _close_all_panels(map_page)
        _open_trading_desk(map_page)
        map_page.locator("#td-tab-stress").click(force=True)
        map_page.wait_for_timeout(1_500)
        yield
        _close_trading_desk(map_page)

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
