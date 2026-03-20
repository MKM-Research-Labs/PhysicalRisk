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

"""Tests for models.floodrisk.flood_risk_model.FloodRiskModel."""

import pytest
import warnings

try:
    import geopandas as gpd
    import pandas as pd
    import numpy as np
    from shapely.geometry import Point
    HAS_GEO = True
except ImportError:
    HAS_GEO = False

pytestmark = pytest.mark.skipif(not HAS_GEO, reason="geopandas not installed")


def _make_properties(n=3, include_elevation=True, include_type=True,
                     include_floor=True, include_id=True):
    """Build a minimal GeoDataFrame for FloodRiskModel."""
    data = {
        "geometry": [Point(-0.1 + i * 0.01, 51.5 + i * 0.01) for i in range(n)],
        "value": [200_000 + i * 50_000 for i in range(n)],
    }
    if include_id:
        data["property_id"] = [f"PROP-{i:04d}" for i in range(n)]
    if include_elevation:
        data["elevation"] = [5.0 + i * 2 for i in range(n)]
    if include_type:
        data["property_type"] = ["residential"] * n
    if include_floor:
        data["floor_level_metres"] = [0.0] * n
    return gpd.GeoDataFrame(data, crs="EPSG:4326")


def _make_gauge_data(n=2):
    """Build a minimal gauge DataFrame."""
    return pd.DataFrame({
        "gauge_id": [f"GAUGE-{i:03d}" for i in range(n)],
        "latitude": [51.50 + i * 0.02 for i in range(n)],
        "longitude": [-0.10 + i * 0.02 for i in range(n)],
        "water_level": [1.5 + i * 0.5 for i in range(n)],
        "severe_level": [3.0 + i * 0.5 for i in range(n)],
        "warning_level": [2.5 + i * 0.5 for i in range(n)],
        "alert_level": [2.0 + i * 0.5 for i in range(n)],
        "ground_level": [5.0 + i * 1.0 for i in range(n)],
    })


class TestFloodRiskModelInit:
    """Tests for __init__ and _validate_and_prepare_properties (lines 59-74)."""

    def test_basic_construction(self):
        """Lines 59-74: model builds without error given valid inputs."""
        from models.floodrisk.flood_risk_model import FloodRiskModel
        props = _make_properties()
        model = FloodRiskModel(props, {"GAUGE-000": 1.5})
        assert model.properties is not None
        assert model.flood_event == {"GAUGE-000": 1.5}

    def test_correlation_matrix_built(self):
        """Line 72-74: correlation_matrix is set after __init__."""
        from models.floodrisk.flood_risk_model import FloodRiskModel
        props = _make_properties()
        model = FloodRiskModel(props, {"GAUGE-000": 1.5})
        assert model.correlation_matrix is not None

    def test_with_gauge_data(self):
        """Line 71: kdtree built when gauge_data provided."""
        from models.floodrisk.flood_risk_model import FloodRiskModel
        props = _make_properties()
        gauges = _make_gauge_data()
        model = FloodRiskModel(props, {"GAUGE-000": 1.5}, gauge_data=gauges)
        assert model.gauge_data is not None

    def test_custom_correlation_params(self):
        """Lines 62-63: custom correlation_distance and base_correlation stored."""
        from models.floodrisk.flood_risk_model import FloodRiskModel
        props = _make_properties()
        model = FloodRiskModel(props, {}, correlation_distance=500, base_correlation=0.6)
        assert model.correlation_distance == 500
        assert model.base_correlation == 0.6

    def test_missing_geometry_raises(self):
        """Line 81: missing 'geometry' column raises ValueError."""
        from models.floodrisk.flood_risk_model import FloodRiskModel
        df = pd.DataFrame({"value": [100_000]})
        with pytest.raises((ValueError, AttributeError)):
            FloodRiskModel(df, {})

    def test_missing_value_raises(self):
        """Line 81: missing 'value' column raises ValueError."""
        from models.floodrisk.flood_risk_model import FloodRiskModel
        props = gpd.GeoDataFrame({"geometry": [Point(0, 0)]})
        with pytest.raises(ValueError, match="value"):
            FloodRiskModel(props, {})

    def test_missing_property_id_auto_assigned(self):
        """Lines 83-84: property_id auto-assigned when absent."""
        from models.floodrisk.flood_risk_model import FloodRiskModel
        props = _make_properties(include_id=False)
        model = FloodRiskModel(props, {})
        assert "property_id" in model.properties.columns
        assert model.properties["property_id"].iloc[0].startswith("PROP_")

    def test_missing_elevation_warns_and_defaults(self):
        """Lines 86-88: missing elevation → warning + default 20.0."""
        from models.floodrisk.flood_risk_model import FloodRiskModel
        props = _make_properties(include_elevation=False)
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            model = FloodRiskModel(props, {})
        assert any("elevation" in str(warning.message).lower() for warning in w)
        assert (model.properties["elevation"] == 20.0).all()

    def test_missing_property_type_warns_and_defaults(self):
        """Lines 90-92: missing property_type → warning + default 'residential'."""
        from models.floodrisk.flood_risk_model import FloodRiskModel
        props = _make_properties(include_type=False)
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            model = FloodRiskModel(props, {})
        assert any("property_type" in str(warning.message).lower() for warning in w)
        assert (model.properties["property_type"] == "residential").all()

    def test_missing_floor_level_defaults_to_zero(self):
        """Lines 94-95: missing floor_level_metres → default 0.0."""
        from models.floodrisk.flood_risk_model import FloodRiskModel
        props = _make_properties(include_floor=False)
        model = FloodRiskModel(props, {})
        assert "floor_level_metres" in model.properties.columns
        assert (model.properties["floor_level_metres"] == 0.0).all()

    def test_properties_copied(self):
        """Line 59: properties is a copy, original not mutated."""
        from models.floodrisk.flood_risk_model import FloodRiskModel
        props = _make_properties(include_id=False)
        original_cols = set(props.columns)
        FloodRiskModel(props, {})
        assert set(props.columns) == original_cols


