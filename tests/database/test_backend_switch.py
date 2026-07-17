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

"""WP2.1 read-source switch: use_configured_backend() binds file or pg by flag.

No live database needed — PostgresRepository constructs lazily, so the switch is
testable without Postgres."""

import pytest

from database import FileRepository
from database.backend import active_backend
from database.config_binding import use_configured_backend, use_file_backend


@pytest.fixture(autouse=True)
def _restore_file_backend():
    yield
    use_file_backend()  # never leave a test-bound backend for the next test


def test_default_binds_file_backend(monkeypatch):
    monkeypatch.delenv("MKM_REPO_BACKEND", raising=False)
    repo = use_configured_backend()
    assert isinstance(repo, FileRepository)
    assert active_backend() is repo


def test_pg_flag_binds_postgres_backend(monkeypatch):
    monkeypatch.setenv("MKM_REPO_BACKEND", "pg")
    from database._pg.pg_repo import PostgresRepository

    repo = use_configured_backend()
    assert isinstance(repo, PostgresRepository)
    assert active_backend() is repo


def test_invalid_flag_raises(monkeypatch):
    monkeypatch.setenv("MKM_REPO_BACKEND", "redis")
    with pytest.raises(ValueError):
        use_configured_backend()


def test_backend_configured_reflects_binding():
    from database import InMemoryRepository, backend_configured, configure_backend
    configure_backend(None)
    assert backend_configured() is False
    configure_backend(InMemoryRepository())
    assert backend_configured() is True


def test_port_ensure_backend_only_binds_when_unbound(monkeypatch):
    """WP2.5: the port run binds the configured backend itself, but never clobbers
    a backend a caller (test fixture / web app) already chose."""
    from app.commands.port.orchestrator import _ensure_backend
    from database import InMemoryRepository, backend_configured, configure_backend

    # Already bound → no-op, the caller's backend stays.
    mem = InMemoryRepository()
    configure_backend(mem)
    _ensure_backend()
    assert active_backend() is mem

    # Unbound + default flag → binds the configured (file) backend.
    configure_backend(None)
    monkeypatch.delenv("MKM_REPO_BACKEND", raising=False)
    _ensure_backend()
    assert isinstance(active_backend(), FileRepository)
