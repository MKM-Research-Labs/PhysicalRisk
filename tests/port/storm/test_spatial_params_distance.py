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
Tests for spatial correlation parameters, distance matrix, config file,
and gauge portfolio file loading.

Spec validation criteria:
  - Distance matrix: symmetric, diagonal = 0, values plausible for Thames
  - Config file round-trip and constants validation
"""

import json

import numpy as np
import pytest

from port.src.storm_multi.models.spatial_correlation import (
    SpatialCorrelationModel,
    SpatialCorrelationParams,
    save_spatial_correlation_config,
)

from .conftest import SYNTHETIC_LOCATIONS, THAMES_GAUGE_PATH


# ---------------------------------------------------------------------------
# SpatialCorrelationParams
# ---------------------------------------------------------------------------

class TestSpatialCorrelationParams:

    def test_defaults(self):
        p = SpatialCorrelationParams()
        assert p.base_range_km == 40.0
        assert p.nugget == 0.05
        assert p.rho_intensity == 0.40
        assert p.sigma_lognormal == 0.40

    def test_from_dict(self):
        d = {
            "spatial_correlation": {
                "base_range_km": 50.0,
                "nugget": 0.10,
                "rho_intensity": 0.5,
                "sigma_lognormal": 0.3,
            }
        }
        p = SpatialCorrelationParams.from_dict(d)
        assert p.base_range_km == 50.0
        assert p.nugget == 0.10

    def test_load_from_file(self, tmp_path):
        path = tmp_path / "sc.json"
        save_spatial_correlation_config(path)
        p = SpatialCorrelationParams.load(path)
        assert p.base_range_km == 40.0
        assert p.nugget == 0.05


# ---------------------------------------------------------------------------
# Distance matrix
# ---------------------------------------------------------------------------

class TestDistanceMatrix:

    def test_shape(self, small_model):
        D = small_model.dist_matrix
        n = small_model.n_gauges
        assert D.shape == (n, n)

    def test_diagonal_zero(self, small_model):
        D = small_model.dist_matrix
        assert np.allclose(np.diag(D), 0.0)

    def test_symmetric(self, small_model):
        D = small_model.dist_matrix
        assert np.allclose(D, D.T)

    def test_positive_off_diagonal(self, small_model):
        D = small_model.dist_matrix
        n = small_model.n_gauges
        for i in range(n):
            for j in range(n):
                if i != j:
                    assert D[i, j] > 0.0

    def test_thames_max_distance_plausible(self, thames_model):
        """Thames gauges span ~80km corridor (Reading to Purfleet)."""
        max_d = thames_model.dist_matrix.max()
        assert 10.0 < max_d < 120.0, f"Max Thames distance {max_d:.1f}km seems implausible"

    def test_thames_n_gauges(self, thames_model):
        assert thames_model.n_gauges == 52

    def test_haversine_known_distance(self):
        """51.5N 0.0 -> 51.5N 1.0E is approximately 69km."""
        d = SpatialCorrelationModel.haversine_km(51.5, 0.0, 51.5, 1.0)
        assert 65.0 < d < 75.0


# ---------------------------------------------------------------------------
# from_gauge_portfolio_file
# ---------------------------------------------------------------------------

class TestFromGaugePortfolioFile:

    def test_loads_52_gauges(self, thames_model):
        assert thames_model.n_gauges == 52

    def test_distance_matrix_built(self, thames_model):
        assert thames_model.dist_matrix.shape == (52, 52)

    def test_from_dict(self):
        with open(THAMES_GAUGE_PATH) as f:
            portfolio = json.load(f)
        model = SpatialCorrelationModel.from_gauge_portfolio(portfolio)
        # 52 real gauges + synthetic gauges (count varies with property portfolio)
        if model.n_gauges < 52:
            pytest.skip(
                f"Partial on-disk gauge.json ({model.n_gauges} gauges); full "
                f"pipeline not generated. Run `python phys.py port --gauges`."
            )
        assert model.n_gauges >= 52, (
            f"Expected at least 52 gauges, got {model.n_gauges} — "
            "run port --gauges first"
        )


# ---------------------------------------------------------------------------
# Config file
# ---------------------------------------------------------------------------

class TestConfigFile:

    def test_save_creates_file(self, tmp_path):
        path = tmp_path / "sc.json"
        save_spatial_correlation_config(path)
        assert path.exists()

    def test_config_structure(self, tmp_path):
        path = tmp_path / "sc.json"
        save_spatial_correlation_config(path)
        with open(path) as f:
            d = json.load(f)
        sc = d["spatial_correlation"]
        assert isinstance(sc["enabled"], bool)
        assert isinstance(sc["model_type"], str)
        assert sc["base_range_km"] > 0
        assert 0 <= sc["nugget"] <= 1
        assert sc["num_gauges"] > 0

    def test_round_trip_params(self, tmp_path):
        path = tmp_path / "sc.json"
        orig = SpatialCorrelationParams(base_range_km=35.0, nugget=0.08)
        save_spatial_correlation_config(path, params=orig)
        loaded = SpatialCorrelationParams.load(path)
        assert loaded.base_range_km == 35.0
        assert loaded.nugget == 0.08

    def test_config_constants_valid(self):
        """Spatial correlation constants in config.port must be self-consistent.

        Values may be overridden at runtime by storm_control.json, so we
        check types, ranges, and dataclass-to-config consistency rather
        than exact values.
        """
        from config.port import (
            SPATIAL_CORR_BASE_RANGE_KM,
            SPATIAL_CORR_ENABLED,
            SPATIAL_CORR_MODEL_TYPE,
            SPATIAL_CORR_NUGGET,
            SPATIAL_CORR_NUM_GAUGES,
            SPATIAL_CORR_RHO_INTENSITY,
            SPATIAL_CORR_SIGMA_LOGNORMAL,
        )
        assert isinstance(SPATIAL_CORR_ENABLED, bool)
        assert isinstance(SPATIAL_CORR_MODEL_TYPE, str)
        assert SPATIAL_CORR_BASE_RANGE_KM > 0
        assert 0 <= SPATIAL_CORR_NUGGET <= 1
        assert 0 <= SPATIAL_CORR_RHO_INTENSITY <= 1
        assert SPATIAL_CORR_SIGMA_LOGNORMAL > 0
        assert SPATIAL_CORR_NUM_GAUGES > 0
        # Dataclass defaults must be valid (config module attrs may differ
        # at runtime due to storm_control.json overrides)
        p = SpatialCorrelationParams()
        assert p.base_range_km > 0
        assert 0 <= p.nugget <= 1
        assert 0 <= p.rho_intensity <= 1
        assert p.sigma_lognormal > 0
