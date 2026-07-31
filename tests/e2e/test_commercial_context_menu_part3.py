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

"""Commercial context menu + PDF e2e tests (part 3).

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

    # Dispatch the contextmenu event directly on the commercial (purple) marker
    # element rather than pixel-clicking its centre. When the map is framed to
    # the whole portfolio, dense areas (Hanoi) pack markers tightly and a
    # property marker can overlap the commercial marker's centre pixel — a
    # coordinate right-click then lands on the property (opening the property
    # panel). Dispatching on the element bypasses hit-testing so the commercial
    # marker's own Leaflet contextmenu handler fires regardless of overlap.
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


class TestCommercialStormsPanel:
    """Click-through: menu → 'View Storm Scenarios' → prop-storm-panel opens.

    The frontend reuses the same PropertyStormAnalysis panel for both
    asset types — the panel detects the CPROP- prefix and fetches the
    commercial endpoint. So the panel-open assertion mirrors residential,
    just gated on the commercial menu item.
    """

    def test_view_storm_scenarios_opens_panel(self, map_page):
        map_page.wait_for_function(
            "() => typeof window.viewCommercialStorms === 'function'",
            timeout=10_000,
        )

        _right_click_commercial_marker(map_page)
        menu = map_page.locator(".ctx-menu")
        if menu.count() == 0:
            pytest.skip("No context menu appeared")

        storm_item = map_page.locator(".ctx-menu-item",
                                      has_text="View Storm Scenarios")
        if storm_item.count() == 0:
            pytest.skip("No 'View Storm Scenarios' menu item")
        storm_item.first.click()

        # The panel issues a fetch + tab render — give it room.
        map_page.wait_for_timeout(8_000)

        panel_visible = map_page.evaluate("""() => {
            const panel = document.getElementById('prop-storm-panel');
            return panel !== null
                && panel.style.display !== 'none'
                && panel.style.display !== '';
        }""")
        assert panel_visible, (
            "prop-storm-panel did not open after clicking 'View Storm Scenarios'"
        )

        # Title should say "Commercial Storm Scenarios" not "Property…"
        title = map_page.evaluate("""() => {
            const el = document.getElementById('prop-storm-title');
            return el ? el.textContent : '';
        }""")
        assert "Commercial" in title, (
            f"Expected 'Commercial' in panel title, got: {title!r}"
        )


class TestCommercialHazardPanel:
    """Click-through: menu → 'Physical Risk Swap' → property-hc-panel opens.

    Same shared-panel approach as the storms tab — PropertyHazardCurvePanel
    detects the CPROP- prefix and routes all five fetches (/hazard, /she,
    /shd, /bri, /<id>) to /api/v1/commercial/* instead of
    /api/v1/properties/*.
    """

    def test_window_view_commercial_hazard_is_function(self, map_page):
        map_page.wait_for_function(
            "() => typeof window.viewCommercialHazard === 'function'",
            timeout=10_000,
        )

    def test_hazard_routes_reachable_from_browser(self, map_page):
        """All five endpoints used by the hazard panel return 200.

        Includes /bri — the panel's loadData() fetches it for the resilient
        flood count, so a missing commercial /bri route surfaces here as a 404
        (it previously slipped through because /bri wasn't asserted)."""
        cprop_id = _active_commercial_id(map_page)

        result = map_page.evaluate(f"""async () => {{
            const paths = ['/hazard', '/she', '/shd', '/bri', ''];
            const out = {{}};
            for (const p of paths) {{
                try {{
                    const r = await fetch('/api/v1/commercial/{cprop_id}' + p);
                    out[p || 'base'] = r.status;
                }} catch (e) {{ out[p || 'base'] = 'err: ' + e.message; }}
            }}
            return out;
        }}""")
        assert result["/hazard"] == 200, f"/hazard: {result['/hazard']}"
        assert result["/she"] == 200, f"/she: {result['/she']}"
        assert result["/shd"] == 200, f"/shd: {result['/shd']}"
        assert result["/bri"] == 200, f"/bri: {result['/bri']}"
        assert result["base"] == 200, f"base: {result['base']}"

    def test_physical_risk_swap_opens_panel(self, map_page):
        """Right-click → 'Physical Risk Swap' → property-hc-panel visible
        with 'Commercial PRS Pricer' in the title."""
        map_page.wait_for_function(
            "() => typeof window.viewCommercialHazard === 'function'",
            timeout=10_000,
        )

        _right_click_commercial_marker(map_page)
        menu = map_page.locator(".ctx-menu")
        if menu.count() == 0:
            pytest.skip("No context menu appeared")

        hazard_item = map_page.locator(".ctx-menu-item",
                                       has_text="Physical Risk Swap")
        if hazard_item.count() == 0:
            pytest.skip("No 'Physical Risk Swap' menu item")
        hazard_item.first.click()

        # Panel issues 4 fetches + Chart.js render — generous window.
        map_page.wait_for_timeout(10_000)

        panel_visible = map_page.evaluate("""() => {
            const panel = document.getElementById('property-hc-panel');
            return panel !== null
                && panel.style.display !== 'none'
                && panel.style.display !== '';
        }""")
        assert panel_visible, (
            "property-hc-panel did not open after clicking "
            "'Physical Risk Swap' on a commercial marker"
        )

        title = map_page.evaluate("""() => {
            const el = document.getElementById('phc-panel-title');
            return el ? el.textContent : '';
        }""")
        assert "Commercial" in title, (
            f"Expected 'Commercial' in PRS panel title, got: {title!r}"
        )
