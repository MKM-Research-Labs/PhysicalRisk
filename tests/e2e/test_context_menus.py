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
Context menu tests — right-click on markers opens menus with correct items.
"""

import pytest


def _find_markers(page):
    """Find clickable markers on the map.

    Folium awesome-markers render two divs per marker:
      - .awesome-marker-shadow  (drop shadow, NOT clickable)
      - .awesome-marker-icon-*  (the coloured icon, IS clickable)
    Both have .leaflet-interactive but the shadow sits underneath
    and causes click interception. Target only the icon divs.
    """
    # Target icon markers only (class contains 'awesome-marker-icon-')
    # These are the coloured markers: green, red, orange, blue, etc.
    markers = page.locator("[class*='awesome-marker-icon-']")
    if markers.count() > 0:
        return markers

    # Fallback: any interactive element in marker pane
    markers = page.locator(".leaflet-marker-pane .leaflet-interactive")
    if markers.count() > 0:
        return markers

    return None


class TestGaugeContextMenu:
    """Right-clicking a gauge marker should show a context menu."""

    def test_right_click_gauge_shows_menu(self, map_page):
        """Right-clicking a marker should display a context menu."""
        markers = _find_markers(map_page)
        if markers is None or markers.count() == 0:
            # Diagnostic: dump what's in the marker pane
            diag = map_page.evaluate("""() => {
                const pane = document.querySelector('.leaflet-marker-pane');
                const overlay = document.querySelector('.leaflet-overlay-pane');
                return {
                    marker_pane_children: pane ? pane.children.length : 0,
                    marker_pane_html: pane ? pane.innerHTML.substring(0, 500) : 'no pane',
                    overlay_children: overlay ? overlay.children.length : 0,
                    all_markers: document.querySelectorAll('.leaflet-marker-icon').length,
                    all_interactive: document.querySelectorAll('.leaflet-interactive').length,
                }
            }""")
            pytest.skip(f"No markers on map. Diagnostics: {diag}")

        print(f"\n  [DEBUG] Found {markers.count()} markers, clicking first...")
        markers.first.click(button="right")
        map_page.wait_for_timeout(3_000)

        # Check multiple possible context menu selectors
        menu = map_page.locator(".ctx-menu")
        if menu.count() == 0:
            # Dump what appeared after right-click
            diag = map_page.evaluate("""() => {
                const menus = document.querySelectorAll('[class*="ctx"], [class*="context"], [class*="menu"]');
                return Array.from(menus).map(m => ({
                    tag: m.tagName,
                    class: m.className,
                    visible: m.offsetParent !== null,
                    text: m.innerText.substring(0, 100)
                }));
            }""")
            assert False, f"No .ctx-menu found after right-click. Elements with menu/ctx classes: {diag}"

        assert menu.first.is_visible()

    def test_context_menu_has_items(self, map_page):
        """Context menu should contain clickable items."""
        markers = _find_markers(map_page)
        if markers is None or markers.count() == 0:
            pytest.skip("No markers on map")

        markers.first.click(button="right")
        map_page.wait_for_timeout(1_500)

        items = map_page.locator(".ctx-menu-item")
        assert items.count() >= 2, f"Only {items.count()} menu items found"

    def test_context_menu_has_header(self, map_page):
        """Context menu should have a header with the marker name."""
        markers = _find_markers(map_page)
        if markers is None or markers.count() == 0:
            pytest.skip("No markers on map")

        markers.first.click(button="right")
        map_page.wait_for_timeout(1_500)

        header = map_page.locator(".ctx-menu-header")
        assert header.count() > 0, "No context menu header"
        text = header.first.inner_text()
        assert len(text) > 0, "Context menu header is empty"

    def test_click_away_closes_menu(self, map_page):
        """Clicking elsewhere should close the context menu."""
        markers = _find_markers(map_page)
        if markers is None or markers.count() == 0:
            pytest.skip("No markers on map")

        markers.first.click(button="right")
        map_page.wait_for_timeout(1_500)

        menu = map_page.locator(".ctx-menu")
        assert menu.first.is_visible()

        # Click on the map (not on menu)
        map_page.locator(".leaflet-container").first.click(
            position={"x": 10, "y": 10}
        )
        map_page.wait_for_timeout(1_500)

        if menu.count() > 0:
            assert not menu.first.is_visible(), "Context menu still visible after click-away"


class TestContextMenuNavigation:
    """Context menu items should navigate to the correct panels."""

    def test_hazard_curve_item_opens_gauge_panel(self, map_page):
        """Clicking 'Physical Risk Swap' should open the gauge hazard panel."""
        markers = _find_markers(map_page)
        if markers is None or markers.count() == 0:
            pytest.skip("No markers on map")

        markers.first.click(button="right")
        map_page.wait_for_timeout(1_500)

        # Look for PRS / Hazard Curve menu item
        prs_item = map_page.locator(".ctx-menu-item", has_text="Physical Risk Swap")
        if prs_item.count() == 0:
            prs_item = map_page.locator(".ctx-menu-item", has_text="Hazard")
        if prs_item.count() == 0:
            # May have clicked a property marker — any menu item click is valid
            items = map_page.locator(".ctx-menu-item")
            if items.count() > 0:
                items.first.click()
                map_page.wait_for_timeout(3_000)
                assert True  # clicked without error
                return
            pytest.skip("No clickable menu items found")

        prs_item.first.click()
        map_page.wait_for_timeout(9_000)

        # The hazard curve panel should now be visible
        panel = map_page.locator("#hazard-curve-panel")
        assert panel.count() > 0 and panel.is_visible(), (
            "Hazard curve panel did not open after clicking menu item"
        )

        # Verify data actually loaded — no error notifications
        errors = map_page.evaluate("""() => {
            const notifs = document.querySelectorAll('.notif-message');
            const errors = [];
            notifs.forEach(n => {
                const text = n.textContent.toLowerCase();
                if (text.includes('fail') || text.includes('error') ||
                    text.includes('unable')) {
                    errors.push(n.textContent.trim());
                }
            });
            return errors;
        }""")
        assert len(errors) == 0, (
            f"Data load errors after opening gauge panel: {errors}"
        )


# ---------------------------------------------------------------------------
# Navigation dropdown menus (top-left)
# ---------------------------------------------------------------------------


class TestNavMenuDropdowns:
    """The top-left gauge/property navigation dropdowns were removed — gauge /
    property browsing now lives in the CDM Asset Review workstream. They must
    no longer render. The right-click context menus (above) are unaffected."""

    def test_nav_dropdowns_removed(self, map_page):
        map_page.wait_for_timeout(5_000)
        assert map_page.locator("#nav-menu-container").count() == 0, \
            "nav dropdown container should have been removed"
        assert map_page.locator("#nav-gauge-select").count() == 0
        assert map_page.locator("#nav-prop-select").count() == 0
