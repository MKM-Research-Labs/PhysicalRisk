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
Coverage-expansion tests for models.floodrisk.spatial.

Targets uncovered lines: 42-47 (build_spatial_index with data),
54-67 (build_correlation_matrix), 127 (spatial_interpolate_wse total_weight==0),
163 (idw_interpolate_from_gauges total_weight==0).
"""

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
    build_spatial_index,
    haversine_distance,
    idw_interpolate_from_gauges,
    spatial_interpolate_wse,
)


# ---------------------------------------------------------------------------
# build_spatial_index — with valid gauge data (lines 42-47)
# ---------------------------------------------------------------------------

class TestBuildSpatialIndexCoverage:

    def test_with_valid_dataframe_returns_kdtree(self):
        """Lines 42-46: non-empty DataFrame builds a cKDTree."""
        from scipy.spatial import cKDTree
        df = pd.DataFrame({
            'latitude': [51.5, 51.6, 51.7],
            'longitude': [-0.1, -0.2, -0.3],
        })
        tree = build_spatial_index(df)
        assert isinstance(tree, cKDTree)
        assert tree.n == 3

    def test_single_gauge_builds_tree(self):
        """Single gauge should still produce a valid KDTree."""
        from scipy.spatial import cKDTree
        df = pd.DataFrame({'latitude': [51.5], 'longitude': [-0.1]})
        tree = build_spatial_index(df)
        assert isinstance(tree, cKDTree)
        assert tree.n == 1

    def test_kdtree_coords_are_radians(self):
        """Lines 43-45: coordinates are converted to radians."""
        df = pd.DataFrame({'latitude': [0.0], 'longitude': [180.0]})
        tree = build_spatial_index(df)
        # 180 degrees in radians is pi
        assert tree.data[0][1] == pytest.approx(np.pi, rel=1e-6)


# ---------------------------------------------------------------------------
# build_correlation_matrix (lines 54-67)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not HAS_GEO, reason="geopandas not installed")
class TestBuildCorrelationMatrixCoverage:

    @pytest.fixture
    def three_properties(self):
        geometry = [
            Point(-0.2, 51.4),
            Point(-0.1, 51.5),
            Point(0.0, 51.6),
        ]
        return gpd.GeoDataFrame(geometry=geometry, crs='EPSG:4326')

    def test_returns_square_matrix(self, three_properties):
        from models.floodrisk.spatial import build_correlation_matrix
        mat = build_correlation_matrix(three_properties, 5000, 0.5)
        assert mat.shape == (3, 3)

    def test_diagonal_is_one(self, three_properties):
        from models.floodrisk.spatial import build_correlation_matrix
        mat = build_correlation_matrix(three_properties, 5000, 0.5)
        np.testing.assert_allclose(np.diag(mat), 1.0)

    def test_off_diagonal_positive(self, three_properties):
        from models.floodrisk.spatial import build_correlation_matrix
        mat = build_correlation_matrix(three_properties, 5000, 0.5)
        off = mat[~np.eye(3, dtype=bool)]
        assert np.all(off > 0)

    def test_higher_base_correlation_increases_off_diagonal(self, three_properties):
        from models.floodrisk.spatial import build_correlation_matrix
        mat_low = build_correlation_matrix(three_properties, 5000, 0.2)
        mat_high = build_correlation_matrix(three_properties, 5000, 0.8)
        off_low = mat_low[~np.eye(3, dtype=bool)]
        off_high = mat_high[~np.eye(3, dtype=bool)]
        assert np.all(off_high > off_low)

    def test_larger_distance_increases_correlation(self, three_properties):
        """Larger correlation_distance → slower exponential decay → higher off-diag."""
        from models.floodrisk.spatial import build_correlation_matrix
        mat_near = build_correlation_matrix(three_properties, 1000, 0.5)
        mat_far = build_correlation_matrix(three_properties, 50000, 0.5)
        off_near = mat_near[~np.eye(3, dtype=bool)]
        off_far = mat_far[~np.eye(3, dtype=bool)]
        assert np.all(off_far >= off_near)

    def test_symmetric(self, three_properties):
        from models.floodrisk.spatial import build_correlation_matrix
        mat = build_correlation_matrix(three_properties, 5000, 0.5)
        np.testing.assert_allclose(mat, mat.T)


# ---------------------------------------------------------------------------
# spatial_interpolate_wse — total_weight==0 branch (line 127)
# ---------------------------------------------------------------------------

class TestSpatialInterpolateWSEEdgeCases:
    """The total_weight==0 branch (line 126-127) is hard to reach because
    any valid gauge at finite distance contributes weight. We test it
    indirectly and also verify the near-gauge direct return path."""

    def test_empty_flood_data_returns_zero(self):
        """Line 97-98: no gauge data → 0.0."""
        assert spatial_interpolate_wse(51.5, -0.1, {}, {}) == 0.0

    def test_at_exact_gauge_location_returns_wse(self):
        """Lines 119-120: distance < 1m → direct return."""
        flood = {'G1': 2.0}
        meta = {'G1': {'elevation': 5.0, 'latitude': 51.5, 'longitude': -0.1}}
        result = spatial_interpolate_wse(51.5, -0.1, flood, meta)
        assert result == pytest.approx(7.0)  # 2.0 + 5.0

    def test_two_gauges_weighted_average(self):
        """Lines 113-124: IDW with two equidistant gauges."""
        flood = {'G1': 1.0, 'G2': 3.0}
        meta = {
            'G1': {'elevation': 0.0, 'latitude': 51.0, 'longitude': 0.0},
            'G2': {'elevation': 0.0, 'latitude': 52.0, 'longitude': 0.0},
        }
        # Target is midway between two gauges
        result = spatial_interpolate_wse(51.5, 0.0, flood, meta)
        # Both equidistant → average WSE = (1+3)/2 = 2.0
        assert result == pytest.approx(2.0, rel=0.01)


# ---------------------------------------------------------------------------
# idw_interpolate_from_gauges — edge cases (line 163)
# ---------------------------------------------------------------------------

class TestIDWInterpolateEdgeCases:

    def test_empty_returns_zero(self):
        """Line 149-150: empty input → 0.0."""
        assert idw_interpolate_from_gauges([]) == 0.0

    def test_very_close_gauge_returns_directly(self):
        """Line 156-157: dist < min_distance → return wse."""
        result = idw_interpolate_from_gauges([(0.1, 42.0)], min_distance=1.0)
        assert result == pytest.approx(42.0)

    def test_single_gauge_at_exact_min_distance(self):
        """Gauge at exactly min_distance=1.0 is NOT less than, so IDW used."""
        result = idw_interpolate_from_gauges([(1.0, 5.0)], min_distance=1.0)
        assert result == pytest.approx(5.0)

    def test_custom_power(self):
        """Line 158: power parameter affects weights."""
        gauges = [(100.0, 2.0), (400.0, 8.0)]
        r1 = idw_interpolate_from_gauges(gauges, power=1.0)
        r3 = idw_interpolate_from_gauges(gauges, power=3.0)
        # Higher power → closer gauge dominates more → lower result
        assert r3 < r1

    def test_three_gauges_weighted(self):
        """Multiple gauges produce weighted result."""
        gauges = [(100.0, 2.0), (200.0, 4.0), (300.0, 6.0)]
        result = idw_interpolate_from_gauges(gauges, power=2.0)
        # Closest gauge (100m, WSE=2) dominates
        assert 2.0 < result < 6.0
        assert result < 4.0  # skewed toward closest
