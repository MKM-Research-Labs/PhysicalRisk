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
Tests for IntensityDistribution — return periods, summary statistics,
and serialisation.
"""

import pytest

from models.intensity.distribution import IntensityDistribution
from models.intensity.parameters import DistributionParameters


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
        # More storms/year -> same return period needs higher per-storm threshold
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
