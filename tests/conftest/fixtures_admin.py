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
Admin-credential scaffolding for route unit tests (largely vestigial post-WP5).

The web admin-password gate (``require_admin_password`` / ``X-Admin-Password``) was
retired in WP5.1 — the 16 mutating trading/prs endpoints are now gated by RBAC
capability (``@require("Func003", …)``). Route tests are granted that capability
centrally by ``tests/routes/conftest.py::_grant_test_rbac``, so the scaffolding here
no longer does the gating; it is kept (harmless) to avoid churning the many fixtures
that still reference it:

  1. ``_test_admin_credential`` — session autouse fixture that writes a ``.port_admin``
     file in a pytest tmp dir and points ``_admin_file_path`` at it. Nothing in the web
     path reads it now; retained because trading control fixtures still monkeypatch the
     same locator.
  2. ``AuthenticatedTestClient`` — a ``FlaskClient`` subclass that auto-attaches
     ``X-Admin-Password: TEST_ADMIN_PW``. That header is now ignored by the server; the
     class stays because many trading fixtures set ``app.test_client_class`` to it.
  3. ``TEST_ADMIN_PW`` — the canonical test password constant.

(A future cleanup may delete 1–3 outright once the trading fixtures are simplified.)
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
