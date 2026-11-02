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

"""Tests for the Postgres backend engine + models (WP1.1).

These exercise engine/session construction and the ORM metadata WITHOUT a live
database — ``create_engine``/``sessionmaker`` are lazy and do not connect until a
statement runs, so the scaffolding is fully unit-testable. Live round-trips
arrive with PostgresRepository (WP1.6) against the native dev Postgres.
"""

import pytest
from db_helpers import active_test_backend
from sqlalchemy import Engine
from sqlalchemy.orm import Session

from database._pg import Base, Catchment, get_engine, get_session, reset_engine


@pytest.fixture(autouse=True)
def _clean_engine():
    """Drop any cached engine before and after each test for isolation."""
    reset_engine()
    yield
    reset_engine()


def test_get_engine_returns_cached_singleton():
    e1 = get_engine()
    e2 = get_engine()
    assert isinstance(e1, Engine)
    assert e1 is e2


def test_reset_engine_rebuilds():
    e1 = get_engine()
    reset_engine()
    e2 = get_engine()
    assert e1 is not e2


def test_reset_engine_is_safe_when_none():
    # No engine built yet (the autouse fixture just reset); a reset must no-op.
    reset_engine()
    assert isinstance(get_engine(), Engine)


@pytest.mark.skipif(
    active_test_backend() == "pg",
    reason="validates get_session's engine-bound default; under MKM_TEST_BACKEND=pg the "
           "autouse pg-isolation binds a test connection, so get_session binds to that "
           "connection (savepoint) instead of the engine.")
def test_get_session_returns_session():
    session = get_session()
    try:
        assert isinstance(session, Session)
        assert session.bind is get_engine()
    finally:
        session.close()


def test_catchment_model_columns():
    cols = {c.name for c in Catchment.__table__.columns}
    assert cols == {"id", "display_name", "currency"}
    assert Catchment.__table__.c.id.primary_key


def test_catchment_registered_in_metadata():
    assert "catchment" in Base.metadata.tables


# ---------------------------------------------------------------------------
# Test-connection rollback isolation (WP4.1) — live Postgres required
# ---------------------------------------------------------------------------

def _pg_available() -> bool:
    try:
        reset_engine()
        from sqlalchemy import text
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
    finally:
        reset_engine()


@pytest.mark.skipif(
    not _pg_available(),
    reason="no live Postgres (run: scripts/pg-native.sh start)",
)
def test_bound_test_connection_rolls_back_repo_writes():
    """A repo write made while a test connection is bound is visible during the
    transaction but vanishes on rollback — the per-test isolation primitive."""
    from database._pg.engine import bind_test_connection
    from database._pg.pg_repo import PostgresRepository

    reset_engine()
    repo = PostgresRepository()
    catchment = "__enginerbtest__"
    doc = {"flood_gauges": [{"FloodGauge": {"Header": {"GaugeID": "G-RB"}}}],
           "generation_metadata": {}}

    conn = get_engine().connect()
    trans = conn.begin()
    bind_test_connection(conn)
    try:
        repo.save("gauge", catchment, doc)        # repo commits → SAVEPOINT release
        assert repo.exists("gauge", catchment) is True   # visible within the txn
    finally:
        bind_test_connection(None)
        trans.rollback()
        conn.close()

    reset_engine()
    assert PostgresRepository().exists("gauge", catchment) is False  # rolled back, gone


def test_json_round_trips_non_finite_floats():
    """Postgres JSON has no Infinity or NaN; the engine tags them and restores them."""
    import json
    import math

    from database._pg.engine import _json_deserializer, _json_serializer

    doc = {"rp": float("inf"), "low": float("-inf"), "gap": float("nan"),
           "nested": [1.5, {"rp": float("inf")}], "label": "Infinity"}
    text = _json_serializer(doc)
    json.loads(text, parse_constant=lambda c: pytest.fail(f"bare {c} in {text}"))
    back = _json_deserializer(text)
    assert back["rp"] == math.inf and back["low"] == -math.inf
    assert math.isnan(back["gap"])
    assert back["nested"] == [1.5, {"rp": math.inf}]
    assert back["label"] == "Infinity"


def test_json_leaves_finite_values_alone():
    from database._pg.engine import _json_deserializer, _json_serializer

    doc = {"a": 1, "b": [0.5, None, True], "c": "text", "d": (1, 2)}
    assert _json_deserializer(_json_serializer(doc)) == {**doc, "d": [1, 2]}
