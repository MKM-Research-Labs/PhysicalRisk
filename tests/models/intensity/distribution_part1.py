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
Tests for IntensityDistribution — construction, exceedance, Pareto internals,
inverse exceedance, and sampling.
"""

import math

import pytest

from models.intensity.distribution import IntensityDistribution
from models.intensity.parameters import DistributionParameters


# ===========================================================================
# Construction
# ===========================================================================

class TestConstruction:

    def test_default_parameters(self):
        d = IntensityDistribution()
        assert d.params.base_mean == 45.0
        assert d.params.base_std == 15.0
        assert d.params.tail_threshold == 60.0
        assert d.params.tail_index == 2.5
        assert d.params.min_intensity == 10.0
        assert d.params.max_intensity == 100.0

    def test_custom_parameters(self):
        d = IntensityDistribution(base_mean=50, base_std=20, tail_threshold=70,
                                  tail_index=3.0, min_intensity=5, max_intensity=95)
        assert d.params.base_mean == 50
        assert d.params.tail_threshold == 70

    def test_from_params_object(self):
        params = DistributionParameters(base_mean=55, base_std=18)
        d = IntensityDistribution(params=params)
        assert d.params.base_mean == 55

    def test_from_scenario_baseline(self):
        d = IntensityDistribution.from_scenario("baseline")
        assert d is not None
        assert d.params.name == "baseline"

    def test_from_scenario_unknown_raises(self):
        with pytest.raises(ValueError, match="Unknown scenario"):
            IntensityDistribution.from_scenario("nonexistent_xyz")

    def test_seed_gives_deterministic_output(self):
        # Re-seed with the same value and verify the sequence repeats
        import random
        random.seed(42)
        d = IntensityDistribution()
        s1 = d.sample(5)
        random.seed(42)
        s2 = d.sample(5)
        assert s1 == s2

    def test_tail_prob_between_0_and_1(self):
        d = IntensityDistribution()
        assert 0.0 < d._tail_prob < 1.0


# ===========================================================================
# Exceedance probability
# ===========================================================================

class TestExceedanceProbability:

    def test_at_min_intensity_is_one(self):
        d = IntensityDistribution()
        assert d.exceedance_probability(d.params.min_intensity) == 1.0

    def test_below_min_is_one(self):
        d = IntensityDistribution()
        assert d.exceedance_probability(d.params.min_intensity - 5) == 1.0

    def test_at_max_intensity_is_zero(self):
        d = IntensityDistribution()
        assert d.exceedance_probability(d.params.max_intensity) == 0.0

    def test_above_max_is_zero(self):
        d = IntensityDistribution()
        assert d.exceedance_probability(d.params.max_intensity + 10) == 0.0

    def test_below_threshold_uses_normal(self):
        d = IntensityDistribution()
        p = d.exceedance_probability(50.0)
        assert 0 < p < 1

    def test_above_threshold_uses_pareto(self):
        d = IntensityDistribution()
        p = d.exceedance_probability(80.0)
        assert 0 < p < 1

    def test_monotonically_decreasing(self):
        d = IntensityDistribution()
        levels = [15, 30, 50, 65, 80, 95]
        probs = [d.exceedance_probability(x) for x in levels]
        assert all(probs[i] > probs[i + 1] for i in range(len(probs) - 1))

    def test_at_threshold_continuous(self):
        d = IntensityDistribution()
        thresh = d.params.tail_threshold
        p_just_below = d.exceedance_probability(thresh - 0.01)
        p_just_above = d.exceedance_probability(thresh + 0.01)
        assert abs(p_just_below - p_just_above) < 0.05  # smooth transition


# ===========================================================================
# Pareto internals
# ===========================================================================

class TestParetoInternals:

    def test_pareto_at_threshold_is_one(self):
        d = IntensityDistribution()
        assert d._pareto_exceedance(d.params.tail_threshold) == 1.0

    def test_pareto_below_threshold_is_one(self):
        d = IntensityDistribution()
        assert d._pareto_exceedance(d.params.tail_threshold - 5) == 1.0

    def test_pareto_above_threshold_between_0_and_1(self):
        d = IntensityDistribution()
        p = d._pareto_exceedance(d.params.tail_threshold * 2)
        assert 0 < p < 1

    def test_fat_tail_higher_exceedance(self):
        fat = IntensityDistribution(tail_index=1.2)
        thin = IntensityDistribution(tail_index=4.0)
        p_fat = fat.exceedance_probability(85)
        p_thin = thin.exceedance_probability(85)
        assert p_fat > p_thin


# ===========================================================================
# Inverse exceedance / quantile
# ===========================================================================

class TestInverseExceedance:

    def test_zero_prob_returns_max(self):
        d = IntensityDistribution()
        assert d.inverse_exceedance(0) == d.params.max_intensity

    def test_one_prob_returns_min(self):
        d = IntensityDistribution()
        assert d.inverse_exceedance(1) == d.params.min_intensity

    def test_roundtrip_below_threshold(self):
        d = IntensityDistribution()
        for target in [20.0, 35.0, 55.0]:
            p = d.exceedance_probability(target)
            recovered = d.inverse_exceedance(p)
            assert abs(recovered - target) < 2.0, f"Roundtrip failed for {target}"

    def test_roundtrip_above_threshold(self):
        d = IntensityDistribution()
        for target in [70.0, 80.0, 90.0]:
            p = d.exceedance_probability(target)
            recovered = d.inverse_exceedance(p)
            assert abs(recovered - target) < 3.0, f"Roundtrip failed for {target}"

    def test_result_in_bounds(self):
        d = IntensityDistribution()
        for p in [0.01, 0.1, 0.5, 0.9, 0.99]:
            v = d.inverse_exceedance(p)
            assert d.params.min_intensity <= v <= d.params.max_intensity


# ===========================================================================
# Sampling
# ===========================================================================

class TestSampling:

    def test_sample_n_returns_correct_length(self):
        d = IntensityDistribution(seed=1)
        samples = d.sample(100)
        assert len(samples) == 100

    def test_samples_within_bounds(self):
        d = IntensityDistribution(seed=2)
        samples = d.sample(500)
        assert all(d.params.min_intensity <= s <= d.params.max_intensity for s in samples)

    def test_sample_single(self):
        d = IntensityDistribution(seed=3)
        v = d.sample_single()
        assert d.params.min_intensity <= v <= d.params.max_intensity

    def test_seeded_reproducibility(self):
        import random
        random.seed(99)
        d = IntensityDistribution()
        s1 = d.sample(20)
        random.seed(99)
        s2 = d.sample(20)
        assert s1 == s2

    def test_different_seeds_different_output(self):
        d1 = IntensityDistribution(seed=1)
        d2 = IntensityDistribution(seed=2)
        # Very unlikely to be identical
        assert d1.sample(10) != d2.sample(10)
