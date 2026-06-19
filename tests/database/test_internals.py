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

"""Edge-case coverage for the internal modules (artifacts, helpers, FileRepository)."""

import pytest

from database import artifacts
from database._helpers import records, matches
from database.file_repo import FileRepository
from database.memory_repo import InMemoryRepository


def test_memory_exists():
    repo = InMemoryRepository()
    assert not repo.exists("gauge", "thames")
    repo.save("gauge", "thames", [])
    assert repo.exists("gauge", "thames")


def test_load_or_propagates_corrupt_json(tmp_path):
    # absence -> default; corruption is NOT swallowed (callers decide tolerance)
    import json
    import database
    p = tmp_path / "thames" / "fire" / "fire.json"
    p.parent.mkdir(parents=True)
    p.write_text("{not valid json")
    database.configure_backend(FileRepository(tmp_path))
    try:
        with pytest.raises(json.JSONDecodeError):
            database.get_fire_results("thames")
    finally:
        database.configure_backend(None)


def test_artifacts_names_includes_core_set():
    names = artifacts.names()
    for expected in ("gauge", "property", "prs_trade", "classifier", "gauge_history"):
        assert expected in names


def test_records_normalisation():
    assert records([1, 2]) == [1, 2]                       # bare list
    assert records({"properties": [{"id": "P1"}]}) == [{"id": "P1"}]  # wrapped
    assert records({"meta": "x"}) == []                    # dict with no list
    assert records(None) == []                             # neither


def test_matches_uses_id_fields():
    assert matches({"swap_id": "PRS-1"}, "PRS-1")
    assert not matches({"swap_id": "PRS-1"}, "PRS-2")
    assert not matches("not-a-dict", "PRS-1")


def test_keyed_artifact_requires_key(tmp_path):
    repo = FileRepository(tmp_path)
    with pytest.raises(ValueError, match="keyed"):
        repo.load("property_timeseries", "thames")          # no key


def test_catchments_empty_when_root_absent(tmp_path):
    repo = FileRepository(tmp_path / "does_not_exist")
    assert repo.catchments() == []


def test_iter_keys_on_empty_dir(tmp_path):
    repo = FileRepository(tmp_path)
    assert list(repo.iter_keys("property_timeseries", "thames")) == []
