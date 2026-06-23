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

"""WP2.4 step 2 — test helpers for binding a scratch data backend + catchment.

These replace the old ``output_dir=tmp_path`` injection that ~111 test files use. A
writer migrated to WP2.4 no longer takes a directory — it reads/writes through the
``database`` package against ``active_catchment()``. To isolate such a writer, a test
binds a scratch backend and a catchment::

    # before
    PropertyPortfolioGenerator(output_dir=str(tmp_path)).generate()
    assert (tmp_path / "property.json").exists()

    # after
    with tmp_catchment(tmp_path):
        PropertyPortfolioGenerator().generate()
    assert database.get_properties("thames")        # read back through the seam

``tmp_catchment`` routes every catchment to ``tmp_path`` on disk (via the existing
``FileRepository`` dir-resolver seam); ``memory_catchment`` keeps everything in-process
for pure-unit writers that don't care about on-disk layout. Both restore the previously
bound backend on exit, so they nest and never leak into the next test (the autouse
``_database_file_backend`` fixture also re-binds before the next test).
"""

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Optional, Union

import database
from database import FileRepository, InMemoryRepository
from database.backend import active_backend, configure_backend
from database import config_binding
from config import config
from config.data_layout import DEFAULT_MODE


def test_backend() -> str:
    """The backend the suite runs against — ``file`` (default) or ``pg`` (WP4.2).
    Set ``MKM_TEST_BACKEND=pg`` to exercise the whole suite on Postgres."""
    return os.getenv("MKM_TEST_BACKEND", "file").strip().lower()


def pg_function_scope(file_scope: str):
    """A pytest fixture-scope callable: ``file_scope`` normally, ``"function"`` under
    ``MKM_TEST_BACKEND=pg``.

    Use it for an expensive module-/class-scoped fixture that performs database
    writes (e.g. runs a generator). On the file backend the wider scope is kept so
    the work runs once and is shared (fast). Under Postgres the fixture must be
    function-scoped: per-test transaction rollback isolation only binds the pg
    backend inside the function-scoped autouse fixture, so a wider-scoped binding
    would find no backend, escape the per-test rollback, and contend for locks on
    the shared catchment. Every fixture in a dependency chain that reaches such a
    fixture must use this same callable, or pytest raises ``ScopeMismatch``."""
    def _scope(fixture_name, config):
        return "function" if test_backend() == "pg" else file_scope
    return _scope

# The real, on-disk ``data/input`` tree, captured at import time (before any
# per-test monkeypatch of ``config.get_input_dir``). Used by the write-guard to
# tell a genuine real-data write apart from a tmp/monkeypatched one.
_REAL_INPUT_ROOT = (config.get_project_root() / "data" / "input").resolve()


def _is_under_real_data(path: Path) -> bool:
    """True if ``path`` resolves inside the real ``data/input`` tree."""
    try:
        path.resolve().relative_to(_REAL_INPUT_ROOT)
        return True
    except (ValueError, OSError):
        return False


class _WriteGuardedFileRepository(FileRepository):
    """The production-pathed file backend with **writes to real data refused**.

    Reads of the real ``data/input`` tree still work (so read-path tests keep
    passing), but any ``save``/``delete`` whose catchment dir resolves inside the
    real tree raises. A test that needs to write must bind a scratch backend
    (``tmp_catchment`` / ``memory_catchment``) or monkeypatch ``config`` paths to a
    tmp dir first — so a migrated writer can never silently clobber real portfolio
    data on the shared SSD. Writes that resolve to a tmp/monkeypatched dir pass
    straight through.
    """

    def _guard(self, catchment: str, op: str) -> None:
        target = self._catchment_dir(catchment)
        if _is_under_real_data(target):
            raise RuntimeError(
                f"database.{op} refused: it would write real data under "
                f"{target} during a test. Wrap the write in tmp_catchment(tmp_path) "
                f"or memory_catchment(), or monkeypatch config.get_input_dir to a "
                f"tmp dir. (This guard protects the shared data/ SSD.)"
            )

    def save(self, artifact, catchment, payload, key=None, *, mode=DEFAULT_MODE):
        self._guard(catchment, "save")
        return super().save(artifact, catchment, payload, key, mode=mode)

    def delete(self, artifact, catchment, key=None, *, mode=DEFAULT_MODE):
        self._guard(catchment, "delete")
        return super().delete(artifact, catchment, key, mode=mode)


