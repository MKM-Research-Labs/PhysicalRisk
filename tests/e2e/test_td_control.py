# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

"""
Storm Portfolio — Control tab e2e tests.

Verifies that the Storm Sequence Control tab opens in the Storm Portfolio
panel, displays parameter sections, loads data from the API, and supports
save/reset interactions.
"""

import pytest


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
    page.wait_for_timeout(3_000)


def _close_storm_portfolio(page):
    page.evaluate("""() => {
        const el = document.getElementById('storm-portfolio-panel');
        if (el) el.style.display = 'none';
    }""")


# ---------------------------------------------------------------------------
# Control tab — structure and rendering
# ---------------------------------------------------------------------------


class TestControlTab:
    """Control tab renders and loads storm control parameters."""

    @pytest.fixture(autouse=True)
    def open_control_tab(self, map_page):
        _close_all_panels(map_page)
        _open_storm_portfolio(map_page)
        map_page.locator("#sp-tab-control").click(force=True)
        map_page.wait_for_timeout(3_000)
        yield
        _close_storm_portfolio(map_page)

    def test_control_view_visible(self, map_page):
        """Control content area should be visible after clicking the tab."""
        view = map_page.locator("#sp-control-view")
        assert view.count() > 0, "No #sp-control-view element found"
        assert view.is_visible(), "#sp-control-view is not visible"

    def test_has_save_button(self, map_page):
        """Toolbar should contain the Save & Apply button."""
        btn = map_page.locator("#sp-ctrl-save-btn")
        assert btn.count() > 0, "No #sp-ctrl-save-btn found"
        assert btn.is_visible(), "Save & Apply button is not visible"

    def test_has_reset_button(self, map_page):
        """Toolbar should contain the Reset Defaults button."""
        btn = map_page.locator("#sp-ctrl-reset-btn")
        assert btn.count() > 0, "No #sp-ctrl-reset-btn found"
        assert btn.is_visible(), "Reset Defaults button is not visible"

    def test_has_all_five_sections(self, map_page):
        """All five parameter sections should be rendered."""
        section_ids = [
            "sp-ctrl-section-storm_generation",
            "sp-ctrl-section-hydrograph_synthesis",
            "sp-ctrl-section-gauge_propagation",
            "sp-ctrl-section-spatial_correlation",
            "sp-ctrl-section-stress_catalogue",
        ]
        for sid in section_ids:
            el = map_page.locator(f"#{sid}")
            assert el.count() > 0, f"Missing section: {sid}"

    def test_sections_have_inputs(self, map_page):
        """Each section should contain editable input fields."""
        body = map_page.locator("#sp-ctrl-body")
        inputs = body.locator("input[data-ctrl-key]")
        assert inputs.count() > 0, "No data-ctrl-key inputs found"

    def test_fields_have_help_tooltips(self, map_page):
        """Parameter fields should have ? help tooltips."""
        body = map_page.locator("#sp-ctrl-body")
        helps = body.locator("[id^='sp-ctrl-tip-']")
        assert helps.count() > 0, "No help tooltip popups found"

    def test_status_bar_shows_source(self, map_page):
        """Status bar should show the data source after loading."""
        bar = map_page.locator("#sp-ctrl-status")
        assert bar.count() > 0, "No #sp-ctrl-status found"
        text = bar.inner_text().lower()
        assert "source" in text, (
            f"Status bar should show source, got: {text}"
        )

    def test_dirty_indicator_hidden_initially(self, map_page):
        """Unsaved changes indicator should be hidden on initial load."""
        ind = map_page.locator("#sp-ctrl-dirty")
        assert ind.count() > 0, "No #sp-ctrl-dirty found"
        assert not ind.is_visible(), (
            "Dirty indicator should be hidden initially"
        )

    def test_section_collapse_toggle(self, map_page):
        """Clicking a section header should toggle its visibility."""
        sec = map_page.locator("#sp-ctrl-section-storm_generation")
        arrow = map_page.locator("#sp-ctrl-arrow-storm_generation")
        assert sec.is_visible(), "Section should be visible initially"

        # Click the header to collapse
        arrow.locator("..").click()
        map_page.wait_for_timeout(500)
        assert not sec.is_visible(), "Section should be hidden after collapse"

        # Click again to expand
        arrow.locator("..").click()
        map_page.wait_for_timeout(500)
        assert sec.is_visible(), "Section should be visible after expand"


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
        """Parameter values should match expected defaults."""
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
