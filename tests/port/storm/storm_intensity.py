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

"""Tests for storm intensity sampler (intensity_sampler.py)."""

import numpy as np
import pytest

from port.src.storm_multi.generators.intensity_sampler import (
    DEFAULT_TYPE_WEIGHTS,
    INTENSITY_VARIATION,
    SEQUENCE_PROBABILITY,
    SEQUENCE_TYPE_WEIGHTS,
    get_storm_count,
    sample_sequence_type,
    sample_storm_intensity,
    should_generate_sequence,
)
from port.src.storm_multi.core.data_structures import SequenceType


class TestShouldGenerateSequence:

    def test_catastrophic_high_probability(self):
        """Catastrophic has 85% chance — over many trials, majority should be True."""
        rng = np.random.RandomState(42)
        results = [should_generate_sequence("catastrophic", rng) for _ in range(200)]
        assert sum(results) > 140  # >70%

    def test_minimal_low_probability(self):
        """Minimal has 5% chance — most should be False."""
        rng = np.random.RandomState(42)
        results = [should_generate_sequence("minimal", rng) for _ in range(200)]
        assert sum(results) < 30  # <15%

    def test_unknown_category_defaults_to_015(self):
        """Unknown category uses default 0.15 probability."""
        # With p=0.15, over 1000 trials expect ~150 True
        rng = np.random.RandomState(0)
        results = [should_generate_sequence("unknown_cat", rng) for _ in range(1000)]
        assert 50 < sum(results) < 350  # reasonable range for 15%

    def test_returns_bool(self):
        rng = np.random.RandomState(1)
        result = should_generate_sequence("moderate", rng)
        assert isinstance(result, bool)

    def test_all_defined_categories(self):
        rng = np.random.RandomState(99)
        for cat in SEQUENCE_PROBABILITY:
            result = should_generate_sequence(cat, rng)
            assert isinstance(result, bool)


class TestSampleSequenceType:

    def test_returns_sequence_type(self):
        rng = np.random.RandomState(42)
        result = sample_sequence_type("severe", rng)
        assert isinstance(result, SequenceType)
        assert result in [SequenceType.DOUBLET, SequenceType.CLUSTER, SequenceType.PERSISTENT]

    def test_unknown_category_uses_default_weights(self):
        """Unknown category uses DEFAULT_TYPE_WEIGHTS."""
        rng = np.random.RandomState(42)
        result = sample_sequence_type("unknown_cat", rng)
        assert isinstance(result, SequenceType)

    @pytest.mark.parametrize("cat", list(SEQUENCE_TYPE_WEIGHTS.keys()))
    def test_defined_categories(self, cat):
        rng = np.random.RandomState(7)
        result = sample_sequence_type(cat, rng)
        assert result in [SequenceType.DOUBLET, SequenceType.CLUSTER, SequenceType.PERSISTENT]

    def test_catastrophic_tends_toward_cluster_persistent(self):
        """Catastrophic weights: 15% doublet, 45% cluster, 40% persistent."""
        rng = np.random.RandomState(42)
        results = [sample_sequence_type("catastrophic", rng) for _ in range(500)]
        doublets = sum(1 for r in results if r == SequenceType.DOUBLET)
        assert doublets < 150  # should be ~15%


class TestGetStormCount:

    def test_isolated_returns_1(self):
        rng = np.random.RandomState(42)
        assert get_storm_count(SequenceType.ISOLATED, rng) == 1

    def test_doublet_returns_2(self):
        rng = np.random.RandomState(42)
        assert get_storm_count(SequenceType.DOUBLET, rng) == 2

    def test_cluster_returns_3_or_4(self):
        rng = np.random.RandomState(42)
        for _ in range(50):
            count = get_storm_count(SequenceType.CLUSTER, rng)
            assert count in (3, 4)

    def test_persistent_returns_4_or_5(self):
        rng = np.random.RandomState(42)
        for _ in range(50):
            count = get_storm_count(SequenceType.PERSISTENT, rng)
            assert count in (4, 5)


class TestSampleStormIntensity:

    def test_first_storm_returns_positive(self):
        rng = np.random.RandomState(42)
        result = sample_storm_intensity(1.0, 0, rng)
        assert result > 0

    def test_subsequent_storm_positive(self):
        rng = np.random.RandomState(42)
        result = sample_storm_intensity(1.0, 1, rng)
        assert result > 0

    def test_first_storm_downward_variation(self):
        """Storm index 0 has downward variation (up to -20%)."""
        rng = np.random.RandomState(42)
        base = 1.0
        results = [sample_storm_intensity(base, 0, rng) for _ in range(200)]
        # Should never exceed base by more than small epsilon (first storm only goes down)
        assert all(r <= base + 0.001 for r in results)

    def test_subsequent_storm_mostly_up(self):
        """70% chance of maintaining/increasing subsequent storm intensity."""
        rng = np.random.RandomState(42)
        base = 1.0
        results = [sample_storm_intensity(base, 1, rng) for _ in range(200)]
        above_base = sum(1 for r in results if r >= base)
        assert above_base > 100  # >50%

    def test_very_low_base_clamped_to_01(self):
        """max(0.1, ...) prevents zero or negative intensity."""
        rng = np.random.RandomState(42)
        result = sample_storm_intensity(0.0001, 0, rng)
        assert result >= 0.1

    def test_intensity_within_20_percent_range(self):
        """Result should be within +/-20% of base for first storm."""
        rng = np.random.RandomState(42)
        base = 2.0
        results = [sample_storm_intensity(base, 0, rng) for _ in range(200)]
        lower = base * (1 - INTENSITY_VARIATION)
        upper = base * (1 + INTENSITY_VARIATION)
        assert all(r >= lower - 0.001 for r in results)
        assert all(r <= upper + 0.001 for r in results)

    def test_decreasing_path_subsequent_storm(self):
        """Lines 122-123: 30% chance subsequent storm goes down."""
        rng = np.random.RandomState(42)
        base = 1.0
        results = [sample_storm_intensity(base, 2, rng) for _ in range(200)]
        below_base = sum(1 for r in results if r < base)
        assert below_base > 10  # some should go down
