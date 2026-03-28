# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

"""
Trading Desk — Port Stress tab e2e tests.

Covers: panel structure, storm selector, 4 sub-tabs (P(flood), Port P&L,
Gauge P&L, Severity), and supporting API endpoints.
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
        state="visible", timeout=10_000
    )
    page.wait_for_timeout(3_000)


def _close_trading_desk(page):
    """Close the trading desk panel via JS."""
    page.evaluate("""() => {
        const el = document.getElementById('trading-desk-panel');
        if (el) el.style.display = 'none';
    }""")


# ---------------------------------------------------------------------------
# Port Stress tab — structure
# ---------------------------------------------------------------------------


class TestPortStressTab:
    """Port Stress tab: storm selector, sub-tabs, charts."""

    @pytest.fixture(autouse=True)
    def open_port_stress_tab(self, map_page):
        _close_all_panels(map_page)
        _open_trading_desk(map_page)
        map_page.locator("#td-tab-portstress").click(force=True)
        map_page.wait_for_timeout(4_000)  # storm load
        yield
        _close_trading_desk(map_page)

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
        _close_all_panels(map_page)
        _open_trading_desk(map_page)
        map_page.locator("#td-tab-portstress").click(force=True)
        map_page.wait_for_timeout(4_000)

        btn = map_page.locator("#ps-tab-pflood")
        if btn.count() == 0:
            pytest.skip("P(flood) sub-tab not found")
        btn.click(force=True)
        map_page.wait_for_timeout(3_000)
        yield
        _close_trading_desk(map_page)

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


# ---------------------------------------------------------------------------
# Port P&L sub-tab
# ---------------------------------------------------------------------------


class TestPortStressPortPnL:
    """Port P&L sub-tab: horizontal bar chart of stress P&L by gauge."""

    @pytest.fixture(autouse=True)
    def open_portpnl(self, map_page):
        _close_all_panels(map_page)
        _open_trading_desk(map_page)
        map_page.locator("#td-tab-portstress").click(force=True)
        map_page.wait_for_timeout(4_000)

        btn = map_page.locator("#ps-tab-portpnl")
        if btn.count() == 0:
            pytest.skip("Port P&L sub-tab not found")
        btn.click(force=True)
        map_page.wait_for_timeout(3_000)
        yield
        _close_trading_desk(map_page)

    def test_portpnl_has_content(self, map_page):
        """Port P&L tab should render content."""
        content = map_page.locator("#ps-content")
        text = content.inner_text()
        has_content = (
            len(text.strip()) > 0
            or content.locator("canvas").count() > 0
        )
        assert has_content, "Port P&L tab is empty"

    def test_portpnl_mentions_pnl_keywords(self, map_page):
        """Should mention P&L-related terms."""
        content = map_page.locator("#ps-content")
        text = content.inner_text().lower()
        keywords = ["p&l", "pnl", "stress", "mtm", "portfolio", "gauge"]
        has_keywords = (
            any(kw in text for kw in keywords)
            or content.locator("canvas").count() > 0
        )
        assert has_keywords, f"No P&L keywords in Port P&L tab: {text[:200]}"


# ---------------------------------------------------------------------------
# Gauge P&L sub-tab
# ---------------------------------------------------------------------------


class TestPortStressGaugePnL:
    """Gauge P&L sub-tab: trade-level table for a selected gauge."""

    @pytest.fixture(autouse=True)
    def open_gaugepnl(self, map_page):
        _close_all_panels(map_page)
        _open_trading_desk(map_page)
        map_page.locator("#td-tab-portstress").click(force=True)
        map_page.wait_for_timeout(4_000)

        btn = map_page.locator("#ps-tab-gaugepnl")
        if btn.count() == 0:
            pytest.skip("Gauge P&L sub-tab not found")
        btn.click(force=True)
        map_page.wait_for_timeout(3_000)
        yield
        _close_trading_desk(map_page)

    def test_gaugepnl_has_content(self, map_page):
        """Gauge P&L tab should render content."""
        content = map_page.locator("#ps-content")
        text = content.inner_text()
        has_content = (
            len(text.strip()) > 0
            or content.locator("table").count() > 0
        )
        assert has_content, "Gauge P&L tab is empty"

    def test_gaugepnl_has_gauge_selector_or_table(self, map_page):
        """Should have a gauge dropdown or trade table."""
        content = map_page.locator("#ps-content")
        selects = content.locator("select")
        tables = content.locator("table")
        has_controls = selects.count() > 0 or tables.count() > 0
        if not has_controls:
            text = content.inner_text().lower()
            has_controls = "gauge" in text or "trade" in text or "swap" in text
        assert has_controls, "No gauge selector or trade table in Gauge P&L"


# ---------------------------------------------------------------------------
# Severity sub-tab
# ---------------------------------------------------------------------------


class TestPortStressSeverity:
    """Severity sub-tab: gauges grouped by severe/warning/alert/clean."""

    @pytest.fixture(autouse=True)
    def open_severity(self, map_page):
        _close_all_panels(map_page)
        _open_trading_desk(map_page)
        map_page.locator("#td-tab-portstress").click(force=True)
        map_page.wait_for_timeout(4_000)

        btn = map_page.locator("#ps-tab-severity")
        if btn.count() == 0:
            pytest.skip("Severity sub-tab not found")
        btn.click(force=True)
        map_page.wait_for_timeout(3_000)
        yield
        _close_trading_desk(map_page)

    def test_severity_has_content(self, map_page):
        """Severity tab should render content."""
        content = map_page.locator("#ps-content")
        text = content.inner_text()
        has_content = len(text.strip()) > 0
        assert has_content, "Severity tab is empty"

    def test_severity_mentions_threshold_keywords(self, map_page):
        """Should mention severity threshold terms."""
        content = map_page.locator("#ps-content")
        text = content.inner_text().lower()
        keywords = ["severe", "warning", "alert", "clean", "gauge", "flood"]
        assert any(kw in text for kw in keywords), \
            f"No severity keywords in tab: {text[:200]}"


# ---------------------------------------------------------------------------
# Data load tests (direct API calls)
# ---------------------------------------------------------------------------


class TestPortStressDataLoads:
    """Verify supporting API endpoints return valid data."""

    def test_classifier_readiness_api(self, map_page):
        """GET /api/v1/trading/classifiers/readiness should return status."""
        result = map_page.evaluate("""async () => {
            var cfg = window.__BACKEND_CONFIG || {};
            var baseUrl = cfg.url || '';
            var resp = await fetch(
                baseUrl + '/api/v1/trading/classifiers/readiness'
            );
            var data = await resp.json();
            return {
                http_status: resp.status,
                has_ready: 'ready' in data,
                has_trained: 'trained' in data,
                has_total: 'total' in data,
            };
        }""")
        assert result["http_status"] == 200, \
            f"Readiness API returned {result['http_status']}"
        assert result["has_ready"], "Response missing 'ready' field"

    def test_portfolio_storms_api(self, map_page):
        """GET /api/v1/trading/stress/portfolio-storms should return storms."""
        result = map_page.evaluate("""async () => {
            var cfg = window.__BACKEND_CONFIG || {};
            var baseUrl = cfg.url || '';
            var resp = await fetch(
                baseUrl + '/api/v1/trading/stress/portfolio-storms'
            );
            var data = await resp.json();
            return {
                http_status: resp.status,
                storm_count: (data.storms || []).length,
            };
        }""")
        assert result["http_status"] == 200, \
            f"Portfolio storms API returned {result['http_status']}"
        assert result["storm_count"] > 0, "No portfolio storms returned"

    def test_portfolio_run_api(self, map_page):
        """POST /api/v1/trading/stress/portfolio-run should return results."""
        result = map_page.evaluate("""async () => {
            var cfg = window.__BACKEND_CONFIG || {};
            var baseUrl = cfg.url || '';
            // First get a storm ID
            var resp1 = await fetch(
                baseUrl + '/api/v1/trading/stress/portfolio-storms'
            );
            var data1 = await resp1.json();
            var storms = data1.storms || [];
            if (storms.length === 0) return { skip: true };
            var stormId = storms[0].storm_id || storms[0].id;

            var resp2 = await fetch(
                baseUrl + '/api/v1/trading/stress/portfolio-run', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({storm_id: stormId}),
            });
            var data2 = await resp2.json();
            return {
                http_status: resp2.status,
                has_gauges: (data2.gauges || []).length > 0,
                has_pnl: 'portfolio_stress_pnl' in data2,
            };
        }""")
        if result.get("skip"):
            pytest.skip("No storms available for portfolio-run test")
        assert result["http_status"] == 200, \
            f"Portfolio run API returned {result['http_status']}"
        assert result["has_pnl"], "Response missing portfolio_stress_pnl"
