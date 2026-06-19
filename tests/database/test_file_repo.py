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

"""Characterization tests for the FileRepository backend — it must reproduce the
existing on-disk JSON layout exactly, and the seam must behave identically across
backends (proving a DB swap changes nothing observable)."""

import json

import pytest

from database.file_repo import FileRepository
from database.memory_repo import InMemoryRepository


def test_document_round_trip_and_layout(tmp_path):
    repo = FileRepository(tmp_path)
    repo.save("gauge", "thames", [{"id": "GAUGE-1"}, {"id": "GAUGE-2"}])
    # lands at the exact historical path
    assert (tmp_path / "thames" / "gauge.json").exists()
    assert repo.load("gauge", "thames") == [{"id": "GAUGE-1"}, {"id": "GAUGE-2"}]


def test_nested_document_path(tmp_path):
    repo = FileRepository(tmp_path)
    repo.save("market_state", "thames", {"bid": 1})
    repo.save("fire_results", "thames", {"assets": []})
    assert (tmp_path / "thames" / "blotter" / "market_state.json").exists()
    assert (tmp_path / "thames" / "fire" / "fire.json").exists()


def test_keyed_round_trip_and_iter(tmp_path):
    repo = FileRepository(tmp_path)
    repo.save("property_timeseries", "thames", {"v": 1}, "PROP-1")
    repo.save("property_timeseries", "thames", {"v": 2}, "PROP-2")
    assert (tmp_path / "thames" / "propertyts" / "PROP-1.json").exists()
    assert sorted(repo.iter_keys("property_timeseries", "thames")) == ["PROP-1", "PROP-2"]
    assert repo.load("property_timeseries", "thames", "PROP-2") == {"v": 2}


def test_mode_routes_to_distinct_directories(tmp_path):
    repo = FileRepository(tmp_path)
    repo.save("property_timeseries", "thames", {"m": "flood"}, "PROP-1")
    repo.save("property_timeseries", "thames", {"m": "she"}, "PROP-1", mode="she")
    assert (tmp_path / "thames" / "propertyts" / "PROP-1.json").exists()
    assert (tmp_path / "thames" / "propertytse" / "PROP-1.json").exists()
    assert repo.load("property_timeseries", "thames", "PROP-1") == {"m": "flood"}
    assert repo.load("property_timeseries", "thames", "PROP-1", mode="she") == {"m": "she"}


def test_gauge_history_special_filename(tmp_path):
    repo = FileRepository(tmp_path)
    repo.save("gauge_history", "thames", {"h": 1}, "GAUGE-1")
    # historical naming: gauge_<id>_hd.json
    assert (tmp_path / "thames" / "gaugehd" / "gauge_GAUGE-1_hd.json").exists()
    assert list(repo.iter_keys("gauge_history", "thames")) == ["GAUGE-1"]
    assert repo.load("gauge_history", "thames", "GAUGE-1") == {"h": 1}


def test_iter_keys_skips_index_file(tmp_path):
    repo = FileRepository(tmp_path)
    repo.save("stress_storm", "thames", {"s": 1}, "STORM-A")
    repo.save("stress_storm_index", "thames", {"storms": ["STORM-A"]})  # stress_storms/_index.json
    assert (tmp_path / "thames" / "stress_storms" / "_index.json").exists()
    assert list(repo.iter_keys("stress_storm", "thames")) == ["STORM-A"]


def test_blob_classifier(tmp_path):
    repo = FileRepository(tmp_path)
    repo.save("classifier", "thames", b"MODELBYTES", "GAUGE-1")
    assert (tmp_path / "thames" / "classifiers" / "GAUGE-1.joblib").exists()
    assert repo.load("classifier", "thames", "GAUGE-1") == b"MODELBYTES"
    assert list(repo.iter_keys("classifier", "thames")) == ["GAUGE-1"]


def test_delete_and_exists(tmp_path):
    repo = FileRepository(tmp_path)
    repo.save("prs_trade", "thames", {"swap_id": "PRS-1"}, "PRS-1")
    assert repo.exists("prs_trade", "thames", "PRS-1")
    repo.delete("prs_trade", "thames", "PRS-1")
    assert not repo.exists("prs_trade", "thames", "PRS-1")
    repo.delete("prs_trade", "thames", "PRS-1")  # idempotent


def test_catchments_listing(tmp_path):
    repo = FileRepository(tmp_path)
    repo.save("gauge", "thames", [])
    repo.save("gauge", "halong", [])
    assert repo.catchments() == ["halong", "thames"]


def test_unknown_artifact_is_explicit(tmp_path):
    repo = FileRepository(tmp_path)
    with pytest.raises(KeyError, match="Unknown artifact"):
        repo.load("nonsense", "thames")


def test_backend_parity_file_vs_memory(tmp_path):
    """Same operations on both backends => identical observable state. This is the
    proof that swapping files -> DB changes nothing for callers."""
    def exercise(repo):
        repo.save("gauge", "thames", [{"id": "G1"}])
        repo.save("property_timeseries", "thames", {"v": 1}, "P1")
        repo.save("property_timeseries", "thames", {"v": 9}, "P1", mode="bri")
        return {
            "gauges": repo.load("gauge", "thames"),
            "ts_keys": sorted(repo.iter_keys("property_timeseries", "thames")),
            "ts_flood": repo.load("property_timeseries", "thames", "P1"),
            "ts_bri": repo.load("property_timeseries", "thames", "P1", mode="bri"),
            "catchments": repo.catchments(),
        }

    assert exercise(FileRepository(tmp_path)) == exercise(InMemoryRepository())
