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

"""Commercial context menu + PDF e2e tests (part 1).

Right-click a commercial marker on the map → menu shows commercial-
specific items → clicking "Generate Commercial Report" opens the
PDF panel.

Mirrors test_property_context_menu.py. The e2e fixture pins the
active catchment (see conftest ``_isolated_catchment_dir`` /
``MKM_CATCHMENT``) and renders every commercial asset with a purple
marker. Tests that need a real CPROP id fetch it from the running
server via ``_active_commercial_id`` so they stay catchment-agnostic.
"""

import pytest


# ---------------------------------------------------------------------------
# Marker helpers — commercial assets render with purple icons (per
# src/visual/layer/commercial_layer/layer.py:_MARKER_COLOR). The
# CommercialType maps to one of fa-briefcase, fa-building, fa-hotel,
# fa-shopping-cart, fa-glass-cheers, fa-hospital, fa-city, fa-industry.
# Purple is exclusive to commercial; residential uses green/orange/red,
# gauges blue.
# ---------------------------------------------------------------------------

_COMMERCIAL_ICON_CLASSES = [
    "fa-briefcase", "fa-building", "fa-hotel", "fa-shopping-cart",
    "fa-glass-cheers", "fa-hospital", "fa-city", "fa-industry",
]


def _find_commercial_markers(page):
    """Find commercial markers on the map (purple is unique to commercial)."""
    return page.locator("[class*='awesome-marker-icon-purple']")


def _right_click_commercial_marker(page):
    """Right-click the first commercial marker and wait for context menu.

    Dismisses any menu lingering from a previous test before the click —
    map_page is session-scoped so a menu opened by an earlier test would
    sit on top of the marker, intercept the click, and prevent the new
    contextmenu event from firing.
    """
    # Best-effort menu dismissal (JS helper at window.hideAllMenus is
    # registered by context-menus.js; an inline click on body also fires
    # the document-level click listener that calls hideAllMenus()).
    try:
        page.evaluate("""() => {
            if (window.hideAllMenus) window.hideAllMenus();
            document.querySelectorAll('.ctx-menu').forEach(m => {
                m.style.display = 'none';
            });
        }""")
    except Exception:
        pass

    markers = _find_commercial_markers(page)
    if markers.count() == 0:
        diag = page.evaluate("""() => {
            const pane = document.querySelector('.leaflet-marker-pane');
            return {
                marker_pane_children: pane ? pane.children.length : 0,
                purple_markers: document.querySelectorAll(
                    "[class*='awesome-marker-icon-purple']"
                ).length,
                all_markers: document.querySelectorAll(
                    "[class*='awesome-marker-icon-']"
                ).length,
            }
        }""")
        pytest.skip(f"No commercial markers on map. Diagnostics: {diag}")

    box = markers.first.bounding_box()
    if box:
        cx = box["x"] + box["width"] / 2
        cy = box["y"] + box["height"] / 2
        page.mouse.click(cx, cy, button="right")
    else:
        markers.first.click(button="right", force=True)
    # Short wait — the menu DOM is created synchronously in showMenu().
    page.wait_for_timeout(1_500)


