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
Tests for models.floodrisk.depth_damage.

Covers: scalar_depth_damage (all branches), depth_damage_function
(property-type adjustments, floor levels), and calculate_flood_depths.
GeoDataFrame-dependent tests are skipped when geopandas is not installed.
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

from models.floodrisk.depth_damage import (
    DAMAGE_POINTS,
    DEPTH_POINTS,
    scalar_depth_damage,
)


# ===========================================================================
# scalar_depth_damage
# ===========================================================================

class TestScalarDepthDamage:

    def test_zero_depth_returns_zero(self):
        assert scalar_depth_damage(0.0) == 0.0

    def test_negative_depth_returns_zero(self):
        assert scalar_depth_damage(-1.0) == 0.0
        assert scalar_depth_damage(-100.0) == 0.0

    def test_max_depth_returns_one(self):
        assert scalar_depth_damage(DEPTH_POINTS[-1]) == pytest.approx(1.0)

    def test_above_max_depth_returns_one(self):
        assert scalar_depth_damage(100.0) == pytest.approx(1.0)

    def test_small_depth_returns_small_damage(self):
        d = scalar_depth_damage(0.05)
        assert d == pytest.approx(DAMAGE_POINTS[1], abs=1e-9)

    def test_half_meter_damage(self):
        # 0.5m is a control point
        d = scalar_depth_damage(0.5)
        assert d == pytest.approx(DAMAGE_POINTS[2], abs=1e-6)

    def test_one_meter_damage(self):
        d = scalar_depth_damage(1.0)
        assert d == pytest.approx(DAMAGE_POINTS[3], abs=1e-6)

    def test_monotonically_increasing(self):
        depths = [0.01, 0.1, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 5.0]
        damages = [scalar_depth_damage(d) for d in depths]
        assert all(damages[i] <= damages[i + 1] for i in range(len(damages) - 1))

    def test_returns_float(self):
        assert isinstance(scalar_depth_damage(0.75), float)

    def test_between_control_points_interpolated(self):
        # Between 0.5m (0.25) and 1.0m (0.40): midpoint should be ~0.325
        d = scalar_depth_damage(0.75)
        assert 0.25 < d < 0.40

    def test_damage_between_0_and_1(self):
        for depth in [0.01, 0.25, 0.5, 1.0, 2.5, 4.9]:
            assert 0 <= scalar_depth_damage(depth) <= 1.0


# ===========================================================================
# depth_damage_function  (requires geopandas)
# ===========================================================================

@pytest.mark.skipif(not HAS_GEO, reason="geopandas not installed")
class TestDepthDamageFunction:

    @pytest.fixture
    def properties(self):
        n = 6
        lons = np.linspace(-0.3, 0.1, n)
        lats = np.linspace(51.4, 51.6, n)
        geometry = [Point(lon, lat) for lon, lat in zip(lons, lats)]
        return gpd.GeoDataFrame(
            {
                'property_id': [f'PROP-{i:03d}' for i in range(n)],
                'value': [300_000] * n,
                'property_type': ['residential', 'commercial', 'industrial',
                                  'residential', 'commercial', 'industrial'],
                'floor_level_metres': [0.0, 0.0, 0.0, 0.3, 0.3, 0.3],
            },
            geometry=geometry,
            crs='EPSG:4326',
        )

    def test_zero_depths_all_zero_damage(self, properties):
        from models.floodrisk.depth_damage import depth_damage_function
        depths = np.zeros(len(properties))
        damages = depth_damage_function(depths, properties)
        np.testing.assert_allclose(damages, 0.0)

    def test_large_depth_all_near_one(self, properties):
        from models.floodrisk.depth_damage import depth_damage_function
        depths = np.full(len(properties), 5.0)
        damages = depth_damage_function(depths, properties)
        assert np.all(damages > 0.5)

    def test_commercial_higher_damage_than_residential(self, properties):
        from models.floodrisk.depth_damage import depth_damage_function
        depths = np.full(len(properties), 1.0)
        damages = depth_damage_function(depths, properties)
        res_damage = damages[0]   # residential
        com_damage = damages[1]   # commercial (factor 1.2)
        assert com_damage > res_damage

    def test_floor_level_reduces_damage(self, properties):
        from models.floodrisk.depth_damage import depth_damage_function
        # Two residential properties; one has floor_level_metres=0, other=0.3
        depths = np.full(len(properties), 0.5)
        damages = depth_damage_function(depths, properties)
        # Index 0 (floor=0): depth 0.5 → some damage
        # Index 3 (floor=0.3): effective depth 0.2 → less damage
        assert damages[0] >= damages[3]

    def test_output_clipped_to_0_1(self, properties):
        from models.floodrisk.depth_damage import depth_damage_function
        depths = np.array([0.0, 0.1, 0.5, 1.0, 2.0, 6.0])
        damages = depth_damage_function(depths, properties)
        assert np.all((damages >= 0) & (damages <= 1))

    def test_returns_array_same_length(self, properties):
        from models.floodrisk.depth_damage import depth_damage_function
        depths = np.random.uniform(0, 3, len(properties))
        damages = depth_damage_function(depths, properties)
        assert len(damages) == len(properties)


