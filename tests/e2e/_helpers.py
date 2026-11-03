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
Non-fixture helpers extracted from conftest.py to keep conftest under 300 lines.

Contains: helper functions, constants, and panel-management utilities
used by e2e test files.
"""

import json
import socket
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------------------
# Server helpers
# ---------------------------------------------------------------------------

def _free_port() -> int:
    """Find an available TCP port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _wait_for_server(port: int, timeout: float = 30.0) -> bool:
    """Block until the server accepts TCP connections or timeout."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                return True
        except OSError:
            time.sleep(0.3)
    return False


# ---------------------------------------------------------------------------
# MRC CRUD helpers (shared by test_gov_mrc_crud.py)
# ---------------------------------------------------------------------------

def close_all_data_panels(page):
    """Close all panels and dismiss notifications (for data load tests)."""
    page.evaluate("""() => {
        ['trading-desk-panel','hazard-curve-panel','property-hc-panel',
         'prop-storm-panel','mortgage-detail-panel','property-pdf-panel'].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.style.display = 'none';
        });
        document.querySelectorAll('.ctx-menu').forEach(m => m.remove());
        document.querySelectorAll('.notif-message').forEach(n => n.remove());
    }""")


# ---------------------------------------------------------------------------
# Storm Portfolio panel helpers (shared by test_storm_portfolio_part*.py)
# ---------------------------------------------------------------------------

# The single list of things that must be out of the way before a test drives
# the UI. It covers overlays as well as panels: a full-screen scrim left up by
# an earlier test in the same session swallows clicks at the coordinates
# force=True dispatches them to, so the click silently does nothing and the
# next assertion blames whatever it was looking for. Six copies of this list
# used to exist and had already drifted apart, which is how td-closeout-modal
# and loan-pricer-panel came to be missing from most of them. Add new ids here
# and nowhere else.
PANEL_IDS_TO_CLOSE = [
    "trading-desk-panel",
    "hazard-curve-panel",
    "property-hc-panel",
    "prop-storm-panel",
    "mortgage-detail-panel",
    "property-pdf-panel",
    "storm-portfolio-panel",
    "gauge-pdf-panel",
    "gauge-graph-panel",
    "loan-pricer-panel",
    "td-closeout-modal",
]

CLOSE_PANELS_JS = """() => {
    %s.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.style.display = 'none';
    });
    document.querySelectorAll('.ctx-menu').forEach(m => m.remove());
}""" % str(PANEL_IDS_TO_CLOSE).replace("'", '"')


def close_all_storm_panels(page):
    """Hide every known panel and remove context menus."""
    page.evaluate(CLOSE_PANELS_JS)


def open_storm_portfolio(page):
    """Open the Storm Portfolio panel via JS global function."""
    has_fn = page.evaluate(
        "() => typeof window.showStormPortfolio === 'function'"
    )
    if not has_fn:
        pytest.skip("window.showStormPortfolio not available")
    page.evaluate("window.showStormPortfolio()")
    page.locator("#storm-portfolio-panel").wait_for(
        state="visible", timeout=10_000
    )
    page.wait_for_timeout(3_000)  # storm list load


def close_storm_portfolio(page):
    """Close the Storm Portfolio panel if visible."""
    panel = page.locator("#storm-portfolio-panel")
    if panel.is_visible():
        close_btn = panel.locator("text=\u00d7").first
        if close_btn.count() > 0 and close_btn.is_visible():
            close_btn.click()
        else:
            page.evaluate("""() => {
                const el = document.getElementById('storm-portfolio-panel');
                if (el) el.style.display = 'none';
            }""")


# ---------------------------------------------------------------------------
# Cross-panel flow helpers (shared by test_cross_panel_flows.py)
# ---------------------------------------------------------------------------

def cpf_close_all_panels(page):
    """Close every known panel and remove context menus."""
    page.evaluate("""() => {
        ['trading-desk-panel','hazard-curve-panel','property-hc-panel','prop-storm-panel','mortgage-detail-panel','property-pdf-panel'].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.style.display = 'none';
        });
        document.querySelectorAll('.ctx-menu').forEach(m => m.remove());
    }""")


def cpf_open_gauge_panel(page, gauge_id):
    """Open the gauge hazard curve panel for the given gauge."""
    has_fn = page.evaluate("() => typeof window.viewHazardCurve === 'function'")
    if has_fn:
        page.evaluate(f"window.viewHazardCurve('{gauge_id}')")
    else:
        page.evaluate(f"window.GaugeHazardCurve.show('{gauge_id}')")
    page.locator("#hazard-curve-panel").wait_for(state="visible", timeout=10_000)
    page.wait_for_timeout(6_000)
    errors = page.evaluate("""() => {
        const notifs = document.querySelectorAll('.notif-message');
        const errors = [];
        notifs.forEach(n => {
            const text = n.textContent.toLowerCase();
            if (text.includes('fail') || text.includes('error') ||
                text.includes('unable')) errors.push(n.textContent.trim());
        });
        return errors;
    }""")
    assert len(errors) == 0, f"Data load errors after opening gauge panel: {errors}"


def cpf_open_trading_desk(page):
    """Click the Pi button to open the trading desk panel."""
    pi_btn = page.locator("text=\u03a0").first
    pi_btn.click(force=True)
    page.locator("#trading-desk-panel").wait_for(state="visible", timeout=5_000)


# ---------------------------------------------------------------------------
# Port stress helpers (shared by test_td_port_stress.py)
# ---------------------------------------------------------------------------

def ps_close_all_panels(page):
    """Hide every known panel and remove context menus."""
    page.evaluate(CLOSE_PANELS_JS)


def ps_open_trading_desk(page):
    """Click the Pi button and wait for the trading desk panel."""
    pi_btn = page.locator("text=\u03a0").first
    pi_btn.click()
    page.locator("#trading-desk-panel").wait_for(
        state="visible", timeout=10_000
    )
    page.wait_for_timeout(3_000)


def ps_close_trading_desk(page):
    """Close the trading desk panel via JS."""
    page.evaluate("""() => {
        const el = document.getElementById('trading-desk-panel');
        if (el) el.style.display = 'none';
    }""")


# ---------------------------------------------------------------------------
# TD tabs helpers (shared by test_td_tabs_part*.py)
# ---------------------------------------------------------------------------

def td_close_all_panels(page):
    """Hide every known panel and remove context menus (for td_tabs tests)."""
    page.evaluate(CLOSE_PANELS_JS)


def td_open_trading_desk(page):
    """Click the Pi button and wait for the trading desk panel (for td_tabs tests)."""
    pi_btn = page.locator("text=\u03a0").first
    pi_btn.click()
    page.locator("#trading-desk-panel").wait_for(
        state="visible", timeout=10_000
    )
    page.wait_for_timeout(3_000)


def td_close_trading_desk(page):
    """Close the trading desk panel via JS (for td_tabs tests)."""
    page.evaluate("""() => {
        const el = document.getElementById('trading-desk-panel');
        if (el) el.style.display = 'none';
    }""")


# ---------------------------------------------------------------------------
# Clustered marker helpers
# ---------------------------------------------------------------------------

# Property and commercial markers live in one Leaflet.markercluster group
# (visual/layer/cluster.py). A pin folded into a cluster bubble has no DOM
# element, so a test that needs a real pin spiderfies one bubble of that
# kind first. Spiderfying fans the pins out in place without changing the
# zoom, so the shared page keeps its landing view for later tests.
_ASSET_KIND_JS = """
    function _mkmKind(layer) {
        var o = layer.options && layer.options.icon && layer.options.icon.options;
        if (!o) return null;
        if (o.markerColor === 'purple') return 'commercial';
        if (o.icon === 'home' || o.icon === 'university') return 'property';
        return null;
    }
    function _mkmMap() {
        var k = Object.keys(window).find(function (k) { return k.startsWith('map_'); });
        return k ? window[k] : (window.mapInstance || null);
    }
    function _mkmClusterGroups(map) {
        var groups = [];
        map.eachLayer(function (l) {
            if (window.L && L.MarkerClusterGroup && l instanceof L.MarkerClusterGroup) {
                groups.push(l);
            }
        });
        return groups;
    }
