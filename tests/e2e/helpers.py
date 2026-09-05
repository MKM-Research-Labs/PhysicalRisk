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
Shared helper functions for e2e tests.

Provides panel open/close, trading desk, gauge panel, property panel,
used across all split e2e test files.
"""

import pytest


# ---------------------------------------------------------------------------
# Panel IDs
# ---------------------------------------------------------------------------

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
]

CLOSE_PANELS_JS = """() => {
    %s.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.style.display = 'none';
    });
    document.querySelectorAll('.ctx-menu').forEach(m => m.remove());
    document.querySelectorAll('.notif-message').forEach(n => n.remove());
}""" % str(PANEL_IDS_TO_CLOSE).replace("'", '"')


# ---------------------------------------------------------------------------
# Generic helpers
# ---------------------------------------------------------------------------

def clear_notifications(page):
    """Remove all notification elements from the page."""
    page.evaluate("""() => {
        document.querySelectorAll('.notif-message, .notif-container, [id*="notif"]')
            .forEach(n => n.remove());
    }""")


def assert_no_error_notifications(page, context=""):
    """Fail if any error notifications appeared *after* the last clear."""
    errors = page.evaluate("""() => {
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
        f"Data load errors after opening {context}: {errors}"
    )


def close_all_panels(page):
    """Hide every known panel and remove context menus / notifications."""
    page.evaluate(CLOSE_PANELS_JS)


# ---------------------------------------------------------------------------
# Trading desk helpers
# ---------------------------------------------------------------------------

def open_trading_desk(page, tab=None):
    """Open the trading desk panel and optionally switch to a tab."""
    # Dismiss notifications and ensure panel is not forcibly hidden
    page.evaluate("""() => {
        document.querySelectorAll('.notif-message, [id*="notif"]').forEach(n => n.remove());
        const p = document.getElementById('trading-desk-panel');
        if (p) p.style.display = '';
    }""")

    # Wait for the startup preload before opening. TradingDesk.show() takes
    # two paths: with window._tdPreloadDone it opens immediately, without it
    # it runs an async preload and opens in the callback — and that callback
    # ends in switchTab('blotter'). Opening before the preload lands means a
    # tab selected here is silently switched back to the blotter a moment
    # later, which is what made the EOD view "still hidden after clicking
    # #td-tab-eod": the view was revealed and then hidden again.
    try:
        page.wait_for_function(
            "() => window._tdPreloadDone === true", timeout=60_000)
    except Exception:
        # Preload never signalled; carry on rather than failing every trading
        # desk test on it, but the race above may recur.
        pass

    page.evaluate("""() => {
        if (window.TradingDesk && window.TradingDesk.show) {
            window.TradingDesk.show();
        }
    }""")
    td = page.locator("#trading-desk-panel")
    try:
        td.wait_for(state="visible", timeout=5_000)
    except Exception:
        # Fallback: click Pi button
        pi_btn = page.locator("text=\u03a0")
        if pi_btn.count() > 0:
            pi_btn.first.click(force=True)
            try:
                td.wait_for(state="visible", timeout=5_000)
            except Exception:
                # Last resort. Forcing display makes the panel visible without
                # _tdOpenPanel having run, so no tab has been selected and a
                # late preload callback can still call switchTab('blotter')
                # over the top of whatever the test picks. Kept so a panel
                # that never opens still produces a specific failure further
                # down rather than a timeout here.
                page.evaluate(
                    "document.getElementById('trading-desk-panel').style.display = ''"
                )
                page.wait_for_timeout(1_500)

    if tab:
        # Check the panel first. A view is not "visible" while its parent is
        # hidden, so asserting on the view alone would blame the tab switch
        # for a panel that never opened — naming the wrong cause is what this
        # helper is meant to stop doing.
        assert page.locator("#trading-desk-panel").is_visible(), (
            "#trading-desk-panel is not visible — the trading desk did not "
            f"open, so the {tab} tab was never reachable"
        )
        tab_btn = page.locator(f"#td-tab-{tab}")
        # A missing tab button used to fall through to the wait, leaving the
        # requested view hidden — every later assertion then failed as though
        # the control it wanted were absent, which sends you looking in the
        # wrong file. Fail here, naming the tab.
        assert tab_btn.count() > 0, (
            f"trading desk has no #td-tab-{tab} button — the panel did not "
            f"build its tab bar, so nothing in the {tab} view can be reached"
        )
        tab_btn.click(force=True)
        page.wait_for_timeout(3_000)
        # is_visible() is False both for a hidden element and for one that is
        # not in the DOM at all, and those want different fixes — so say which.
        view = page.locator(f"#td-{tab}-view")
        assert view.count() > 0, (
            f"#td-{tab}-view is not in the DOM — the panel was built without "
            f"it (see trading/tradingdesk/panel_create.js)"
        )
        assert view.is_visible(), (
            f"#td-{tab}-view exists but is hidden after clicking "
            f"#td-tab-{tab}, with the panel itself visible — switchTab did "
            f"not reveal it, or something switched away afterwards (see "
            f"trading/tradingdesk/panel_tabs.js)"
        )


def close_trading_desk(page):
    """Close the trading desk panel if visible."""
    panel = page.locator("#trading-desk-panel")
    if panel.is_visible():
        close_btn = panel.locator("text=\u00d7").first
        if close_btn.is_visible():
            close_btn.click(force=True)


# ---------------------------------------------------------------------------
# Gauge panel helpers
# ---------------------------------------------------------------------------

