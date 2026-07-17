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

"""
Tests for Phase 2: JSON serialization round-trip and summary.
"""

import json

import pytest

from port.src.storm_multi.generators.batch_generator import generate_event_set
from port.src.storm_multi.utils.serialization import (
    SCHEMA_VERSION,
    SEQUENCES_FILENAME,
    SUMMARY_FILENAME,
    load_sequences,
    save_sequences,
    save_summary,
)
from port.src.storm_multi.utils.validation import validate_event_set

import database
from db_helpers import tmp_catchment


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _iso_catchment(tmp_path):
    """Bind a tmp-rooted backend (catchment "thames"); the migrated serialization
    helpers persist/read storm sequences + summary through database."""
    with tmp_catchment(tmp_path, catchment="thames"):
        yield


@pytest.fixture(scope="module")
def small_batch():
    """Generate 200 sequences (fast, reproducible)."""
    return generate_event_set(count=200, seed=42)


# ---------------------------------------------------------------------------
# Serialization — save_sequences / load_sequences round-trip
# ---------------------------------------------------------------------------

class TestSaveLoadRoundTrip:

    def test_save_creates_file(self, small_batch, tmp_path):
        save_sequences(small_batch)
        assert database.get_storm_sequences("thames") is not None

    def test_load_returns_correct_count(self, small_batch, tmp_path):
        out = tmp_path / "seqs.json"
        save_sequences(small_batch)
        loaded = load_sequences()
        assert len(loaded) == len(small_batch)

    def test_round_trip_sequence_type(self, small_batch, tmp_path):
        out = tmp_path / "seqs.json"
        save_sequences(small_batch)
        loaded = load_sequences()
        for orig, back in zip(small_batch, loaded):
            assert orig.sequence_type == back.sequence_type

    def test_round_trip_num_storms(self, small_batch, tmp_path):
        out = tmp_path / "seqs.json"
        save_sequences(small_batch)
        loaded = load_sequences()
        for orig, back in zip(small_batch, loaded):
            assert orig.num_storms == back.num_storms

    def test_round_trip_total_duration(self, small_batch, tmp_path):
        out = tmp_path / "seqs.json"
        save_sequences(small_batch)
        loaded = load_sequences()
        for orig, back in zip(small_batch, loaded):
            assert abs(orig.total_duration_hours - back.total_duration_hours) < 0.01

    def test_round_trip_precipitation(self, small_batch, tmp_path):
        out = tmp_path / "seqs.json"
        save_sequences(small_batch)
        loaded = load_sequences()
        for orig, back in zip(small_batch, loaded):
            assert abs(orig.total_precipitation_mm - back.total_precipitation_mm) < 0.01

    def test_round_trip_storm_fields(self, small_batch, tmp_path):
        out = tmp_path / "seqs.json"
        save_sequences(small_batch)
        loaded = load_sequences()
        for orig, back in zip(small_batch, loaded):
            for os_, bs_ in zip(orig.storms, back.storms):
                assert os_.storm_index == bs_.storm_index
                assert abs(os_.duration_hours - bs_.duration_hours) < 0.01
                assert abs(os_.intensity_factor - bs_.intensity_factor) < 1e-4

    def test_schema_version_in_file(self, small_batch, tmp_path):
        out = tmp_path / "seqs.json"
        save_sequences(small_batch)
        raw = database.get_storm_sequences("thames")
        assert raw["schema_version"] == SCHEMA_VERSION

    def test_load_wrong_schema_raises(self, tmp_path):
        database.save_storm_sequences("thames", {
            "schema_version": "1.0-old",
            "sequences": [],
        })
        with pytest.raises(ValueError, match="schema_version"):
            load_sequences()

    def test_load_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_sequences()

    def test_loaded_sequences_still_valid(self, small_batch, tmp_path):
        out = tmp_path / "seqs.json"
        save_sequences(small_batch)
        loaded = load_sequences()
        result = validate_event_set(loaded)
        assert result["invalid"] == 0

    def test_creates_parent_dirs(self, small_batch, tmp_path):
        save_sequences(small_batch)
        assert database.get_storm_sequences("thames") is not None


# ---------------------------------------------------------------------------
# save_summary
# ---------------------------------------------------------------------------

class TestSaveSummary:

    def test_creates_file(self, small_batch, tmp_path):
        save_summary(small_batch)
        assert database.get_sequence_summary("thames") is not None

    def test_schema_version(self, small_batch, tmp_path):
        out = tmp_path / "summary.json"
        save_summary(small_batch)
        data = database.get_sequence_summary("thames")
        assert data["schema_version"] == SCHEMA_VERSION

    def test_num_sequences_matches(self, small_batch, tmp_path):
        out = tmp_path / "summary.json"
        save_summary(small_batch)
        data = database.get_sequence_summary("thames")
        assert data["num_sequences"] == len(small_batch)

    def test_type_counts_sum_to_total(self, small_batch, tmp_path):
        out = tmp_path / "summary.json"
        save_summary(small_batch)
        data = database.get_sequence_summary("thames")
        assert sum(data["sequence_type_counts"].values()) == len(small_batch)

    def test_type_fractions_sum_to_one(self, small_batch, tmp_path):
        out = tmp_path / "summary.json"
        save_summary(small_batch)
        data = database.get_sequence_summary("thames")
        total_frac = sum(data["sequence_type_fractions"].values())
        assert abs(total_frac - 1.0) < 0.001

    def test_precipitation_stats_present(self, small_batch, tmp_path):
        out = tmp_path / "summary.json"
        save_summary(small_batch)
        data = database.get_sequence_summary("thames")
        p = data["precipitation_mm"]
        assert p["min"] > 0
        assert p["max"] >= p["min"]
        assert p["mean"] >= p["min"]

    def test_duration_stats_present(self, small_batch, tmp_path):
        out = tmp_path / "summary.json"
        save_summary(small_batch)
        data = database.get_sequence_summary("thames")
        d = data["duration_hours"]
        assert d["min"] > 0
        assert d["max"] <= 156  # all durations within precipitation window
        assert d["mean"] >= d["min"]
