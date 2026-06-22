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

"""Live-Postgres smoke tests (WP1) — connectivity + schema round-trip.

These exercise a *real* database (the dev ``docker compose up postgres`` after
``alembic upgrade head``). They SKIP automatically when no Postgres is reachable,
so the normal no-docker suite and CI stay green; run docker locally to exercise
them. All writes roll back, so the database is left untouched.
"""

import pytest
from sqlalchemy import inspect, text

from database._pg import Catchment, get_engine, get_session, reset_engine


def _postgres_available() -> bool:
    try:
        reset_engine()
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
    finally:
        reset_engine()


pytestmark = pytest.mark.skipif(
    not _postgres_available(),
    reason="no live Postgres (run: docker compose -f docker/docker-compose.yml up -d postgres)",
)


def test_expected_tables_exist_in_db():
    names = set(inspect(get_engine()).get_table_names())
    assert {"catchment", "port_run", "gauge"} <= names
    reset_engine()


def test_catchment_roundtrip_then_rollback():
    session = get_session()
    try:
        session.add(Catchment(id="__smoke__", display_name="Smoke", currency="GBP"))
        session.flush()
        got = session.get(Catchment, "__smoke__")
        assert got is not None
        assert got.display_name == "Smoke"
        assert got.currency == "GBP"
    finally:
        session.rollback()  # leave the database exactly as we found it
        session.close()
        reset_engine()
