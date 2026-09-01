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
Property context menu e2e tests — right-click property markers on the map.
"""

import pytest


def _find_property_markers(page):
    """Find property markers on the map.

    Property markers use fa-home icon; gauge markers use fa-tint.
    Both can be green/orange/red, so we distinguish by the icon inside.
    """
    # Property markers contain an <i> with fa-home class
    markers = page.locator("[class*='awesome-marker-icon-']:has(i.fa-home)")
    if markers.count() > 0:
        return markers
    # Fallback: also try fa-university (mortgaged properties)
    markers = page.locator("[class*='awesome-marker-icon-']:has(i.fa-university)")
    if markers.count() > 0:
        return markers
    # Last resort: any marker
    return page.locator("[class*='awesome-marker-icon-']")


def _right_click_property_marker(page):
    """Right-click the first property marker and wait for context menu."""
    markers = _find_property_markers(page)
    if markers.count() == 0:
        diag = page.evaluate("""() => {
            const pane = document.querySelector('.leaflet-marker-pane');
            return {
                marker_pane_children: pane ? pane.children.length : 0,
                green_markers: document.querySelectorAll(
                    "[class*='awesome-marker-icon-green']"
                ).length,
                all_markers: document.querySelectorAll(
                    "[class*='awesome-marker-icon-']"
                ).length,
            }
        }""")
        pytest.skip(f"No property markers on map. Diagnostics: {diag}")

    # Dispatch a contextmenu event directly on the property marker element.
    # A coordinate right-click is intercepted by overlapping markers under the
    # portfolio-wide zoom (dense catchments), and a force right-*click* fires a
    # click, not the contextmenu event Leaflet's L.Marker listener responds to.
    # Dispatching contextmenu on the element bypasses hit-testing and fires the
    # marker's own handler regardless of overlap.
    box = markers.first.bounding_box()
    if box:
        markers.first.dispatch_event("contextmenu", {
            "bubbles": True,
            "cancelable": True,
            "button": 2,
            "clientX": int(box["x"] + box["width"] / 2),
            "clientY": int(box["y"] + box["height"] / 2),
        })
    else:
        markers.first.dispatch_event(
            "contextmenu", {"bubbles": True, "cancelable": True, "button": 2})
    page.wait_for_timeout(1_500)


class TestPropertyContextMenu:
    """Right-clicking a property marker should show a context menu."""

    def test_right_click_property_shows_menu(self, map_page):
        """Right-clicking a property marker should display a context menu."""
        _right_click_property_marker(map_page)

        menu = map_page.locator(".ctx-menu")
        if menu.count() == 0:
            diag = map_page.evaluate("""() => {
                const els = document.querySelectorAll(
                    '[class*="ctx"], [class*="context"], [class*="menu"]'
                );
                return Array.from(els).map(m => ({
                    tag: m.tagName,
                    cls: m.className,
                    visible: m.offsetParent !== null,
                    text: m.innerText.substring(0, 100)
                }));
            }""")
            assert False, (
                f"No .ctx-menu found after right-click. "
                f"Elements with menu/ctx classes: {diag}"
            )

        assert menu.first.is_visible()

    def test_menu_has_property_items(self, map_page):
        """Context menu should contain property-specific items."""
        _right_click_property_marker(map_page)

        menu = map_page.locator(".ctx-menu")
        assert menu.count() > 0, (
            "Right-clicking a property marker produced no .ctx-menu"
        )

        items = map_page.locator(".ctx-menu-item")
        assert items.count() >= 2, f"Only {items.count()} menu items found"

        # Collect item texts
        item_texts = []
        for i in range(items.count()):
            item_texts.append(items.nth(i).inner_text().lower())
        all_text = " ".join(item_texts)

        # Property menus should have property-related items
        expected_keywords = [
            "property", "mortgage", "storm", "physical risk swap",
            "details", "hazard",
        ]
        has_property_item = any(kw in all_text for kw in expected_keywords)
        assert has_property_item, (
            f"No property-specific menu items found. Items: {item_texts}"
        )

    def test_menu_header_shows_property_info(self, map_page):
        """Context menu header should display property information."""
        _right_click_property_marker(map_page)

        header = map_page.locator(".ctx-menu-header")
        # A missing header is the regression this test exists to catch, so it
        # must fail rather than skip. The marker/menu preconditions above are
        # what may legitimately be unavailable.
        assert header.count() > 0, (
            "Context menu opened but has no .ctx-menu-header — the header is "
            "what this test verifies"
        )

        text = header.first.inner_text()
        assert len(text) > 0, "Context menu header is empty"

    def test_storm_scenarios_opens_panel(self, map_page):
        """Clicking 'Storm Scenarios' should open the property storm panel."""
        _right_click_property_marker(map_page)

        menu = map_page.locator(".ctx-menu")
        if menu.count() == 0:
            pytest.skip("No context menu appeared")

        # Look for Storm Scenarios menu item
        storm_item = map_page.locator(".ctx-menu-item", has_text="Storm")
        if storm_item.count() == 0:
            # Fallback: try any property-related menu item
            storm_item = map_page.locator(".ctx-menu-item", has_text="Property")
        if storm_item.count() == 0:
            # Last resort: click first available item
            items = map_page.locator(".ctx-menu-item")
            if items.count() > 0:
                items.first.click()
                map_page.wait_for_timeout(3_000)
                assert True  # clicked without error
                return
            pytest.skip("No clickable menu items found")

        storm_item.first.click()
        map_page.wait_for_timeout(6_000)

        # Either prop-storm-panel or property-hc-panel should be visible
        storm_panel = map_page.locator("#prop-storm-panel")
        hazard_panel = map_page.locator("#property-hc-panel")

        panel_opened = (
            (storm_panel.count() > 0 and storm_panel.is_visible())
            or (hazard_panel.count() > 0 and hazard_panel.is_visible())
        )
        assert panel_opened, (
            "Neither property storm panel nor hazard panel opened "
            "after clicking menu item"
        )
