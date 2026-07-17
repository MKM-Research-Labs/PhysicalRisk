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
Tests for correlation matrix, Cholesky decomposition, and effective range.

Spec validation criteria:
  - Correlation matrix: positive definite, diagonal = 1, off-diagonal in (0, 1)
  - Cholesky: L @ L.T == C within numerical tolerance
  - Higher intensity -> longer effective range
"""

import numpy as np
import pytest

from port.src.storm_multi.models.spatial_correlation import (
    SpatialCorrelationModel,
    SpatialCorrelationParams,
)

from .conftest import SYNTHETIC_LOCATIONS


# ---------------------------------------------------------------------------
# Correlation matrix
# ---------------------------------------------------------------------------

class TestCorrelationMatrix:

    def test_diagonal_is_one(self, small_model):
        C = small_model.correlation_matrix(40.0)
        assert np.allclose(np.diag(C), 1.0)

    def test_symmetric(self, small_model):
        C = small_model.correlation_matrix(40.0)
        assert np.allclose(C, C.T)

    def test_off_diagonal_in_open_interval(self, small_model):
        C = small_model.correlation_matrix(40.0)
        n = small_model.n_gauges
        for i in range(n):
            for j in range(n):
                if i != j:
                    assert 0.0 < C[i, j] < 1.0

    def test_positive_definite(self, small_model):
        C = small_model.correlation_matrix(40.0)
        eigenvalues = np.linalg.eigvalsh(C)
        assert np.all(eigenvalues > 0), f"Not PD: min eigenvalue = {eigenvalues.min():.6f}"

    def test_thames_positive_definite(self, thames_model):
        C = thames_model.correlation_matrix(40.0)
        eigenvalues = np.linalg.eigvalsh(C)
        assert np.all(eigenvalues > 0)

    def test_longer_range_higher_correlation(self, small_model):
        """Longer range -> higher off-diagonal correlations."""
        C_short = small_model.correlation_matrix(20.0)
        C_long = small_model.correlation_matrix(80.0)
        # Average off-diagonal correlation should be higher for longer range
        n = small_model.n_gauges
        mask = ~np.eye(n, dtype=bool)
        assert C_long[mask].mean() > C_short[mask].mean()

    def test_nugget_reduces_off_diagonal(self):
        """Higher nugget -> lower off-diagonal values."""
        locs = SYNTHETIC_LOCATIONS[:3]
        p_low = SpatialCorrelationParams(nugget=0.01)
        p_high = SpatialCorrelationParams(nugget=0.20)
        m_low = SpatialCorrelationModel(locs, params=p_low)
        m_high = SpatialCorrelationModel(locs, params=p_high)
        C_low = m_low.correlation_matrix(40.0)
        C_high = m_high.correlation_matrix(40.0)
        mask = ~np.eye(3, dtype=bool)
        assert C_high[mask].mean() < C_low[mask].mean()


# ---------------------------------------------------------------------------
# Cholesky decomposition
# ---------------------------------------------------------------------------

class TestCholesky:

    def test_cholesky_reconstruction(self, small_model):
        """L @ L.T == C within numerical tolerance."""
        range_km = 40.0
        C = small_model.correlation_matrix(range_km)
        L = small_model._get_cholesky(range_km)
        assert np.allclose(L @ L.T, C, atol=1e-10)

    def test_cholesky_lower_triangular(self, small_model):
        L = small_model._get_cholesky(40.0)
        assert np.allclose(np.triu(L, k=1), 0.0)

    def test_cholesky_cached(self, small_model):
        """Second call at same range returns cached object."""
        L1 = small_model._get_cholesky(40.0)
        L2 = small_model._get_cholesky(40.0)
        assert L1 is L2

    def test_cholesky_cache_key_rounding(self, small_model):
        """Nearby ranges round to same cache key."""
        L1 = small_model._get_cholesky(40.04)
        L2 = small_model._get_cholesky(40.0)
        assert L1 is L2

    def test_thames_cholesky_reconstruction(self, thames_model):
        C = thames_model.correlation_matrix(40.0)
        L = thames_model._get_cholesky(40.0)
        assert np.allclose(L @ L.T, C, atol=1e-8)


# ---------------------------------------------------------------------------
# Effective range
# ---------------------------------------------------------------------------

class TestEffectiveRange:

    def test_moderate_intensity_equals_base(self, small_model):
        """intensity_factor = 1.0 -> range = base_range."""
        r = small_model.effective_range_km(1.0)
        assert r == pytest.approx(small_model.params.base_range_km)

    def test_higher_intensity_longer_range(self, small_model):
        """Spec requirement: stronger storms -> broader spatial footprint."""
        r_moderate = small_model.effective_range_km(1.0)
        r_severe = small_model.effective_range_km(1.8)
        r_extreme = small_model.effective_range_km(3.0)
        assert r_moderate < r_severe < r_extreme

    def test_range_scales_with_rho(self):
        """range = base * (1 + rho * (factor - 1))."""
        p = SpatialCorrelationParams(base_range_km=40.0, rho_intensity=0.4)
        m = SpatialCorrelationModel(SYNTHETIC_LOCATIONS[:2], params=p)
        # intensity_factor = 2.0: range = 40 * (1 + 0.4 * 1) = 56
        assert m.effective_range_km(2.0) == pytest.approx(56.0)

    def test_minimal_intensity_no_reduction(self, small_model):
        """intensity_factor < 1 still gives at least base range."""
        r = small_model.effective_range_km(0.5)
        assert r == pytest.approx(small_model.params.base_range_km)
