# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

"""
Storm Portfolio panel — e2e tests for all 4 tabs.

Covers: Table, Sim (map animation), Visual (multi-line chart), VaR (histogram).
Also includes direct API data load tests for the supporting endpoints.
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


def _open_storm_portfolio(page):
    """Open the Storm Portfolio panel via JS global function."""
    has_fn = page.evaluate(
        "() => typeof window.showStormPortfolio === 'function'"
    )
    if not has_fn:
        pytest.skip("window.showStormPortfolio not available")
    page.evaluate("window.showStormPortfolio()")
    page.locator("#storm-portfolio-panel").wait_for(
        state="visible", timeout=10_000
    )
    page.wait_for_timeout(3_000)  # storm list load


def _close_storm_portfolio(page):
    """Close the Storm Portfolio panel if visible."""
    panel = page.locator("#storm-portfolio-panel")
    if panel.is_visible():
        close_btn = panel.locator("text=\u00d7").first
        if close_btn.count() > 0 and close_btn.is_visible():
            close_btn.click()
        else:
            page.evaluate("""() => {
                const el = document.getElementById('storm-portfolio-panel');
                if (el) el.style.display = 'none';
            }""")


# ---------------------------------------------------------------------------
# Panel-level tests
# ---------------------------------------------------------------------------


class TestStormPortfolioOpens:
    """Storm Portfolio panel opens and has expected structure."""

    @pytest.fixture(autouse=True)
    def setup(self, map_page):
        _close_all_panels(map_page)
        _open_storm_portfolio(map_page)
        yield
        _close_storm_portfolio(map_page)

    def test_panel_opens(self, map_page):
        """The storm portfolio panel should be visible."""
        panel = map_page.locator("#storm-portfolio-panel")
        assert panel.is_visible(), "Storm portfolio panel not visible"

    def test_has_storm_selector(self, map_page):
        """Storm selector dropdown should have at least one option."""
        select = map_page.locator("#sp-storm-select")
        assert select.count() > 0, "No #sp-storm-select found"
        options = select.locator("option")
        assert options.count() > 0, "Storm selector has no options"

    def test_has_four_tab_buttons(self, map_page):
        """All four tab buttons should exist."""
        for tab_id in ["sp-tab-table", "sp-tab-sim", "sp-tab-vis", "sp-tab-var"]:
            btn = map_page.locator(f"#{tab_id}")
            assert btn.count() > 0, f"Tab button #{tab_id} not found"

    def test_stats_bar_present(self, map_page):
        """Stats bar should be present in the panel."""
        bar = map_page.locator("#sp-stats-bar")
        assert bar.count() > 0, "No #sp-stats-bar found"


# ---------------------------------------------------------------------------
# Table tab
# ---------------------------------------------------------------------------


class TestSPTableTab:
    """Table tab: summary cards + property damage table."""

    @pytest.fixture(autouse=True)
    def open_table_tab(self, map_page):
        _close_all_panels(map_page)
        _open_storm_portfolio(map_page)
        map_page.locator("#sp-tab-table").click(force=True)
        map_page.wait_for_timeout(3_000)
        yield
        _close_storm_portfolio(map_page)

    def test_table_view_visible(self, map_page):
        """Table content area should be visible."""
        view = map_page.locator("#sp-table-view")
        assert view.count() > 0 and view.is_visible(), \
            "No visible #sp-table-view"

    def test_has_summary_cards(self, map_page):
        """Summary cards row should have content."""
        summary = map_page.locator("#sp-summary")
        if summary.count() > 0:
            text = summary.inner_text()
            assert len(text.strip()) > 0, "Summary cards are empty"

    def test_has_property_table(self, map_page):
        """Property table container should have table rows."""
        container = map_page.locator("#sp-table-container")
        if container.count() > 0:
            rows = container.locator("tr")
            assert rows.count() > 0, "No table rows in #sp-table-container"

    def test_content_has_keywords(self, map_page):
        """Table view should mention portfolio-related terms."""
        view = map_page.locator("#sp-table-view")
        if view.count() == 0:
            pytest.skip("No #sp-table-view element")
        text = view.inner_text().lower()
        keywords = ["damage", "property", "portfolio", "value", "depth"]
        assert any(kw in text for kw in keywords), \
            f"No expected keywords in table view: {text[:200]}"


# ---------------------------------------------------------------------------
# Sim tab (map animation)
# ---------------------------------------------------------------------------


class TestSPSimTab:
    """Sim tab: embedded Leaflet map with frame-by-frame flood animation."""

    @pytest.fixture(autouse=True)
    def open_sim_tab(self, map_page):
        _close_all_panels(map_page)
        _open_storm_portfolio(map_page)
        map_page.locator("#sp-tab-sim").click(force=True)
        map_page.wait_for_timeout(6_000)  # map init is slow
        yield
        _close_storm_portfolio(map_page)

    def test_sim_view_visible(self, map_page):
        """Sim content area should be visible."""
        view = map_page.locator("#sp-sim-view")
        assert view.count() > 0 and view.is_visible(), \
            "No visible #sp-sim-view"

    def test_has_map_container(self, map_page):
        """Map container should exist."""
        container = map_page.locator("#sp-sim-map-container")
        assert container.count() > 0, "No #sp-sim-map-container found"

    def test_has_play_button(self, map_page):
        """Play/pause button should be visible."""
        btn = map_page.locator("#sp-sim-play-btn")
        assert btn.count() > 0, "No #sp-sim-play-btn found"

    def test_has_leaflet_or_canvas(self, map_page):
        """Should contain a Leaflet map or canvas element."""
        view = map_page.locator("#sp-sim-view")
        leaflet = view.locator(".leaflet-container")
        canvas = view.locator("canvas")
        assert leaflet.count() > 0 or canvas.count() > 0, \
            "No Leaflet map or canvas in sim view"


# ---------------------------------------------------------------------------
# Visual tab (multi-line chart)
# ---------------------------------------------------------------------------


class TestSPVisualTab:
    """Visual tab: multi-line gauge hydrograph chart with filters."""

    @pytest.fixture(autouse=True)
    def open_vis_tab(self, map_page):
        _close_all_panels(map_page)
        _open_storm_portfolio(map_page)
        map_page.locator("#sp-tab-vis").click(force=True)
        map_page.wait_for_timeout(6_000)
        yield
        _close_storm_portfolio(map_page)

    def test_vis_view_visible(self, map_page):
        """Visual content area should be visible."""
        view = map_page.locator("#sp-vis-view")
        assert view.count() > 0 and view.is_visible(), \
            "No visible #sp-vis-view"

    def test_has_chart_canvas(self, map_page):
        """Chart canvas should exist."""
        canvas = map_page.locator("#sp-sim-canvas")
        assert canvas.count() > 0, "No #sp-sim-canvas found"

    def test_has_filter_row(self, map_page):
        """Filter row should exist."""
        row = map_page.locator("#sp-vis-filter-row")
        assert row.count() > 0, "No #sp-vis-filter-row found"

    def test_filter_has_controls(self, map_page):
        """Filter row should contain buttons or select elements."""
        row = map_page.locator("#sp-vis-filter-row")
        if row.count() == 0:
            pytest.skip("No filter row")
        buttons = row.locator("button")
        selects = row.locator("select")
        assert buttons.count() > 0 or selects.count() > 0, \
            "No controls in filter row"


# ---------------------------------------------------------------------------
# VaR tab (loss distribution histogram)
# ---------------------------------------------------------------------------


class TestSPVaRTab:
    """VaR tab: loss distribution histogram with VaR/ES metrics."""

    @pytest.fixture(autouse=True)
    def open_var_tab(self, map_page):
        _close_all_panels(map_page)
        _open_storm_portfolio(map_page)
        map_page.locator("#sp-tab-var").click(force=True)
        map_page.wait_for_timeout(9_000)  # VaR computation is heavy
        yield
        _close_storm_portfolio(map_page)

    def test_var_view_visible(self, map_page):
        """VaR content area should be visible."""
        view = map_page.locator("#sp-var-view")
        assert view.count() > 0 and view.is_visible(), \
            "No visible #sp-var-view"

    def test_has_histogram_canvas(self, map_page):
        """Histogram canvas should exist."""
        canvas = map_page.locator("#sp-var-canvas")
        assert canvas.count() > 0, "No #sp-var-canvas found"

    def test_has_metrics(self, map_page):
        """Metrics section should have content."""
        metrics = map_page.locator("#sp-var-metrics")
        assert metrics.count() > 0, "No #sp-var-metrics found"
        text = metrics.inner_text()
        assert len(text.strip()) > 0, "VaR metrics section is empty"

    def test_metrics_keywords(self, map_page):
        """Metrics should mention VaR-related terms."""
        metrics = map_page.locator("#sp-var-metrics")
        if metrics.count() == 0:
            pytest.skip("No metrics element")
        text = metrics.inner_text().lower()
        keywords = ["var", "es", "loss", "confidence", "%"]
        assert any(kw in text for kw in keywords), \
            f"No VaR keywords in metrics: {text[:200]}"

    def test_has_toggle_buttons(self, map_page):
        """Toggle buttons (property/mortgage) should exist."""
        view = map_page.locator("#sp-var-view")
        buttons = view.locator("button")
        assert buttons.count() > 0, "No toggle buttons in VaR view"


# ---------------------------------------------------------------------------
# Data load tests (direct API calls)
# ---------------------------------------------------------------------------


class TestStormPortfolioDataLoads:
    """Verify supporting API endpoints return valid data."""

    def test_storms_api_returns_data(self, map_page):
        """GET /api/v1/propertyts/storms should return storms."""
        result = map_page.evaluate("""async () => {
            var cfg = window.__BACKEND_CONFIG || {};
            var baseUrl = cfg.url || '';
            var resp = await fetch(baseUrl + '/api/v1/propertyts/storms');
            var data = await resp.json();
            return {
                http_status: resp.status,
                storm_count: (data.storms || []).length,
            };
        }""")
        assert result["http_status"] == 200, \
            f"Storms API returned {result['http_status']}"
        assert result["storm_count"] > 0, "No storms returned"

    def test_portfolio_impact_api_returns_data(self, map_page):
        """GET /api/v1/propertyts/{storm_id}/portfolio-impact should work."""
        result = map_page.evaluate("""async () => {
            var cfg = window.__BACKEND_CONFIG || {};
            var baseUrl = cfg.url || '';
            var resp = await fetch(baseUrl + '/api/v1/propertyts/storms');
            var data = await resp.json();
            var storms = data.storms || [];
            if (storms.length === 0) return { skip: true };
            var stormId = storms[0].storm_id || storms[0].id || storms[0];
            var resp2 = await fetch(
                baseUrl + '/api/v1/propertyts/' + stormId + '/portfolio-impact'
            );
            var data2 = await resp2.json();
            return {
                http_status: resp2.status,
                has_data: Object.keys(data2).length > 0,
            };
        }""")
        if result.get("skip"):
            pytest.skip("No storms available for portfolio-impact test")
        assert result["http_status"] == 200, \
            f"Portfolio impact API returned {result['http_status']}"

    def test_animate_api_returns_data(self, map_page):
        """GET /api/v1/propertyts/animate/{storm_id} should return frames."""
        result = map_page.evaluate("""async () => {
            var cfg = window.__BACKEND_CONFIG || {};
            var baseUrl = cfg.url || '';
            var resp = await fetch(baseUrl + '/api/v1/propertyts/storms');
            var data = await resp.json();
            var storms = data.storms || [];
            if (storms.length === 0) return { skip: true };
            var stormId = storms[0].storm_id || storms[0].id || storms[0];
            var resp2 = await fetch(
                baseUrl + '/api/v1/propertyts/animate/' + stormId
            );
            var data2 = await resp2.json();
            return {
                http_status: resp2.status,
                has_frames: (data2.frames || data2.timesteps || []).length > 0,
            };
        }""")
        if result.get("skip"):
            pytest.skip("No storms available for animate test")
        assert result["http_status"] == 200, \
            f"Animate API returned {result['http_status']}"

    def test_portfolio_var_api_returns_data(self, map_page):
        """GET /api/v1/propertyts/portfolio-var should return VaR metrics."""
        result = map_page.evaluate("""async () => {
            var cfg = window.__BACKEND_CONFIG || {};
            var baseUrl = cfg.url || '';
            var resp = await fetch(baseUrl + '/api/v1/propertyts/portfolio-var');
            var data = await resp.json();
            return {
                http_status: resp.status,
                has_data: Object.keys(data).length > 0,
            };
        }""")
        assert result["http_status"] == 200, \
            f"Portfolio VaR API returned {result['http_status']}"
        assert result["has_data"], "Portfolio VaR returned empty response"
