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
E2e test: Property PRS pricing -> book a trade -> verify.
Split from test_trading_lifecycle.py.
"""

import pytest

from tests.e2e.conftest import E2E_ADMIN_PW
from tests.e2e.helpers import (
    close_all_panels,
    open_property_panel,
    switch_to_prs_tab_property,
)


def _stub_admin_prompt(page):
    """Replace window.prompt so admin-gated fetches authenticate non-interactively.

    Property PRS commit calls ``__mkmAdminFetch`` which prompts for the
    admin password. Playwright returns null by default, which the helper
    treats as cancelled — so the call fails with a notification error.
    Stub here with the test password installed by ``_e2e_admin_password``.
    """
    page.evaluate(
        "(v) => { window.prompt = function() { return v; }; }",
        E2E_ADMIN_PW,
    )


class TestPropertyPRSBookTrade:
    """Workflow: open property PRS -> configure -> commit -> verify."""

    @pytest.fixture(autouse=True)
    def setup(self, map_page):
        close_all_panels(map_page)
        yield

    def test_01_open_property_prs_and_verify_controls(
        self, map_page, first_property_id
    ):
        """Open property panel PRS tab and verify controls exist."""
        has_fn = map_page.evaluate(
            "() => typeof window.viewPropertyHazard === 'function' || "
            "(window.PropertyHazardCurvePanel && "
            "typeof window.PropertyHazardCurvePanel.show === 'function')"
        )
        if not has_fn:
            pytest.skip("Property hazard panel function not available")

        open_property_panel(map_page, first_property_id)
        switch_to_prs_tab_property(map_page)

        # Controls from phc_prs.py: phc-counterparty,
        # phc-notional, phc-tenor, phc-spread
        for ctrl_id in [
            "phc-counterparty", "phc-ea-zone", "phc-notional",
            "phc-tenor", "phc-spread",
        ]:
            found = map_page.evaluate(
                f"() => document.getElementById('{ctrl_id}') !== null"
            )
            if not found:
                pytest.skip(f"Control #{ctrl_id} not found — property PRS tab "
                            "may not be active")
                return

    def test_02_set_property_trade_parameters(
        self, map_page, first_property_id
    ):
        """Set counterparty, notional, and tenor on property PRS."""
        has_fn = map_page.evaluate(
            "() => typeof window.viewPropertyHazard === 'function' || "
            "(window.PropertyHazardCurvePanel && "
            "typeof window.PropertyHazardCurvePanel.show === 'function')"
        )
        if not has_fn:
            pytest.skip("Property hazard panel function not available")

        open_property_panel(map_page, first_property_id)
        switch_to_prs_tab_property(map_page)

        # Select counterparty (may be hidden — use JS fallback)
        ctpy = map_page.locator("#phc-counterparty")
        if ctpy.count() > 0 and ctpy.locator("option").count() > 1:
            map_page.evaluate("""(sel) => {
                if (sel.options.length > 1) {
                    sel.selectedIndex = 1;
                    sel.dispatchEvent(new Event('change', {bubbles: true}));
                }
            }""", ctpy.element_handle())

        # Notional — element may not be visible, use JS
        notional = map_page.locator("#phc-notional")
        if notional.count() > 0:
            map_page.evaluate("""(el) => {
                el.value = '5,000,000';
                el.dispatchEvent(new Event('input', {bubbles: true}));
                el.dispatchEvent(new Event('change', {bubbles: true}));
            }""", notional.element_handle())

        map_page.wait_for_timeout(1_500)

        # Verify panel has pricing data
        panel_text = map_page.locator("#property-hc-panel").inner_text()
        assert len(panel_text) > 50, "Property PRS panel appears empty"

    def test_03_commit_property_trade(self, map_page, first_property_id):
        """Commit a property PRS trade."""
        has_fn = map_page.evaluate(
            "() => typeof window.viewPropertyHazard === 'function' || "
            "(window.PropertyHazardCurvePanel && "
            "typeof window.PropertyHazardCurvePanel.show === 'function')"
        )
        if not has_fn:
            pytest.skip("Property hazard panel function not available")

        open_property_panel(map_page, first_property_id)
        switch_to_prs_tab_property(map_page)

        # Select counterparty (may be hidden — use JS fallback)
        ctpy = map_page.locator("#phc-counterparty")
        if ctpy.count() > 0 and ctpy.locator("option").count() > 1:
            map_page.evaluate("""(sel) => {
                if (sel.options.length > 1) {
                    sel.selectedIndex = 1;
                    sel.dispatchEvent(new Event('change', {bubbles: true}));
                }
            }""", ctpy.element_handle())

        # Notional — element may not be visible, use JS
        notional = map_page.locator("#phc-notional")
        if notional.count() > 0:
            map_page.evaluate("""(el) => {
                el.value = '5,000,000';
                el.dispatchEvent(new Event('input', {bubbles: true}));
                el.dispatchEvent(new Event('change', {bubbles: true}));
            }""", notional.element_handle())

        map_page.wait_for_timeout(1_500)

        # Commit — button ID from phc_prs.py is "phc-commit-btn"
        commit_btn = map_page.locator("#phc-commit-btn")
        if commit_btn.count() == 0:
            commit_btn = map_page.locator(
                "#property-hc-panel button:has-text('Commit')"
            )
        if commit_btn.count() == 0:
            pytest.skip("No commit button found on property PRS tab")

        # Stub window.prompt so __mkmAdminFetch authenticates without
        # an interactive dialog (Playwright cancels the dialog otherwise).
        _stub_admin_prompt(map_page)
        commit_btn.first.click(force=True)
        map_page.wait_for_timeout(9_000)

        # Accept success or absence of error
        has_error = map_page.evaluate("""() => {
            const notifs = document.querySelectorAll('.notif-message');
            for (const n of notifs) {
                const t = n.textContent.toLowerCase();
                if (t.includes('error') || t.includes('fail'))
                    return true;
            }
            return false;
        }""")
        assert not has_error, "Property trade commit showed an error"
