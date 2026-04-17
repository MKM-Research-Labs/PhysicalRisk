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


class TestControlTab:
    """Control tab renders and loads storm control parameters."""

    @pytest.fixture(autouse=True)
    def open_control_tab(self, map_page):
        _close_all_panels(map_page)
        _open_storm_portfolio(map_page)
        map_page.locator("#sp-tab-control").click(force=True)
        map_page.locator("#sp-control-view").wait_for(
            state="attached", timeout=10_000
        )
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

    def test_has_user_guide_button(self, map_page):
        """Toolbar should contain the User Guide button."""
        btn = map_page.locator("#sp-ctrl-guide-btn")
        assert btn.count() > 0, "No #sp-ctrl-guide-btn found"
        assert btn.is_visible(), "User Guide button is not visible"
        text = btn.inner_text()
        assert "user guide" in text.lower(), (
            f"Expected 'User Guide' label, got: {text}"
        )

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
        sec.wait_for(state="hidden", timeout=3_000)
        assert not sec.is_visible(), "Section should be hidden after collapse"

        # Click again to expand
        arrow.locator("..").click()
        sec.wait_for(state="visible", timeout=3_000)
        assert sec.is_visible(), "Section should be visible after expand"

    def test_input_change_marks_dirty(self, map_page):
        """Changing an input value should show the dirty indicator."""
        ind = map_page.locator("#sp-ctrl-dirty")
        assert not ind.is_visible(), "Dirty should be hidden initially"

        # Find first number input and change its value
        first_input = map_page.locator("input[data-ctrl-key][type='number']").first
        first_input.fill("999")
        ind.wait_for(state="visible", timeout=3_000)
        assert ind.is_visible(), "Dirty indicator should appear after input change"

    def test_save_button_persists_and_clears_dirty(self, map_page):
        """Save button should POST changes (with admin password) and clear dirty."""
        ind = map_page.locator("#sp-ctrl-dirty")

        # Stub window.prompt to return the admin password set up in conftest
        _stub_prompt(map_page, E2E_ADMIN_PW)

        # Modify a value to make dirty
        first_input = map_page.locator("input[data-ctrl-key][type='number']").first
        original_value = first_input.input_value()
        first_input.fill("999")
        ind.wait_for(state="visible", timeout=3_000)
        assert ind.is_visible(), "Should be dirty after change"

        # Click Save
        save_btn = map_page.locator("#sp-ctrl-save-btn")
        save_btn.click()
        ind.wait_for(state="hidden", timeout=5_000)

        # Dirty indicator should clear after successful save
        assert not ind.is_visible(), "Dirty should clear after save"

        # Status bar should show 'json' source
        bar = map_page.locator("#sp-ctrl-status")
        bar_text = bar.inner_text().lower()
        assert "json" in bar_text or "saved" in bar_text, (
            f"Status bar should confirm save, got: {bar_text}"
        )

        # Restore original value
        first_input.fill(original_value)
        save_btn.click()
        ind.wait_for(state="hidden", timeout=5_000)

    def test_reset_button_reverts_to_defaults(self, map_page):
        """Reset button should revert all values to Python defaults."""
        # Stub both prompt (password) and confirm (reset-defaults dialog)
        _stub_prompt(map_page, E2E_ADMIN_PW)
        map_page.evaluate("() => { window.confirm = function() { return true; }; }")

        # Get a known default value
        result = map_page.evaluate("""async () => {
            var cfg = window.__BACKEND_CONFIG || {};
            var base = cfg.url || '';
            var resp = await fetch(base + '/api/v1/trading/control/params');
            var data = await resp.json();
            return data.params.sections.storm_generation.event_window_hours;
        }""")
        original = result

        # Modify event_window_hours
        ew_input = map_page.locator(
            "input[data-ctrl-key='storm_generation.event_window_hours']"
        )
        if ew_input.count() > 0:
            ew_input.fill("120")
            map_page.locator("#sp-ctrl-save-btn").click()
            map_page.locator("#sp-ctrl-dirty").wait_for(
                state="hidden", timeout=5_000
            )

            # Click reset (confirm + prompt already stubbed)
            map_page.locator("#sp-ctrl-reset-btn").click()
            map_page.locator("#sp-ctrl-dirty").wait_for(
                state="hidden", timeout=5_000
            )

            # Verify the value is back to the original
            new_value = ew_input.input_value()
            assert new_value == str(original), (
                f"Expected {original} after reset, got {new_value}"
            )

    def test_user_guide_button_opens_pdf(self, map_page):
        """Clicking User Guide button should request the guide PDF."""
        # Intercept the window.open call to verify URL
        result = map_page.evaluate("""() => {
            var openedUrl = null;
            var origOpen = window.open;
            window.open = function(url, target) { openedUrl = url; };
            var btn = document.getElementById('sp-ctrl-guide-btn');
            if (btn) btn.click();
            window.open = origOpen;
            return openedUrl;
        }""")
        assert result is not None, "window.open was not called"
        assert "/governance/storm-control/guide/pdf" in result, (
            f"Expected guide PDF URL, got: {result}"
        )

    # ---------------------------------------------------------------------
    # Admin-only gating visibility
    # ---------------------------------------------------------------------

    def test_admin_only_badge_visible(self, map_page):
        """Toolbar must display a visible 'Admin Only' badge."""
        toolbar_text = map_page.locator("#sp-control-view").inner_text().lower()
        assert "admin only" in toolbar_text, (
            f"Expected 'Admin Only' badge in toolbar, got: {toolbar_text[:200]}"
        )

    def test_save_prompts_for_password(self, map_page):
        """Clicking Save must invoke window.prompt for the admin password."""
        # Install a spy that records the last prompt message and returns null (cancel)
        map_page.evaluate("""() => {
            window.__lastPrompt = null;
            window.prompt = function(msg) { window.__lastPrompt = msg; return null; };
        }""")
        # Make dirty so save proceeds past the ctrlCollect guard
        first_input = map_page.locator("input[data-ctrl-key][type='number']").first
        first_input.fill("999")
        map_page.locator("#sp-ctrl-save-btn").click()
        msg = map_page.evaluate("() => window.__lastPrompt")
        assert msg is not None, "Save did not call window.prompt for password"
        assert "admin" in msg.lower() and "password" in msg.lower(), (
            f"Password prompt missing admin/password wording, got: {msg}"
        )

    def test_save_rejects_empty_password(self, map_page):
        """Cancelling the password prompt must not clear the dirty flag."""
        map_page.evaluate("() => { window.prompt = function() { return null; }; }")
        first_input = map_page.locator("input[data-ctrl-key][type='number']").first
        first_input.fill("999")
        ind = map_page.locator("#sp-ctrl-dirty")
        ind.wait_for(state="visible", timeout=3_000)
        map_page.locator("#sp-ctrl-save-btn").click()
        # Dirty should stay visible because save was cancelled
        assert ind.is_visible(), "Dirty indicator should remain after cancelled save"


    def test_help_tooltip_shows_on_hover(self, map_page):
        """Hovering over a ? icon should show the tooltip popup."""
        tip = map_page.locator("[id^='sp-ctrl-tip-']").first
        assert tip.count() > 0, "No tooltip elements found"
        assert not tip.is_visible(), "Tooltip should be hidden initially"

        # Find the ? icon (sibling before the tooltip div)
        icon = tip.locator("xpath=preceding-sibling::span").first
        if icon.count() > 0:
            icon.hover()
            tip.wait_for(state="visible", timeout=2_000)
            assert tip.is_visible(), "Tooltip should appear on hover"


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
