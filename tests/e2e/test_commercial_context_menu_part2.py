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

"""Commercial context menu + PDF e2e tests (part 2).

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


class TestCommercialReportRouteFromBrowser:
    """Exercise the /api/v1/commercial/report endpoint from the page context.

    These tests fire the API directly via ``page.evaluate`` so we get
    coverage even when right-click event dispatch is finicky in headless
    mode. They confirm the backend handler is wired, the route is
    registered, and the PDF payload is valid base64-encoded.
    """

    def test_route_returns_base64_pdf(self, map_page):
        """POST /api/v1/commercial/report → 200 + base64 PDF magic."""
        map_page.wait_for_function(
            "() => typeof window.__BACKEND_CONFIG === 'object'",
            timeout=10_000,
        )

        # Grab a real commercial PropertyID from the active catchment.
        cprop_id = _active_commercial_id(map_page)

        # Hit the route from the browser context.
        result = map_page.evaluate(f"""async () => {{
            const resp = await fetch('/api/v1/commercial/report', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{'propertyId': '{cprop_id}'}})
            }});
            const data = await resp.json();
            return {{
                status: resp.status,
                hasBase64: Boolean(data && data.pdf_base64),
                pdfMagic: data && data.pdf_base64
                          ? atob(data.pdf_base64).substring(0, 4)
                          : null,
            }};
        }}""")

        assert result["status"] == 200, f"Route returned {result['status']}"
        assert result["hasBase64"], "Response missing pdf_base64"
        assert result["pdfMagic"] == "%PDF", (
            f"Expected PDF magic '%PDF', got: {result['pdfMagic']!r}"
        )

    def test_route_returns_404_for_unknown_id(self, map_page):
        """Unknown PropertyID → 404 with status='error'."""
        result = map_page.evaluate("""async () => {
            const resp = await fetch('/api/v1/commercial/report', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({'propertyId': 'CPROP-doesnotexist'})
            });
            const data = await resp.json();
            return {status: resp.status, payload: data};
        }""")
        assert result["status"] == 404
        assert result["payload"].get("status") == "error"

    def test_window_generate_commercial_report_is_function(self, map_page):
        """``window.generateCommercialReport`` exposed after backend handler init."""
        map_page.wait_for_function(
            "() => typeof window.generateCommercialReport === 'function'",
            timeout=10_000,
        )

    def test_window_view_commercial_storms_is_function(self, map_page):
        """``window.viewCommercialStorms`` exposed after backend handler init."""
        map_page.wait_for_function(
            "() => typeof window.viewCommercialStorms === 'function'",
            timeout=10_000,
        )

    def test_storms_route_returns_data_for_real_id(self, map_page):
        """GET /api/v1/commercial/<id>/storms → 200 + expected shape."""
        cprop_id = _active_commercial_id(map_page)

        result = map_page.evaluate(f"""async () => {{
            const resp = await fetch('/api/v1/commercial/{cprop_id}/storms');
            const data = await resp.json();
            return {{
                status: resp.status,
                ok: data.status === 'success',
                hasEvents: Array.isArray(data.flood_events),
                hasGauges: Array.isArray(data.nearest_gauges),
                hasSummary: typeof data.summary === 'object',
            }};
        }}""")
        assert result["status"] == 200, f"Status: {result['status']}"
        assert result["ok"]
        assert result["hasEvents"]
        assert result["hasGauges"]
        assert result["hasSummary"]
