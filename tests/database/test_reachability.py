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

"""Service-reachability probes: ``engine.reachable`` and the public wrappers.

The engine is stubbed, so these run with or without a live Postgres and assert
the probe's own logic — that it answers truthfully, never raises, and always
drops the cached engine.
"""

import database
from database import meta
from database._pg import engine as eng


class _FakeConn:
    def __init__(self, log, fail=False):
        self._log, self._fail = log, fail

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self._log.append('closed')
        return False

    def execute(self, statement):
        self._log.append('executed')
        if self._fail:
            raise RuntimeError('connection lost mid-statement')


class _FakeEngine:
    def __init__(self, log, connect_fails=False, execute_fails=False):
        self._log = log
        self._connect_fails = connect_fails
        self._execute_fails = execute_fails

    def connect(self):
        if self._connect_fails:
            raise RuntimeError('could not connect')
        return _FakeConn(self._log, fail=self._execute_fails)


def _stub_engine(monkeypatch, **kw):
    """Point engine.reachable at a fake engine; returns its call log."""
    log = []
    monkeypatch.setattr(eng, 'get_engine', lambda: _FakeEngine(log, **kw))
    monkeypatch.setattr(eng, 'reset_engine', lambda: log.append('reset'))
    return log


def test_reachable_true_when_statement_round_trips(monkeypatch):
    log = _stub_engine(monkeypatch)
    assert eng.reachable() is True
    assert 'executed' in log


def test_reachable_false_when_connect_raises(monkeypatch):
    _stub_engine(monkeypatch, connect_fails=True)
    assert eng.reachable() is False


def test_reachable_false_when_statement_raises(monkeypatch):
    _stub_engine(monkeypatch, execute_fails=True)
    assert eng.reachable() is False


def test_reachable_resets_the_engine_either_side(monkeypatch):
    """A probe against a dead service must not poison the cached singleton for a
    later, live call — so it resets before and after, even on failure."""
    log = _stub_engine(monkeypatch)
    eng.reachable()
    assert log.count('reset') == 2
    assert log[0] == 'reset' and log[-1] == 'reset'

    fail_log = _stub_engine(monkeypatch, connect_fails=True)
    eng.reachable()
    assert fail_log.count('reset') == 2       # still reset despite the failure


def test_reachable_closes_the_connection(monkeypatch):
    log = _stub_engine(monkeypatch)
    eng.reachable()
    assert 'closed' in log


def test_postgres_reachable_delegates_to_the_engine_probe(monkeypatch):
    monkeypatch.setattr(eng, 'reachable', lambda: True)
    assert meta.postgres_reachable() is True
    monkeypatch.setattr(eng, 'reachable', lambda: False)
    assert meta.postgres_reachable() is False


def test_object_store_reachable_delegates_to_the_objectstore_probe(monkeypatch):
    from database._pg import _objectstore as obj

    monkeypatch.setattr(obj, 'reachable', lambda: True)
    assert meta.object_store_reachable() is True
    monkeypatch.setattr(obj, 'reachable', lambda: False)
    assert meta.object_store_reachable() is False


def test_probes_are_exported_on_the_public_api():
    """Callers outside src/database reach these through the package (rule R6)."""
    assert 'postgres_reachable' in database.__all__
    assert 'object_store_reachable' in database.__all__
    assert database.postgres_reachable is meta.postgres_reachable
    assert database.object_store_reachable is meta.object_store_reachable


def test_postgres_reachable_is_not_the_active_backend_ping(monkeypatch):
    """The distinction that motivates it: ``ping`` asks whichever backend is
    bound (file by default), so it cannot answer 'is Postgres up?'."""
    monkeypatch.setattr(eng, 'reachable', lambda: False)
    assert meta.postgres_reachable() is False
    assert meta.postgres_reachable is not meta.ping
