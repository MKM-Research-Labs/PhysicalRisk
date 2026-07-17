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
Tests for models.floodrisk.risk_analytics.

Covers: calculate_hhi (pure NumPy), simulate_portfolio_impact,
analyze_spatial_concentration, calculate_advanced_metrics,
and analyze_risk_clusters. GeoDataFrame tests skipped without geopandas.
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

from models.floodrisk.risk_analytics import calculate_hhi


# ===========================================================================
# calculate_hhi  (pure NumPy — no geopandas needed)
# ===========================================================================

class TestCalculateHHI:

    def test_zero_total_returns_zero(self):
        assert calculate_hhi(np.array([0.0, 0.0, 0.0])) == 0.0

    def test_single_element_returns_one(self):
        assert calculate_hhi(np.array([100.0])) == pytest.approx(1.0)

    def test_two_equal_elements_returns_half(self):
        result = calculate_hhi(np.array([50.0, 50.0]))
        assert result == pytest.approx(0.5)

    def test_uniform_distribution_n_elements(self):
        n = 5
        result = calculate_hhi(np.ones(n))
        assert result == pytest.approx(1.0 / n)

    def test_monopoly_returns_one(self):
        result = calculate_hhi(np.array([100.0, 0.0, 0.0]))
        assert result == pytest.approx(1.0)

    def test_result_between_0_and_1(self):
        for vals in [
            np.array([1.0, 2.0, 3.0]),
            np.array([10.0, 20.0, 70.0]),
            np.array([25.0, 25.0, 25.0, 25.0]),
        ]:
            result = calculate_hhi(vals)
            assert 0.0 <= result <= 1.0

    def test_higher_concentration_higher_hhi(self):
        uniform = calculate_hhi(np.array([25.0, 25.0, 25.0, 25.0]))
        concentrated = calculate_hhi(np.array([80.0, 10.0, 5.0, 5.0]))
        assert concentrated > uniform


# ===========================================================================
# GeoDataFrame-dependent tests
# ===========================================================================

@pytest.mark.skipif(not HAS_GEO, reason="geopandas not installed")
class TestSimulatePortfolioImpact:

    @pytest.fixture
    def synthetic_data(self):
        n = 8
        lons = np.linspace(-0.3, 0.1, n)
        lats = np.linspace(51.4, 51.6, n)
        geometry = [Point(lon, lat) for lon, lat in zip(lons, lats)]
        props = gpd.GeoDataFrame(
            {
                'property_id': [f'P{i}' for i in range(n)],
                'value': np.full(n, 300_000),
            },
            geometry=geometry, crs='EPSG:4326',
        )
        depths = np.array([0.0, 0.2, 0.5, 1.0, 0.0, 0.3, 0.8, 0.0])
        impacts = np.array([0.0, 0.05, 0.15, 0.35, 0.0, 0.08, 0.25, 0.0])
        return props, depths, impacts

    def test_returns_required_keys(self, synthetic_data):
        from models.floodrisk.risk_analytics import simulate_portfolio_impact
        props, depths, impacts = synthetic_data
        result = simulate_portfolio_impact(props, depths, impacts, None, n_simulations=200)
        for key in ('mean_impact', 'std_impact', 'var_95', 'var_99',
                    'es_95', 'es_99', 'max_impact', 'min_impact', 'impact_distribution'):
            assert key in result

    def test_var_99_ge_var_95(self, synthetic_data):
        from models.floodrisk.risk_analytics import simulate_portfolio_impact
        props, depths, impacts = synthetic_data
        result = simulate_portfolio_impact(props, depths, impacts, None, n_simulations=500)
        assert result['var_99'] >= result['var_95']

    def test_es_ge_var(self, synthetic_data):
        from models.floodrisk.risk_analytics import simulate_portfolio_impact
        props, depths, impacts = synthetic_data
        result = simulate_portfolio_impact(props, depths, impacts, None, n_simulations=500)
        assert result['es_95'] >= result['var_95']
        assert result['es_99'] >= result['var_99']

    def test_max_ge_mean(self, synthetic_data):
        from models.floodrisk.risk_analytics import simulate_portfolio_impact
        props, depths, impacts = synthetic_data
        result = simulate_portfolio_impact(props, depths, impacts, None, n_simulations=200)
        assert result['max_impact'] >= result['mean_impact']

    def test_impact_distribution_length(self, synthetic_data):
        from models.floodrisk.risk_analytics import simulate_portfolio_impact
        props, depths, impacts = synthetic_data
        result = simulate_portfolio_impact(props, depths, impacts, None, n_simulations=300)
        assert len(result['impact_distribution']) == 300