def use_guarded_file_backend() -> _WriteGuardedFileRepository:
    """Bind the write-guarded production file backend (used by the autouse fixture)."""
    repo = _WriteGuardedFileRepository(
        input_root=config_binding._input_root(),
        dir_resolver=config_binding._resolve_catchment_dir,
    )
    configure_backend(repo)
    return repo


# ── Postgres test mode (WP4.2) ───────────────────────────────────────────────
# Under MKM_TEST_BACKEND=pg the autouse fixture binds PostgresRepository inside a
# single transaction and rolls it back on teardown (see engine.bind_test_connection),
# so every test is isolated with zero per-table cleanup. Read-path tests see the
# imported catchments (committed before the run); write-path tests get a clean
# slate via _purge_catchment, which is itself rolled back so the import survives.

@contextmanager
def pg_test_isolation() -> Iterator[None]:
    """Bind PostgresRepository wrapped in a rolled-back transaction for one test."""
    from database._pg.engine import bind_test_connection, get_engine, reset_engine
    from database._pg.pg_repo import PostgresRepository

    reset_engine()
    connection = get_engine().connect()
    transaction = connection.begin()
    bind_test_connection(connection)
    configure_backend(PostgresRepository())
    try:
        yield
    finally:
        bind_test_connection(None)
        transaction.rollback()
        connection.close()
        reset_engine()


def _purge_catchment(catchment: str) -> None:
    """Delete every artifact row for ``catchment`` (within the test transaction, so
    it is rolled back) — gives a write-path test the clean slate ``tmp_path`` used
    to provide, without disturbing the imported data once the test rolls back."""
    from database._pg import get_session
    from database._pg._models import (
        Commercial, CommercialLoan, Counterparty, EodSnapshot, Gauge,
        GaugeHazardCurve, Loan, PortBlob, PortDocument, PortRecord, PortRun,
        Property, PrsTrade,
    )
    models = (Gauge, Property, Loan, Commercial, CommercialLoan, Counterparty,
              GaugeHazardCurve, PrsTrade, EodSnapshot, PortDocument, PortRecord,
              PortBlob, PortRun)
    with get_session() as session:
        for model in models:
            session.query(model).filter_by(catchment_id=catchment).delete()
        session.commit()


def _current_backend() -> Optional[database.Repository]:
    """The bound backend, or ``None`` if startup never configured one."""
    try:
        return active_backend()
    except RuntimeError:
        return None


@contextmanager
def _bound(repo: database.Repository, catchment: str) -> Iterator[database.Repository]:
    """Bind ``repo`` + ``catchment`` for the block, restoring the prior backend after."""
    previous = _current_backend()
    configure_backend(repo)
    try:
        with database.catchment_context(catchment):
            yield repo
    finally:
        configure_backend(previous)


@contextmanager
def tmp_catchment(
    tmp_path: Union[str, Path], catchment: str = "thames"
) -> Iterator[FileRepository]:
    """Bind a file backend rooted at ``tmp_path`` and make ``catchment`` active.

    Every catchment resolves to ``tmp_path`` (a single scratch dir per test), so a
    writer's reads and writes land there and can be read back through ``database``.

    Under ``MKM_TEST_BACKEND=pg`` there is no scratch dir: the autouse fixture has
    already bound Postgres in a rolled-back transaction, so this just clears the
    catchment to a clean slate and makes it active — writes land in Postgres and
    are rolled back with the rest of the test.
    """
    if test_backend() == "pg":
        _purge_catchment(catchment)
        with database.catchment_context(catchment):
            yield active_backend()
        return
    root = Path(tmp_path)
    repo = FileRepository(dir_resolver=lambda _catchment: root)
    with _bound(repo, catchment) as bound:
        yield bound


@contextmanager
def memory_catchment(catchment: str = "thames") -> Iterator[InMemoryRepository]:
    """Bind an in-memory backend and make ``catchment`` active (no disk I/O)."""
    repo = InMemoryRepository()
    with _bound(repo, catchment) as bound:
        yield bound
