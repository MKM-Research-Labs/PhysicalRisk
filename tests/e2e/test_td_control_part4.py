# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

"""
Storm Portfolio — Control tab e2e tests (part 4).

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

        # Clicking the Control tab fires an async loadControlData() fetch
        # which, on resolve, calls ctrlClearDirty() and re-renders sections.
        # If we let a test interact with the form before that settles,
        # the load's trailing ctrlClearDirty clobbers dirty state the test
        # has deliberately set (see test_save_rejects_empty_password).
        #
        # The status bar persists across tab re-opens and still shows the
        # previous test's final state (e.g. "Source: defaults (reset) ..."),
        # so we stamp a sentinel BEFORE clicking the tab and wait for the
        # fresh load to overwrite it.
        map_page.evaluate("""() => {
            var b = document.getElementById('sp-ctrl-status');
            if (b) b.textContent = '__CTRL_LOADING__';
        }""")
        map_page.locator("#sp-tab-control").click(force=True)
        map_page.locator("#sp-control-view").wait_for(
            state="attached", timeout=10_000
        )
        try:
            map_page.wait_for_function(
                "() => {"
                "  var b = document.getElementById('sp-ctrl-status');"
                "  if (!b) return false;"
                "  var t = b.textContent || '';"
                "  return t.indexOf('__CTRL_LOADING__') === -1"
                "      && t.toLowerCase().indexOf('loading') === -1"
                "      && t.toLowerCase().indexOf('source:') !== -1;"
                "}",
                timeout=10_000,
            )
        except Exception:
            # Fall back to a fixed wait rather than failing the fixture.
            map_page.wait_for_timeout(2_000)
        yield
        _close_storm_portfolio(map_page)

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

            # Click reset (confirm + prompt already stubbed).
            # After save, dirty is already hidden — waiting for dirty=hidden
            # here resolves immediately and does not prove the async reset
            # .then() (which re-renders section inputs with defaults) has
            # run. Wait instead for the status bar to confirm the reset,
            # which is set inside that same .then().
            map_page.locator("#sp-ctrl-reset-btn").click()
            map_page.wait_for_function(
                "() => {"
                "  var b = document.getElementById('sp-ctrl-status');"
                "  return !!b && /reset/i.test(b.textContent || '');"
                "}",
                timeout=10_000,
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

