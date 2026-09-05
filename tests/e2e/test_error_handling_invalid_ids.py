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
Error handling e2e tests: invalid gauge and property IDs.

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
# TestInvalidGaugeId
# ---------------------------------------------------------------------------

class TestInvalidGaugeId:
    """Calling viewHazardCurve with a non-existent gauge ID."""

    @pytest.fixture(autouse=True)
    def _setup(self, map_page):
        _close_all_panels(map_page)
        yield
        _close_all_panels(map_page)

    def test_nonexistent_gauge_shows_error(self, map_page):
        """viewHazardCurve('GAUGE-nonexistent') should show an error notification."""
        has_fn = map_page.evaluate("() => typeof window.viewHazardCurve === 'function'")
        if not has_fn:
            pytest.skip("viewHazardCurve not available")

        map_page.evaluate("window.viewHazardCurve('GAUGE-nonexistent')")
        map_page.wait_for_timeout(6_000)

        # One contract, asserted once. The previous version branched through
        # four cases and `assert True`'d two of them, so it passed when the
        # app showed an error AND when it did nothing visible at all — which
        # is the failure it exists to catch, since a trader clicking a stale
        # id would be left with no feedback.
        notification = (
            map_page.locator("[class*='notification']")
            .or_(map_page.locator("[class*='toast']"))
            .or_(map_page.locator("[class*='alert']"))
            .or_(map_page.locator("[class*='error']"))
            .or_(map_page.locator("[class*='snackbar']"))
        )
        panel = map_page.locator("#hazard-curve-panel")

        notified = any(
            any(word in notification.nth(i).inner_text().lower()
                for word in ("not found", "error", "invalid"))
            for i in range(notification.count())
        )

        panel_text = panel.inner_text().lower() if panel.is_visible() else ""
        panel_says_error = any(
            word in panel_text for word in ("error", "not found", "no data"))
        panel_is_empty = panel.is_visible() and len(panel_text.strip()) < 50

        assert notified or panel_says_error or panel_is_empty, (
            "An invalid gauge id produced no error notification and left the "
            "hazard panel showing full content — the user is given no signal "
            "that the gauge does not exist"
        )

    def test_nonexistent_gauge_does_not_crash_page(self, map_page):
        """After an invalid gauge call the map should still be functional."""
        has_fn = map_page.evaluate("() => typeof window.viewHazardCurve === 'function'")
        if not has_fn:
            pytest.skip("viewHazardCurve not available")

        map_page.evaluate("window.viewHazardCurve('GAUGE-nonexistent')")
        map_page.wait_for_timeout(3_000)

        # The Leaflet map should still be present and interactive
        leaflet = map_page.locator(".leaflet-container")
        assert leaflet.count() > 0, "Leaflet map container disappeared after invalid gauge call"
        assert leaflet.is_visible(), "Leaflet map is no longer visible after invalid gauge call"


# ---------------------------------------------------------------------------
# TestInvalidPropertyId
# ---------------------------------------------------------------------------

class TestInvalidPropertyId:
    """Calling viewPropertyStorms with a non-existent property ID."""

    @pytest.fixture(autouse=True)
    def _setup(self, map_page):
        _close_all_panels(map_page)
        yield
        _close_all_panels(map_page)

    def test_nonexistent_property_shows_error(self, map_page):
        """viewPropertyStorms('PROP-nonexistent') should handle gracefully."""
        has_fn = map_page.evaluate(
            "() => typeof window.viewPropertyStorms === 'function'"
        )
        if not has_fn:
            # Try alternative function name
            has_fn = map_page.evaluate(
                "() => typeof window.viewPropertyHazard === 'function'"
            )
            if not has_fn:
                pytest.skip("viewPropertyStorms/viewPropertyHazard not available")
            fn_name = "viewPropertyHazard"
        else:
            fn_name = "viewPropertyStorms"

        map_page.evaluate(f"window.{fn_name}('PROP-nonexistent')")
        map_page.wait_for_timeout(6_000)

        # Check for error notification
        notification = (
            map_page.locator("[class*='notification']")
            .or_(map_page.locator("[class*='toast']"))
            .or_(map_page.locator("[class*='alert']"))
            .or_(map_page.locator("[class*='error']"))
        )

        # Check relevant panels
        prop_panel = map_page.locator("#property-hc-panel").or_(
            map_page.locator("#prop-storm-panel")
        )
        panel_visible = prop_panel.count() > 0 and prop_panel.first.is_visible()

        # Single contract, matching the gauge case above: an invalid id must
        # leave the user with some signal. The previous version asserted True
        # on three of its four branches, so it also passed when nothing
        # happened.
        notified = any(
            any(word in notification.nth(i).inner_text().lower()
                for word in ("not found", "error", "invalid"))
            for i in range(notification.count())
        )

        panel_text = prop_panel.first.inner_text().lower() if panel_visible else ""
        panel_says_error = any(
            word in panel_text for word in ("error", "not found", "no data"))
        panel_is_empty = panel_visible and len(panel_text.strip()) < 50

        assert notified or panel_says_error or panel_is_empty, (
            "An invalid property id produced no error notification and left "
            "the panel showing full content — the user is given no signal "
            "that the property does not exist"
        )

    def test_nonexistent_property_does_not_crash_page(self, map_page):
        """After an invalid property call the map should still be functional."""
        has_fn = map_page.evaluate(
            "() => typeof window.viewPropertyStorms === 'function'"
        )
        fn_name = "viewPropertyStorms"
        if not has_fn:
            has_fn = map_page.evaluate(
                "() => typeof window.viewPropertyHazard === 'function'"
            )
            fn_name = "viewPropertyHazard"
            if not has_fn:
                pytest.skip("viewPropertyStorms/viewPropertyHazard not available")

        map_page.evaluate(f"window.{fn_name}('PROP-nonexistent')")
        map_page.wait_for_timeout(3_000)

        leaflet = map_page.locator(".leaflet-container")
        assert leaflet.count() > 0, "Leaflet map disappeared after invalid property call"
        assert leaflet.is_visible(), "Leaflet map not visible after invalid property call"
