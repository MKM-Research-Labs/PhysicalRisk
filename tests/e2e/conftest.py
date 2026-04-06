# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

"""
Playwright e2e test fixtures.

Starts a Flask dev server on a free port, provides a Playwright page
pre-navigated to the map, and tears everything down after the session.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from tests.e2e._helpers import (
    ROOT,
    _free_port,
    _wait_for_server,
    # Re-export helpers so existing `from tests.e2e.conftest import X` works
    get_first_meeting_id,
    open_meeting_detail,
    close_all_data_panels,
    PANEL_IDS_TO_CLOSE,
    CLOSE_PANELS_JS,
    close_all_storm_panels,
    open_storm_portfolio,
    close_storm_portfolio,
    cpf_close_all_panels,
    cpf_open_gauge_panel,
    cpf_open_trading_desk,
    ps_close_all_panels,
    ps_open_trading_desk,
    ps_close_trading_desk,
    td_close_all_panels,
    td_open_trading_desk,
    td_close_trading_desk,
)


# ---------------------------------------------------------------------------
# Session-scoped: one server + one browser for the entire test session
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def server_port():
    """Start Flask server on a free port; yield the port; kill on teardown."""
    import os
    port = _free_port()
    # Inherit parent environment so config, data paths, and libraries resolve
    env = os.environ.copy()
    env.update({
        "MKM_SERVER_PORT": str(port),
        "MKM_SERVER_HOST": "127.0.0.1",
        "PYTHONUNBUFFERED": "1",
    })

    # Always delete cached visualization so it regenerates with current
    # BACKEND_CONFIG (url='', relative paths). Without this, a stale HTML
    # file from a previous server run may contain an absolute URL pointing
    # to a dead port — causing "Failed to load hazard curve data".
    for cached in (ROOT / "data" / "results").glob("visualization_*.html"):
        cached.unlink(missing_ok=True)

    proc = subprocess.Popen(
        [sys.executable, "app.py", "server"],
        cwd=str(ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    if not _wait_for_server(port):
        # Dump whatever the server printed for debugging
        proc.kill()
        out, _ = proc.communicate(timeout=5)
        pytest.fail(
            f"Flask server did not start on port {port} within 30s.\n"
            f"Server output:\n{out.decode(errors='replace')[:2000]}"
        )

    yield port

    proc.kill()
    proc.wait(timeout=5)


@pytest.fixture(scope="session")
def base_url(server_port):
    return f"http://127.0.0.1:{server_port}"


# ---------------------------------------------------------------------------
# Session-scoped page — load the visualization ONCE for all tests
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def _browser_page(browser, base_url):
    """Create a single browser page for the entire test session.

    Loads /visualization once (~2 min), waits for preloader, then
    reuses the same page for every test. Much faster than reloading.
    """
    context = browser.new_context(viewport={"width": 1400, "height": 900})
    page = context.new_page()
    page.set_default_timeout(300_000)  # 5 min for all actions (storm sequences take 3-5 min to load)

    viz_url = f"{base_url}/visualization"
    page.goto(viz_url, wait_until="networkidle", timeout=180_000)

    # Wait for Leaflet map
    page.wait_for_selector(".leaflet-container", timeout=60_000)

    # Wait for startup preloader to finish
    try:
        page.wait_for_function(
            "() => window._tdPreloadDone === true",
            timeout=120_000,
        )
    except Exception:
        page.wait_for_timeout(15_000)

    yield page

    context.close()


@pytest.fixture
def map_page(_browser_page):
    """Provide the shared page to each test.

    Closes any open panels between tests to keep state clean.
    """
    page = _browser_page

    # Clean up: close ALL open panels from previous test
    page.evaluate("""() => {
        // Close every known panel
        const panels = [
            'trading-desk-panel',
            'hazard-curve-panel',
            'property-hc-panel',
            'prop-storm-panel',
            'mortgage-detail-panel',
            'mg-panel',
            'property-pdf-panel',
            'storm-portfolio-panel',
            'gauge-pdf-panel',
            'gauge-graph-panel',
        ];
        panels.forEach(id => {
            const el = document.getElementById(id);
            if (el) el.style.display = 'none';
        });
        // Close any context menus
        document.querySelectorAll('.ctx-menu').forEach(m => m.remove());
    }""")

    return page


# ---------------------------------------------------------------------------
# Data helpers — load from production data files for assertion values
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def gauge_data():
    """Load gauge.json for test assertions."""
    path = ROOT / "data" / "input" / "thames" / "gauge.json"
    if not path.exists():
        pytest.skip("gauge.json not found — run `python app.py port` first")
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="session")
def property_data():
    """Load property.json for test assertions."""
    path = ROOT / "data" / "input" / "thames" / "property.json"
    if not path.exists():
        pytest.skip("property.json not found — run `python app.py port` first")
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="session")
def trade_data(base_url):
    """Fetch blotter data from the running server."""
    import urllib.request
    try:
        resp = urllib.request.urlopen(f"{base_url}/api/v1/trading/blotter", timeout=5)
        return json.loads(resp.read())
    except Exception:
        return {"trades": []}


@pytest.fixture(scope="session")
def first_traded_gauge_id():
    """Return a gauge ID that has open (non-closed) trades."""
    # Trades live in data/input/<catchment>/prs/
    prs_dir = ROOT / "data" / "input" / "thames" / "prs"
    if not prs_dir.exists():
        # Fallback to legacy location
        prs_dir = ROOT / "data" / "output" / "prs"
    if not prs_dir.exists():
        pytest.skip("No PRS trade directory")
    for f in sorted(prs_dir.glob("PRS-*.json")):
        try:
            with open(f) as fh:
                d = json.load(fh)
            ps = d.get("PhysicalSwap", {})
            status = ps.get("Header", {}).get("TradeStatus", "")
            if status == "Closed":
                continue
            basket = ps.get("GaugeSet", {}).get("GaugeBasket", [])
            for g in basket:
                gid = g.get("GaugeID", "")
                if gid:
                    return gid
        except Exception:
            continue
    pytest.skip("No open trades with gauge IDs found")


@pytest.fixture(scope="session")
def first_gauge_id(first_traded_gauge_id):
    """Return a gauge ID for targeted tests."""
    return first_traded_gauge_id


@pytest.fixture(scope="session")
def first_property_id(property_data):
    """Return the first property ID for targeted tests."""
    props = property_data.get("properties", [])
    if not props:
        pytest.skip("No properties in property.json")
    p = props[0]
    prop_id = (p.get("PropertyHeader", {})
                .get("Header", {})
                .get("PropertyID", ""))
    if not prop_id:
        prop_id = p.get("property_id", "")
    assert prop_id, "Could not find property ID in property.json"
    return prop_id
