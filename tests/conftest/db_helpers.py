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

from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Optional, Union

import database
from database import FileRepository, InMemoryRepository
from database.backend import active_backend, configure_backend


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
    """
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
