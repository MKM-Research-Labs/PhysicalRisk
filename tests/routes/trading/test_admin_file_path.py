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

"""Locator for the shared admin credential, on the web side.

Covered here because nothing else covers it. ``tests/conftest/fixtures_admin``
replaces ``_admin_file_path`` with a lambda in a *session-scoped autouse*
fixture, so the real body never executes anywhere in the suite — a fixture
that patches out the code it exists to protect. The coverage figure (4 of 8
statements) was reporting that honestly and nobody was reading it.

These tests call the function directly, so the session patch is irrelevant to
them.
"""

import importlib.util

from config import config

_MODULE = "routes.trading._admin_auth"


def _unpatched():
    """The real module function, behind the session-scoped fixture's lambda.

    Loaded as a *separate* module object rather than via
    ``importlib.reload``: reload rebinds the name in ``sys.modules``, which
    would throw away the session fixture's patch and leave every later test
    resolving the real ``data/`` credential. This leaves sys.modules alone.
    Coverage still attributes the executed lines to the file, since it keys
    on filename rather than module identity.
    """
    spec = importlib.util.find_spec(_MODULE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod._admin_file_path


class TestAdminFilePath:
    def test_env_override_wins(self, monkeypatch, tmp_path):
        """The e2e suite redirects the Flask subprocess with this variable."""
        target = tmp_path / "e2e" / ".port_admin"
        monkeypatch.setenv("MKM_ADMIN_FILE_PATH", str(target))
        assert _unpatched()() == target

    def test_falls_back_to_the_config_accessor(self, monkeypatch, tmp_path):
        """Without an override it follows the data root.

        The path comes from ``config.get_admin_credential_path`` rather than a
        literal here, so it moves with ``MKM_DATA_ROOT``.
        """
        monkeypatch.delenv("MKM_ADMIN_FILE_PATH", raising=False)
        monkeypatch.setenv("MKM_DATA_ROOT", str(tmp_path))
        assert _unpatched()() == config.get_admin_credential_path()
        assert _unpatched()() == tmp_path / ".port_admin"

    def test_an_empty_override_is_not_an_override(self, monkeypatch, tmp_path):
        """An unset-but-exported variable must not resolve to a bare Path('')."""
        monkeypatch.setenv("MKM_ADMIN_FILE_PATH", "")
        monkeypatch.setenv("MKM_DATA_ROOT", str(tmp_path))
        assert _unpatched()() == tmp_path / ".port_admin"
