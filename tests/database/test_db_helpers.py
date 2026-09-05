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

"""WP2.4 step 2 — self-test for the ``tmp_catchment`` / ``memory_catchment`` helpers."""

import pytest

import database
from database import FileRepository, InMemoryRepository
from database.backend import active_backend
from config import config

from db_helpers import tmp_catchment, memory_catchment, active_test_backend

# These self-tests assert the file-backend behaviour of tmp_catchment and the
# write-guard (a FileRepository rooted at the scratch dir, on-disk gauge.json, the
# guard refusing real-data writes). Under MKM_TEST_BACKEND=pg these helpers bind
# Postgres instead (purge + rolled-back transaction, no FileRepository / disk file /
# guard) by design, so they are file-backend-only.
_file_mode_only = pytest.mark.skipif(
    active_test_backend() == "pg",
    reason="validates the file-backend behaviour of tmp_catchment / the write-guard; "
           "under pg the helper binds Postgres instead.")


@_file_mode_only
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


@_file_mode_only
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


@_file_mode_only
def test_write_guard_refuses_real_data_writes():
    """The autouse backend refuses a save that resolves under the real data tree."""
    with pytest.raises(RuntimeError, match="refused"):
        database.save_gauges("thames", [])


@_file_mode_only
def test_write_guard_allows_monkeypatched_tmp_writes(tmp_path, monkeypatch):
    """A save passes through once config paths point at a tmp dir (no tmp_catchment)."""
    monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
    database.save_gauges(config.catchment_id, [{"gauge_id": "GAUGE-1"}])
    assert (tmp_path / "gauge.json").exists()


@_file_mode_only
def test_write_guard_allows_tmp_catchment_writes(tmp_path):
    """tmp_catchment binds a scratch backend, so writes are allowed and isolated."""
    with tmp_catchment(tmp_path):
        database.save_gauges("thames", [{"gauge_id": "GAUGE-2"}])
    assert (tmp_path / "gauge.json").exists()


@_file_mode_only
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
