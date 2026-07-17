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

"""Fixtures for the standalone CDM Asset Review tool tests.

The tool ships as two standalone modules (``app.py``, ``cdm_workbook.py``) that
are not importable by package name (``import app`` would collide with the repo's
top-level ``app`` package). We load them by file path under unique module names,
registering each in ``sys.modules`` *before* exec so the Flask app created at
import time resolves its template/static root correctly.

The ``client``/``seed`` fixtures keep everything hermetic: the sandbox and audit
log are redirected under ``tmp_path`` and the module cache is cleared per test,
so no test touches the real ``data/`` tree or the tool's own data dir.
"""

import importlib.util
import json
import sys
from pathlib import Path

import pytest

TOOL_DIR = Path(__file__).resolve().parents[3] / "tools" / "cdm_property_editor"


def _load(modname, filename):
    spec = importlib.util.spec_from_file_location(modname, TOOL_DIR / filename)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[modname] = mod  # set before exec so Flask(__name__) finds __file__
    # app.py imports its siblings by bare name (``import recompute`` /
    # ``import price_new``); put the tool dir on the path only for the exec, then
    # restore it so the tool's ``app.py`` never shadows the repo's ``app`` package
    # for the rest of the suite. The siblings stay cached in sys.modules.
    added = str(TOOL_DIR) not in sys.path
    if added:
        sys.path.insert(0, str(TOOL_DIR))
    try:
        spec.loader.exec_module(mod)
    finally:
        if added:
            sys.path.remove(str(TOOL_DIR))
    return mod


@pytest.fixture(scope="session")
def app_mod():
    return _load("cdm_tool_app", "app.py")


@pytest.fixture(scope="session")
def workbook_mod():
    return _load("cdm_tool_workbook", "cdm_workbook.py")


@pytest.fixture(scope="session")
def recompute_mod():
    return _load("recompute", "recompute.py")


@pytest.fixture(scope="session")
def price_new_mod():
    return _load("price_new", "price_new.py")


@pytest.fixture(scope="session")
def demo_mod():
    return _load("cdm_tool_demo", "cdm_demo.py")


@pytest.fixture(scope="session")
def oracle_mod(recompute_mod):
    # _recompute_oracle imports its sibling ``recompute`` by bare name.
    return _load("cdm_tool_oracle", "_recompute_oracle.py")


@pytest.fixture
def sandbox(app_mod, tmp_path, monkeypatch):
    """Isolate the tool's sandbox (WP3.2): an in-memory seam backs the scratch
    catchment for portfolio/priced writes; the audit log stays JSON under a tmp dir.
    Clears caches and restores the configured backend afterwards."""
    import database
    from database.config_binding import use_configured_backend
    database.configure_backend(database.InMemoryRepository())
    monkeypatch.setattr(app_mod, "SANDBOX_DIR", tmp_path)
    monkeypatch.setattr(app_mod, "AUDIT_FILE", tmp_path / "audit_log.json")
    app_mod._CACHE.clear()
    yield tmp_path
    use_configured_backend()
    app_mod._CACHE.clear()


@pytest.fixture
def seed(sandbox, app_mod):
    """Pre-populate an asset's sandbox via the seam (the scratch catchment). Deep-copies
    so a route mutating the loaded record can't leak back into a shared test fixture."""
    import copy

    def _seed(asset, doc):
        app_mod._save_doc(asset, copy.deepcopy(doc))
    return _seed


@pytest.fixture
def seam(app_mod):
    """Bind an in-memory database backend for the tool's seam reads (WP3.1), seeded
    under the tool's catchment. Yields the ``database`` module so tests can call
    ``save_*(app_mod.CATCHMENT, doc)``; restores the configured backend afterwards."""
    import database
    from database.config_binding import use_configured_backend
    database.configure_backend(database.InMemoryRepository())
    app_mod._CACHE.clear()
    yield database
    use_configured_backend()
    app_mod._CACHE.clear()


@pytest.fixture
def client(app_mod, sandbox):
    app_mod.app.config["TESTING"] = True
    return app_mod.app.test_client()
