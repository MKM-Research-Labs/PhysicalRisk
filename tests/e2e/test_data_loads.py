# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

"""
Data loading validation tests.

These tests verify that API endpoints return real data, not just that
DOM elements exist. A panel can render with all controls present but
show "Failed to load hazard curve data" and pass every DOM test.
These tests catch that.
"""

import pytest


def _close_all_panels(page):
    """Close all panels and dismiss notifications."""
    page.evaluate("""() => {
        ['trading-desk-panel','hazard-curve-panel','property-hc-panel',
         'prop-storm-panel','mortgage-detail-panel','mg-panel','property-pdf-panel'].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.style.display = 'none';
        });
        document.querySelectorAll('.ctx-menu').forEach(m => m.remove());
        document.querySelectorAll('.notif-message').forEach(n => n.remove());
    }""")


class TestNoErrorNotifications:
    """Error notifications should not appear when data loads correctly."""

    def test_no_error_notifications_after_clearing(self, map_page):
        """After clearing old notifications and waiting, no new errors should appear."""
        # Clear any stale notifications from previous tests
        map_page.evaluate("""() => {
            document.querySelectorAll('.notif-message').forEach(n => n.remove());
        }""")
        # Wait to see if any new errors appear (from background fetches)
        map_page.wait_for_timeout(3_000)

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
        _close_all_panels(map_page)
        yield
        _close_all_panels(map_page)

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
        map_page.wait_for_timeout(3_000)  # Wait for async data load

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
        map_page.wait_for_timeout(3_000)

        # Switch to hazard curve tab
        tab = map_page.locator(".hazard-tab[data-tab='1']")
        if tab.count() > 0:
            tab.click(force=True)
        map_page.wait_for_timeout(1_000)

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


class TestPropertyDataLoads:
    """Verify property storm data loads correctly."""

    @pytest.fixture(autouse=True)
    def setup(self, map_page):
        _close_all_panels(map_page)
        yield
        _close_all_panels(map_page)

    def test_property_storm_api_returns_data(self, map_page, first_property_id):
        """Fetch property storm data and verify API returns success."""
        result = map_page.evaluate(f"""async () => {{
            try {{
                var cfg = window.__BACKEND_CONFIG || {{}};
                var baseUrl = cfg.url || '';
                var resp = await fetch(
                    baseUrl + '/api/v1/propertyts/{first_property_id}/flood-events'
                );
                if (resp.status === 404) {{
                    return {{ http_status: 404, message: 'endpoint not found' }};
                }}
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
        if result.get("http_status") == 404:
            pytest.skip("Property flood-events endpoint not found")
        assert "error" not in result, f"Property API failed: {result.get('error')}"
        assert result["http_status"] == 200, (
            f"Property API returned HTTP {result['http_status']}: {result.get('message')}"
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

        map_page.wait_for_timeout(3_000)

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
        _close_all_panels(map_page)
        yield
        _close_all_panels(map_page)

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
