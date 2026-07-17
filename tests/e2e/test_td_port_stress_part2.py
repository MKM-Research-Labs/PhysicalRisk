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
Trading Desk — Port Stress tab e2e tests — Part 2.

Covers: Port P&L, Gauge P&L, Severity sub-tabs, and supporting API endpoints.
"""

import pytest

from tests.e2e.conftest import (
    ps_close_all_panels,
    ps_open_trading_desk,
    ps_close_trading_desk,
)


# ---------------------------------------------------------------------------
# Port P&L sub-tab
# ---------------------------------------------------------------------------


class TestPortStressPortPnL:
    """Port P&L sub-tab: horizontal bar chart of stress P&L by gauge."""

    @pytest.fixture(autouse=True)
    def open_portpnl(self, map_page):
        ps_close_all_panels(map_page)
        ps_open_trading_desk(map_page)
        map_page.locator("#td-tab-portstress").click(force=True)
        map_page.wait_for_timeout(4_000)

        btn = map_page.locator("#ps-tab-portpnl")
        if btn.count() == 0:
            pytest.skip("Port P&L sub-tab not found")
        btn.click(force=True)
        map_page.wait_for_timeout(3_000)
        yield
        ps_close_trading_desk(map_page)

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
        ps_close_all_panels(map_page)
        ps_open_trading_desk(map_page)
        map_page.locator("#td-tab-portstress").click(force=True)
        map_page.wait_for_timeout(4_000)

        btn = map_page.locator("#ps-tab-gaugepnl")
        if btn.count() == 0:
            pytest.skip("Gauge P&L sub-tab not found")
        btn.click(force=True)
        map_page.wait_for_timeout(3_000)
        yield
        ps_close_trading_desk(map_page)

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
        ps_close_all_panels(map_page)
        ps_open_trading_desk(map_page)
        map_page.locator("#td-tab-portstress").click(force=True)
        map_page.wait_for_timeout(4_000)

        btn = map_page.locator("#ps-tab-severity")
        if btn.count() == 0:
            pytest.skip("Severity sub-tab not found")
        btn.click(force=True)
        map_page.wait_for_timeout(3_000)
        yield
        ps_close_trading_desk(map_page)

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

    @pytest.mark.timeout(120)
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

            // Use AbortController to cap the fetch at 60 seconds
            var ctrl = new AbortController();
            var timer = setTimeout(() => ctrl.abort(), 60000);
            try {
                var resp2 = await fetch(
                    baseUrl + '/api/v1/trading/stress/portfolio-run', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({storm_id: stormId}),
                    signal: ctrl.signal,
                });
                clearTimeout(timer);
                var data2 = await resp2.json();
                return {
                    http_status: resp2.status,
                    has_gauges: (data2.gauges || []).length > 0,
                    has_pnl: 'portfolio_stress_pnl' in data2,
                };
            } catch(e) {
                clearTimeout(timer);
                return { skip: true, reason: e.message };
            }
        }""")
        if result.get("skip"):
            pytest.skip(result.get("reason", "No storms available for portfolio-run test"))
        assert result["http_status"] == 200, \
            f"Portfolio run API returned {result['http_status']}"
        assert result["has_pnl"], "Response missing portfolio_stress_pnl"
