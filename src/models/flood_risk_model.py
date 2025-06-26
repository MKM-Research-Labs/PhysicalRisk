# Copyright (c) 2025 MKM Research Labs. All rights reserved.
# 
# This software is provided under license by MKM Research Labs. 
# Use, reproduction, distribution, or modification of this code is subject to the 
# terms and conditions of the license agreement provided with this software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Flood Risk Model

Core flood risk calculation engine that performs spatial analysis, 
flood depth calculations, and risk assessments for property portfolios.
"""

import numpy as np
import pandas as pd
import geopandas as gpd
from scipy.spatial import cKDTree
from scipy.spatial.distance import cdist
from scipy.stats import norm
from scipy.interpolate import interp1d
import folium
import matplotlib.pyplot as plt
import seaborn as sns
from shapely.geometry import Point, Polygon
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from sklearn.cluster import KMeans
import warnings
from math import radians, sin, cos, sqrt, atan2


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
        """
        Initialize the flood risk model.
        
        Parameters:
        -----------
        properties: GeoDataFrame with columns:
            - geometry: Property location (Point)
            - property_id: Unique identifier
            - value: Current market value
            - floor_level_metres: Height above ground (optional)
            - property_type: Type of construction (optional)
            - elevation: Ground elevation (optional)
        ...
        """
        self.properties = properties.copy()
        self.flood_event = flood_event
        self.gauge_data = gauge_data
        self.correlation_distance = correlation_distance
        self.base_correlation = base_correlation
        
        # Initialize derived attributes
        self.correlation_matrix = None
        self.kdtree = None
        self.risk_clusters = None
        
        # Validate and prepare property data
        self._validate_and_prepare_properties()
        
        # Build spatial structures
        self._build_spatial_index()
        self._build_correlation_matrix()
    
    def _validate_and_prepare_properties(self):
        """Validate and prepare property data with defaults for missing columns."""
        required_columns = ['geometry', 'value']
        for col in required_columns:
            if col not in self.properties.columns:
                raise ValueError(f"Properties must contain '{col}' column")
        
        # Add property_id if missing
        if 'property_id' not in self.properties.columns:
            self.properties['property_id'] = [f"PROP_{i}" for i in range(len(self.properties))]
        
        if 'elevation' not in self.properties.columns:
            warnings.warn("'elevation' not found, defaulting to 20.0")
            self.properties['elevation'] = 20.0
        
        # Add property_type if missing
        if 'property_type' not in self.properties.columns:
            warnings.warn("'property_type' not found, defaulting to 'residential'")
            self.properties['property_type'] = 'residential'
    
    def _build_spatial_index(self):
        """Build KDTree for efficient spatial queries on gauge data."""
        if self.gauge_data is not None and len(self.gauge_data) > 0:
            # Convert gauge coordinates to radians for KDTree
            gauge_coords = np.deg2rad(
                self.gauge_data[['latitude', 'longitude']].values
            )
            self.kdtree = cKDTree(gauge_coords)
    
    def _build_correlation_matrix(self):
        """Build spatial correlation matrix between properties."""
        # Extract property coordinates
        coords = np.column_stack([
            self.properties.geometry.x,
            self.properties.geometry.y
        ])
        
        # Calculate distance matrix
        distances = cdist(coords, coords)
        
        # Convert to kilometers and apply exponential decay
        distances_km = distances * 111.0  # Rough conversion degrees to km
        
        # Build correlation matrix with exponential decay
        self.correlation_matrix = self.base_correlation * np.exp(
            -distances_km / (self.correlation_distance / 1000)
        )
        np.fill_diagonal(self.correlation_matrix, 1.0)
    
    def calculate_flood_depths(self) -> np.ndarray:
        """
        Calculate flood depth at each property location.
        
        Returns:
            Array of flood depths in meters (positive = flooding, negative = safe)
        """
        n_properties = len(self.properties)
        flood_depths = np.zeros(n_properties)
        
        if self.gauge_data is None or len(self.gauge_data) == 0:
            # Fallback: use synthetic flood event
            return self._calculate_synthetic_flood_depths()
        
        # Use gauge-based interpolation
        for i, (_, property_row) in enumerate(self.properties.iterrows()):
            try:
                # Find nearest gauges and interpolate
                property_depth = self._interpolate_flood_depth_at_property(property_row)
                flood_depths[i] = property_depth
            except Exception as e:
                warnings.warn(f"Error calculating flood depth for property {i}: {str(e)}")
                flood_depths[i] = 0.0
        
        return flood_depths


    def _calculate_synthetic_flood_depths(self) -> np.ndarray:
        """
        MINIMAL FIX: Use gauge data directly if available, otherwise return zeros.
        """
        n_properties = len(self.properties)
        flood_depths = np.zeros(n_properties)
        
        # If we have gauge data, use it properly
        if self.gauge_data is not None and len(self.gauge_data) > 0:
            print(f"Using gauge data for {len(self.gauge_data)} gauges")
            
            # Get maximum water level and severe level from gauges
            max_water_level = self.gauge_data['water_level'].max()
            mean_severe_level = self.gauge_data['severe_level'].mean()
            
            if max_water_level > mean_severe_level:
                # There is flooding - calculate depths based on property elevation
                flood_wse = max_water_level  # Water surface elevation
                
                for i, (_, property_row) in enumerate(self.properties.iterrows()):
                    prop_elevation = property_row.get('elevation', 20.0)
                    
                    # Simple calculation: depth = water_level - ground_elevation
                    depth = max(0.0, flood_wse - prop_elevation)
                    
                    # Apply distance decay (properties farther from Thames get less flooding)
                    prop_lat = property_row.geometry.y
                    prop_lon = property_row.geometry.x
                    
                    # Distance from central London (Thames)
                    thames_lat, thames_lon = 51.5, -0.1
                    distance = self._haversine_distance(thames_lat, thames_lon, prop_lat, prop_lon)
                    
                    # Decay factor - flooding decreases with distance
                    max_distance = 25000  # 25km
                    if distance < max_distance:
                        distance_factor = 1.0 - (distance / max_distance)
                        depth = depth * distance_factor
                    else:
                        depth = 0.0
                    
                    flood_depths[i] = min(depth, 5.0)  # Cap at 5m
            
            flooded_count = np.sum(flood_depths > 0)
            print(f"Flood calculation: {flooded_count}/{n_properties} properties flooded")
            print(f"Max depth: {np.max(flood_depths):.2f}m using gauge WSE: {max_water_level:.2f}m")
            
        else:
            print("No gauge data available - no flooding calculated")
        
        return flood_depths
    
    def _interpolate_flood_depth_at_property(self, property_id, gauge_flood_data):
        '''
        Calculate property-specific flood depth using spatial interpolation and elevation correction.
        
        Args:
            property_id: Unique property identifier
            gauge_flood_ Dict with gauge_id -> flood depth at gauge location
        
        Returns:
            float: Interpolated flood depth at property location (meters)
        '''
        
        try:
            # Get property information
            property_info = self.property_data[property_id]
            prop_elevation = property_info['elevation']
            prop_lat = property_info['latitude']
            prop_lon = property_info['longitude']
            
            # CRITICAL FIX: Use spatial interpolation instead of direct assignment
            interpolated_wse = self._spatial_interpolate_wse(
                target_lat=prop_lat, 
                target_lon=prop_lon, 
                gauge_flood_data=gauge_flood_data
            )
            
            # CRITICAL FIX: Calculate elevation-aware flood depth
            property_flood_depth = max(0.0, interpolated_wse - prop_elevation)
            
            # CRITICAL FIX: Add distance-based validation
            nearest_gauge_distance = self._get_nearest_gauge_distance(property_id)
            if nearest_gauge_distance > self.MAX_INTERPOLATION_DISTANCE:
                logging.warning(
                    f"Property {property_id} is {nearest_gauge_distance:.0f}m from nearest gauge. "
                    f"Interpolation may be unreliable."
                )
                property_flood_depth *= self.DISTANCE_UNCERTAINTY_FACTOR
            
            # CRITICAL FIX: Validate against local topography
            if not self._validate_topographic_consistency(property_id, property_flood_depth):
                logging.warning(f"Topographic inconsistency detected for property {property_id}")
                property_flood_depth = 0.0  # Conservative approach
            
            return property_flood_depth
            
        except KeyError as e:
            logging.error(f"Missing data for property {property_id}: {str(e)}")
            return 0.0
        except Exception as e:
            logging.error(f"Error interpolating flood depth for property {property_id}: {str(e)}")
            return 0.0

    def _spatial_interpolate_wse(self, target_lat, target_lon, gauge_flood_data):
        '''
        Spatially interpolate water surface elevation using inverse distance weighting.
        '''
        if not gauge_flood
            return 0.0
        
        # Calculate water surface elevations at gauges
        gauge_wse_data = {}
        for gauge_id, gauge_depth in gauge_flood_data.items():
            gauge_info = self.gauge_metadata[gauge_id]
            gauge_wse = gauge_depth + gauge_info['elevation']  # Convert depth to WSE
            gauge_wse_data[gauge_id] = {
                'wse': gauge_wse,
                'lat': gauge_info['latitude'],
                'lon': gauge_info['longitude']
            }
        
        # Inverse distance weighting interpolation
        total_weight = 0.0
        weighted_wse = 0.0
        
        for gauge_id, gauge_data in gauge_wse_data.items():
            distance = self._calculate_distance(
                target_lat, target_lon, 
                gauge_data['lat'], gauge_data['lon']
            )
            
            if distance < 1.0:  # Very close to gauge
                return gauge_data['wse']
            
            weight = 1.0 / (distance ** 2)  # Inverse distance squared weighting
            weighted_wse += weight * gauge_data['wse']
            total_weight += weight
        
        if total_weight == 0:
            return 0.0
        
        return weighted_wse / total_weight

        
    
    
    
    def _haversine_distance(self, lat1, lon1, lat2, lon2) -> float:
        """Calculate distance between two points using Haversine formula (in meters)."""
        R = 6371000  # Earth's radius in meters
        
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        return R * c
    
    def calculate_direct_impacts(self, flood_depths: np.ndarray) -> np.ndarray:
        """
        Calculate direct impact (damage ratio) from flood depths.
        
        Args:
            flood_depths: Array of flood depths in meters
            
        Returns:
            Array of damage ratios (0 to 1)
        """
        return self._depth_damage_function(flood_depths)
    
    def _depth_damage_function(self, depths: np.ndarray) -> np.ndarray:
        """
        Advanced depth-damage function with property type and location adjustments.
        
        Args:
            depths: Array of flood depths in meters
            
        Returns:
            Array of damage ratios (0 to 1)
        """
        # Base vulnerability curve
        depth_points = np.array([0, 0.05, 0.5, 1, 1.5, 2, 3, 4, 5, 6])
        vulnerability_points = np.array([0, 0.05, 0.25, 0.4, 0.5, 0.6, 0.75, 0.85, 0.95, 1])
        
        # Create interpolation function
        vulnerability_curve = interp1d(
            depth_points, vulnerability_points,
            kind='linear', fill_value=(0, 1), bounds_error=False
        )
        
        # Calculate base damage
        base_damage = vulnerability_curve(np.maximum(depths, 0))
        
        # Apply property type adjustments
        property_type_factors = {
            'residential': 1.0,
            'commercial': 1.2,
            'industrial': 0.9
        }
        
        type_adjustments = np.array([
            property_type_factors.get(str(pt).lower(), 1.0)
            for pt in self.properties['property_type']
        ])
        
        # Apply floor level adjustments
        floor_levels = self.properties['floor_level_metres'].values
        adjusted_depths = np.maximum(depths - floor_levels, 0)
        adjusted_damage = vulnerability_curve(adjusted_depths)
        
        # Combine adjustments
        final_damage = adjusted_damage * type_adjustments
        
        return np.clip(final_damage, 0, 1)
    
    def simulate_portfolio_impact(self, n_simulations: int = 1000) -> Dict[str, float]:
        """
        Simulate portfolio impact using Monte Carlo methods with spatial correlations.
        
        Args:
            n_simulations: Number of simulation runs
            
        Returns:
            Dictionary with portfolio risk metrics
        """
        # Calculate baseline impacts
        flood_depths = self.calculate_flood_depths()
        direct_impacts = self.calculate_direct_impacts(flood_depths)
        property_values = self.properties['value'].values
        
        # Monte Carlo simulation with correlated shocks
        np.random.seed(42)  # For reproducibility
        
        # Generate correlated random shocks
        if self.correlation_matrix is not None:
            shocks = np.random.multivariate_normal(
                mean=np.zeros(len(self.properties)),
                cov=self.correlation_matrix,
                size=n_simulations
            )
        else:
            # Independent shocks if correlation matrix not available
            shocks = np.random.normal(0, 1, (n_simulations, len(self.properties)))
        
        # Calculate portfolio impacts for each simulation
        portfolio_impacts = []
        
        for sim_idx in range(n_simulations):
            shock = shocks[sim_idx]
            
            # Apply correlated shock to damage ratios (with bounds checking)
            shocked_impacts = np.clip(
                direct_impacts * (1 + 0.2 * shock),  # 20% shock magnitude
                0, 1
            )
            
            # Calculate total portfolio impact
            sim_impact = np.sum(property_values * shocked_impacts)
            portfolio_impacts.append(sim_impact)
        
        portfolio_impacts = np.array(portfolio_impacts)
        
        # Calculate risk metrics
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
    
    def analyze_spatial_concentration(self, grid_size: float = 1000) -> pd.DataFrame:
        """
        Analyze spatial concentration of flood risk using grid-based approach.
        
        Args:
            grid_size: Size of grid cells in meters
            
        Returns:
            DataFrame with concentration metrics by grid cell
        """
        # Calculate impacts
        flood_depths = self.calculate_flood_depths()
        direct_impacts = self.calculate_direct_impacts(flood_depths)
        
        # Create spatial grid
        min_x, min_y = self.properties.geometry.x.min(), self.properties.geometry.y.min()
        max_x, max_y = self.properties.geometry.x.max(), self.properties.geometry.y.max()
        
        # Convert grid size from meters to degrees (approximate)
        grid_size_deg = grid_size / 111000  # Rough conversion
        
        # Create grid IDs
        grid_x = ((self.properties.geometry.x - min_x) // grid_size_deg).astype(int)
        grid_y = ((self.properties.geometry.y - min_y) // grid_size_deg).astype(int)
        grid_ids = grid_x.astype(str) + '_' + grid_y.astype(str)
        
        # Create analysis DataFrame
        analysis_df = pd.DataFrame({
            'grid_id': grid_ids,
            'property_id': self.properties['property_id'],
            'value': self.properties['value'],
            'flood_depth': flood_depths,
            'impact_ratio': direct_impacts,
            'value_at_risk': self.properties['value'].values * direct_impacts
        })
        
        # Aggregate by grid cell
        grid_summary = analysis_df.groupby('grid_id').agg({
            'property_id': 'count',
            'value': 'sum',
            'flood_depth': 'mean',
            'impact_ratio': 'mean',
            'value_at_risk': 'sum'
        }).rename(columns={'property_id': 'property_count'})
        
        # Calculate concentration metrics
        grid_summary['concentration_index'] = (
            grid_summary['value_at_risk'] / grid_summary['value_at_risk'].sum()
        ) ** 2
        
        return grid_summary.reset_index()
    
    def calculate_advanced_metrics(self) -> Dict[str, float]:
        """
        Calculate advanced portfolio risk metrics.
        
        Returns:
            Dictionary of advanced risk metrics
        """
        flood_depths = self.calculate_flood_depths()
        direct_impacts = self.calculate_direct_impacts(flood_depths)
        property_values = self.properties['value'].values
        
        # Portfolio-level metrics
        total_value = np.sum(property_values)
        total_value_at_risk = np.sum(property_values * (direct_impacts > 0))
        expected_loss = np.sum(property_values * direct_impacts)
        
        # Concentration metrics
        impact_values = property_values * direct_impacts
        concentration_hhi = self._calculate_hhi(impact_values)
        geographic_concentration = self._calculate_geographic_concentration()
        
        # Risk distribution metrics
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
            'high_risk_properties': high_risk_properties,
            'medium_risk_properties': medium_risk_properties,
            'low_risk_properties': low_risk_properties,
            'average_flood_depth': np.mean(flood_depths),
            'max_flood_depth': np.max(flood_depths),
            'properties_with_flooding': np.sum(flood_depths > 0),
            'percentage_flooded': (np.sum(flood_depths > 0) / len(flood_depths)) * 100
        }
    
    def _calculate_hhi(self, values: np.ndarray) -> float:
        """Calculate Herfindahl-Hirschman Index for concentration measurement."""
        total = np.sum(values)
        if total == 0:
            return 0.0
        
        shares = values / total
        return np.sum(shares ** 2)
    
    def _calculate_geographic_concentration(self, grid_size: float = 1000) -> float:
        """Calculate geographic concentration using spatial grid."""
        spatial_analysis = self.analyze_spatial_concentration(grid_size)
        
        if len(spatial_analysis) == 0:
            return 0.0
        
        # Calculate HHI based on value at risk distribution across grid cells
        return self._calculate_hhi(spatial_analysis['value_at_risk'].values)
    
    def analyze_risk_clusters(self, n_clusters: int = 5) -> pd.DataFrame:
        """
        Perform risk-based clustering analysis of properties.
        
        Args:
            n_clusters: Number of clusters to identify
            
        Returns:
            DataFrame with cluster assignments and statistics
        """
        # Calculate risk features
        flood_depths = self.calculate_flood_depths()
        direct_impacts = self.calculate_direct_impacts(flood_depths)
        
        # Create feature matrix
        features = np.column_stack([
            flood_depths,
            direct_impacts,
            self.properties.geometry.x,
            self.properties.geometry.y,
            np.log1p(self.properties['value'].values)  # Log-transformed values
        ])
        
        # Normalize features
        features_normalized = (features - features.mean(axis=0)) / features.std(axis=0)
        
        # Perform clustering
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(features_normalized)
        
        # Create results DataFrame
        cluster_results = pd.DataFrame({
            'property_id': self.properties['property_id'],
            'cluster': cluster_labels,
            'flood_depth': flood_depths,
            'impact_ratio': direct_impacts,
            'property_value': self.properties['value'],
            'value_at_risk': self.properties['value'].values * direct_impacts,
            'latitude': self.properties.geometry.y,
            'longitude': self.properties.geometry.x
        })
        
        self.risk_clusters = cluster_labels
        
        return cluster_results
    
    def visualize_risk(self, output_file_base: str = 'flood_risk'):
        """
        Create risk visualization maps and charts.
        
        Args:
            output_file_base: Base filename for output files
        """
        # Calculate risk metrics
        flood_depths = self.calculate_flood_depths()
        direct_impacts = self.calculate_direct_impacts(flood_depths)
        
        # Create interactive map
        self._create_interactive_map(flood_depths, direct_impacts, f"{output_file_base}.html")
        
        # Create static plots
        self._create_static_plots(flood_depths, direct_impacts, f"{output_file_base}.png")
    
    def _create_interactive_map(self, flood_depths, direct_impacts, output_file):
        """Create interactive Folium map of flood risk."""
        # Calculate map center
        center_lat = self.properties.geometry.y.mean()
        center_lon = self.properties.geometry.x.mean()
        
        # Create map
        m = folium.Map(location=[center_lat, center_lon], zoom_start=12)
        
        # Add properties as markers
        for i, (_, row) in enumerate(self.properties.iterrows()):
            impact = direct_impacts[i]
            depth = flood_depths[i]
            
            # Determine marker color based on risk level
            if impact > 0.6:
                color = 'red'
                risk_label = 'High'
            elif impact > 0.3:
                color = 'orange'
                risk_label = 'Medium'
            elif impact > 0.1:
                color = 'yellow'
                risk_label = 'Low'
            else:
                color = 'green'
                risk_label = 'Minimal'
            
            # Create popup text
            popup_text = f"""
            <b>Property ID:</b> {row.get('property_id', 'Unknown')}<br>
            <b>Risk Level:</b> {risk_label}<br>
            <b>Flood Depth:</b> {depth:.2f}m<br>
            <b>Impact Ratio:</b> {impact:.2%}<br>
            <b>Property Value:</b> £{row['value']:,.0f}<br>
            <b>Value at Risk:</b> £{row['value'] * impact:,.0f}
            """
            
            folium.CircleMarker(
                location=[row.geometry.y, row.geometry.x],
                radius=8,
                color=color,
                fill=True,
                fillOpacity=0.7,
                popup=folium.Popup(popup_text, max_width=300)
            ).add_to(m)
        
        # Add flood event center if using synthetic event
        if 'center_lat' in self.flood_event and 'center_lon' in self.flood_event:
            folium.Circle(
                location=[self.flood_event['center_lat'], self.flood_event['center_lon']],
                radius=self.flood_event.get('radius', 10000),
                color='blue',
                fill=True,
                fillOpacity=0.2,
                popup="Flood Event Center"
            ).add_to(m)
        
        # Add gauge locations if available
        if self.gauge_data is not None:
            for _, gauge in self.gauge_data.iterrows():
                folium.Marker(
                    location=[gauge['latitude'], gauge['longitude']],
                    popup=f"Gauge: {gauge.get('gauge_id', 'Unknown')}<br>Water Level: {gauge['water_level']:.2f}m",
                    icon=folium.Icon(color='blue', icon='tint')
                ).add_to(m)
        
        # Save map
        m.save(output_file)
        print(f"Interactive map saved to: {output_file}")
    
    def _create_static_plots(self, flood_depths, direct_impacts, output_file):
        """Create static matplotlib plots."""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
        
        # Plot 1: Flood depth histogram
        ax1.hist(flood_depths, bins=30, alpha=0.7, color='blue', edgecolor='black')
        ax1.set_xlabel('Flood Depth (m)')
        ax1.set_ylabel('Number of Properties')
        ax1.set_title('Distribution of Flood Depths')
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: Impact ratio histogram
        ax2.hist(direct_impacts, bins=30, alpha=0.7, color='red', edgecolor='black')
        ax2.set_xlabel('Impact Ratio')
        ax2.set_ylabel('Number of Properties')
        ax2.set_title('Distribution of Impact Ratios')
        ax2.grid(True, alpha=0.3)
        
        # Plot 3: Scatter plot of depth vs impact
        scatter = ax3.scatter(flood_depths, direct_impacts, 
                            c=self.properties['value'], 
                            cmap='viridis', alpha=0.6)
        ax3.set_xlabel('Flood Depth (m)')
        ax3.set_ylabel('Impact Ratio')
        ax3.set_title('Flood Depth vs Impact Ratio')
        ax3.grid(True, alpha=0.3)
        plt.colorbar(scatter, ax=ax3, label='Property Value (£)')
        
        # Plot 4: Risk level pie chart
        risk_levels = []
        for impact in direct_impacts:
            if impact > 0.6:
                risk_levels.append('High')
            elif impact > 0.3:
                risk_levels.append('Medium')
            elif impact > 0.1:
                risk_levels.append('Low')
            else:
                risk_levels.append('Minimal')
        
        risk_counts = pd.Series(risk_levels).value_counts()
        colors = ['red', 'orange', 'yellow', 'green']
        ax4.pie(risk_counts.values, labels=risk_counts.index, autopct='%1.1f%%',
                colors=colors[:len(risk_counts)])
        ax4.set_title('Properties by Risk Level')
        
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"Static plots saved to: {output_file}")


# Example usage and testing
if __name__ == "__main__":
    # This would typically be called by PortfolioFloodModel
    # Here's an example of how to use the FloodRiskModel directly
    
    import geopandas as gpd
    from shapely.geometry import Point
    
    # Create sample property data
    sample_properties = gpd.GeoDataFrame({
        'property_id': ['PROP_1', 'PROP_2', 'PROP_3'],
        'value': [500000, 750000, 300000],
        'property_type': ['residential', 'commercial', 'residential'],
        'floor_level_metres': [0.5, 0.0, 1.0],
        'elevation': [20.0, 18.0, 22.0],
        'geometry': [Point(-0.1, 51.5), Point(-0.15, 51.52), Point(-0.05, 51.48)]
    })
    
    # Create sample flood event
    flood_event = {
        'center_lat': 51.5,
        'center_lon': -0.1,
        'radius': 5000,
        'max_depth': 3.0
    }
    
    # Create and run model
    model = FloodRiskModel(sample_properties, flood_event)
    
    # Run analysis
    depths = model.calculate_flood_depths()
    impacts = model.calculate_direct_impacts(depths)
    portfolio_risk = model.simulate_portfolio_impact()
    advanced_metrics = model.calculate_advanced_metrics()
    
    print("Sample Flood Risk Analysis Results:")
    print(f"Flood depths: {depths}")
    print(f"Impact ratios: {impacts}")
    print(f"Portfolio VaR 95%: £{portfolio_risk['var_95']:,.2f}")
    print(f"Expected loss: £{advanced_metrics['expected_loss']:,.2f}")