# ===========================================================================
# calculate_flood_depths / calculate_synthetic_flood_depths (geopandas)
# ===========================================================================

@pytest.mark.skipif(not HAS_GEO, reason="geopandas not installed")
class TestCalculateFloodDepths:

    @pytest.fixture
    def properties(self):
        n = 4
        geometry = [Point(lon, lat) for lon, lat in
                    zip(np.linspace(-0.2, 0.0, n), np.linspace(51.4, 51.6, n))]
        return gpd.GeoDataFrame(
            {'property_id': [f'P{i}' for i in range(n)], 'elevation': [2.0] * n},
            geometry=geometry, crs='EPSG:4326',
        )

    @pytest.fixture
    def gauge_data_flooded(self):
        return pd.DataFrame({
            'water_level': [6.0, 5.8],
            'severe_level': [5.0, 5.0],
            'latitude': [51.48, 51.52],
            'longitude': [-0.15, -0.05],
        })

    @pytest.fixture
    def gauge_data_dry(self):
        return pd.DataFrame({
            'water_level': [3.0, 3.5],
            'severe_level': [5.0, 5.0],
            'latitude': [51.48, 51.52],
            'longitude': [-0.15, -0.05],
        })

    def test_no_gauge_data_returns_zeros(self, properties):
        from models.floodrisk.depth_damage import calculate_flood_depths
        depths = calculate_flood_depths(properties, None)
        np.testing.assert_allclose(depths, 0.0)

    def test_empty_gauge_data_returns_zeros(self, properties):
        from models.floodrisk.depth_damage import calculate_flood_depths
        empty = pd.DataFrame({'water_level': [], 'severe_level': []})
        depths = calculate_flood_depths(properties, empty)
        np.testing.assert_allclose(depths, 0.0)

    def test_below_severe_level_returns_zeros(self, properties, gauge_data_dry):
        from models.floodrisk.depth_damage import calculate_flood_depths
        depths = calculate_flood_depths(properties, gauge_data_dry)
        np.testing.assert_allclose(depths, 0.0)

    def test_above_severe_level_some_positive(self, properties, gauge_data_flooded):
        from models.floodrisk.depth_damage import calculate_flood_depths
        depths = calculate_flood_depths(properties, gauge_data_flooded)
        assert np.any(depths > 0)

    def test_depths_capped_at_5m(self, properties, gauge_data_flooded):
        from models.floodrisk.depth_damage import calculate_flood_depths
        depths = calculate_flood_depths(properties, gauge_data_flooded)
        assert np.all(depths <= 5.0)

    def test_returns_correct_length(self, properties, gauge_data_flooded):
        from models.floodrisk.depth_damage import calculate_flood_depths
        depths = calculate_flood_depths(properties, gauge_data_flooded)
        assert len(depths) == len(properties)
