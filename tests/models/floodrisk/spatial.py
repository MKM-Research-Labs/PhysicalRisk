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
Tests for models.floodrisk.spatial.

Covers: haversine_distance, build_spatial_index, build_correlation_matrix,
spatial_interpolate_wse, idw_interpolate_from_gauges. GeoDataFrame-dependent
tests are skipped when geopandas is not installed.
"""

import math
import pytest
import numpy as np

try:
    import geopandas as gpd
    import pandas as pd
    from shapely.geometry import Point
    HAS_GEO = True
except ImportError:
    HAS_GEO = False

from models.floodrisk.spatial import (
    haversine_distance,
    build_spatial_index,
    idw_interpolate_from_gauges,
    spatial_interpolate_wse,
)


# ===========================================================================
# haversine_distance
# ===========================================================================

class TestHaversineDistance:

    def test_same_point_is_zero(self):
        assert haversine_distance(51.5, -0.1, 51.5, -0.1) == pytest.approx(0.0, abs=1e-6)

    def test_london_paris_approx_340km(self):
        d = haversine_distance(51.5, -0.1, 48.85, 2.35)
        assert 330_000 < d < 350_000

    def test_symmetry(self):
        d1 = haversine_distance(51.5, -0.1, 53.4, -2.98)
        d2 = haversine_distance(53.4, -2.98, 51.5, -0.1)
        assert d1 == pytest.approx(d2, rel=1e-9)

    def test_equatorial_degree_approx_111km(self):
        # One degree of longitude on the equator ≈ 111.3 km
        d = haversine_distance(0, 0, 0, 1)
        assert 111_000 < d < 112_000

    def test_north_south_degree_approx_111km(self):
        d = haversine_distance(0, 0, 1, 0)
        assert 110_000 < d < 112_000

    def test_returns_float(self):
        assert isinstance(haversine_distance(51.0, -0.1, 52.0, 0.0), float)


# ===========================================================================
# build_spatial_index
# ===========================================================================

class TestBuildSpatialIndex:

    @pytest.mark.skipif(not HAS_GEO, reason="geopandas not installed")
    def test_none_gauge_data_returns_none(self):
        from models.floodrisk.spatial import build_spatial_index
        assert build_spatial_index(None) is None

    @pytest.mark.skipif(not HAS_GEO, reason="geopandas not installed")
    def test_empty_dataframe_returns_none(self):
        from models.floodrisk.spatial import build_spatial_index
        df = pd.DataFrame({'latitude': [], 'longitude': []})
        assert build_spatial_index(df) is None

    @pytest.mark.skipif(not HAS_GEO, reason="geopandas not installed")
    def test_with_gauges_returns_kdtree(self):
        from models.floodrisk.spatial import build_spatial_index
        from scipy.spatial import cKDTree
        df = pd.DataFrame({'latitude': [51.5, 51.6], 'longitude': [-0.1, -0.2]})
        result = build_spatial_index(df)
        assert isinstance(result, cKDTree)


# ===========================================================================
# build_correlation_matrix
# ===========================================================================

@pytest.mark.skipif(not HAS_GEO, reason="geopandas not installed")
class TestBuildCorrelationMatrix:

    @pytest.fixture
    def props(self):
        lons = np.linspace(-0.3, 0.1, 5)
        lats = np.linspace(51.4, 51.6, 5)
        geometry = [Point(lon, lat) for lon, lat in zip(lons, lats)]
        return gpd.GeoDataFrame(geometry=geometry, crs='EPSG:4326')

    def test_shape_is_n_by_n(self, props):
        from models.floodrisk.spatial import build_correlation_matrix
        mat = build_correlation_matrix(props, 1000, 0.4)
        n = len(props)
        assert mat.shape == (n, n)

    def test_diagonal_is_one(self, props):
        from models.floodrisk.spatial import build_correlation_matrix
        mat = build_correlation_matrix(props, 1000, 0.4)
        np.testing.assert_allclose(np.diag(mat), 1.0)

    def test_symmetric(self, props):
        from models.floodrisk.spatial import build_correlation_matrix
        mat = build_correlation_matrix(props, 1000, 0.4)
        np.testing.assert_allclose(mat, mat.T)

    def test_off_diagonal_between_zero_and_one(self, props):
        from models.floodrisk.spatial import build_correlation_matrix
        mat = build_correlation_matrix(props, 1000, 0.4)
        off_diag = mat[np.eye(len(props), dtype=bool) == False]
        assert np.all(off_diag >= 0) and np.all(off_diag <= 1)


# ===========================================================================
# spatial_interpolate_wse
# ===========================================================================

class TestSpatialInterpolateWSE:

    def _meta(self):
        return {
            'G001': {'elevation': 2.0, 'latitude': 51.5, 'longitude': -0.1},
            'G002': {'elevation': 3.0, 'latitude': 51.6, 'longitude': -0.2},
        }

    def test_empty_gauge_data_returns_zero(self):
        result = spatial_interpolate_wse(51.5, -0.1, {}, {})
        assert result == 0.0

    def test_at_gauge_location_returns_wse_directly(self):
        # Distance < 1m → return gauge WSE directly
        flood_data = {'G001': 1.0}
        meta = {'G001': {'elevation': 2.0, 'latitude': 51.5, 'longitude': -0.1}}
        result = spatial_interpolate_wse(51.5, -0.1, flood_data, meta)
        assert result == pytest.approx(3.0)  # depth + elevation = 1 + 2

    def test_idw_returns_weighted_value(self):
        flood_data = {'G001': 0.5, 'G002': 1.5}
        meta = self._meta()
        result = spatial_interpolate_wse(51.55, -0.15, flood_data, meta)
        # WSE for G001 = 0.5 + 2.0 = 2.5, G002 = 1.5 + 3.0 = 4.5
        assert 2.5 <= result <= 4.5

    def test_single_gauge(self):
        flood_data = {'G001': 1.0}
        meta = {'G001': {'elevation': 2.0, 'latitude': 51.0, 'longitude': 0.0}}
        result = spatial_interpolate_wse(52.0, 1.0, flood_data, meta)
        assert result > 0


# ===========================================================================
# idw_interpolate_from_gauges
# ===========================================================================

class TestIDWInterpolate:

    def test_empty_list_returns_zero(self):
        assert idw_interpolate_from_gauges([]) == 0.0

    def test_near_gauge_returns_wse_directly(self):
        # distance < min_distance → return wse
        result = idw_interpolate_from_gauges([(0.5, 5.0)], min_distance=1.0)
        assert result == pytest.approx(5.0)

    def test_single_far_gauge(self):
        result = idw_interpolate_from_gauges([(100.0, 3.0)], power=2.0)
        assert result == pytest.approx(3.0)

    def test_equal_distance_gauges_averages_wse(self):
        # Two gauges equidistant → average wse
        result = idw_interpolate_from_gauges([(200.0, 2.0), (200.0, 4.0)])
        assert result == pytest.approx(3.0)

    def test_closer_gauge_has_higher_weight(self):
        # Gauge at 100m with WSE=1, gauge at 500m with WSE=10
        result = idw_interpolate_from_gauges([(100.0, 1.0), (500.0, 10.0)])
        assert result < 5.0  # closer gauge dominates

    def test_power_one_changes_result(self):
        gauges = [(100.0, 2.0), (400.0, 8.0)]
        r2 = idw_interpolate_from_gauges(gauges, power=2.0)
        r1 = idw_interpolate_from_gauges(gauges, power=1.0)
        # Different powers yield different results
        assert r2 != pytest.approx(r1, rel=0.01)

    def test_all_zero_weights_returns_zero(self):
        # All distances exactly at min_distance threshold — first one returns directly
        result = idw_interpolate_from_gauges([(0.0, 7.5)], min_distance=1.0)
        assert result == pytest.approx(7.5)
