# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

"""
Storm Portfolio — Control tab e2e tests.

Verifies that the Storm Sequence Control tab opens in the Storm Portfolio
panel, displays parameter sections, loads data from the API, and supports
save/reset interactions.

Save and Reset require an admin password (same credential as ``python app.py
port``); the conftest ``_e2e_admin_password`` session fixture installs a
known one at ``data/.port_admin``. Tests below stub ``window.prompt`` to
return it.
"""

import pytest

from .conftest import E2E_ADMIN_PW


def _stub_prompt(page, value):
    """Replace window.prompt on the page so save/reset skip the interactive dialog."""
    page.evaluate(
        "(v) => { window.prompt = function() { return v; }; }",
        value,
    )


# ---------------------------------------------------------------------------
# Helpers
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
    page.evaluate(CLOSE_PANELS_JS)


def _open_storm_portfolio(page):
    """Open the Storm Portfolio panel via window.showStormPortfolio()."""
    page.evaluate("() => { if (window.showStormPortfolio) window.showStormPortfolio(); }")
    page.locator("#storm-portfolio-panel").wait_for(
        state="visible", timeout=10_000
    )


def _close_storm_portfolio(page):
    page.evaluate("""() => {
        const el = document.getElementById('storm-portfolio-panel');
        if (el) el.style.display = 'none';
    }""")


# ---------------------------------------------------------------------------
# Control tab — structure and rendering
# ---------------------------------------------------------------------------




class TestControlFlowThrough:
    """Control value must propagate to consumers — single source of truth.

    Guards against the regression where FloodPoly (and any other client-side
    consumer) hardcoded 168 while the Control tab saved a different value.
    """

    @pytest.fixture(autouse=True)
    def setup(self, map_page):
        _close_all_panels(map_page)
        yield
        _close_all_panels(map_page)

    def test_control_hours_matches_backend(self, map_page):
        """window.__STORM_CONTROL_HOURS (populated on startup) must equal the API value."""
        # Give startup preload a moment to complete
        map_page.wait_for_timeout(500)
        result = map_page.evaluate("""async () => {
            var cfg = window.__BACKEND_CONFIG || {};
            var base = cfg.url || '';
            var resp = await fetch(base + '/api/v1/trading/control/params');
            var data = await resp.json();
            var apiHrs = data.params.sections.storm_generation.event_window_hours;
            return {api: apiHrs, window: window.__STORM_CONTROL_HOURS};
        }""")
        assert result['window'] == result['api'], (
            f"window.__STORM_CONTROL_HOURS={result['window']} but API returned "
            f"{result['api']} — client-side FloodPoly would use a stale value."
        )


# ---------------------------------------------------------------------------
# Control tab — API integration
# ---------------------------------------------------------------------------


class TestControlAPI:
    """Control tab API returns valid parameter data."""

    @pytest.fixture(autouse=True)
    def setup(self, map_page):
        _close_all_panels(map_page)
        yield
        _close_all_panels(map_page)

    def test_control_params_api_returns_data(self, map_page):
        """GET /trading/control/params should return parameter sections."""
        result = map_page.evaluate("""async () => {
            try {
                var cfg = window.__BACKEND_CONFIG || {};
                var baseUrl = cfg.url || '';
                var resp = await fetch(baseUrl + '/api/v1/trading/control/params');
                var data = await resp.json();
                var sections = data.params && data.params.sections
                    ? Object.keys(data.params.sections) : [];
                return {
                    http_status: resp.status,
                    status: data.status,
                    source: data.source,
                    section_count: sections.length,
                    sections: sections,
                    version: data.params ? data.params.version : null
                };
            } catch (e) {
                return { error: e.message };
            }
        }""")
        assert "error" not in result, (
            f"Control params API failed: {result.get('error')}"
        )
        assert result["http_status"] == 200, (
            f"Control params returned HTTP {result['http_status']}"
        )
        assert result["status"] == "success"
        assert result["section_count"] == 5, (
            f"Expected 5 sections, got {result['section_count']}: "
            f"{result['sections']}"
        )
        expected = {
            "storm_generation",
            "hydrograph_synthesis",
            "gauge_propagation",
            "spatial_correlation",
            "stress_catalogue",
        }
        assert set(result["sections"]) == expected

    def test_control_params_contain_key_values(self, map_page):
        """Parameter values should match expected defaults.

        The session-level ``_isolated_catchment_dir`` fixture copies the
        catchment dir to tmp and removes ``storm_control.json`` there, so
        the server starts with no overlay and the API reports the Python
        source constants rather than any prior mutation.
        """
        result = map_page.evaluate("""async () => {
            try {
                var cfg = window.__BACKEND_CONFIG || {};
                var baseUrl = cfg.url || '';
                var resp = await fetch(baseUrl + '/api/v1/trading/control/params');
                var data = await resp.json();
                var sg = data.params.sections.storm_generation;
                var gp = data.params.sections.gauge_propagation;
                return {
                    event_window_hours: sg.event_window_hours,
                    intensity_variation: sg.intensity_variation,
                    default_roughness: gp.default_roughness,
                    n_nearest_gauges: gp.n_nearest_gauges,
                    bankfull_offset_m: gp.bankfull_offset_m
                };
            } catch (e) {
                return { error: e.message };
            }
        }""")
        assert "error" not in result, (
            f"Control params API failed: {result.get('error')}"
        )
        assert result["event_window_hours"] == 168
        assert result["intensity_variation"] == 0.20
        assert result["default_roughness"] == 0.04
        assert result["n_nearest_gauges"] == 3
        assert result["bankfull_offset_m"] == 0.5

    def test_guide_pdf_endpoints_respond(self, map_page):
        """All 6 user guide PDF endpoints should return 200 or 404."""
        guide_keys = [
            "storm-control",
            "gauge-prs-pricing",
            "property-prs-pricing",
            "market-making",
            "eod-process",
            "stress-testing",
        ]
        result = map_page.evaluate("""async (keys) => {
            var cfg = window.__BACKEND_CONFIG || {};
            var baseUrl = cfg.url || '';
            var results = {};
            for (var i = 0; i < keys.length; i++) {
                try {
                    var resp = await fetch(
                        baseUrl + '/api/v1/governance/' + keys[i] + '/guide/pdf'
                    );
                    results[keys[i]] = {
                        http_status: resp.status,
                        content_type: resp.headers.get('content-type')
                    };
                } catch (e) {
                    results[keys[i]] = { error: e.message };
                }
            }
            return results;
        }""", guide_keys)

        for key in guide_keys:
            r = result[key]
            assert "error" not in r, (
                f"{key} guide request failed: {r.get('error')}"
            )
            assert r["http_status"] in (200, 404), (
                f"{key}: unexpected HTTP {r['http_status']}"
            )
            if r["http_status"] == 200:
                assert "pdf" in r["content_type"].lower(), (
                    f"{key}: expected PDF content type, got {r['content_type']}"
                )

    def test_unknown_guide_returns_404(self, map_page):
        """Unknown guide key should return 404."""
        result = map_page.evaluate("""async () => {
            var cfg = window.__BACKEND_CONFIG || {};
            var baseUrl = cfg.url || '';
            var resp = await fetch(baseUrl + '/api/v1/governance/nonexistent/guide/pdf');
            return { http_status: resp.status };
        }""")
        assert result["http_status"] == 404
