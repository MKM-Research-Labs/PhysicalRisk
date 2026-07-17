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
Tests for Phase 2: batch generation — correctness, distribution, validation.
"""

import pytest

from port.src.storm_multi.generators.batch_generator import (
    DEFAULT_INTENSITY_WEIGHTS,
    generate_event_set,
)
from port.src.storm_multi.core.data_structures import StormSequence
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
