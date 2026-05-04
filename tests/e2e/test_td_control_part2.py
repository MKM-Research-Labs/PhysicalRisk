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




# ---------------------------------------------------------------------------
# Control tab — admin-gating + tooltip (split from TestControlTab)
# ---------------------------------------------------------------------------


class TestControlTabAdmin:
    """Admin-only gating + help-tooltip tests on the Control tab.

    Mirrors the autouse ``open_control_tab`` fixture from
    test_td_control_part1.TestControlTab so each test starts with the
    Storm Portfolio panel open at the Control tab.
    """

    @pytest.fixture(autouse=True)
    def open_control_tab(self, map_page):
        _close_all_panels(map_page)
        _open_storm_portfolio(map_page)
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
            map_page.wait_for_timeout(2_000)
        yield
        _close_storm_portfolio(map_page)

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

