"""Coverage expansion tests for spatial_correlation.py — Block B6.

Targets missing lines:
  - 211-217: Cholesky fallback when LinAlgError occurs (jitter added)
  - 251: sample_multipliers without rng (uses np.random.randn)
  - 323-325: from_gauge_portfolio_file class method
"""

import json
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


# ---------------------------------------------------------------------------
# Lines 323-325: from_gauge_portfolio_file
# ---------------------------------------------------------------------------

class TestFromGaugePortfolioFile:

    def test_from_gauge_portfolio_file(self, tmp_path):
        """Lines 323-325: construct model from a gauge.json file."""
        portfolio = {
            "flood_gauges": [
                {"FloodGauge": {"Location": {"GaugeLatitude": 51.45, "GaugeLongitude": -0.30}}},
                {"FloodGauge": {"Location": {"GaugeLatitude": 51.46, "GaugeLongitude": -0.20}}},
                {"FloodGauge": {"Location": {"GaugeLatitude": 51.47, "GaugeLongitude": -0.10}}},
            ]
        }
        path = tmp_path / "gauge.json"
        path.write_text(json.dumps(portfolio))

        model = SpatialCorrelationModel.from_gauge_portfolio_file(path)
        assert model.n_gauges == 3
        assert model.dist_matrix.shape == (3, 3)
