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

"""Commercial context menu + PDF e2e tests (part 4).

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


from tests.e2e._helpers import (
    find_commercial_markers,
    open_commercial_context_menu,
)

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

class TestCommercialLoanReport:
    """Wiring for the "Loan Details" + "Generate Loan Report" menu items.

    Both menu actions resolve to the same PDF-report code path
    (window.viewCLoanDetails delegates to window.generateCLoanReport,
    same pattern as viewCommercialDetails / generateCommercialReport).
    """

    def test_window_generate_loan_report_is_function(self, map_page):
        map_page.wait_for_function(
            "() => typeof window.generateCLoanReport === 'function'",
            timeout=10_000,
        )

    def test_window_view_loan_details_is_function(self, map_page):
        map_page.wait_for_function(
            "() => typeof window.viewCLoanDetails === 'function'",
            timeout=10_000,
        )

    def test_loan_report_route_returns_pdf_for_real_id(self, map_page):
        """POST /api/v1/commercial/loan-report → 200 + base64 PDF."""
        cprop_id = _active_commercial_id(map_page)

        result = map_page.evaluate(f"""async () => {{
            const resp = await fetch('/api/v1/commercial/loan-report', {{
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
        assert result["status"] == 200, f"Status: {result['status']}"
        assert result["hasBase64"]
        assert result["pdfMagic"] == "%PDF"

    def test_loan_report_route_returns_404_for_unknown_id(self, map_page):
        result = map_page.evaluate("""async () => {
            const resp = await fetch('/api/v1/commercial/loan-report', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({'propertyId': 'CPROP-doesnotexist'})
            });
            return {status: resp.status, payload: await resp.json()};
        }""")
        assert result["status"] == 404
        assert result["payload"].get("status") == "error"

    def test_generate_loan_report_menu_opens_pdf_panel(self, map_page):
        """Right-click → 'Generate Loan Report' → property-pdf-panel visible."""
        map_page.wait_for_function(
            "() => typeof window.generateCLoanReport === 'function'",
            timeout=10_000,
        )

        open_commercial_context_menu(map_page)
        menu = map_page.locator(".ctx-menu")
        if menu.count() == 0:
            pytest.skip("No context menu appeared")

        loan_item = map_page.locator(".ctx-menu-item",
                                     has_text="Generate Loan Report")
        # Sibling tests confirm window.generateLoanReport exists and the route
        # returns a PDF, so the menu item missing is a UI gap, not absent data.
        #
        # Report which menu actually opened. createMenu builds one element per
        # type ('{type}-context-menu') and only removes the one it is
        # replacing, so several can coexist with one displayed — "no item"
        # therefore means either the commercial menu lacks it or the
        # right-click landed on a property/gauge marker, and those want
        # different fixes.
        menus = map_page.evaluate("""() => Array.from(
            document.querySelectorAll('.ctx-menu')).map(function (m) {
                return {
                    id: m.id,
                    shown: m.style.display !== 'none',
                    items: Array.from(m.querySelectorAll('.ctx-menu-item'))
                                .map(function (i) { return i.textContent; })
                };
            })""")
        assert loan_item.count() > 0, (
            "Commercial context menu has no 'Generate Loan Report' item — the "
            f"entry point this test exercises is missing. Menus present: {menus}"
        )
        loan_item.first.click()

        map_page.wait_for_timeout(8_000)
        panel_visible = map_page.evaluate("""() => {
            const panel = document.getElementById('property-pdf-panel');
            return panel !== null && panel.style.display !== 'none';
        }""")
        assert panel_visible, (
            "property-pdf-panel did not open after clicking 'Generate Loan Report'"
        )


class TestStartupStatusPopupCommercial:
    """The bottom-left "Loading MKM Research Platform…" popup should list
    Commercial assets + Commercial loans alongside the existing residential
    entries.
    """

    def test_preloader_cache_vars_populated(self, map_page):
        """window._preCommercial + window._preCommercialLoans should hold
        the data fetched by the startup preloader."""
        # Generous wait — preloader fires on DOMContentLoaded; popup
        # closes when all fetches settle.
        map_page.wait_for_function(
            "() => window._preCommercial !== null && "
            "      window._preCommercialLoans !== null",
            timeout=20_000,
        )
        result = map_page.evaluate("""() => ({
            commercialCount:
                (window._preCommercial && window._preCommercial.count) || 0,
            loanCount:
                (window._preCommercialLoans && window._preCommercialLoans.count) || 0,
        })""")
        assert result["commercialCount"] >= 1, (
            f"Expected ≥1 commercial asset, got {result['commercialCount']}"
        )
        assert result["loanCount"] >= 1, (
            f"Expected ≥1 commercial loan, got {result['loanCount']}"
        )

    def test_commercial_asset_names_in_property_names_lookup(self, map_page):
        """CPROP-* ids should resolve in window._propertyNames so the
        right-click menu titles can show the building name."""
        map_page.wait_for_function(
            "() => window._preCommercial !== null",
            timeout=20_000,
        )
        result = map_page.evaluate("""() => {
            const names = window._propertyNames || {};
            const cprops = Object.keys(names).filter(k => k.indexOf('CPROP-') === 0);
            return {count: cprops.length};
        }""")
        assert result["count"] >= 1, (
            f"No CPROP-* ids in window._propertyNames; got {result}"
        )
