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
Storm Portfolio — Control tab e2e tests.

Verifies that the Storm Sequence Control tab opens in the Storm Portfolio
panel, displays parameter sections, loads data from the API, and supports
save/reset interactions.

Save and Reset require an admin password (same credential as ``python phys.py
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
        """Saving while unauthenticated must trigger the RBAC login prompt.

        WP5.1 replaced the ``X-Admin-Password`` prompt with an ``/auth/login``
        session: ``__mkmAdminFetch`` retries via ``__mkmLogin``, which prompts
        for a username then a password — but only after the first write returns
        401. Log out first so the save is unauthenticated and the prompt is
        guaranteed to fire, and record prompts (returning null to cancel).
        """
        map_page.evaluate("""async () => {
            window.__prompts = [];
            window.prompt = function(msg) { window.__prompts.push(msg); return null; };
            try { await fetch('/auth/logout', {method: 'POST', mode: 'cors'}); }
            catch (e) {}
        }""")
        # Make dirty so save proceeds past the ctrlCollect guard
        first_input = map_page.locator("input[data-ctrl-key][type='number']").first
        first_input.fill("999")
        map_page.locator("#sp-ctrl-save-btn").click()
        # __mkmLogin prompts asynchronously, after the first fetch returns 401.
        map_page.wait_for_function(
            "() => (window.__prompts || []).length > 0", timeout=10_000)
        msgs = map_page.evaluate("() => window.__prompts")
        assert any(
            ("sign in" in m.lower() or "username" in m.lower()) for m in msgs
        ), f"Save did not trigger the RBAC login prompt, got: {msgs}"

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

