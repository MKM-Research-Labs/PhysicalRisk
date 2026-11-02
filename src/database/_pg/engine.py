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

"""SQLAlchemy engine + session factory for the Postgres backend (WP1).

Private to ``src/database``. The connection *values* come from
``config.database`` (rule R1); this module turns them into an engine/session
(the access — rule R6). The engine is a lazily-built, process-wide singleton;
tests that point at a different database call :func:`reset_engine` to drop it.
"""

import json
import math

from sqlalchemy import Connection, Engine, create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from config.database import get_database_url

# Postgres JSON has no Infinity or NaN, but the models emit them (a return period
# for a gauge that never floods is infinite) and the file backend stores them as
# bare tokens. Store them as these tagged strings and turn them back on read, so
# both backends return the same values.
_NON_FINITE = {"inf": "__mkm_float__:Infinity", "-inf": "__mkm_float__:-Infinity",
               "nan": "__mkm_float__:NaN"}
_FROM_TAG = {tag: float(name) for name, tag in _NON_FINITE.items()}


def _tag_non_finite(value):
    if isinstance(value, float) and not math.isfinite(value):
        return _NON_FINITE[repr(value)]
    if isinstance(value, dict):
        return {k: _tag_non_finite(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_tag_non_finite(v) for v in value]
    return value


def _untag_non_finite(value):
    if isinstance(value, str):
        return _FROM_TAG.get(value, value)
    if isinstance(value, dict):
        return {k: _untag_non_finite(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_untag_non_finite(v) for v in value]
    return value


def _json_serializer(value) -> str:
    return json.dumps(_tag_non_finite(value), allow_nan=False)


def _json_deserializer(text_value: str):
    return _untag_non_finite(json.loads(text_value))


_engine: Engine | None = None
_Session: sessionmaker | None = None
# When set (by a test), every session binds to this external connection instead
# of the engine — so a test can wrap all its writes in one outer transaction and
# roll it back for per-test isolation (WP4.1). None in normal operation.
_test_connection: Connection | None = None


def get_engine() -> Engine:
    """The process-wide SQLAlchemy engine, built on first use.

    ``pool_pre_ping`` recovers from dropped connections (the dev container can be
    restarted under the app); ``future=True`` selects 2.0 semantics.
    """
    global _engine
    if _engine is None:
        _engine = create_engine(get_database_url(), future=True, pool_pre_ping=True,
                                json_serializer=_json_serializer,
                                json_deserializer=_json_deserializer)
    return _engine


def get_session() -> Session:
    """A new ORM session.

    Normally bound to :func:`get_engine`. Under a bound test connection (see
    :func:`bind_test_connection`) it instead joins that connection's transaction
    via a SAVEPOINT, so the repository's explicit ``commit`` releases the savepoint
    but the outer transaction (rolled back on teardown) still owns every write.
    ``expire_on_commit=False`` lets callers read attributes off returned objects
    after commit — the repository hands back plain dict/JSON payloads.
    """
    if _test_connection is not None:
        return Session(bind=_test_connection, future=True, expire_on_commit=False,
                       join_transaction_mode="create_savepoint")
    global _Session
    if _Session is None:
        _Session = sessionmaker(bind=get_engine(), future=True, expire_on_commit=False)
    return _Session()


def bind_test_connection(connection: Connection | None) -> None:
    """Route every session through ``connection`` (a test's transaction) for
    rollback-based isolation, or pass ``None`` to restore engine-bound sessions."""
    global _test_connection
    _test_connection = connection


def reset_engine() -> None:
    """Drop the cached engine + session factory (e.g. when a test repoints the
    database URL). The next :func:`get_engine` rebuilds against the current URL."""
    global _engine, _Session
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _Session = None


def reachable() -> bool:
    """True if Postgres answers a trivial statement — the health check callers
    outside the seam gate on (mirrors ``_objectstore.reachable``).

    Unlike ``database.ping``, this asks Postgres specifically rather than the
    *active* backend, so it answers "is the service up?" even while the file
    backend is bound. Drops the cached engine either side so a probe against a
    dead service cannot poison the singleton for a later, live call.
    """
    try:
        reset_engine()
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
    finally:
        reset_engine()
