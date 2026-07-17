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

"""Tests for extended duration sampler."""

import numpy as np
import pytest

from port.src.storm_multi.generators.duration_sampler import (
    DURATION_PARAMS,
    get_duration_range,
    get_max_duration,
    sample_duration,
)


class TestDurationParams:
    """Tests for duration parameter definitions."""

    def test_all_categories_defined(self):
        expected = {"minimal", "baseline", "moderate", "severe", "extreme", "catastrophic"}
        assert set(DURATION_PARAMS.keys()) == expected

    def test_moderate_extended(self):
        low, mode, high = DURATION_PARAMS["moderate"]
        assert low == 12
        assert mode == 30
        assert high == 60

    def test_severe_extended(self):
        assert DURATION_PARAMS["severe"] == (24, 48, 96)

    def test_extreme_extended(self):
        assert DURATION_PARAMS["extreme"] == (36, 72, 144)

    def test_catastrophic_extended(self):
        low, mode, high = DURATION_PARAMS["catastrophic"]
        assert high == 240  # 10 days

    def test_each_tier_doubles_approx(self):
        """Each tier's max roughly doubles the previous."""
        cats = ["minimal", "baseline", "moderate", "severe", "extreme", "catastrophic"]
        maxes = [DURATION_PARAMS[c][2] for c in cats]
        for i in range(1, len(maxes)):
            ratio = maxes[i] / maxes[i - 1]
            assert 1.5 <= ratio <= 3.0, f"{cats[i]}/{cats[i-1]} ratio = {ratio}"


class TestSampleDuration:
    """Tests for duration sampling."""

    @pytest.mark.parametrize("category", DURATION_PARAMS.keys())
    def test_within_bounds(self, category):
        """All sampled durations fall within [min, max] for the category."""
        rng = np.random.RandomState(42)
        low, mode, high = DURATION_PARAMS[category]
        for _ in range(200):
            d = sample_duration(category, rng)
            assert low <= d <= high, f"{category}: {d} not in [{low}, {high}]"

    def test_invalid_category(self):
        with pytest.raises(ValueError, match="Unknown intensity category"):
            sample_duration("nonexistent")

    def test_reproducibility(self):
        rng1 = np.random.RandomState(123)
        rng2 = np.random.RandomState(123)
        d1 = [sample_duration("moderate", rng1) for _ in range(10)]
        d2 = [sample_duration("moderate", rng2) for _ in range(10)]
        assert d1 == d2

    def test_mode_is_most_common(self):
        """Mode should be near the most frequent value in a large sample."""
        rng = np.random.RandomState(42)
        low, mode, high = DURATION_PARAMS["severe"]
        samples = [sample_duration("severe", rng) for _ in range(5000)]
        median = np.median(samples)
        # Median of triangular is near mode (for symmetric-ish distributions)
        assert abs(median - mode) < 15

    def test_no_rng_uses_default(self):
        """Line 50: rng=None → creates np.random.RandomState() internally."""
        low, mode, high = DURATION_PARAMS["moderate"]
        d = sample_duration("moderate")  # no rng passed → hits line 50
        assert low <= d <= high


class TestHelpers:
    """Tests for helper functions."""

    def test_get_max_duration(self):
        assert get_max_duration("catastrophic") == 240
        assert get_max_duration("minimal") == 12

    def test_get_duration_range(self):
        assert get_duration_range("moderate") == (12, 30, 60)
