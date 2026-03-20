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
Tests for sample_multipliers and apply_to_sequence.

Spec validation criteria:
  - Lognormal multipliers: mean(M) == 1 after normalisation
  - Catchment mean preserved after normalisation
  - Higher intensity -> longer effective range
  - Empirical spatial correlation consistent with model for large samples
"""

import numpy as np
import pytest

from port.src.storm_multi.models.sequence_response import _make_precip_series


# ---------------------------------------------------------------------------
# sample_multipliers
# ---------------------------------------------------------------------------

class TestSampleMultipliers:

    def test_shape(self, small_model, rng):
        M = small_model.sample_multipliers(1.0, rng=rng)
        assert M.shape == (small_model.n_gauges,)

    def test_mean_is_one(self, small_model, rng):
        """Normalisation ensures catchment mean is preserved."""
        rng2 = np.random.RandomState(1)
        for _ in range(20):
            M = small_model.sample_multipliers(1.0, rng=rng2)
            assert M.mean() == pytest.approx(1.0, abs=1e-10)

    def test_all_positive(self, small_model, rng):
        rng2 = np.random.RandomState(2)
        for _ in range(20):
            M = small_model.sample_multipliers(1.0, rng=rng2)
            assert np.all(M > 0.0)

    def test_pre_normalisation_lognormal_mean(self, small_model):
        """Pre-normalisation, E[M] = exp(sigma^2/2) / exp(sigma^2/2) = 1 theoretically.
        With our parameterisation: M = exp(sigma*z - sigma^2/2), so E[M] = 1."""
        rng = np.random.RandomState(7)
        L = small_model._get_cholesky(40.0)
        sigma = small_model.params.sigma_lognormal
        pre_norms = []
        for _ in range(500):
            z = L @ rng.randn(small_model.n_gauges)
            M = np.exp(sigma * z - 0.5 * sigma ** 2)
            pre_norms.append(M.mean())
        # Mean of pre-normalised M should be approximately 1.0 (lognormal property)
        assert np.mean(pre_norms) == pytest.approx(1.0, abs=0.05)

    def test_reproducible_with_seed(self, small_model):
        M1 = small_model.sample_multipliers(1.0, rng=np.random.RandomState(0))
        M2 = small_model.sample_multipliers(1.0, rng=np.random.RandomState(0))
        assert np.allclose(M1, M2)

    def test_higher_intensity_lower_variance(self, thames_model):
        """Higher intensity -> longer range -> more spatially coherent (lower variance).

        With longer range, all gauges are more strongly correlated, so the
        per-gauge multipliers vary less around the mean.
        """
        rng1 = np.random.RandomState(10)
        rng2 = np.random.RandomState(10)
        n_samples = 300
        vars_moderate = [thames_model.sample_multipliers(1.0, rng=rng1).var() for _ in range(n_samples)]
        vars_extreme = [thames_model.sample_multipliers(3.0, rng=rng2).var() for _ in range(n_samples)]
        # Extreme should have lower variance (stronger coherence)
        assert np.mean(vars_extreme) < np.mean(vars_moderate)

    def test_empirical_correlation_consistent_with_model(self, small_model):
        """Empirical pairwise correlation approximately matches model correlation for large samples."""
        rng = np.random.RandomState(42)
        n_samples = 2000
        # Sample many multipliers (pre-normalisation, to check raw correlation)
        L = small_model._get_cholesky(40.0)
        sigma = small_model.params.sigma_lognormal
        raw_samples = np.zeros((n_samples, small_model.n_gauges))
        for k in range(n_samples):
            z = L @ rng.randn(small_model.n_gauges)
            raw_samples[k] = np.exp(sigma * z - 0.5 * sigma ** 2)

        # Empirical log-space correlation (lognormal: Cor(X,Y) = model corr)
        log_samples = np.log(raw_samples)
        emp_corr = np.corrcoef(log_samples.T)
        model_corr = small_model.correlation_matrix(40.0)

        # Check a few off-diagonal elements are within 0.15 of model
        for i in range(small_model.n_gauges):
            for j in range(i + 1, small_model.n_gauges):
                assert abs(emp_corr[i, j] - model_corr[i, j]) < 0.15, (
                    f"Empirical corr[{i},{j}]={emp_corr[i,j]:.3f} vs "
                    f"model={model_corr[i,j]:.3f}"
                )


# ---------------------------------------------------------------------------
# apply_to_sequence
# ---------------------------------------------------------------------------

class TestApplyToSequence:

    def test_output_shape(self, thames_model, small_batch):
        seq = small_batch[0]
        precip = _make_precip_series(seq)
        result = thames_model.apply_to_sequence(seq, precip, rng=np.random.RandomState(0))
        assert result.shape == (thames_model.n_gauges, 168)

    def test_zero_precip_hours_remain_zero(self, thames_model, small_batch):
        seq = small_batch[0]
        precip = _make_precip_series(seq)
        result = thames_model.apply_to_sequence(seq, precip, rng=np.random.RandomState(1))
        zero_hours = np.where(precip == 0)[0]
        assert np.all(result[:, zero_hours] == 0.0)

    def test_catchment_mean_preserved_per_hour(self, thames_model, small_batch):
        """For each active hour, mean(gauge_precip) approximately equals catchment_precip."""
        seq = small_batch[0]
        precip = _make_precip_series(seq)
        result = thames_model.apply_to_sequence(seq, precip, rng=np.random.RandomState(2))
        for h in range(168):
            if precip[h] > 0:
                assert result[:, h].mean() == pytest.approx(precip[h], rel=1e-6), (
                    f"Mean not preserved at h={h}"
                )

    def test_all_non_negative(self, thames_model, small_batch):
        seq = small_batch[0]
        precip = _make_precip_series(seq)
        result = thames_model.apply_to_sequence(seq, precip, rng=np.random.RandomState(3))
        assert np.all(result >= 0.0)

    def test_spatial_variation_present(self, thames_model, small_batch):
        """Different gauges get different precipitation amounts."""
        seq = next(s for s in small_batch if s.total_precipitation_mm > 0)
        precip = _make_precip_series(seq)
        result = thames_model.apply_to_sequence(seq, precip, rng=np.random.RandomState(4))
        active_hours = precip > 0
        if active_hours.any():
            # Not all gauges should get identical precipitation
            col = result[:, np.where(active_hours)[0][0]]
            assert col.std() > 0.0

    def test_total_precipitation_conserved(self, thames_model, small_batch):
        """Mean across gauges of total precip approximately equals original catchment total."""
        seq = small_batch[0]
        precip = _make_precip_series(seq)
        result = thames_model.apply_to_sequence(seq, precip, rng=np.random.RandomState(5))
        per_gauge_total = result.sum(axis=1)  # total precip per gauge
        catchment_total = precip.sum()
        assert per_gauge_total.mean() == pytest.approx(catchment_total, rel=1e-6)
