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

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from config.database import get_database_url

_engine: Engine | None = None
_Session: sessionmaker | None = None


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
    """A new ORM session bound to :func:`get_engine`.

    ``expire_on_commit=False`` lets callers read attributes off returned objects
    after commit without a re-fetch — the repository hands back plain dict/JSON
    payloads, not live ORM rows.
    """
    global _Session
    if _Session is None:
        _Session = sessionmaker(bind=get_engine(), future=True, expire_on_commit=False)
    return _Session()


def reset_engine() -> None:
    """Drop the cached engine + session factory (e.g. when a test repoints the
    database URL). The next :func:`get_engine` rebuilds against the current URL."""
    global _engine, _Session
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _Session = None
