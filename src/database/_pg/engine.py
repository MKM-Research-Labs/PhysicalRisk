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

"""SQLAlchemy engine + session factory for the Postgres backend (WP1).

Private to ``src/database``. The connection *values* come from
``config.database`` (rule R1); this module turns them into an engine/session
(the access — rule R6). The engine is a lazily-built, process-wide singleton;
tests that point at a different database call :func:`reset_engine` to drop it.
"""

from sqlalchemy import Connection, Engine, create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from config.database import get_database_url

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
        _engine = create_engine(get_database_url(), future=True, pool_pre_ping=True)
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
