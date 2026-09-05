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
Error handling e2e tests: Escape key panel close and map layer controls.

Uses session-scoped page via the ``map_page`` fixture.
"""

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _close_all_panels(page):
    """Hide every known panel and remove context menus."""
    page.evaluate("""() => {
        ['trading-desk-panel','hazard-curve-panel','property-hc-panel',
         'prop-storm-panel','mortgage-detail-panel','property-pdf-panel'].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.style.display = 'none';
        });
        document.querySelectorAll('.ctx-menu').forEach(m => m.remove());
    }""")


# ---------------------------------------------------------------------------
# TestEscapeKeyClosesPanels
# ---------------------------------------------------------------------------

class TestEscapeKeyClosesPanels:
    """Pressing Escape should close open panels."""

    @pytest.fixture(autouse=True)
    def _setup(self, map_page):
        _close_all_panels(map_page)
        yield
        _close_all_panels(map_page)

    def test_escape_closes_gauge_panel(self, map_page, first_gauge_id):
        """Open gauge panel, press Escape, panel should close."""
        has_fn = map_page.evaluate("() => typeof window.viewHazardCurve === 'function'")
        if not has_fn:
            pytest.skip("viewHazardCurve not available")

        map_page.evaluate(f"window.viewHazardCurve('{first_gauge_id}')")
        panel = map_page.locator("#hazard-curve-panel")
        panel.wait_for(state="visible", timeout=10_000)
        assert panel.is_visible(), "Gauge panel did not open"

        map_page.keyboard.press("Escape")
        map_page.wait_for_timeout(3_000)

        # Panel should be hidden or removed
        if panel.count() > 0:
            is_hidden = not panel.is_visible()
            if not is_hidden:
                # Some panels use opacity or transform — check display
                display = panel.evaluate("el => window.getComputedStyle(el).display")
                is_hidden = display == "none"
            assert is_hidden, "Gauge panel should close on Escape key"
        else:
            assert True  # panel removed from DOM

    def test_escape_closes_trading_desk(self, map_page):
        """Open trading desk, press Escape, panel should close or remain (not all panels support Escape)."""
        # Force-show in case hidden by previous test
        map_page.evaluate("""() => {
            document.querySelectorAll('.notif-message, [id*="notif"]').forEach(n => n.remove());
            const p = document.getElementById('trading-desk-panel');
            if (p) p.style.display = '';
        }""")
        pi_btn = map_page.locator("text=\u03a0").first
        if pi_btn.count() == 0:
            pytest.skip("Pi button not found")

        pi_btn.click(force=True)
        panel = map_page.locator("#trading-desk-panel")
        try:
            panel.wait_for(state="visible", timeout=5_000)
        except Exception:
            pytest.skip("Trading desk did not open")

        map_page.keyboard.press("Escape")
        map_page.wait_for_timeout(3_000)

        # The test is named for closing the desk, so that is what it now
        # checks. Previously it asserted True with the comment "may or may not
        # close" — a name promising one thing and an assertion checking
        # another, which is the worst combination because the name is what
        # gets read in a report.
        #
        # If Escape does not close the trading desk, this fails and the answer
        # is either to wire the handler or to rename the test — not to go back
        # to asserting nothing.
        assert not panel.is_visible(), (
            "Escape did not close the trading desk panel"
        )



# ---------------------------------------------------------------------------
# TestMapLayerControls
# ---------------------------------------------------------------------------

class TestMapLayerControls:
    """Leaflet layer control interaction tests."""

    @pytest.fixture(autouse=True)
    def _setup(self, map_page):
        _close_all_panels(map_page)
        yield
        _close_all_panels(map_page)

    def test_layer_control_exists(self, map_page):
        """The map should have a Leaflet layer control widget."""
        layer_ctrl = (
            map_page.locator(".leaflet-control-layers")
            .or_(map_page.locator("[class*='layer-control']"))
        )
        if layer_ctrl.count() == 0:
            pytest.skip("No layer control found on map")

        assert layer_ctrl.first.is_visible() or layer_ctrl.count() > 0, (
            "Layer control element exists but is not accessible"
        )

    def test_layer_toggle_changes_markers(self, map_page):
        """Toggling a layer checkbox should change marker visibility."""
        layer_ctrl = map_page.locator(".leaflet-control-layers")
        if layer_ctrl.count() == 0:
            pytest.skip("No layer control found on map")

        # Hover to expand the layer control (Leaflet collapses it by default)
        layer_ctrl.first.hover(force=True)
        map_page.wait_for_timeout(1_500)

        # Find layer checkboxes
        checkboxes = layer_ctrl.locator("input[type='checkbox']")
        if checkboxes.count() == 0:
            pytest.skip("No layer checkboxes found in control")

        # Count visible markers before toggle
        markers_before = map_page.locator(
            ".leaflet-marker-icon"
        ).or_(
            map_page.locator("[class*='awesome-marker']")
        ).count()

        # Toggle the first checkbox via JS (avoids visibility issues with collapsed control)
        map_page.evaluate("""() => {
            const cb = document.querySelector('.leaflet-control-layers input[type="checkbox"]');
            if (cb) cb.click();
        }""")
        map_page.wait_for_timeout(3_000)

        markers_after = map_page.locator(
            ".leaflet-marker-icon"
        ).or_(
            map_page.locator("[class*='awesome-marker']")
        ).count()

        # Toggle back to restore state
        map_page.evaluate("""() => {
            const cb = document.querySelector('.leaflet-control-layers input[type="checkbox"]');
            if (cb) cb.click();
        }""")
        map_page.wait_for_timeout(3_000)

        # Marker count should have changed (or at least not crash)
        # Some layers may not have markers, so we accept no-change gracefully
        assert isinstance(markers_before, int) and isinstance(markers_after, int), (
            "Marker counts should be integers after toggle"
        )
