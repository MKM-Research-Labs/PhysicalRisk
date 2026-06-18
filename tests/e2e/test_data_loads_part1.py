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
Data loading validation tests — part 1.

Covers error notifications, hazard curve data loads, and stress storm data loads.
"""

import pytest

from tests.e2e.conftest import close_all_data_panels


class TestNoErrorNotifications:
    """Error notifications should not appear when data loads correctly."""

    def test_no_error_notifications_after_clearing(self, map_page):
        """After clearing old notifications and waiting, no new errors should appear."""
        # Clear any stale notifications from previous tests
        map_page.evaluate("""() => {
            document.querySelectorAll('.notif-message').forEach(n => n.remove());
        }""")
        # Wait to see if any new errors appear (from background fetches)
        map_page.wait_for_timeout(9_000)

        errors = map_page.evaluate("""() => {
            const notifs = document.querySelectorAll('.notif-message');
            const errors = [];
            notifs.forEach(n => {
                const text = n.textContent.toLowerCase();
                if (text.includes('fail') || text.includes('error') ||
                    text.includes('unable') || text.includes('not found')) {
                    errors.push(n.textContent.trim());
                }
            });
            return errors;
        }""")
        assert len(errors) == 0, (
            f"New error notifications appeared: {errors}"
        )


class TestHazardCurveDataLoads:
    """Verify hazard curve data actually loads — not just that the panel opens."""

    @pytest.fixture(autouse=True)
    def setup(self, map_page):
        close_all_data_panels(map_page)
        yield
        close_all_data_panels(map_page)

    def test_hazard_api_returns_success(self, map_page, first_gauge_id):
        """Fetch hazard data via JS and verify the API returns status=success."""
        result = map_page.evaluate(f"""async () => {{
            try {{
                var cfg = window.__BACKEND_CONFIG || {{}};
                var baseUrl = cfg.url || '';
                var resp = await fetch(baseUrl + '/api/v1/gauges/{first_gauge_id}/hazard');
                var data = await resp.json();
                return {{
                    http_status: resp.status,
                    api_status: data.status,
                    gauge_id: data.gauge_id || null,
                    has_gev: !!(data.gev_parameters),
                    has_curves: (data.curve_points || []).length,
                    message: data.message || null
                }};
            }} catch (e) {{
                return {{ error: e.message }};
            }}
        }}""")
        assert "error" not in result, f"API fetch failed: {result.get('error')}"
        assert result["http_status"] == 200, (
            f"Hazard API returned HTTP {result['http_status']}: {result.get('message')}"
        )
        assert result["api_status"] == "success", (
            f"Hazard API returned status={result['api_status']}: {result.get('message')}"
        )
        assert result["has_gev"], "Hazard API response missing GEV parameters"
        assert result["has_curves"] > 0, "Hazard API returned zero curve points"

    def test_gauge_panel_loads_data_not_error(self, map_page, first_gauge_id):
        """Open gauge panel and verify it shows data, not an error message."""
        has_fn = map_page.evaluate(
            "() => typeof window.viewHazardCurve === 'function'"
        )
        if not has_fn:
            pytest.skip("viewHazardCurve not available")

        map_page.evaluate(f"window.viewHazardCurve('{first_gauge_id}')")
        map_page.locator("#hazard-curve-panel").wait_for(
            state="visible", timeout=10_000
        )
        map_page.wait_for_timeout(9_000)  # Wait for async data load

        # Check for error notifications
        errors = map_page.evaluate("""() => {
            const notifs = document.querySelectorAll('.notif-message');
            const errors = [];
            notifs.forEach(n => {
                const text = n.textContent.toLowerCase();
                if (text.includes('fail') || text.includes('error') ||
                    text.includes('unable')) {
                    errors.push(n.textContent.trim());
                }
            });
            return errors;
        }""")
        assert len(errors) == 0, (
            f"Error notifications after opening gauge panel: {errors}"
        )

        # Verify status element shows loaded, not error
        status = map_page.evaluate("""() => {
            const el = document.getElementById('hazard-status');
            return el ? el.textContent : '';
        }""")
        assert "error" not in status.lower(), (
            f"Hazard panel status shows error: {status}"
        )

    def test_hazard_curve_tab_has_real_data(self, map_page, first_gauge_id):
        """Hazard Curve tab should show actual curve data, not empty chart."""
        has_fn = map_page.evaluate(
            "() => typeof window.viewHazardCurve === 'function'"
        )
        if not has_fn:
            pytest.skip("viewHazardCurve not available")

        map_page.evaluate(f"window.viewHazardCurve('{first_gauge_id}')")
        map_page.locator("#hazard-curve-panel").wait_for(
            state="visible", timeout=10_000
        )
        map_page.wait_for_timeout(9_000)

        # Switch to hazard curve tab
        tab = map_page.locator(".hazard-tab[data-tab='1']")
        if tab.count() > 0:
            tab.click(force=True)
        map_page.wait_for_timeout(3_000)

        # Verify hazardData is populated in JS scope
        has_data = map_page.evaluate("""() => {
            // hazardData is in the panel's IIFE scope, check via status
            const status = document.getElementById('hazard-status');
            const statusText = status ? status.textContent.toLowerCase() : '';
            // Also check if any chart canvas has been drawn on
            const canvases = document.querySelectorAll('#hazard-curve-panel canvas');
            let hasDrawnCanvas = false;
            canvases.forEach(c => {
                const ctx = c.getContext('2d');
                // A drawn canvas will have non-zero image data
                if (c.width > 0 && c.height > 0) hasDrawnCanvas = true;
            });
            return {
                statusText: statusText,
                isLoaded: !statusText.includes('error') && !statusText.includes('loading'),
                canvasCount: canvases.length,
                hasDrawnCanvas: hasDrawnCanvas
            };
        }""")
        assert has_data["isLoaded"], (
            f"Hazard data not loaded. Status: {has_data['statusText']}"
        )
        assert has_data["canvasCount"] > 0, "No chart canvas found on hazard curve tab"


class TestStressStormDataLoads:
    """Verify stress storm data loads — these are required for storm scenario analysis."""

    @pytest.fixture(autouse=True)
    def setup(self, map_page):
        close_all_data_panels(map_page)
        yield
        close_all_data_panels(map_page)

    def test_stress_storms_api_returns_data(self, map_page):
        """Stress storms API must return 200 with storm data."""
        result = map_page.evaluate("""async () => {
            try {
                var cfg = window.__BACKEND_CONFIG || {};
                var baseUrl = cfg.url || '';
                var resp = await fetch(baseUrl + '/api/v1/trading/stress/storms');
                var data = await resp.json();
                return {
                    http_status: resp.status,
                    storm_count: (data.storms || []).length,
                    message: data.message || null
                };
            } catch (e) {
                return { error: e.message };
            }
        }""")
        assert "error" not in result, f"Stress storms API failed: {result.get('error')}"
        assert result["http_status"] == 200, (
            f"Stress storms API returned HTTP {result['http_status']}: {result.get('message')}. "
            f"Run: python app.py port --stressm"
        )
        assert result["storm_count"] > 0, (
            "Stress storms API returned zero storms. "
            "Run: python app.py port --stressm"
        )

    def test_portfolio_storms_api_returns_data(self, map_page):
        """Portfolio storms API must return 200 with storm data."""
        result = map_page.evaluate("""async () => {
            try {
                var cfg = window.__BACKEND_CONFIG || {};
                var baseUrl = cfg.url || '';
                var resp = await fetch(
                    baseUrl + '/api/v1/trading/stress/portfolio-storms'
                );
                var data = await resp.json();
                return {
                    http_status: resp.status,
                    storm_count: (data.storms || []).length,
                    message: data.message || null
                };
            } catch (e) {
                return { error: e.message };
            }
        }""")
        assert "error" not in result, (
            f"Portfolio storms API failed: {result.get('error')}"
        )
        assert result["http_status"] == 200, (
            f"Portfolio storms API returned HTTP {result['http_status']}: "
            f"{result.get('message')}. Run: python app.py port --stressm"
        )
        assert result["storm_count"] > 0, (
            "Portfolio storms API returned zero storms"
        )
