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

"""
Admin-password scaffolding for route unit tests.

The ``@require_admin_password`` decorator now gates every port-process
write (``/trading/market-state``, ``/trading/yield-curve/*``,
``/trading/hazard-term-structure/*``, ``/trading/eod``,
``/trading/close/<swap_id>``, ``/trading/stress/train/<gauge_id>``,
``/trading/classifiers/{train-all,clear-all}``, ``/prs/commit``, plus the
pre-existing ``/trading/control/*``).

Route unit tests call those endpoints via Flask's ``test_client()``. Without
intervention they would all regress with 503 ("Admin password not initialised")
or 401 ("Admin password required"). This module provides:

  1. ``_test_admin_credential`` — session autouse fixture that writes a
     ``.port_admin`` file in a pytest tmp dir and monkeypatches
     ``routes.trading._admin_auth._admin_file_path`` to point at it.
  2. ``AuthenticatedTestClient`` — a ``FlaskClient`` subclass that auto-attaches
     ``X-Admin-Password: TEST_ADMIN_PW`` to every request. This lets the
     existing 30+ route tests that POST to the newly-gated endpoints pass
     unchanged; tests that specifically exercise the gate (missing or wrong
     password) can still override the header.
  3. ``TEST_ADMIN_PW`` — the canonical test password constant, re-exported
     so individual test files can compute the expected hash if they need to
     test misconfigured ``.port_admin`` scenarios.

Tests that opt INTO a different credential path (e.g.
``tests/routes/trading/test_control_routes.py::admin_file``) continue to work
because the per-test fixture's ``monkeypatch.setattr`` takes precedence over
the session-level one.
"""

import hashlib
import json
import os

import pytest
from flask.testing import FlaskClient


TEST_ADMIN_PW = "testpw123"


class AuthenticatedTestClient(FlaskClient):
    """Flask test client that auto-attaches the admin password header.

    Every request defaults to ``X-Admin-Password: TEST_ADMIN_PW``. Tests that
    need to exercise the gate (401/503 paths) can pass ``headers={}`` or
    ``headers={'X-Admin-Password': 'wrong'}`` explicitly — the explicit value
    wins because we use ``setdefault``.
    """

    def open(self, *args, **kwargs):
        headers = kwargs.pop("headers", None)
        if headers is None:
            headers = {}
        if isinstance(headers, dict):
            headers.setdefault("X-Admin-Password", TEST_ADMIN_PW)
        kwargs["headers"] = headers
        return super().open(*args, **kwargs)


@pytest.fixture(scope="session", autouse=True)
def _test_admin_credential(tmp_path_factory):
    """Install a known admin credential for the whole test session.

    Writes ``<tmp>/.port_admin`` with a hash of ``TEST_ADMIN_PW`` and
    monkeypatches ``routes.trading._admin_auth._admin_file_path`` to return
    it. The monkeypatch uses a manual ``setattr``/``delattr`` pair because
    pytest's ``monkeypatch`` fixture is function-scoped and we need session
    scope so this fires once at collection time.
    """
    admin_dir = tmp_path_factory.mktemp("test_admin")
    admin_path = admin_dir / ".port_admin"
    salt = os.urandom(16).hex()
    h = hashlib.sha256((salt + TEST_ADMIN_PW).encode()).hexdigest()
    admin_path.write_text(json.dumps({"salt": salt, "hash": h}))

    import routes.trading._admin_auth as _auth
    original = _auth._admin_file_path
    _auth._admin_file_path = lambda: admin_path
    try:
        yield admin_path
    finally:
        _auth._admin_file_path = original