"""

REVEAL_CLUSTERED_JS = """(kind) => {""" + _ASSET_KIND_JS + """
    var map = _mkmMap();
    if (!map) return false;
    var groups = _mkmClusterGroups(map);
    for (var i = 0; i < groups.length; i++) {
        var markers = groups[i].getLayers();
        for (var j = 0; j < markers.length; j++) {
            if (_mkmKind(markers[j]) !== kind) continue;
            var parent = groups[i].getVisibleParent(markers[j]);
            if (parent && parent !== markers[j] && parent.spiderfy) {
                parent.spiderfy();
                return true;
            }
        }
    }
    return false;
}"""

# What the map shows for each kind: the markers the cluster holds, what the
# visible bubbles and single pins account for, and what is drawn — the
# per-type numbers each bubble carries (data-property / data-commercial)
# plus the single pins in the DOM.
SHOWN_ASSET_COUNTS_JS = """() => {""" + _ASSET_KIND_JS + """
    var map = _mkmMap();
    var out = {property: {held: 0, shown: 0}, commercial: {held: 0, shown: 0},
               bubbles: 0, bubbleLabelsMatch: true};
    if (!map) return out;
    _mkmClusterGroups(map).forEach(function (g) {
        g.getLayers().forEach(function (m) {
            var kind = _mkmKind(m);
            if (!kind) return;
            out[kind].held++;
            if (g.getVisibleParent(m)) out[kind].shown++;
        });
    });
    var bubbles = document.querySelectorAll('.mkm-cluster div[data-property]');
    out.bubbles = bubbles.length;
    out.property.bubbleTotal = 0;
    out.commercial.bubbleTotal = 0;
    Array.prototype.forEach.call(bubbles, function (b) {
        var np = parseInt(b.dataset.property, 10), nc = parseInt(b.dataset.commercial, 10);
        out.property.bubbleTotal += np;
        out.commercial.bubbleTotal += nc;
        if (parseInt(b.textContent, 10) !== np + nc) out.bubbleLabelsMatch = false;
    });
    out.commercial.pins = document.querySelectorAll(
        ".leaflet-marker-pane [class*='awesome-marker-icon-purple']").length;
    out.property.pins = document.querySelectorAll(
        ".leaflet-marker-pane [class*='awesome-marker-icon-']:has(i.fa-home), " +
        ".leaflet-marker-pane [class*='awesome-marker-icon-']:has(i.fa-university)").length;
    return out;
}"""


def reveal_clustered_markers(page, kind):
    """Make at least one ``kind`` ('property' or 'commercial') pin exist in
    the DOM by spiderfying a bubble that holds one. Returns False when no
    pin of that kind is folded into a bubble."""
    revealed = page.evaluate(REVEAL_CLUSTERED_JS, kind)
    if revealed:
        page.wait_for_timeout(500)
    return revealed


# ---------------------------------------------------------------------------
# Commercial marker helpers
# ---------------------------------------------------------------------------

# Purple is unique to commercial markers: the property layer only ever emits
# red/orange/green (property_layer/layer.py::_get_property_icon) and the gauge
# layer blue/orange/red/gray (gauge_layer/marker.py::get_gauge_icon). No
# client-side code creates map markers at all, so anything purple came from
# commercial_layer/layer.py, where _MARKER_COLOR = "purple".
COMMERCIAL_MARKER_SELECTOR = "[class*='awesome-marker-icon-purple']"


def find_commercial_markers(page):
    """Locator over every commercial (purple) marker on the map, spiderfying
    a cluster bubble first when every commercial pin is folded into one."""
    markers = page.locator(COMMERCIAL_MARKER_SELECTOR)
    if markers.count() == 0:
        reveal_clustered_markers(page, "commercial")
    return markers


def _commercial_marker_diagnostics(page):
    """State needed to tell the ways this can fail apart.

    ``_markerType`` / ``_hasContextMenu`` are stamped by initializeMenus() onto
    the Leaflet *layer*, not onto the icon element, so this walks the map's
    layers the same way context-menus.js does rather than reading attributes
    off the DOM node (which would silently report null for everything).
    """
    return page.evaluate("""(sel) => {
        var pane = document.querySelector('.leaflet-marker-pane');
        var mapKey = Object.keys(window).find(
            function (k) { return k.startsWith('map_'); });
        var map = mapKey ? window[mapKey] : (window.mapInstance || null);
        var purpleLayers = [];
        if (map && window.L) {
            map.eachLayer(function (layer) {
                if (!(layer instanceof L.Marker)) return;
                var icon = layer._icon;
                if (!icon || !icon.className ||
                    icon.className.indexOf('awesome-marker-icon-purple') < 0) {
                    return;
                }
                purpleLayers.push({
                    id: layer._markerId || null,
                    type: layer._markerType || null,
                    bound: !!layer._hasContextMenu,
                });
            });
        }
        return {
            mapFound: !!map,
            markerPaneChildren: pane ? pane.children.length : 0,
            purpleElements: document.querySelectorAll(sel).length,
            allMarkerElements: document.querySelectorAll(
                "[class*='awesome-marker-icon-']").length,
            purpleLayers: purpleLayers,
            menus: Array.from(document.querySelectorAll('.ctx-menu')).map(
                function (m) {
                    return {
                        id: m.id,
                        shown: m.style.display !== 'none',
                        items: Array.from(
                            m.querySelectorAll('.ctx-menu-item')).map(
                                function (i) { return i.textContent; }),
                    };
                }),
        };
    }""", COMMERCIAL_MARKER_SELECTOR)


def open_commercial_context_menu(page):
    """Open the commercial context menu and prove it is the commercial one.

    Dispatches ``contextmenu`` on the marker element rather than pixel-clicking
    its centre. At the zoom the map fits the whole portfolio to, markers pack
    tightly — the nearest commercial/property pair in the thames set is 123 m
    apart, a few pixels, well inside a ~35 px icon — so a coordinate click can
    land on whichever marker paints on top. Dispatching on the element bypasses
    hit-testing entirely.

    That is not sufficient on its own, which is why this helper verifies the
    result. The tests here previously asserted only that *a* menu appeared, so
    a run that opened the property menu passed just as happily as one that
    opened the commercial menu, and the single test that looked for a specific
    commercial item was left to fail alone and unexplained. Each purple marker
    is tried in turn and the helper returns only once
    ``#commercial-context-menu`` is actually displayed.
    """
    # Remove rather than hide: a stale hidden menu from an earlier test is
    # indistinguishable from one this call created if we only toggle display.
    page.evaluate("""() => {
        if (window.hideAllMenus) window.hideAllMenus();
        document.querySelectorAll('.ctx-menu').forEach(m => m.remove());
    }""")

    markers = find_commercial_markers(page)
    count = markers.count()
    if count == 0:
        pytest.skip(
            "No commercial markers on the map. Diagnostics: "
            f"{_commercial_marker_diagnostics(page)}"
        )

    for i in range(count):
        marker = markers.nth(i)
        box = marker.bounding_box()
        detail = {"bubbles": True, "cancelable": True, "button": 2}
        if box:
            detail["clientX"] = int(box["x"] + box["width"] / 2)
            detail["clientY"] = int(box["y"] + box["height"] / 2)
        marker.dispatch_event("contextmenu", detail)
        # showMenu() builds the menu synchronously; this only covers the
        # Leaflet event plumbing in between.
        page.wait_for_timeout(500)
        opened = page.evaluate("""() => {
            const m = document.getElementById('commercial-context-menu');
            return !!m && m.style.display !== 'none';
        }""")
        if opened:
            return
        page.evaluate(
            "() => document.querySelectorAll('.ctx-menu')"
            ".forEach(m => m.remove())")

    raise AssertionError(
        f"Dispatched contextmenu on all {count} commercial (purple) markers "
        "and #commercial-context-menu never appeared. If a property menu "
        "opened instead, the marker was registered as type 'property' by "
        "initializeMenus() in context-menus.js — check that the popup still "
        "carries the CPROP- id, since the tooltip deliberately omits it. "
        f"Diagnostics: {_commercial_marker_diagnostics(page)}"
    )
