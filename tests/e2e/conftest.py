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
Playwright e2e test fixtures.

Starts a Flask dev server on a free port, provides a Playwright page
pre-navigated to the map, and tears everything down after the session.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import pytest

from tests.e2e import _js_coverage
from tests.e2e._helpers import (
    ROOT,
    _free_port,
    _wait_for_server,
    # Re-export helpers so existing `from tests.e2e.conftest import X` works
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
# Guard mutable data files against E2E mutation
# ---------------------------------------------------------------------------

# Shared across conftest and test_td_control — Playwright tests stub
# window.prompt() with this value to exercise the admin password gate.
E2E_ADMIN_PW = "e2etestpw"


def _volume_mount_root(path):
    """Mount point of the volume containing ``path``.

    APFS ``clonefile`` (``cp -c``) needs source and destination on the *same*
    volume, so clones live under the source volume's mount root — not the
    internal tmp dir (a different volume, which would fall back to a deep copy).
    """
    path = os.path.realpath(path)
    dev = os.stat(path).st_dev
    while True:
        parent = os.path.dirname(path)
        if parent == path or os.stat(parent).st_dev != dev:
            return path
        path = parent


def _sweep_stale_clones(base, prefix=".e2e_catch_", max_age_s=6 * 3600):
    """Remove clone dirs orphaned by a SIGKILLed run (older than max_age)."""
    try:
        now = time.time()
        for name in os.listdir(base):
            if not name.startswith(prefix):
                continue
            p = os.path.join(base, name)
            try:
                if now - os.path.getmtime(p) > max_age_s:
                    shutil.rmtree(p, ignore_errors=True)
            except OSError:
                pass
    except OSError:
        pass


@pytest.fixture(scope="session", autouse=True)
def _isolated_catchment_dir(tmp_path_factory):
    """Point the Flask subprocess at a tmp copy of data/input/<catchment>/.

    Why this exists:
      - E2E tests (notably ``test_td_control.py::test_reset_button_reverts_to_defaults``)
        exercise the admin-gated Control tab by POSTing arbitrary values
        (including ``event_window_hours=120``) through the real save endpoint.
      - The Flask subprocess inherits the parent env and resolves
        ``config.get_input_dir()`` to ``data/input/<catchment>/``, so without
        isolation the real file on disk gets mutated by the test.
      - A previous "snapshot + restore" fixture protected the file only when
        teardown completed cleanly. If the suite was SIGKILLed between the
        test's save and its reset, the real file was left at ``120`` and
        cascaded into 29 downstream unit-test failures.

    The fix: copy the real catchment dir into a ``tmp_path_factory`` location
    once, and set ``MKM_CATCHMENT_INPUT_OVERRIDE`` on the subprocess env so
    ``PortfolioPaths._init_paths`` points ``self.input_dir`` at the copy.
    All writes (storm_control.json, classifiers, prs, blotter, eod, etc.)
    land in the tmp copy; the real tree is never touched, even on SIGKILL.

    The fixtures in ``tests/e2e/conftest.py`` that read real port data
    (``gauge_data``, ``property_data``, ``first_traded_gauge_id``, etc.)
    continue to work unchanged because the tmp dir is a full copy.
    """
    real = ROOT / "data" / "input" / "halong"
    real_resolved = os.path.realpath(real)

    tmp_root = None
    tmp_thames = None
    # Fast path: a same-volume APFS copy-on-write clone (metadata-only, ~2s for
    # 2.8 GB, vs a ~30-90s deep copy). Each batch still gets a *fully isolated*
    # copy — writes are copy-on-write and never touch the real tree — so this
    # keeps the isolation the write tests rely on while removing the per-batch
    # copy from the critical path. clonefile requires same-volume placement, so
    # clone under the source volume's mount root (tmp_path_factory is on the
    # internal disk = cross-volume). Falls back to a deep copy if that fails.
    try:
        vol_root = _volume_mount_root(real_resolved)
        _sweep_stale_clones(vol_root)
        clone_root = tempfile.mkdtemp(prefix=".e2e_catch_", dir=vol_root)
        clone_thames = os.path.join(clone_root, "halong")
        subprocess.run(["cp", "-c", "-R", real_resolved, clone_thames],
                       check=True, capture_output=True)
        tmp_root = clone_root
        tmp_thames = Path(clone_thames)
    except Exception:
        if tmp_root:
            shutil.rmtree(tmp_root, ignore_errors=True)
        # Portable fallback: deep copy into tmp_path_factory (non-APFS /
        # cross-volume setups, e.g. CI on a single ext4 disk).
        tmp_root = str(tmp_path_factory.mktemp("e2e_catchment"))
        tmp_thames = Path(tmp_root) / "halong"
        shutil.copytree(real, tmp_thames)

    # Scrub any user override that may live in the real file so the e2e
    # suite starts from Python-source defaults (as the control tests assert).
    ctrl_json = tmp_thames / "storm_control.json"
    if ctrl_json.exists():
        ctrl_json.unlink()
    try:
        yield tmp_thames
    finally:
        shutil.rmtree(tmp_root, ignore_errors=True)


@pytest.fixture(scope="session", autouse=True)
def _e2e_admin_password(tmp_path_factory):
    """Write a known admin credential to a tmp file for E2E tests.

    The Flask subprocess receives ``MKM_ADMIN_FILE_PATH`` pointing at this tmp
    file, so ``_admin_file_path()`` never reads or writes ``data/.port_admin``.
    A crash or SIGKILL leaves the real credential completely untouched because
    the real file is never opened.

    Yields the Path to the tmp credential file so ``server_port`` can pass it
    to the subprocess environment.
    """
    import hashlib
    import json as _json
    import os as _os

    tmp_dir = tmp_path_factory.mktemp("e2e_admin")
    admin_path = tmp_dir / ".port_admin"
    salt = _os.urandom(16).hex()
    h = hashlib.sha256((salt + E2E_ADMIN_PW).encode()).hexdigest()
    admin_path.write_text(_json.dumps({"salt": salt, "hash": h}))
    yield admin_path
    # tmp_path_factory auto-cleans the directory; no restore logic needed.


@pytest.fixture(scope="session", autouse=True)
def _e2e_rbac_user():
    """Provision an RBAC user so write-path tests can authenticate.

    The WP5.1 RBAC cutover retired the ``X-Admin-Password`` header: mutating
    trading/PRS endpoints now ``@require(Func003)`` via an ``/auth/login``
    session. The write tests stub ``window.prompt`` to return ``E2E_ADMIN_PW``
    for both the username and password prompts of ``__mkmLogin``, so create a
    user whose username == password == ``E2E_ADMIN_PW`` and grant it the
    function permissions. The RBAC store is always Postgres, and the Flask
    subprocess inherits this process's environment (``os.environ.copy()`` in
    ``server_port``), so the user created here is visible to the server.
    """
    import database
    from routes.auth import set_password

    database.seed_function_registry()
    if database.get_user(E2E_ADMIN_PW) is None:
        database.create_user(E2E_ADMIN_PW, display_name="e2e")
    set_password(E2E_ADMIN_PW, E2E_ADMIN_PW)
    # Grant every registered function (Func000–Func003); the write endpoints
    # gate on Func003 (FUNC_TRADE_PRS) but granting all keeps the fixture
    # robust to other gated actions the tests may exercise.
    for func in ("Func000", "Func001", "Func002", "Func003"):
        database.set_permission(
            E2E_ADMIN_PW, func,
            read=True, write=True, create=True, delete=True,
        )


# ---------------------------------------------------------------------------
# Session-scoped: one server + one browser for the entire test session
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def server_port(_isolated_catchment_dir, _e2e_admin_password):
    """Start Flask server on a free port; yield the port; kill on teardown.

    Depends on ``_isolated_catchment_dir`` so the tmp copy of
    ``data/input/<catchment>/`` exists before the Flask subprocess imports
    ``config``. The subprocess's ``PortfolioConfig`` sees
    ``MKM_CATCHMENT_INPUT_OVERRIDE`` and points ``self.input_dir`` at the tmp
    copy, so every port-process write (storm_control, classifiers, prs,
    blotter, eod) lands in the tmp dir and the real tree is untouched.

    Depends on ``_e2e_admin_password`` to receive the path to the tmp
    credential file. ``MKM_ADMIN_FILE_PATH`` redirects ``_admin_file_path()``
    in the subprocess so ``data/.port_admin`` is never read or written.
    """
    import os
    port = _free_port()
    # Inherit parent environment so config, data paths, and libraries resolve
    env = os.environ.copy()
    env.update({
        "MKM_SERVER_PORT": str(port),
        "MKM_SERVER_HOST": "127.0.0.1",
        "PYTHONUNBUFFERED": "1",
        # Pin the catchment so the server resolver doesn't fall through to
        # an interactive `input()` prompt (no TTY in the subprocess).
        # MKM_CATCHMENT_INPUT_OVERRIDE points at the tmp dir copied above.
        "MKM_CATCHMENT": "halong",
        "MKM_CATCHMENT_INPUT_OVERRIDE": str(_isolated_catchment_dir),
        "MKM_ADMIN_FILE_PATH": str(_e2e_admin_password),
    })

    # Always delete cached visualization so it regenerates with current
    # BACKEND_CONFIG (url='', relative paths) and current JS source
    # (context-menus.js / backend-handler.js are embedded INLINE in the
    # generated HTML — edits to those source files have no effect until
    # the HTML is rebuilt). Without this, stale HTML may carry both
    # dead-port absolute URLs and out-of-date JS dispatch logic.
    results_dir = ROOT / "data" / "results"
    for cached in results_dir.glob("visualization_*.html"):
        cached.unlink(missing_ok=True)
    interactive = results_dir / "interactive_visualization.html"
    interactive.unlink(missing_ok=True)

    proc = subprocess.Popen(
        [sys.executable, "phys.py", "server"],
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
    # Default for actions/assertions. Kept generous (well above any real
    # click/fill) but not so high that a blocked action — e.g. a modal
    # overlapping the target — hangs for minutes before failing. The genuinely
    # slow operations (page load, preloader, storm sequences) set their own
    # explicit timeouts at the call site, so they are unaffected by this.
    page.set_default_timeout(60_000)
    page.set_default_navigation_timeout(180_000)

    # V8 precise coverage, opt-in via MKM_E2E_JS_COVERAGE=1. Started before the
    # first navigation so module top-level execution counts, not just handlers
    # fired by tests.
    _jscov = _js_coverage.JsCoverageCollector(page)
    if _js_coverage.enabled():
        _jscov.start()

    viz_url = f"{base_url}/visualization"
    page.goto(viz_url, wait_until="networkidle", timeout=180_000)

    # Wait for Leaflet map
    page.wait_for_selector(".leaflet-container", timeout=60_000)

    # Dismiss the licence gate (introduced with license_gate.js). Its overlay
    # (#license-gate-overlay, z-index 10000) covers the whole viewport and
    # intercepts every non-force click; its Accept handler is also what kicks
    # off the startup preloader (_runStartupPreload). Without accepting it here
    # the preloader never runs — so _tdPreloadDone never flips (the wait below
    # would burn its full 120 s) — and the overlay blocks every real click.
    gate = page.locator("#license-gate-overlay")
    if gate.count() > 0:
        gate.locator("button:has-text('Accept')").click(timeout=10_000)
        page.wait_for_selector(
            "#license-gate-overlay", state="detached", timeout=10_000
        )

    # Wait for startup preloader to finish
    try:
        page.wait_for_function(
            "() => window._tdPreloadDone === true",
            timeout=120_000,
        )
    except Exception:
        page.wait_for_timeout(15_000)

    yield page

    # Take coverage before the context closes — the profiler dies with it.
    # Each batch is a separate pytest session, so each write is per-session and
    # tools/coverage/js_coverage_report.py unions them.
    if _js_coverage.enabled():
        try:
            _jscov.write(
                ROOT / "data" / "output" / "audit" / "e2e" / "js_coverage",
                f"session-{os.getpid()}",
            )
        except Exception:
            pass

    context.close()


@pytest.fixture
def map_page(_browser_page):
    """Provide the shared page to each test.

    Closes any open panels between tests to keep state clean.
    """
    page = _browser_page

    # Clean up: close ALL open panels and overlays left by the previous test.
    # This used to inline its own copy of the id list, which drifted from the
    # others; it now shares the one in _helpers.py.
    page.evaluate(CLOSE_PANELS_JS)

    return page


# ---------------------------------------------------------------------------
# Data helpers — load from production data files for assertion values
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def gauge_data():
    """Load gauge.json for test assertions."""
    path = ROOT / "data" / "input" / "halong" / "gauge.json"
    if not path.exists():
        pytest.skip("gauge.json not found — run `python phys.py port` first")
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="session")
def property_data():
    """Load property.json for test assertions."""
    path = ROOT / "data" / "input" / "halong" / "property.json"
    if not path.exists():
        pytest.skip("property.json not found — run `python phys.py port` first")
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
def first_traded_gauge_id(base_url):
    """Return a gauge ID the backend considers to have open trades.

    Sourced from the same ``/trading/blotter/active-gauges`` endpoint that the
    gauge panel's blotter-link enable logic uses, so the "Gauge Blotter" button
    is guaranteed enabled for this gauge. (Previously this scanned PRS files for
    ``Header.TradeStatus != "Closed"`` — a different definition of "traded" than
    the backend's trade-mark logic, which could leave the button disabled for
    the very gauge the test selected.)
    """
    import urllib.request
    try:
        resp = urllib.request.urlopen(
            f"{base_url}/api/v1/trading/blotter/active-gauges", timeout=10
        )
        data = json.loads(resp.read())
        gauge_ids = (
            data.get("gauge_ids", []) if data.get("status") == "success" else []
        )
    except Exception:
        gauge_ids = []
    if not gauge_ids:
        pytest.skip("No active (open-trade) gauges reported by /active-gauges")
    return gauge_ids[0]


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


@pytest.fixture(scope="session")
def first_commercial_peril_id():
    """Return a commercial (CPROP-) asset ID that has BOTH fire and seismic
    peril results AND a commercial hazard curve.

    The PRS pricer's independent-peril (FIRE/SEISMIC) rows are folded into the
    spread decomposition by the commercial hazard route's read-time joins, so
    they only render for assets present in fire.json/seismic.json *and* in
    commercialhc.json. Skips when the active catchment's peril data does not
    intersect its commercial hazard curves (e.g. fire/seismic generated for a
    since-regenerated commercial portfolio) — the rows cannot render there.
    """
    base = ROOT / "data" / "input" / "halong"
    fire_path = base / "fire" / "fire.json"
    seismic_path = base / "seismic" / "seismic.json"
    hc_path = base / "commercialhc.json"
    if not (fire_path.exists() and seismic_path.exists() and hc_path.exists()):
        pytest.skip(
            "fire/seismic/commercialhc not generated for the active catchment"
        )
    with open(fire_path) as f:
        fire_ids = {a.get("asset_id") for a in json.load(f).get("assets", [])}
    with open(seismic_path) as f:
        seis_ids = {a.get("asset_id") for a in json.load(f).get("assets", [])}
    with open(hc_path) as f:
        hc_ids = set(json.load(f).get("property_hazard_curves", {}).keys())
    candidates = sorted((fire_ids & seis_ids & hc_ids) - {None})
    if not candidates:
        pytest.skip(
            "No commercial asset has both peril (fire+seismic) results and a "
            "hazard curve in the active catchment — the independent-peril rows "
            "cannot render (peril data is stale vs the commercial portfolio)"
        )
    return candidates[0]
