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

"""Tests for the Postgres backend engine + models (WP1.1).

These exercise engine/session construction and the ORM metadata WITHOUT a live
database — ``create_engine``/``sessionmaker`` are lazy and do not connect until a
statement runs, so the scaffolding is fully unit-testable. Live round-trips
arrive with PostgresRepository (WP1.6) against the docker Postgres.
"""

import pytest
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
