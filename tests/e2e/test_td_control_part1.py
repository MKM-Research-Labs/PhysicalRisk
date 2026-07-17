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
Storm Portfolio — Control tab e2e tests (part 1).

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

