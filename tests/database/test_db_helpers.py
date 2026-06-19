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

"""WP2.4 step 2 — self-test for the ``tmp_catchment`` / ``memory_catchment`` helpers."""

import database
from database import FileRepository, InMemoryRepository
from database.backend import active_backend

from db_helpers import tmp_catchment, memory_catchment


def test_tmp_catchment_routes_writes_to_tmp_path_and_sets_catchment(tmp_path):
    with tmp_catchment(tmp_path, catchment="halong") as repo:
        assert isinstance(repo, FileRepository)
        assert database.active_catchment() == "halong"
        database.save_gauges("halong", [{"id": "G1"}])
        # the write landed under the scratch dir (every catchment routes there)
        assert (tmp_path / "gauge.json").exists()
        # and reads back through the seam
        assert database.get_gauge_portfolio("halong") == [{"id": "G1"}]


def test_tmp_catchment_default_catchment_is_thames(tmp_path):
    with tmp_catchment(tmp_path):
        assert database.active_catchment() == "thames"


def test_tmp_catchment_restores_previous_backend(tmp_path):
    before = active_backend()
    with tmp_catchment(tmp_path):
        assert active_backend() is not before
    # the autouse file backend is restored afterwards
    assert active_backend() is before


def test_memory_catchment_keeps_data_in_process(tmp_path):
    with memory_catchment(catchment="mekong") as repo:
        assert isinstance(repo, InMemoryRepository)
        assert database.active_catchment() == "mekong"
        database.save_properties("mekong", [{"id": "P1"}])
        assert database.get_property_portfolio("mekong") == [{"id": "P1"}]
    # nothing written to disk
    assert not any(tmp_path.iterdir())


def test_helpers_nest_and_unwind_to_outer(tmp_path):
    outer = tmp_path / "outer"
    outer.mkdir()
    with tmp_catchment(outer, catchment="halong"):
        assert database.active_catchment() == "halong"
        with memory_catchment(catchment="mekong"):
            assert database.active_catchment() == "mekong"
            assert isinstance(active_backend(), InMemoryRepository)
        # inner unwinds: outer file backend + catchment restored
        assert database.active_catchment() == "halong"
        assert isinstance(active_backend(), FileRepository)
