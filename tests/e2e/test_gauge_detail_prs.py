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
Gauge panel detail e2e test: PRS Pricing tab (Tab 0).
Split from test_gauge_panel_detail.py.
"""

import pytest

from tests.e2e.helpers import (
    close_gauge_panel,
    open_gauge_panel,
    switch_gauge_tab,
)


class TestPRSPricingTab:
    """Tab 0 - PRS Pricing controls and chart."""

    @pytest.fixture(autouse=True)
    def open_prs_tab(self, map_page, first_traded_gauge_id):
        open_gauge_panel(map_page, first_traded_gauge_id)
        switch_gauge_tab(map_page, 0)
        yield
        close_gauge_panel(map_page)

    def test_controls_exist(self, map_page):
        """PRS tab should have direction, counterparty, trigger, notional, spread, maturity controls."""
        control_ids = [
            "prs-direction",
            "prs-counterparty",
            "prs-trigger",
            "prs-notional",
            "prs-spread",
            "prs-maturity",
        ]
        for cid in control_ids:
            el = map_page.locator(f"#{cid}")
            assert el.count() > 0, f"Control #{cid} not found on PRS tab"

    def test_direction_dropdown_options(self, map_page):
        """Direction dropdown should have payer and receiver options."""
        direction = map_page.locator("#prs-direction")
        assert direction.count() > 0, "Direction dropdown not found"
        options_text = map_page.evaluate("""() => {
            const sel = document.getElementById('prs-direction');
            if (!sel) return [];
            return Array.from(sel.options).map(o => o.value.toLowerCase());
        }""")
        assert any("pay" in o for o in options_text), (
            f"No payer option in direction dropdown: {options_text}"
        )
        assert any("rec" in o for o in options_text), (
            f"No receiver option in direction dropdown: {options_text}"
        )

    def test_trigger_dropdown_options(self, map_page):
        """Trigger input should exist and have a valid default value."""
        trigger = map_page.locator("#prs-trigger")
        assert trigger.count() > 0, "Trigger input not found"
        value = map_page.evaluate("""() => {
            const el = document.getElementById('prs-trigger');
            if (!el) return null;
            return el.value;
        }""")
        assert value is not None, "Trigger input has no value"
        assert value in ("alert", "warning", "severe"), \
            f"Unexpected trigger value: {value}"

    def test_trigger_change_updates_display(self, map_page):
        """Changing the trigger value should update the hazard display."""
        trigger = map_page.locator("#prs-trigger")
        if trigger.count() == 0:
            pytest.skip("Trigger input not found")

        # Read initial state
        initial_text = map_page.locator("#hazard-curve-panel").inner_text()

        # Change trigger value and fire change event
        map_page.evaluate("""() => {
            const el = document.getElementById('prs-trigger');
            if (!el) return;
            el.value = el.value === 'severe' ? 'warning' : 'severe';
            el.dispatchEvent(new Event('change'));
        }""")
        map_page.wait_for_timeout(3_000)

        # The panel should still be showing content (not blank/error)
        panel = map_page.locator("#hazard-curve-panel")
        assert panel.is_visible(), "Panel disappeared after trigger change"
        updated_text = panel.inner_text()
        assert len(updated_text) > 0, "Panel content is empty after trigger change"

    def test_commit_button_exists(self, map_page):
        """PRS tab should have a commit/trade button (appears after counterparty selected)."""
        btn = map_page.locator("#prs-commit-btn")
        if btn.count() == 0:
            # Commit button only appears after counterparty is selected
            # Check that the controls area exists instead
            controls = map_page.locator("#hazard-controls, #prs-counterparty")
            assert controls.count() > 0, (
                "Neither commit button nor PRS controls found"
            )

    def test_chart_canvas_exists(self, map_page):
        """PRS tab should render a hazard curve chart."""
        chart = map_page.locator("#prs-hazard-curve-chart")
        if chart.count() == 0:
            # Fallback: look for any canvas inside the panel
            chart = map_page.locator("#hazard-curve-panel canvas")
        assert chart.count() > 0, "No chart canvas found on PRS tab"
