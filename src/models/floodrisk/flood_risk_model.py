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
Flood Risk Model

Core flood risk calculation engine for property portfolios.
Implements spatial flood depth interpolation, depth-damage functions,
correlation modeling, Monte Carlo simulation, and risk visualization.

Delegates to submodules:
  - spatial: KDTree, correlation matrix, haversine, IDW interpolation
  - depth_damage: flood depth calculations, vulnerability curves
  - risk_analytics: Monte Carlo, spatial concentration, HHI, clustering
  - risk_visualization: Folium maps, matplotlib plots
"""

import warnings
from typing import Dict, Optional

import geopandas as gpd
import numpy as np
import pandas as pd

from models.floodrisk.depth_damage import (
    calculate_flood_depths,
    depth_damage_function,
)
from models.floodrisk.risk_analytics import (
    analyze_risk_clusters,
    analyze_spatial_concentration,
    calculate_advanced_metrics,
    simulate_portfolio_impact,
)
from models.floodrisk.risk_visualization import visualize_risk
from models.floodrisk.spatial import (
    build_correlation_matrix,
    build_spatial_index,
    haversine_distance,
)


class FloodRiskModel:
    """
    Core flood risk calculation engine for property portfolios.

    This model implements:
    - Spatial flood depth interpolation from gauge readings
    - Depth-damage functions for impact assessment
    - Correlation modeling for portfolio-level risk
    - Monte Carlo simulation for uncertainty quantification
    """

    def __init__(self,
                 properties: gpd.GeoDataFrame,
                 flood_event: Dict[str, float],
                 gauge_data: Optional[pd.DataFrame] = None,
                 correlation_distance: float = 1000,
                 base_correlation: float = 0.4):
        self.properties = properties.copy()
        self.flood_event = flood_event
        self.gauge_data = gauge_data
        self.correlation_distance = correlation_distance
        self.base_correlation = base_correlation

        self.correlation_matrix = None
        self.kdtree = None
        self.risk_clusters = None

        self._validate_and_prepare_properties()

        self.kdtree = build_spatial_index(self.gauge_data)
        self.correlation_matrix = build_correlation_matrix(
            self.properties, self.correlation_distance, self.base_correlation
        )

    def _validate_and_prepare_properties(self):
        """Validate and prepare property data with defaults for missing columns."""
        required_columns = ['geometry', 'value']
        for col in required_columns:
            if col not in self.properties.columns:
                raise ValueError(f"Properties must contain '{col}' column")

        if 'property_id' not in self.properties.columns:
            self.properties['property_id'] = [f"PROP_{i}" for i in range(len(self.properties))]

        if 'elevation' not in self.properties.columns:
            warnings.warn("'elevation' not found, defaulting to 20.0")
            self.properties['elevation'] = 20.0

        if 'property_type' not in self.properties.columns:
            warnings.warn("'property_type' not found, defaulting to 'residential'")
            self.properties['property_type'] = 'residential'

        if 'floor_level_metres' not in self.properties.columns:
            self.properties['floor_level_metres'] = 0.0

    def calculate_flood_depths(self) -> np.ndarray:
        """Calculate flood depth at each property location."""
        return calculate_flood_depths(self.properties, self.gauge_data)

    def calculate_direct_impacts(self, flood_depths: np.ndarray) -> np.ndarray:
        """Calculate direct impact (damage ratio) from flood depths."""
        return depth_damage_function(flood_depths, self.properties)

    def simulate_portfolio_impact(self, n_simulations: int = 1000) -> Dict[str, float]:
        """Simulate portfolio impact using Monte Carlo with spatial correlations."""
        flood_depths = self.calculate_flood_depths()
        direct_impacts = self.calculate_direct_impacts(flood_depths)
        return simulate_portfolio_impact(
            self.properties, flood_depths, direct_impacts,
            self.correlation_matrix, n_simulations
        )

    def analyze_spatial_concentration(self, grid_size: float = 1000) -> pd.DataFrame:
        """Analyze spatial concentration of flood risk using grid-based approach."""
        flood_depths = self.calculate_flood_depths()
        direct_impacts = self.calculate_direct_impacts(flood_depths)
        return analyze_spatial_concentration(
            self.properties, flood_depths, direct_impacts, grid_size
        )

    def calculate_advanced_metrics(self) -> Dict[str, float]:
        """Calculate advanced portfolio risk metrics."""
        flood_depths = self.calculate_flood_depths()
        direct_impacts = self.calculate_direct_impacts(flood_depths)
        spatial_analysis = self.analyze_spatial_concentration()
        return calculate_advanced_metrics(
            self.properties, flood_depths, direct_impacts, spatial_analysis
        )

    def analyze_risk_clusters(self, n_clusters: int = 5) -> pd.DataFrame:
        """Perform risk-based clustering analysis of properties."""
        flood_depths = self.calculate_flood_depths()
        direct_impacts = self.calculate_direct_impacts(flood_depths)
        result = analyze_risk_clusters(
            self.properties, flood_depths, direct_impacts, n_clusters
        )
        self.risk_clusters = result['cluster'].values
        return result

    def visualize_risk(self, output_file_base: str = 'flood_risk'):
        """Create risk visualization maps and charts."""
        flood_depths = self.calculate_flood_depths()
        direct_impacts = self.calculate_direct_impacts(flood_depths)
        visualize_risk(
            self.properties, flood_depths, direct_impacts,
            self.flood_event, self.gauge_data, output_file_base
        )

    def _haversine_distance(self, lat1, lon1, lat2, lon2) -> float:
        return haversine_distance(lat1, lon1, lat2, lon2)
