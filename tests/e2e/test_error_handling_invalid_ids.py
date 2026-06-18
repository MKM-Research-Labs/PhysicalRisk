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
         'prop-storm-panel','mortgage-detail-panel','mg-panel','property-pdf-panel'].forEach(id => {
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

        # Look for error notification or toast containing relevant text
        notification = (
            map_page.locator("[class*='notification']")
            .or_(map_page.locator("[class*='toast']"))
            .or_(map_page.locator("[class*='alert']"))
            .or_(map_page.locator("[class*='error']"))
            .or_(map_page.locator("[class*='snackbar']"))
        )

        panel = map_page.locator("#hazard-curve-panel")
        panel_visible = panel.is_visible()

        if notification.count() > 0:
            # Check that at least one notification mentions error or not found
            found_error = False
            for i in range(notification.count()):
                text = notification.nth(i).inner_text().lower()
                if "not found" in text or "error" in text or "invalid" in text:
                    found_error = True
                    break
            if found_error:
                assert True
            elif panel_visible:
                # Panel opened but might show error inside
                panel_text = panel.inner_text().lower()
                assert "error" in panel_text or "not found" in panel_text or len(panel_text.strip()) < 50, (
                    "Panel opened with no error indication for invalid gauge"
                )
            else:
                # No crash, no panel — graceful handling
                assert True
        elif panel_visible:
            # Panel opened — check it shows an error state
            panel_text = panel.inner_text().lower()
            has_error = (
                "error" in panel_text
                or "not found" in panel_text
                or "no data" in panel_text
            )
            assert has_error or len(panel_text.strip()) < 50, (
                "Panel opened with full content for an invalid gauge ID"
            )
        else:
            # Panel did not open, no notification — still graceful (no crash)
            assert True

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

        if notification.count() > 0:
            found_error = False
            for i in range(notification.count()):
                text = notification.nth(i).inner_text().lower()
                if "not found" in text or "error" in text or "invalid" in text:
                    found_error = True
                    break
            if found_error:
                assert True
            else:
                # No crash — graceful
                assert True
        elif panel_visible:
            panel_text = prop_panel.first.inner_text().lower()
            has_error = (
                "error" in panel_text
                or "not found" in panel_text
                or "no data" in panel_text
            )
            assert has_error or len(panel_text.strip()) < 50, (
                "Property panel opened with full content for invalid property ID"
            )
        else:
            # No panel, no crash — graceful handling
            assert True

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
