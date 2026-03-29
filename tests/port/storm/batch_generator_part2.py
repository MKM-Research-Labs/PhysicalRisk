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


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def small_batch():
    """Generate 200 sequences (fast, reproducible)."""
    return generate_event_set(count=200, seed=42)


# ---------------------------------------------------------------------------
# Serialization — save_sequences / load_sequences round-trip
# ---------------------------------------------------------------------------

class TestSaveLoadRoundTrip:

    def test_save_creates_file(self, small_batch, tmp_path):
        out = tmp_path / "test_sequences.json"
        save_sequences(small_batch, out)
        assert out.exists()

    def test_load_returns_correct_count(self, small_batch, tmp_path):
        out = tmp_path / "seqs.json"
        save_sequences(small_batch, out)
        loaded = load_sequences(out)
        assert len(loaded) == len(small_batch)

    def test_round_trip_sequence_type(self, small_batch, tmp_path):
        out = tmp_path / "seqs.json"
        save_sequences(small_batch, out)
        loaded = load_sequences(out)
        for orig, back in zip(small_batch, loaded):
            assert orig.sequence_type == back.sequence_type

    def test_round_trip_num_storms(self, small_batch, tmp_path):
        out = tmp_path / "seqs.json"
        save_sequences(small_batch, out)
        loaded = load_sequences(out)
        for orig, back in zip(small_batch, loaded):
            assert orig.num_storms == back.num_storms

    def test_round_trip_total_duration(self, small_batch, tmp_path):
        out = tmp_path / "seqs.json"
        save_sequences(small_batch, out)
        loaded = load_sequences(out)
        for orig, back in zip(small_batch, loaded):
            assert abs(orig.total_duration_hours - back.total_duration_hours) < 0.01

    def test_round_trip_precipitation(self, small_batch, tmp_path):
        out = tmp_path / "seqs.json"
        save_sequences(small_batch, out)
        loaded = load_sequences(out)
        for orig, back in zip(small_batch, loaded):
            assert abs(orig.total_precipitation_mm - back.total_precipitation_mm) < 0.01

    def test_round_trip_storm_fields(self, small_batch, tmp_path):
        out = tmp_path / "seqs.json"
        save_sequences(small_batch, out)
        loaded = load_sequences(out)
        for orig, back in zip(small_batch, loaded):
            for os_, bs_ in zip(orig.storms, back.storms):
                assert os_.storm_index == bs_.storm_index
                assert abs(os_.duration_hours - bs_.duration_hours) < 0.01
                assert abs(os_.intensity_factor - bs_.intensity_factor) < 1e-4

    def test_schema_version_in_file(self, small_batch, tmp_path):
        out = tmp_path / "seqs.json"
        save_sequences(small_batch, out)
        with open(out) as f:
            raw = json.load(f)
        assert raw["schema_version"] == SCHEMA_VERSION

    def test_load_wrong_schema_raises(self, tmp_path):
        bad = tmp_path / "bad.json"
        bad.write_text(json.dumps({
            "schema_version": "1.0-old",
            "sequences": [],
        }))
        with pytest.raises(ValueError, match="schema_version"):
            load_sequences(bad)

    def test_load_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_sequences(tmp_path / "nonexistent.json")

    def test_loaded_sequences_still_valid(self, small_batch, tmp_path):
        out = tmp_path / "seqs.json"
        save_sequences(small_batch, out)
        loaded = load_sequences(out)
        result = validate_event_set(loaded)
        assert result["invalid"] == 0

    def test_creates_parent_dirs(self, small_batch, tmp_path):
        out = tmp_path / "nested" / "deep" / "seqs.json"
        save_sequences(small_batch, out)
        assert out.exists()


# ---------------------------------------------------------------------------
# save_summary
# ---------------------------------------------------------------------------

class TestSaveSummary:

    def test_creates_file(self, small_batch, tmp_path):
        out = tmp_path / "summary.json"
        save_summary(small_batch, out)
        assert out.exists()

    def test_schema_version(self, small_batch, tmp_path):
        out = tmp_path / "summary.json"
        save_summary(small_batch, out)
        with open(out) as f:
            data = json.load(f)
        assert data["schema_version"] == SCHEMA_VERSION

    def test_num_sequences_matches(self, small_batch, tmp_path):
        out = tmp_path / "summary.json"
        save_summary(small_batch, out)
        with open(out) as f:
            data = json.load(f)
        assert data["num_sequences"] == len(small_batch)

    def test_type_counts_sum_to_total(self, small_batch, tmp_path):
        out = tmp_path / "summary.json"
        save_summary(small_batch, out)
        with open(out) as f:
            data = json.load(f)
        assert sum(data["sequence_type_counts"].values()) == len(small_batch)

    def test_type_fractions_sum_to_one(self, small_batch, tmp_path):
        out = tmp_path / "summary.json"
        save_summary(small_batch, out)
        with open(out) as f:
            data = json.load(f)
        total_frac = sum(data["sequence_type_fractions"].values())
        assert abs(total_frac - 1.0) < 0.001

    def test_precipitation_stats_present(self, small_batch, tmp_path):
        out = tmp_path / "summary.json"
        save_summary(small_batch, out)
        with open(out) as f:
            data = json.load(f)
        p = data["precipitation_mm"]
        assert p["min"] > 0
        assert p["max"] >= p["min"]
        assert p["mean"] >= p["min"]

    def test_duration_stats_present(self, small_batch, tmp_path):
        out = tmp_path / "summary.json"
        save_summary(small_batch, out)
        with open(out) as f:
            data = json.load(f)
        d = data["duration_hours"]
        assert d["min"] > 0
        assert d["max"] <= 156  # all durations within precipitation window
        assert d["mean"] >= d["min"]
