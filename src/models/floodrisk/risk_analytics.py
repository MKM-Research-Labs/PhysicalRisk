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
Risk analytics for flood risk model.

Monte Carlo portfolio simulation, spatial concentration analysis,
HHI concentration metrics, KMeans risk clustering, and advanced metrics.
"""

from typing import Dict, Optional

import geopandas as gpd
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans


def simulate_portfolio_impact(properties: gpd.GeoDataFrame,
                               flood_depths: np.ndarray,
                               direct_impacts: np.ndarray,
                               correlation_matrix: Optional[np.ndarray],
                               n_simulations: int = 1000) -> Dict[str, float]:
    """
    Simulate portfolio impact using Monte Carlo methods with spatial correlations.

    Args:
        properties: GeoDataFrame with property data
        flood_depths: Pre-calculated flood depths
        direct_impacts: Pre-calculated damage ratios
        correlation_matrix: Spatial correlation matrix (or None for independent)
        n_simulations: Number of simulation runs

    Returns:
        Dictionary with portfolio risk metrics
    """
    property_values = properties['value'].values

    np.random.seed(42)

    if correlation_matrix is not None:
        shocks = np.random.multivariate_normal(
            mean=np.zeros(len(properties)),
            cov=correlation_matrix,
            size=n_simulations
        )
    else:
        shocks = np.random.normal(0, 1, (n_simulations, len(properties)))

    portfolio_impacts = []

    for sim_idx in range(n_simulations):
        shock = shocks[sim_idx]
        shocked_impacts = np.clip(
            direct_impacts * (1 + 0.2 * shock),
            0, 1
        )
        sim_impact = np.sum(property_values * shocked_impacts)
        portfolio_impacts.append(sim_impact)

    portfolio_impacts = np.array(portfolio_impacts)

    return {
        'mean_impact': np.mean(portfolio_impacts),
        'std_impact': np.std(portfolio_impacts),
        'var_95': np.percentile(portfolio_impacts, 95),
        'var_99': np.percentile(portfolio_impacts, 99),
        'es_95': np.mean(portfolio_impacts[portfolio_impacts >= np.percentile(portfolio_impacts, 95)]),
        'es_99': np.mean(portfolio_impacts[portfolio_impacts >= np.percentile(portfolio_impacts, 99)]),
        'max_impact': np.max(portfolio_impacts),
        'min_impact': np.min(portfolio_impacts),
        'impact_distribution': portfolio_impacts
    }


def analyze_spatial_concentration(properties: gpd.GeoDataFrame,
                                    flood_depths: np.ndarray,
                                    direct_impacts: np.ndarray,
                                    grid_size: float = 1000) -> pd.DataFrame:
    """
    Analyze spatial concentration of flood risk using grid-based approach.

    Args:
        properties: GeoDataFrame with property data
        flood_depths: Pre-calculated flood depths
        direct_impacts: Pre-calculated damage ratios
        grid_size: Size of grid cells in meters

    Returns:
        DataFrame with concentration metrics by grid cell
    """
    min_x = properties.geometry.x.min()
    min_y = properties.geometry.y.min()

    grid_size_deg = grid_size / 111000

    grid_x = ((properties.geometry.x - min_x) // grid_size_deg).astype(int)
    grid_y = ((properties.geometry.y - min_y) // grid_size_deg).astype(int)
    grid_ids = grid_x.astype(str) + '_' + grid_y.astype(str)

    analysis_df = pd.DataFrame({
        'grid_id': grid_ids,
        'property_id': properties['property_id'],
        'value': properties['value'],
        'flood_depth': flood_depths,
        'impact_ratio': direct_impacts,
        'value_at_risk': properties['value'].values * direct_impacts
    })

    grid_summary = analysis_df.groupby('grid_id').agg({
        'property_id': 'count',
        'value': 'sum',
        'flood_depth': 'mean',
        'impact_ratio': 'mean',
        'value_at_risk': 'sum'
    }).rename(columns={'property_id': 'property_count'})

    grid_summary['concentration_index'] = (
        grid_summary['value_at_risk'] / grid_summary['value_at_risk'].sum()
    ) ** 2

    return grid_summary.reset_index()


def calculate_hhi(values: np.ndarray) -> float:
    """Calculate Herfindahl-Hirschman Index for concentration measurement."""
    total = np.sum(values)
    if total == 0:
        return 0.0
    shares = values / total
    return np.sum(shares ** 2)


def calculate_advanced_metrics(properties: gpd.GeoDataFrame,
                                flood_depths: np.ndarray,
                                direct_impacts: np.ndarray,
                                spatial_analysis: pd.DataFrame) -> Dict[str, float]:
    """
    Calculate advanced portfolio risk metrics.

    Returns:
        Dictionary of advanced risk metrics including HHI, concentration,
        and risk distribution breakdowns.
    """
    property_values = properties['value'].values

    total_value = np.sum(property_values)
    total_value_at_risk = np.sum(property_values * (direct_impacts > 0))
    expected_loss = np.sum(property_values * direct_impacts)

    impact_values = property_values * direct_impacts
    concentration_hhi = calculate_hhi(impact_values)

    geographic_concentration = 0.0
    if len(spatial_analysis) > 0:
        geographic_concentration = calculate_hhi(spatial_analysis['value_at_risk'].values)

    high_risk_properties = np.sum(direct_impacts > 0.6)
    medium_risk_properties = np.sum((direct_impacts > 0.3) & (direct_impacts <= 0.6))
    low_risk_properties = np.sum((direct_impacts > 0.1) & (direct_impacts <= 0.3))

    return {
        'total_portfolio_value': total_value,
        'total_value_at_risk': total_value_at_risk,
        'expected_loss': expected_loss,
        'expected_loss_ratio': expected_loss / total_value if total_value > 0 else 0,
        'max_single_property_impact': np.max(property_values * direct_impacts),
        'concentration_hhi': concentration_hhi,
        'geographic_concentration': geographic_concentration,
        'high_risk_properties': int(high_risk_properties),
        'medium_risk_properties': int(medium_risk_properties),
        'low_risk_properties': int(low_risk_properties),
        'average_flood_depth': np.mean(flood_depths),
        'max_flood_depth': np.max(flood_depths),
        'properties_with_flooding': int(np.sum(flood_depths > 0)),
        'percentage_flooded': (np.sum(flood_depths > 0) / len(flood_depths)) * 100
    }


def analyze_risk_clusters(properties: gpd.GeoDataFrame,
                           flood_depths: np.ndarray,
                           direct_impacts: np.ndarray,
                           n_clusters: int = 5) -> pd.DataFrame:
    """
    Perform risk-based clustering analysis of properties using KMeans.

    Args:
        properties: GeoDataFrame with property data
        flood_depths: Pre-calculated flood depths
        direct_impacts: Pre-calculated damage ratios
        n_clusters: Number of clusters to identify

    Returns:
        DataFrame with cluster assignments and statistics
    """
    features = np.column_stack([
        flood_depths,
        direct_impacts,
        properties.geometry.x,
        properties.geometry.y,
        np.log1p(properties['value'].values)
    ])

    features_normalized = (features - features.mean(axis=0)) / features.std(axis=0)

    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    cluster_labels = kmeans.fit_predict(features_normalized)

    return pd.DataFrame({
        'property_id': properties['property_id'],
        'cluster': cluster_labels,
        'flood_depth': flood_depths,
        'impact_ratio': direct_impacts,
        'property_value': properties['value'],
        'value_at_risk': properties['value'].values * direct_impacts,
        'latitude': properties.geometry.y,
        'longitude': properties.geometry.x
    })
