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

"""Coverage expansion tests for spatial_correlation.py — Block B6.

Targets missing lines:
  - 211-217: Cholesky fallback when LinAlgError occurs (jitter added)
  - 251: sample_multipliers without rng (uses np.random.randn)
  - 323-325: from_gauge_portfolio_file class method
"""

from unittest.mock import patch

import numpy as np
import pytest

from port.src.storm_multi.models.spatial_correlation import (
    SpatialCorrelationModel,
    SpatialCorrelationParams,
)

SYNTHETIC_LOCATIONS = [
    (51.45, -0.30),
    (51.46, -0.20),
    (51.47, -0.10),
    (51.48,  0.00),
    (51.49,  0.10),
]


# ---------------------------------------------------------------------------
# Lines 211-217: Cholesky fallback with jitter on LinAlgError
# ---------------------------------------------------------------------------

class TestCholeskyFallback:

    def test_cholesky_fallback_adds_jitter(self):
        """When np.linalg.cholesky raises LinAlgError on first call,
        the model adds jitter and retries successfully."""
        model = SpatialCorrelationModel(SYNTHETIC_LOCATIONS)
        range_km = model.effective_range_km(1.0)

        call_count = [0]
        original_cholesky = np.linalg.cholesky

        def mock_cholesky(C):
            call_count[0] += 1
            if call_count[0] == 1:
                raise np.linalg.LinAlgError("not positive definite")
            return original_cholesky(C)

        # Clear cache so _get_cholesky rebuilds
        model._cholesky_cache.clear()

        with patch("numpy.linalg.cholesky", side_effect=mock_cholesky):
            L = model._get_cholesky(range_km)

        assert L.shape == (model.n_gauges, model.n_gauges)
        assert call_count[0] == 2  # first failed, second succeeded


# ---------------------------------------------------------------------------
# Line 251: sample_multipliers without rng argument
# ---------------------------------------------------------------------------

class TestSampleMultipliersNoRng:

    def test_sample_without_rng(self):
        """When rng is None, falls back to np.random.randn (line 251)."""
        model = SpatialCorrelationModel(SYNTHETIC_LOCATIONS)
        M = model.sample_multipliers(1.0, rng=None)
        assert M.shape == (model.n_gauges,)
        assert M.mean() == pytest.approx(1.0, abs=1e-10)
        assert np.all(M > 0.0)
