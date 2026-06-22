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