class TestFloodRiskModelMethods:
    """Tests for delegate methods (lines 97-151)."""

    @pytest.fixture
    def model(self):
        from models.floodrisk.flood_risk_model import FloodRiskModel
        props = _make_properties(n=5)
        props["elevation"] = [2.0 + i * 0.5 for i in range(5)]
        gauges = pd.DataFrame({
            "gauge_id": ["GAUGE-000", "GAUGE-001"],
            "latitude": [51.50, 51.52],
            "longitude": [-0.10, -0.08],
            "water_level": [8.0, 9.0],
            "severe_level": [3.0, 3.5],
            "warning_level": [2.5, 3.0],
            "alert_level": [2.0, 2.5],
            "ground_level": [2.0, 2.5],
        })
        return FloodRiskModel(props, {"GAUGE-000": 8.0}, gauge_data=gauges)

    def test_calculate_flood_depths_returns_array(self, model):
        """Line 99: calculate_flood_depths() returns ndarray."""
        depths = model.calculate_flood_depths()
        assert isinstance(depths, np.ndarray)
        assert len(depths) == len(model.properties)

    def test_calculate_direct_impacts_returns_array(self, model):
        """Line 103: calculate_direct_impacts() returns ndarray."""
        depths = model.calculate_flood_depths()
        impacts = model.calculate_direct_impacts(depths)
        assert isinstance(impacts, np.ndarray)
        assert len(impacts) == len(model.properties)

    def test_simulate_portfolio_impact_returns_dict(self, model):
        """Lines 107-112: simulate_portfolio_impact() returns dict."""
        result = model.simulate_portfolio_impact(n_simulations=100)
        assert isinstance(result, dict)

    def test_analyze_spatial_concentration_returns_df(self, model):
        """Lines 114-120: analyze_spatial_concentration() returns DataFrame."""
        result = model.analyze_spatial_concentration()
        assert isinstance(result, pd.DataFrame)

    def test_calculate_advanced_metrics_returns_dict(self, model):
        """Lines 122-129: calculate_advanced_metrics() returns dict."""
        result = model.calculate_advanced_metrics()
        assert isinstance(result, dict)

    def test_analyze_risk_clusters_returns_df(self):
        """Lines 131-139: analyze_risk_clusters() returns DataFrame, sets risk_clusters."""
        from models.floodrisk.flood_risk_model import FloodRiskModel
        # Use more properties with varied elevations and high water levels to produce varied floods
        n = 10
        props = _make_properties(n=n)
        props["elevation"] = [3.0 + i * 0.5 for i in range(n)]
        # Water level above severe_level triggers flooding
        gauges = pd.DataFrame({
            "gauge_id": ["GAUGE-000", "GAUGE-001"],
            "latitude": [51.50, 51.52],
            "longitude": [-0.10, -0.08],
            "water_level": [8.0, 9.0],
            "severe_level": [3.0, 3.5],
            "warning_level": [2.5, 3.0],
            "alert_level": [2.0, 2.5],
            "ground_level": [2.0, 2.5],
        })
        model = FloodRiskModel(props, {"GAUGE-000": 8.0}, gauge_data=gauges)
        result = model.analyze_risk_clusters(n_clusters=2)
        assert isinstance(result, pd.DataFrame)
        assert model.risk_clusters is not None

    def test_haversine_distance_delegate(self, model):
        """Line 151: _haversine_distance() delegates to haversine_distance."""
        d = model._haversine_distance(51.5, -0.1, 51.6, -0.0)
        assert isinstance(d, float)
        assert d > 0