@pytest.mark.skipif(not HAS_GEO, reason="geopandas not installed")
class TestAnalyzeSpatialConcentration:

    @pytest.fixture
    def synthetic_data(self):
        n = 6
        lons = np.linspace(-0.3, 0.1, n)
        lats = np.linspace(51.4, 51.6, n)
        geometry = [Point(lon, lat) for lon, lat in zip(lons, lats)]
        props = gpd.GeoDataFrame(
            {
                'property_id': [f'P{i}' for i in range(n)],
                'value': np.full(n, 200_000),
            },
            geometry=geometry, crs='EPSG:4326',
        )
        depths = np.array([0.0, 0.3, 0.8, 0.0, 0.5, 0.1])
        impacts = np.array([0.0, 0.1, 0.3, 0.0, 0.2, 0.05])
        return props, depths, impacts

    def test_returns_dataframe(self, synthetic_data):
        from models.floodrisk.risk_analytics import analyze_spatial_concentration
        props, depths, impacts = synthetic_data
        result = analyze_spatial_concentration(props, depths, impacts)
        assert isinstance(result, pd.DataFrame)

    def test_has_required_columns(self, synthetic_data):
        from models.floodrisk.risk_analytics import analyze_spatial_concentration
        props, depths, impacts = synthetic_data
        result = analyze_spatial_concentration(props, depths, impacts)
        for col in ('grid_id', 'property_count', 'value', 'flood_depth',
                    'impact_ratio', 'value_at_risk', 'concentration_index'):
            assert col in result.columns

    def test_total_property_count_matches(self, synthetic_data):
        from models.floodrisk.risk_analytics import analyze_spatial_concentration
        props, depths, impacts = synthetic_data
        result = analyze_spatial_concentration(props, depths, impacts)
        assert result['property_count'].sum() == len(props)


@pytest.mark.skipif(not HAS_GEO, reason="geopandas not installed")
class TestCalculateAdvancedMetrics:

    @pytest.fixture
    def synthetic_data(self):
        n = 8
        lons = np.linspace(-0.3, 0.1, n)
        lats = np.linspace(51.4, 51.6, n)
        geometry = [Point(lon, lat) for lon, lat in zip(lons, lats)]
        props = gpd.GeoDataFrame(
            {
                'property_id': [f'P{i}' for i in range(n)],
                'value': np.full(n, 400_000),
            },
            geometry=geometry, crs='EPSG:4326',
        )
        depths = np.array([0.0, 0.2, 0.4, 1.5, 0.8, 2.5, 0.05, 0.7])
        impacts = np.array([0.02, 0.12, 0.35, 0.65, 0.45, 0.7, 0.08, 0.32])
        return props, depths, impacts

    def test_returns_required_keys(self, synthetic_data):
        from models.floodrisk.risk_analytics import (
            calculate_advanced_metrics, analyze_spatial_concentration
        )
        props, depths, impacts = synthetic_data
        spatial = analyze_spatial_concentration(props, depths, impacts)
        result = calculate_advanced_metrics(props, depths, impacts, spatial)
        for key in ('total_portfolio_value', 'expected_loss', 'expected_loss_ratio',
                    'concentration_hhi', 'high_risk_properties', 'medium_risk_properties',
                    'low_risk_properties', 'percentage_flooded'):
            assert key in result

    def test_expected_loss_positive(self, synthetic_data):
        from models.floodrisk.risk_analytics import (
            calculate_advanced_metrics, analyze_spatial_concentration
        )
        props, depths, impacts = synthetic_data
        spatial = analyze_spatial_concentration(props, depths, impacts)
        result = calculate_advanced_metrics(props, depths, impacts, spatial)
        assert result['expected_loss'] > 0

    def test_risk_bands_sum_to_affected(self, synthetic_data):
        from models.floodrisk.risk_analytics import (
            calculate_advanced_metrics, analyze_spatial_concentration
        )
        props, depths, impacts = synthetic_data
        spatial = analyze_spatial_concentration(props, depths, impacts)
        result = calculate_advanced_metrics(props, depths, impacts, spatial)
        total = (result['high_risk_properties'] + result['medium_risk_properties']
                 + result['low_risk_properties'])
        # All properties with impact > 0.1 sum to total
        expected_affected = int(np.sum(impacts > 0.1))
        assert total == expected_affected


@pytest.mark.skipif(not HAS_GEO, reason="geopandas not installed")
class TestAnalyzeRiskClusters:

    def test_returns_dataframe_with_correct_rows(self):
        from models.floodrisk.risk_analytics import analyze_risk_clusters
        n = 10
        lons = np.linspace(-0.3, 0.1, n)
        lats = np.linspace(51.4, 51.6, n)
        geometry = [Point(lon, lat) for lon, lat in zip(lons, lats)]
        props = gpd.GeoDataFrame(
            {
                'property_id': [f'P{i}' for i in range(n)],
                'value': np.linspace(200_000, 600_000, n),
            },
            geometry=geometry, crs='EPSG:4326',
        )
        depths = np.random.default_rng(0).uniform(0, 3, n)
        impacts = np.random.default_rng(0).uniform(0, 0.8, n)
        result = analyze_risk_clusters(props, depths, impacts, n_clusters=3)
        assert isinstance(result, pd.DataFrame)
        assert len(result) == n
        assert 'cluster' in result.columns
        assert result['cluster'].nunique() == 3
