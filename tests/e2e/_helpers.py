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
         'prop-storm-panel','mortgage-detail-panel','mg-panel','property-pdf-panel'].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.style.display = 'none';
        });
        document.querySelectorAll('.ctx-menu').forEach(m => m.remove());
        document.querySelectorAll('.notif-message').forEach(n => n.remove());
    }""")


# ---------------------------------------------------------------------------
# Storm Portfolio panel helpers (shared by test_storm_portfolio_part*.py)
# ---------------------------------------------------------------------------

PANEL_IDS_TO_CLOSE = [
    "trading-desk-panel",
    "hazard-curve-panel",
    "property-hc-panel",
    "prop-storm-panel",
    "mortgage-detail-panel",
    "mg-panel",
    "property-pdf-panel",
    "storm-portfolio-panel",
    "gauge-pdf-panel",
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
        ['trading-desk-panel','hazard-curve-panel','property-hc-panel','prop-storm-panel','mortgage-detail-panel','mg-panel','property-pdf-panel'].forEach(id => {
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
