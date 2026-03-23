# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

"""
Shared helper functions for e2e tests.

Provides panel open/close, trading desk, gauge panel, property panel,
and governance panel helpers used across all split e2e test files.
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
    "mg-panel",
    "property-pdf-panel",
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

def assert_no_error_notifications(page, context=""):
    """Fail if any error notifications are present on the page."""
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
                page.evaluate(
                    "document.getElementById('trading-desk-panel').style.display = ''"
                )
                page.wait_for_timeout(1_500)

    if tab:
        tab_btn = page.locator(f"#td-tab-{tab}")
        if tab_btn.count() > 0:
            tab_btn.click(force=True)
        page.wait_for_timeout(3_000)


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

def open_gauge_panel(page, gauge_id):
    """Open the gauge hazard curve panel and assert no load errors."""
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
    assert_no_error_notifications(page, "gauge panel")


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


def switch_to_prs_tab_property(page):
    """Switch to the PRS pricing tab (tab index 2) in property panel."""
    tabs = page.locator("#property-hc-panel .property-tab")
    if tabs.count() > 0:
        if tabs.count() > 2:
            tabs.nth(2).click(force=True)
        else:
            tabs.last.click(force=True)
    page.wait_for_timeout(3_000)


# ---------------------------------------------------------------------------
# Governance panel helpers
# ---------------------------------------------------------------------------

def open_governance(page):
    """Open the governance panel using button click or JS fallback."""
    close_all_panels(page)
    mg_btn = page.locator("#mg-panel-btn")
    if mg_btn.count() == 0:
        mg_btn = (
            page.locator("[title*='Governance']")
            .or_(page.locator("[title*='Regulatory']"))
            .or_(page.locator("[title*='Model']"))
        )
    if mg_btn.count() > 0:
        mg_btn.first.click(force=True)
        page.locator("#mg-panel").wait_for(state="visible", timeout=10_000)
    else:
        pytest.skip("No governance button found")


def switch_governance_tab(page, tab_name):
    """Switch to a governance tab by clicking the button or JS fallback."""
    tab_btn = page.locator(f"#mg-tab-{tab_name}")
    if tab_btn.count() > 0:
        tab_btn.first.click(force=True)
    else:
        page.evaluate(
            f"typeof switchMgTab === 'function' && switchMgTab('{tab_name}')"
        )
    page.wait_for_timeout(1_500)


def get_governance_content_text(page):
    """Return lowercase text content of the governance content area."""
    content = page.locator("#mg-content")
    if content.count() > 0:
        return content.inner_text().lower()
    return ""
