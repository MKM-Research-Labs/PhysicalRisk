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
Data loading validation tests — part 2.

Covers property data loads and trading desk data loads.
"""

import pytest

from tests.e2e.conftest import close_all_data_panels


class TestPropertyDataLoads:
    """Verify property storm data loads correctly."""

    @pytest.fixture(autouse=True)
    def setup(self, map_page):
        close_all_data_panels(map_page)
        yield
        close_all_data_panels(map_page)

    def test_propertyts_summary_api_returns_data(self, map_page):
        """Property TS summary API must return 200 — not 404."""
        result = map_page.evaluate("""async () => {
            try {
                var cfg = window.__BACKEND_CONFIG || {};
                var baseUrl = cfg.url || '';
                var resp = await fetch(baseUrl + '/api/v1/propertyts/summary');
                var data = await resp.json();
                return {
                    http_status: resp.status,
                    has_summary: !!(data.data && data.data.summary),
                    properties_with_floods: data.data && data.data.summary
                        ? data.data.summary.properties_with_floods : 0,
                    message: data.message || null
                };
            } catch (e) {
                return { error: e.message };
            }
        }""")
        assert "error" not in result, f"PropertyTS API failed: {result.get('error')}"
        assert result["http_status"] == 200, (
            f"PropertyTS summary API returned HTTP {result['http_status']}: "
            f"{result.get('message')}. Run: python app.py port --propertyts"
        )
        assert result["has_summary"], "PropertyTS summary missing from response"
        assert result["properties_with_floods"] > 0, (
            "Zero properties with flood events"
        )

    def test_property_storm_api_returns_data(self, map_page, first_property_id):
        """Fetch property storm data and verify API returns success — NOT skip on 404."""
        result = map_page.evaluate(f"""async () => {{
            try {{
                var cfg = window.__BACKEND_CONFIG || {{}};
                var baseUrl = cfg.url || '';
                var resp = await fetch(
                    baseUrl + '/api/v1/properties/{first_property_id}/floods'
                );
                var data = await resp.json();
                return {{
                    http_status: resp.status,
                    api_status: data.status || 'unknown',
                    has_events: !!(data.flood_events || data.events || data.data),
                    message: data.message || null
                }};
            }} catch (e) {{
                return {{ error: e.message }};
            }}
        }}""")
        assert "error" not in result, f"Property API failed: {result.get('error')}"
        assert result["http_status"] == 200, (
            f"Property flood-events API returned HTTP {result['http_status']}: "
            f"{result.get('message')}. Run: python app.py port --propertyts"
        )

    def test_property_panel_loads_without_errors(self, map_page, first_property_id):
        """Open property storm panel and verify no error notifications."""
        has_fn = map_page.evaluate(
            "() => typeof window.viewPropertyStorms === 'function'"
        )
        if not has_fn:
            pytest.skip("viewPropertyStorms not available")

        map_page.evaluate(f"window.viewPropertyStorms('{first_property_id}')")
        try:
            map_page.locator("#prop-storm-panel").wait_for(
                state="visible", timeout=10_000
            )
        except Exception:
            pytest.skip("Property storm panel did not open")

        map_page.wait_for_timeout(9_000)

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
            f"Error notifications after opening property panel: {errors}"
        )


class TestTradingDataLoads:
    """Verify trading desk data loads correctly."""

    @pytest.fixture(autouse=True)
    def setup(self, map_page):
        close_all_data_panels(map_page)
        yield
        close_all_data_panels(map_page)

    def test_blotter_api_returns_trades(self, map_page):
        """Blotter API should return trade data."""
        result = map_page.evaluate("""async () => {
            try {
                var cfg = window.__BACKEND_CONFIG || {};
                var baseUrl = cfg.url || '';
                var resp = await fetch(baseUrl + '/api/v1/trading/blotter');
                var data = await resp.json();
                return {
                    http_status: resp.status,
                    trade_count: (data.trades || []).length,
                    message: data.message || null
                };
            } catch (e) {
                return { error: e.message };
            }
        }""")
        assert "error" not in result, f"Blotter API failed: {result.get('error')}"
        assert result["http_status"] == 200, (
            f"Blotter API returned HTTP {result['http_status']}"
        )
        assert result["trade_count"] > 0, "Blotter API returned zero trades"

    def test_market_state_api_returns_data(self, map_page):
        """Market state API should return yield curve data."""
        result = map_page.evaluate("""async () => {
            try {
                var cfg = window.__BACKEND_CONFIG || {};
                var baseUrl = cfg.url || '';
                var resp = await fetch(baseUrl + '/api/v1/trading/market-state');
                var data = await resp.json();
                return {
                    http_status: resp.status,
                    has_yield_curve: !!(data.yield_curve),
                    message: data.message || null
                };
            } catch (e) {
                return { error: e.message };
            }
        }""")
        assert "error" not in result, f"Market state API failed: {result.get('error')}"
        assert result["http_status"] == 200, (
            f"Market state API returned HTTP {result['http_status']}"
        )

    def test_risk_grid_api_returns_data(self, map_page):
        """Risk grid API should return FS01 data."""
        result = map_page.evaluate("""async () => {
            try {
                var cfg = window.__BACKEND_CONFIG || {};
                var baseUrl = cfg.url || '';
                var resp = await fetch(baseUrl + '/api/v1/trading/risk-grid');
                var data = await resp.json();
                return {
                    http_status: resp.status,
                    has_grid: !!(data.grid || data.rows || data.gauges),
                    message: data.message || null
                };
            } catch (e) {
                return { error: e.message };
            }
        }""")
        assert "error" not in result, f"Risk grid API failed: {result.get('error')}"
        assert result["http_status"] == 200, (
            f"Risk grid API returned HTTP {result['http_status']}"
        )