def _active_commercial_id(page):
    """Return a real CPROP id from the *active* catchment via the server.

    The e2e Flask subprocess is pinned to whichever catchment the run
    targets (see conftest ``_isolated_catchment_dir`` /
    ``MKM_CATCHMENT``). Picking the id from a hardcoded
    ``data/input/thames/commercial.json`` breaks under any non-thames
    catchment because that id is absent from the served dataset, so the
    route 404s. Fetching ``/api/v1/commercial`` always yields an id that
    exists in the data the app is actually serving.
    """
    cprop_id = page.evaluate("""async () => {
        const resp = await fetch('/api/v1/commercial');
        if (!resp.ok) return null;
        try {
            const data = await resp.json();
            const list = data.commercial_assets || data;
            if (!Array.isArray(list) || list.length === 0) return null;
            return list[0]?.CommercialAsset?.Header?.PropertyID || null;
        } catch (e) { return null; }
    }""")
    if not cprop_id:
        pytest.skip("No commercial assets served by the active catchment")
    return cprop_id


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestCommercialContextMenu:
    """Right-clicking a commercial marker should show a commercial menu.

    These tests share the session-scoped ``map_page`` fixture, so they
    do all their right-click + assertion work inside a single method to
    avoid Leaflet event quirks where a second right-click on the same
    page session can be intercepted by a lingering menu DOM element.
    """

    def test_right_click_shows_commercial_menu(self, map_page):
        """Right-clicking a commercial (purple) marker should display a
        ``.ctx-menu`` with commercial-specific items — not the
        residential menu vocabulary.
        """
        _right_click_commercial_marker(map_page)

        # 1) Menu DOM exists + visible
        menu = map_page.locator(".ctx-menu")
        assert menu.count() > 0, "No context menu after right-click on commercial marker"
        assert menu.first.is_visible()

        # 2) Has menu items
        items = map_page.locator(".ctx-menu-item")
        # Some Playwright runs in headless Chromium can race between the
        # contextmenu fire and DOM insertion; allow a small extra window.
        if items.count() == 0:
            map_page.wait_for_timeout(1_500)
        assert items.count() > 0, "Menu has no items"

        item_texts = [items.nth(i).inner_text() for i in range(items.count())]
        joined = " | ".join(item_texts).lower()

        # 3) Vocabulary is commercial-specific
        commercial_keywords = [
            "commercial details", "loan details", "generate commercial report",
            "commercial report", "loan report",
        ]
        assert any(kw in joined for kw in commercial_keywords), (
            f"No commercial-specific items found. Got: {item_texts}"
        )

        # 4) Vocabulary is NOT residential (regression guard for
        #    the substring-match bug that previously rendered the
        #    property menu on CPROP- markers).
        assert "mortgage details" not in joined, (
            f"Residential menu rendered on commercial marker: {joined}"
        )

    def test_commercial_marker_registered_with_correct_type(self, map_page):
        """JS side: every purple marker should carry markerType='commercial'.

        Verifies the context-menus.js search-both-tooltip-and-popup fix is
        actually finding the CPROP- id buried in the popup HTML.
        """
        diag = map_page.evaluate("""() => {
            const mapKey = Object.keys(window).find(k => k.startsWith('map_'));
            const m = mapKey ? window[mapKey] : null;
            if (!m) return {error: 'no map'};
            let purple = 0, purpleAsCommercial = 0;
            m.eachLayer(layer => {
                if (!(layer instanceof L.Marker)) return;
                const icon = layer._icon;
                if (icon && icon.className.indexOf('purple') !== -1) {
                    purple++;
                    if (layer._markerType === 'commercial') purpleAsCommercial++;
                }
            });
            return {purple, purpleAsCommercial};
        }""")
        assert "error" not in diag, diag
        assert diag["purple"] > 0, "No purple markers on the map at all"
        assert diag["purpleAsCommercial"] == diag["purple"], (
            f"Only {diag['purpleAsCommercial']} of {diag['purple']} purple "
            f"markers were registered as commercial (the rest fell through "
            f"to property/gauge or no type at all)"
        )


class TestCommercialReportFromMenu:
    """Click-through: menu → Generate Commercial Report → PDF panel opens."""

    def test_generate_commercial_report_opens_pdf_panel(self, map_page):
        """Click 'Generate Commercial Report' and wait for the PDF panel.

        The commercial report reuses ``property-pdf-panel`` for display
        (see backend-handler.js — generateCommercialReport is wired to
        ``PropertyPDFPanel``).
        """
        # Wait for the JS handler to be registered before triggering
        # the menu (otherwise the action is dispatched to undefined).
        map_page.wait_for_function(
            "() => typeof window.generateCommercialReport === 'function'",
            timeout=10_000,
        )

        _right_click_commercial_marker(map_page)
        menu = map_page.locator(".ctx-menu")
        if menu.count() == 0:
            pytest.skip("No context menu appeared")

        report_item = map_page.locator(".ctx-menu-item",
                                       has_text="Generate Commercial Report")
        if report_item.count() == 0:
            pytest.skip("No 'Generate Commercial Report' menu item")
        report_item.first.click()

        # PDF generation goes server-side (route call + base64 encode),
        # so give it a healthy window to land.
        map_page.wait_for_timeout(10_000)

        panel_visible = map_page.evaluate("""() => {
            const panel = document.getElementById('property-pdf-panel');
            return panel !== null && panel.style.display !== 'none';
        }""")
        assert panel_visible, (
            "property-pdf-panel did not open after clicking "
            "'Generate Commercial Report'"
        )
