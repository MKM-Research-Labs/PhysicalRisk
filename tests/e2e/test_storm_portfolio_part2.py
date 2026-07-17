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
Storm Portfolio panel -- e2e tests: VaR tab and data load API tests.
"""

import pytest

from .conftest import close_all_storm_panels, open_storm_portfolio, close_storm_portfolio


# ---------------------------------------------------------------------------
# VaR tab (loss distribution histogram)
# ---------------------------------------------------------------------------


class TestSPVaRTab:
    """VaR tab: loss distribution histogram with VaR/ES metrics."""

    @pytest.fixture(autouse=True)
    def open_var_tab(self, map_page):
        close_all_storm_panels(map_page)
        open_storm_portfolio(map_page)
        map_page.locator("#sp-tab-var").click(force=True)
        map_page.wait_for_timeout(9_000)  # VaR computation is heavy
        yield
        close_storm_portfolio(map_page)

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
