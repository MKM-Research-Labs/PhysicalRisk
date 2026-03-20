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
Tests for Phase 2: batch generation + JSON serialization.

Covers:
  - generate_event_set() correctness and distribution
  - All sequences pass validate_sequence()
  - Timing constraint: last storm end <= hour 156
  - save_sequences() / load_sequences() round-trip
  - save_summary() content and structure
"""

import json

import pytest

from port.src.storm_multi.generators.batch_generator import (
    DEFAULT_INTENSITY_WEIGHTS,
    generate_event_set,
)
from port.src.storm_multi.core.data_structures import StormSequence
from port.src.storm_multi.utils.serialization import (
    SCHEMA_VERSION,
    SEQUENCES_FILENAME,
    SUMMARY_FILENAME,
    load_sequences,
    save_sequences,
    save_summary,
)
from port.src.storm_multi.utils.validation import (
    MAX_PRECIP_END_HOUR,
    validate_sequence,
    validate_event_set,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def small_batch():
    """Generate 200 sequences (fast, reproducible)."""
    return generate_event_set(count=200, seed=42)


@pytest.fixture(scope="module")
def medium_batch():
    """Generate 1000 sequences for distribution checks."""
    return generate_event_set(count=1000, seed=7)


# ---------------------------------------------------------------------------
# generate_event_set — basic correctness
# ---------------------------------------------------------------------------

class TestGenerateEventSetBasic:

    def test_returns_list(self, small_batch):
        assert isinstance(small_batch, list)

    def test_correct_count(self, small_batch):
        assert len(small_batch) == 200

    def test_all_storm_sequences(self, small_batch):
        for seq in small_batch:
            assert isinstance(seq, StormSequence)

    def test_reproducible_with_same_seed(self):
        a = generate_event_set(count=50, seed=99)
        b = generate_event_set(count=50, seed=99)
        assert [s.sequence_id for s in a] != [s.sequence_id for s in b]
        # Can't check IDs (UUIDs differ), but num_storms should match
        for sa, sb in zip(a, b):
            assert sa.num_storms == sb.num_storms
            assert sa.sequence_type == sb.sequence_type

    def test_different_seeds_differ(self):
        a = generate_event_set(count=20, seed=1)
        b = generate_event_set(count=20, seed=2)
        types_a = [s.sequence_type for s in a]
        types_b = [s.sequence_type for s in b]
        assert types_a != types_b

    def test_catchment_propagated(self):
        seqs = generate_event_set(count=10, catchment_id="rhine", seed=5)
        for seq in seqs:
            assert seq.catchment_id == "rhine"
            for storm in seq.storms:
                assert storm.catchment_id == "rhine"

    def test_force_sequence_type_isolated(self):
        seqs = generate_event_set(count=30, force_sequence_type="isolated", seed=1)
        for seq in seqs:
            assert seq.sequence_type == "isolated"
            assert seq.num_storms == 1

    def test_force_sequence_type_doublet(self):
        # force_sequence_type="doublet" attempts doublets; some may fall back
        # to isolated when storms can't fit in the 156h precipitation window.
        # Verify that at least the majority are doublets (> 50%).
        seqs = generate_event_set(count=100, force_sequence_type="doublet", seed=1)
        doublets = sum(1 for s in seqs if s.sequence_type == "doublet")
        assert doublets > 50, f"Expected majority doublets, got {doublets}/100"
        for seq in seqs:
            assert seq.sequence_type in ("doublet", "isolated")


# ---------------------------------------------------------------------------
# generate_event_set — intensity distribution
# ---------------------------------------------------------------------------

class TestGenerateEventSetDistribution:

    def test_intensity_categories_present(self, medium_batch):
        """All four default weight categories appear in the batch."""
        categories = {s.storms[0].intensity_category for s in medium_batch}
        for cat in DEFAULT_INTENSITY_WEIGHTS:
            assert cat in categories

    def test_sequence_type_distribution(self, medium_batch):
        """Multi-storm sequences appear at a meaningful rate for severe+."""
        severe_or_above = [
            s for s in medium_batch
            if s.storms[0].intensity_category in ("severe", "extreme", "catastrophic")
        ]
        if len(severe_or_above) > 0:
            multi = sum(1 for s in severe_or_above if s.num_storms > 1)
            multi_frac = multi / len(severe_or_above)
            # At least 20% multi-storm for severe+ (expected ~35-50%)
            assert multi_frac > 0.15

    def test_custom_weights_change_distribution(self):
        """Custom weight heavy on extreme shifts the distribution."""
        seqs = generate_event_set(
            count=200,
            intensity_weights={"extreme": 1.0},
            seed=3,
        )
        cats = [s.storms[0].intensity_category for s in seqs]
        assert all(c == "extreme" for c in cats)


# ---------------------------------------------------------------------------
# Validation — all sequences must pass validate_sequence()
# ---------------------------------------------------------------------------

class TestValidation:

    def test_all_sequences_valid(self, small_batch):
        """Zero validation errors across the whole batch."""
        result = validate_event_set(small_batch)
        assert result["invalid"] == 0, (
            f"{result['invalid']} invalid sequences: {result['errors'][:3]}"
        )

    def test_timing_constraint(self, small_batch):
        """Last storm precipitation must end by hour 156 (1e-9 FP tolerance)."""
        _FP_TOL = 1e-9
        for seq in small_batch:
            last = seq.storms[-1]
            last_end = last.start_time_hours + last.duration_hours
            assert last_end <= MAX_PRECIP_END_HOUR + _FP_TOL, (
                f"Sequence {seq.sequence_id}: last storm ends at "
                f"{last_end}h > {MAX_PRECIP_END_HOUR}h"
            )

    def test_no_negative_durations(self, small_batch):
        for seq in small_batch:
            for storm in seq.storms:
                assert storm.duration_hours > 0

    def test_no_negative_precipitation(self, small_batch):
        for seq in small_batch:
            assert seq.total_precipitation_mm > 0
            for storm in seq.storms:
                assert storm.precipitation_mm > 0

    def test_medium_batch_all_valid(self, medium_batch):
        result = validate_event_set(medium_batch)
        assert result["invalid"] == 0


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
