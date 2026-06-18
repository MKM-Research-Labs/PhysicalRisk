# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial 
# research and educational use only. Any commercial use, including 
# but not limited to use in or for products or services offered for sale, 
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

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
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="session")
def app_mod():
    return _load("cdm_tool_app", "app.py")


@pytest.fixture(scope="session")
def workbook_mod():
    return _load("cdm_tool_workbook", "cdm_workbook.py")


@pytest.fixture
def sandbox(app_mod, tmp_path, monkeypatch):
    """Redirect the tool's sandbox + audit file under tmp_path; clear caches."""
    monkeypatch.setattr(app_mod, "SANDBOX_DIR", tmp_path)
    monkeypatch.setattr(app_mod, "AUDIT_FILE", tmp_path / "audit_log.json")
    app_mod._CACHE.clear()
    return tmp_path


@pytest.fixture
def seed(sandbox):
    """Return a helper that writes a sandbox JSON document for an asset."""
    def _seed(asset, doc):
        (sandbox / f"{asset}_sandbox.json").write_text(
            json.dumps(doc), encoding="utf-8")
    return _seed


@pytest.fixture
def client(app_mod, sandbox):
    app_mod.app.config["TESTING"] = True
    return app_mod.app.test_client()
