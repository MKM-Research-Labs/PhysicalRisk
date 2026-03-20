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
Tests for models.intensity.distribution — IntensityDistribution.

Covers: construction, exceedance probability, inverse exceedance,
sampling, return periods, summary statistics, Pareto vs normal tail,
and serialisation. All branches exercised.
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


# ===========================================================================
# Return period intensities
# ===========================================================================

class TestReturnPeriod:

    @pytest.fixture
    def uncapped(self):
        """Distribution with high max_intensity so long return periods don't hit the cap."""
        return IntensityDistribution(
            base_mean=45, base_std=15, tail_threshold=60,
            tail_index=2.5, min_intensity=10, max_intensity=500,
        )

    def test_100yr_greater_than_10yr(self, uncapped):
        i10 = uncapped.return_period_intensity(10)
        i100 = uncapped.return_period_intensity(100)
        assert i100 > i10

    def test_ordering_10_50_100(self, uncapped):
        i10 = uncapped.return_period_intensity(10)
        i50 = uncapped.return_period_intensity(50)
        i100 = uncapped.return_period_intensity(100)
        assert i10 < i50 < i100

    def test_result_in_bounds(self):
        d = IntensityDistribution()
        for rp in [2, 5, 10]:
            v = d.return_period_intensity(rp)
            assert d.params.min_intensity <= v <= d.params.max_intensity

    def test_storms_per_year_affects_result(self, uncapped):
        few = uncapped.return_period_intensity(20, storms_per_year=5)
        many = uncapped.return_period_intensity(20, storms_per_year=30)
        # More storms/year → same return period needs higher per-storm threshold
        assert many > few


# ===========================================================================
# Summary statistics
# ===========================================================================

class TestSummaryStatistics:

    @pytest.fixture(scope="class")
    def stats(self):
        return IntensityDistribution(seed=42).summary_statistics(5000)

    def test_required_keys_present(self, stats):
        for k in ['mean', 'std', 'min', 'max', 'p10', 'p25', 'p50',
                  'p75', 'p90', 'p95', 'p99', 'prob_exceed_60',
                  'prob_exceed_70', 'prob_exceed_80', 'prob_exceed_90']:
            assert k in stats

    def test_percentiles_ordered(self, stats):
        assert stats['p10'] <= stats['p25'] <= stats['p50'] <= \
               stats['p75'] <= stats['p90'] <= stats['p95'] <= stats['p99']

    def test_mean_in_reasonable_range(self, stats):
        assert 30 < stats['mean'] < 70

    def test_exceedance_probs_decreasing(self, stats):
        assert (stats['prob_exceed_60'] >= stats['prob_exceed_70'] >=
                stats['prob_exceed_80'] >= stats['prob_exceed_90'])

    def test_fat_tail_higher_p99_than_thin(self):
        fat = IntensityDistribution(tail_index=1.5, seed=42).summary_statistics(5000)
        thin = IntensityDistribution(tail_index=5.0, seed=42).summary_statistics(5000)
        assert fat['p99'] > thin['p99']


# ===========================================================================
# Serialisation
# ===========================================================================

class TestSerialisation:

    def test_to_dict_keys(self):
        d = IntensityDistribution()
        result = d.to_dict()
        assert 'parameters' in result
        assert 'tail_probability' in result

    def test_tail_probability_matches_internal(self):
        d = IntensityDistribution()
        assert d.to_dict()['tail_probability'] == pytest.approx(d._tail_prob)

    def test_describe_returns_string(self):
        d = IntensityDistribution(seed=42)
        desc = d.describe()
        assert isinstance(desc, str)
        assert "base_mean" in desc.lower() or "Base mean" in desc

    def test_params_roundtrip(self):
        original = DistributionParameters(base_mean=52, base_std=12, name="custom")
        d = IntensityDistribution(params=original)
        recovered = DistributionParameters.from_dict(d.params.to_dict())
        assert recovered.base_mean == 52
        assert recovered.name == "custom"