def _open_gauge_panel_once(page, gauge_id):
    """Attempt to open the gauge hazard curve panel. Returns True on success."""
    clear_notifications(page)
    has_fn = page.evaluate("() => typeof window.viewHazardCurve === 'function'")
    if has_fn:
        page.evaluate(f"window.viewHazardCurve('{gauge_id}')")
    else:
        has_alt = page.evaluate(
            "() => window.GaugeHazardCurve && "
            "typeof window.GaugeHazardCurve.show === 'function'"
        )
        if has_alt:
            page.evaluate(f"window.GaugeHazardCurve.show('{gauge_id}')")
        else:
            pytest.skip(
                "Neither viewHazardCurve nor GaugeHazardCurve.show available"
            )
    page.locator("#hazard-curve-panel").wait_for(
        state="visible", timeout=10_000
    )
    page.wait_for_timeout(6_000)


def open_gauge_panel(page, gauge_id):
    """Open the gauge hazard curve panel, retrying once on load error."""
    _open_gauge_panel_once(page, gauge_id)
    errors = page.evaluate("""() => {
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
    if errors:
        # Retry once — transient server startup or data load lag
        close_gauge_panel(page)
        page.wait_for_timeout(3_000)
        _open_gauge_panel_once(page, gauge_id)
        assert_no_error_notifications(page, "gauge panel (retry)")


def close_gauge_panel(page):
    """Close the gauge panel if open (JS-based, avoids notification interception)."""
    page.evaluate("""() => {
        document.querySelectorAll('.notif-message, .notif-container, [id*="notif"]')
            .forEach(n => n.remove());
        const p = document.getElementById('hazard-curve-panel');
        if (p) p.style.display = 'none';
    }""")


def switch_gauge_tab(page, tab_index):
    """Click a gauge panel tab by index and wait for rendering."""
    tab = page.locator(f".hazard-tab[data-tab='{tab_index}']")
    assert tab.count() > 0, f"Tab {tab_index} not found in tab bar"
    page.evaluate("""() => {
        document.querySelectorAll('.notif-message').forEach(n => n.remove());
        const m = document.getElementById('td-closeout-modal');
        if (m) m.style.display = 'none';
        const pdf = document.getElementById('gauge-pdf-panel');
        if (pdf) pdf.style.display = 'none';
    }""")
    tab.click(force=True)
    page.wait_for_timeout(3_000)


def switch_to_prs_tab_gauge(page):
    """Switch to the PRS pricing tab (tab index 0) in gauge panel."""
    tabs = page.locator("#hazard-curve-panel .hazard-tab")
    if tabs.count() > 0:
        tabs.first.click(force=True)
    page.wait_for_timeout(3_000)


# ---------------------------------------------------------------------------
# Property panel helpers
# ---------------------------------------------------------------------------

def open_property_panel(page, property_id):
    """Open the property hazard curve panel for a given property."""
    has_fn = page.evaluate(
        "() => typeof window.viewPropertyHazard === 'function'"
    )
    if has_fn:
        page.evaluate(f"window.viewPropertyHazard('{property_id}')")
    else:
        has_alt = page.evaluate(
            "() => window.PropertyHazardCurvePanel && "
            "typeof window.PropertyHazardCurvePanel.show === 'function'"
        )
        if has_alt:
            page.evaluate(
                f"window.PropertyHazardCurvePanel.show('{property_id}')"
            )
        else:
            pytest.skip("window.viewPropertyHazard not available")
    page.locator("#property-hc-panel").wait_for(
        state="visible", timeout=10_000
    )
    _wait_property_panel_loaded(page)


def _wait_property_panel_loaded(page):
    """Wait for the property panel's async data load to finish.

    ``viewPropertyHazard`` shows ``#property-hc-panel`` immediately, but
    ``loadData`` then fetches hazard + SHE/SHD/BRI/storms + counterparties
    before setting ``phcData`` and re-rendering the active tab. Until that
    completes the phcData-gated tabs (Basis Explorer, PRS, Flood History)
    render nothing, so a caller that proceeds on "panel visible" alone races
    an empty panel. ``#phc-status`` reads ``Loading...`` on entry and the
    loaded summary (or an error) when done — wait for it to leave that state.
    """
    try:
        page.wait_for_function(
            "() => { var s = document.getElementById('phc-status');"
            " return s && s.textContent"
            " && s.textContent.indexOf('Loading') === -1; }",
            timeout=20_000,
        )
    except Exception:
        pass


def switch_to_prs_tab_property(page):
    """Switch to the PRS pricing tab (tab index 2) in property panel."""
    tabs = page.locator("#property-hc-panel .phc-tab")
    if tabs.count() > 2:
        tabs.nth(2).click(force=True)
    elif tabs.count() > 0:
        tabs.last.click(force=True)
    page.wait_for_timeout(3_000)


def switch_to_basis_explorer_tab(page):
    """Switch to the Basis Explorer tab (tab index 3) in property panel."""
    tabs = page.locator("#property-hc-panel .phc-tab")
    if tabs.count() > 3:
        tabs.nth(3).click(force=True)
    elif tabs.count() > 0:
        tabs.last.click(force=True)
    page.wait_for_timeout(2_000)


def switch_basis_sub_tab(page, sub_tab_index):
    """Switch to a Basis Explorer sub-tab by index (0=Gauge, 1=SHE, 2=SHD, 3=Property)."""
    sub_tabs = page.locator(".phc-basis-subtab")
    if sub_tabs.count() > sub_tab_index:
        sub_tabs.nth(sub_tab_index).click(force=True)
    page.wait_for_timeout(2_000)
