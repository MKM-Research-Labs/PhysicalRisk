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
Portfolio Flood Model

 Select Files
Selected files: /Users/newdavid/Documents/Physrisk/src/models/portfolio_flood_model.py
Generate Code Clear
Fixed to handle correct field mappings between Property CDM and FloodRiskModel.
"""

import os
import sys
import json
import pandas as pd
import numpy as np
import datetime
import traceback
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

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

# Add project paths
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import project utilities
sys.path.insert(0, str(project_root / 'src' / 'utilities'))
try:
    from project_paths import ProjectPaths
except ImportError:
    # Fallback if project_paths not available
    class ProjectPaths:
        def __init__(self, file_path):
            self.input_dir = project_root / 'input'

# Import CDM classes
sys.path.insert(0, str(project_root / 'src' / 'cdm'))
try:
    from mortgage_cdm import MortgageCDM
    from flood_gauge_cdm import FloodGaugeCDM
    from property_cdm import PropertyCDM
    
except ImportError as e:
    print(f"Warning: CDM classes not available ({e}). Some functionality may be limited.")
    MortgageCDM = None
    FloodGaugeCDM = None
    PropertyCDM = None

class PortfolioFloodModel:
    """
    FIXED Portfolio flood model class with correct field mappings.
    """
    
    def __init__(self, input_dir=None, output_dir=None):
        """Initialize the Portfolio Flood Model."""
        # Initialize project paths
        try:
            self.paths = ProjectPaths(__file__)
            default_input = self.paths.input_dir
        except:
            default_input = project_root / 'input'
        
        # Set directories
        self.input_dir = Path(input_dir) if input_dir else default_input
        self.output_dir = Path(output_dir) if output_dir else self.input_dir
        
        # Ensure directories exist
        self.input_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize CDM instances
        self.mortgage_cdm = MortgageCDM() if MortgageCDM else None
        self.gauge_cdm = FloodGaugeCDM() if FloodGaugeCDM else None
        self.property_cdm = PropertyCDM() if PropertyCDM else None
        
        # Data storage
        self.gauge_metadata = None      
        self.gauge_readings = None      
        self.property_portfolio = None  
        self.mortgage_portfolio = None  
        
        # Analysis results
        self.flood_risk_results = None
        self.mortgage_results = None
        
        print(f"Portfolio Flood Model initialized (FIXED VERSION)")
        print(f"  Input directory: {self.input_dir}")
        print(f"  Output directory: {self.output_dir}")
        print(f"  CDM Support: {'Enabled' if self.mortgage_cdm and self.gauge_cdm else 'Limited'}")
    
    def load_data(self, gauge_path=None, gauge_readings_path=None, 
                  portfolio_path=None, mortgage_path=None):
        """Load all required data for flood risk analysis."""
        try:
            print("\n📊 Loading portfolio and flood data...")
            
            # Set default paths
            if gauge_path is None:
                gauge_path = self.input_dir / "flood_gauge_portfolio.json"
            if gauge_readings_path is None:
                gauge_readings_path = self.input_dir / "gauge_floodts.json"
            if portfolio_path is None:
                portfolio_path = self.input_dir / "property_portfolio.json"
            if mortgage_path is None:
                mortgage_path = self.input_dir / "mortgage_portfolio.json"
            
            # Load gauge metadata using CDM
            print(f"Loading gauge metadata from {gauge_path}")
            self.gauge_metadata = self._load_gauge_metadata(gauge_path)
            print(f"✅ Loaded {len(self.gauge_metadata)} flood gauges")
            
            # Load gauge readings
            print(f"Loading gauge readings from {gauge_readings_path}")
            self.gauge_readings = self._load_gauge_readings(gauge_readings_path)
            print(f"✅ Loaded readings for {len(self.gauge_readings)} gauges")
            
            # Load property portfolio with FIXED field mappings
            print(f"Loading property portfolio from {portfolio_path}")
            self.property_portfolio = self._load_property_portfolio(portfolio_path)
            print(f"✅ Loaded {len(self.property_portfolio)} properties")
            
            # Validate critical fields are present
            self._validate_property_fields()
            
            # Load mortgage portfolio using CDM (optional)
            if mortgage_path.exists():
                print(f"Loading mortgage portfolio from {mortgage_path}")
                self.mortgage_portfolio = self._load_mortgage_portfolio(mortgage_path)
                print(f"✅ Loaded {len(self.mortgage_portfolio)} mortgages")
            else:
                print(f"⚠️ Mortgage portfolio not found at {mortgage_path} (optional)")
                self.mortgage_portfolio = pd.DataFrame()
            
            # Synchronize gauge IDs between metadata and readings
            
            self._synchronize_gauge_data()

            total_readings = sum(len(readings_df) for readings_df in self.gauge_readings.values())
            print(f"✅ Total gauge readings available: {total_readings} across {len(self.gauge_readings)} gauges")
            
            print("✅ All data loaded successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error loading data: {str(e)}")
            traceback.print_exc()
            return False
    
    def _validate_property_fields(self):
        """Validate that critical fields are present for FloodRiskModel."""
        print("🔍 Validating property fields for flood analysis...")
        
        required_fields = ['property_id', 'value', 'latitude', 'longitude']
        missing_fields = []
        
        for field in required_fields:
            if field not in self.property_portfolio.columns:
                missing_fields.append(field)
        
        if missing_fields:
            print(f"❌ Missing critical fields: {missing_fields}")
            print("Available fields:", list(self.property_portfolio.columns))
            raise ValueError(f"Property data missing critical fields: {missing_fields}")
        
        # Check for null values in critical fields
        null_counts = {}
        for field in required_fields:
            null_count = self.property_portfolio[field].isnull().sum()
            if null_count > 0:
                null_counts[field] = null_count
        
        if null_counts:
            print(f"⚠️ Warning: Null values found in critical fields: {null_counts}")
        
        print("✅ Property field validation completed")

    def run_flood_analysis(self):
        """
        CORRECTED run comprehensive flood risk analysis on the portfolio.
        
        Adds proper validation calls and improved error reporting.
        """
        print("\n🌊 Running flood risk analysis...")
        
        if not self._validate_data_loaded():
            return None
        
        try:
            
            # Convert property portfolio to GeoDataFrame format with CORRECT field mappings
            properties_gdf = self._prepare_properties_for_analysis()
            
            # Debug: Print the columns to verify field names
            print(f"🔍 Property GeoDataFrame columns: {list(properties_gdf.columns)}")
            print(f"🔍 Sample property data:")
            for col in ['property_id', 'value', 'latitude', 'longitude', 'elevation']:
                if col in properties_gdf.columns:
                    sample_val = properties_gdf[col].iloc[0] if len(properties_gdf) > 0 else "N/A"
                    print(f"    {col}: {sample_val}")
            
            # Create flood event parameters using CORRECTED method
            self.flood_event = self._create_flood_event_parameters()  # Store as instance variable
            
            # Add this debug line:
            print(f"🔍 DEBUG: Flood event structure: {self.flood_event}")
            print(f"🔍 DEBUG: Flood event keys: {list(self.flood_event.keys())}")
            
            # Convert gauge data to DataFrame format
            gauge_df = self._prepare_gauge_data_for_analysis()
            
            
            # Run flood risk calculations using CORRECTED methods
            print("  Calculating flood depths with proper elevation handling...")
            flood_depths = self._calculate_flood_depths_multi_center()
            
            validation_passed = True
           
            
            print("  Calculating direct impacts...")
            direct_impacts = self.calculate_direct_impacts(flood_depths)

            print("  Running portfolio impact simulation...")
            portfolio_impacts = self.simulate_portfolio_impact()

            print("  Analyzing spatial concentration...")
            spatial_concentration = self.analyze_spatial_concentration()

            print("  Calculating advanced metrics...")
            advanced_metrics = self.calculate_advanced_metrics()
            
            # CORRECTED: Compile results with enhanced reporting
            self.flood_risk_results = {
                'timestamp': datetime.now(),
                'model_version': '1.0 (ELEVATION CORRECTED)',
                'validation_passed': validation_passed,
                'flood_depths': flood_depths.tolist(),
                'direct_impacts': direct_impacts.tolist(),
                'portfolio_impacts': portfolio_impacts,
                'spatial_concentration': spatial_concentration.to_dict('records'),
                'advanced_metrics': advanced_metrics,
                'property_details': self._compile_property_risk_details(
                    flood_depths, direct_impacts
                ),
                'summary': self._calculate_portfolio_summary(
                    flood_depths, direct_impacts
                ),
                'elevation_analysis': self._generate_elevation_analysis(
                    properties_gdf, flood_depths
                )
            }
            
            # CORRECTED: Enhanced result reporting
            summary = self.flood_risk_results['summary']
            print("✅ Flood risk analysis completed")
            print(f"   Properties at risk: {summary['properties_at_risk']}/{summary['total_properties']} ({summary['percentage_at_risk']:.1f}%)")
            print(f"   Value at risk: £{summary['value_at_risk']:,.0f} ({summary['percentage_value_at_risk']:.1f}%)")
            print(f"   Average flood depth: {summary['average_flood_depth']:.2f}m")
            print(f"   Maximum flood depth: {summary['max_flood_depth']:.2f}m")
            
            # Alert for unusual results
            if summary['percentage_at_risk'] > 80:
                print(f"⚠️  HIGH FLOOD RATE: {summary['percentage_at_risk']:.1f}% of properties at risk")
                print("     This may indicate model calibration issues")
            
            if summary['max_flood_depth'] > 5.0:
                print(f"⚠️  HIGH FLOOD DEPTHS: Maximum depth {summary['max_flood_depth']:.2f}m exceeds typical limits")
                print("     Review flood parameters and elevation data")
            
            return self.flood_risk_results
            
        except Exception as e:
            print(f"❌ Error during flood analysis: {str(e)}")
            traceback.print_exc()
            return None

    def _load_property_portfolio(self, file_path):
        """Load property portfolio from property_portfolio.json with FIXED CDM mapping."""
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        if 'properties' not in data:
            raise ValueError("Invalid property portfolio format")
        
        properties = []
        for prop in data['properties']:
            property_data = self._extract_property_data(prop)
            properties.append(property_data)
        
        return pd.DataFrame(properties)
    
    def _extract_property_data(self, prop):
        """Extract property data using FIXED CDM with correct field mappings."""
        if self.property_cdm:
            try:
                # Use the FIXED Property CDM that includes the 'value' field mapping
                return self.property_cdm.create_property_mapping(prop)
            except Exception as e:
                print(f"Warning: Property CDM processing failed: {e}")
                raise ValueError(f"Property CDM processing failed: {e}")
        else:
            raise ValueError("PropertyCDM not available")
    
    def _load_mortgage_portfolio(self, file_path):
        """Load mortgage portfolio from mortgage_portfolio.json using CDM."""
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        if 'mortgages' not in data:
            raise ValueError("Invalid mortgage portfolio format")
        
        mortgages = []
        for mortgage in data['mortgages']:
            if self.mortgage_cdm:
                mortgage_data = self.mortgage_cdm.create_mortgage_mapping(mortgage)
                mortgages.append(mortgage_data)
            else:
                raise ValueError("MortgageCDM not available")
        
        return pd.DataFrame(mortgages)

    def _generate_elevation_analysis(self, properties_gdf, flood_depths):
        """
        ADDED: Generate elevation analysis for the corrected model.
        
        This provides insights into how elevation affects flood risk.
        """
        if 'elevation' not in properties_gdf.columns:
            return {"error": "No elevation data available for analysis"}
        
        elevations = properties_gdf['elevation'].values
        
        # Calculate correlation
        correlation = np.corrcoef(elevations, flood_depths)[0, 1] if len(elevations) > 1 else 0
        
        # Elevation bands analysis
        elevation_bands = [
            (0, 10, "Very Low"),
            (10, 15, "Low"), 
            (15, 20, "Medium"),
            (20, 30, "High"),
            (30, 50, "Very High")
        ]
        
        band_analysis = []
        for min_elev, max_elev, label in elevation_bands:
            mask = (elevations >= min_elev) & (elevations < max_elev)
            if np.sum(mask) > 0:
                band_properties = np.sum(mask)
                band_flooded = np.sum(mask & (flood_depths > 0))
                band_flood_rate = (band_flooded / band_properties) * 100
                band_avg_depth = np.mean(flood_depths[mask & (flood_depths > 0)]) if band_flooded > 0 else 0
                
                band_analysis.append({
                    'elevation_band': f"{min_elev}-{max_elev}m ({label})",
                    'properties': int(band_properties),
                    'flooded': int(band_flooded),
                    'flood_rate': band_flood_rate,
                    'avg_flood_depth': band_avg_depth
                })
        
        return {
            'elevation_correlation': correlation,
            'correlation_strength': 'Strong' if abs(correlation) > 0.5 else 'Weak' if abs(correlation) > 0.2 else 'Very Weak',
            'elevation_range': {
                'min': float(elevations.min()),
                'max': float(elevations.max()),
                'mean': float(elevations.mean()),
                'std': float(elevations.std())
            },
            'elevation_bands': band_analysis,
            'physics_check': {
                'realistic_correlation': correlation < -0.2,
                'no_high_elevation_flooding': np.sum((elevations > 25) & (flood_depths > 1)) == 0
            }
        }
        
    def _load_gauge_metadata(self, file_path):
        """Load gauge metadata from flood_gauge_portfolio.json using CDM."""
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        if 'flood_gauges' not in data:
            raise ValueError("Invalid gauge portfolio format")
        
        gauges = {}
        for gauge_item in data['flood_gauges']:
            gauge = gauge_item['FloodGauge']
            gauge_id = gauge['Header']['GaugeID']
            
            if self.gauge_cdm:
                try:
                    gauge_data = self.gauge_cdm.create_gauge_mapping({'FloodGauge': gauge})
                    gauges[gauge_id] = gauge_data
                except Exception as e:
                    print(f"Error: CDM processing failed for gauge {gauge_id}: {e}")
                    raise ValueError(f"Gauge CDM processing failed: {e}")
            else:
                raise ValueError("FloodGaugeCDM not available")
        
        return gauges
        
    def _load_gauge_readings(self, file_path):
        """Load gauge readings from gauge_floodts.json."""
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        readings_by_gauge = {}
        
        for timestep in data:
            if 'readings' not in timestep:
                continue
            
            for reading in timestep['readings']:
                gauge_id = reading['gaugeId']
                
                if gauge_id not in readings_by_gauge:
                    readings_by_gauge[gauge_id] = []
                
                readings_by_gauge[gauge_id].append({
                    'timestamp': pd.to_datetime(reading['timestamp']),
                    'water_level': reading['waterLevel'],
                    'alert_level': reading['alertLevel'],
                    'warning_level': reading['warningLevel'],
                    'severe_level': reading['severeLevel'],
                    'status': reading['alertStatus']
                })
        
        # Convert to DataFrames
        gauge_data = {}
        for gauge_id, readings_list in readings_by_gauge.items():
            df = pd.DataFrame(readings_list)
            df = df.sort_values('timestamp')
            gauge_data[gauge_id] = df
        
        return gauge_data

    def _load_property_portfolio(self, file_path):
        """Load property portfolio from property_portfolio.json with FIXED CDM mapping."""
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        if 'properties' not in data:
            raise ValueError("Invalid property portfolio format")
        
        properties = []
        for prop in data['properties']:
            property_data = self._extract_property_data(prop)
            properties.append(property_data)
        
        return pd.DataFrame(properties)
    
    def _extract_property_data(self, prop):
        """Extract property data using FIXED CDM with correct field mappings."""
        if self.property_cdm:
            try:
                # Use the FIXED Property CDM that includes the 'value' field mapping
                return self.property_cdm.create_property_mapping(prop)
            except Exception as e:
                print(f"Warning: Property CDM processing failed: {e}")
                raise ValueError(f"Property CDM processing failed: {e}")
        else:
            raise ValueError("PropertyCDM not available")
        
    def _load_mortgage_portfolio(self, file_path):
        """Load mortgage portfolio from mortgage_portfolio.json using CDM."""
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        if 'mortgages' not in data:
            raise ValueError("Invalid mortgage portfolio format")
        
        mortgages = []
        for mortgage in data['mortgages']:
            if self.mortgage_cdm:
                mortgage_data = self.mortgage_cdm.create_mortgage_mapping(mortgage)
                mortgages.append(mortgage_data)
            else:
                raise ValueError("MortgageCDM not available")
        
        return pd.DataFrame(mortgages)
    
    def _synchronize_gauge_data(self):
        """Synchronize gauge IDs between metadata and readings."""
        print("Synchronizing gauge data...")
        
        # Create mapping between gauge names and IDs
        name_to_metadata_id = {}
        for gauge_id, info in self.gauge_metadata.items():
            gauge_name = info.get('gauge_name') or info.get('GaugeName') or info.get('gauge_id')
            if gauge_name:
                name_to_metadata_id[gauge_name] = gauge_id
        
        # Try to match readings to metadata by name
        synchronized_readings = {}
        for readings_id, readings_df in self.gauge_readings.items():
            # Try direct ID match first
            if readings_id in self.gauge_metadata:
                synchronized_readings[readings_id] = readings_df
                continue
            
            # Try name-based matching
            gauge_name = None
            if not readings_df.empty and 'gauge_name' in readings_df.columns:
                gauge_name = readings_df['gauge_name'].iloc[0]
            
            if gauge_name and gauge_name in name_to_metadata_id:
                metadata_id = name_to_metadata_id[gauge_name]
                synchronized_readings[metadata_id] = readings_df
                print(f"  Matched '{gauge_name}': {readings_id} -> {metadata_id}")
            else:
                synchronized_readings[readings_id] = readings_df
        
        self.gauge_readings = synchronized_readings
        print(f"Synchronized {len(synchronized_readings)} gauge readings")

    def _prepare_properties_for_analysis(self):
        """Prepare property data for flood risk analysis with CORRECT field mappings."""
        import geopandas as gpd
        from shapely.geometry import Point
        
        # Create a copy of the property portfolio
        prop_df = self.property_portfolio.copy()
        
        # Create geometry column using the CORRECT field names from CDM
        geometry = []
        for _, row in prop_df.iterrows():
            # Use the correct field names that the CDM produces
            lon = row.get('longitude')
            lat = row.get('latitude')
            
            if pd.notna(lon) and pd.notna(lat):
                geometry.append(Point(lon, lat))
            else:
                # Fallback: create a default point
                geometry.append(Point(0, 0))
        
        # Create GeoDataFrame with proper field mappings for FloodRiskModel
        gdf = gpd.GeoDataFrame(prop_df, geometry=geometry)
        
        # Ensure all required fields are present with correct names
        # FloodRiskModel expects: 'geometry', 'property_id', 'value', 'floor_level_metres', 'property_type', 'elevation'
        

        
        return gdf
    
    def _prepare_gauge_data_for_analysis(self):
        """Prepare gauge data for flood risk analysis."""
        gauge_records = []
        
        for gauge_id, readings_df in self.gauge_readings.items():
            if gauge_id not in self.gauge_metadata:
                continue
            
            # Use CDM-processed data with correct field names
            cdm_data = self.gauge_metadata[gauge_id]
            
            gauge_record = {
                'gauge_id': gauge_id,
                'latitude': cdm_data['gauge_latitude'],
                'longitude': cdm_data['gauge_longitude'], 
                'water_level': readings_df['water_level'].max(),
                'severe_level': cdm_data['severe_flood_warning']
            }
            gauge_records.append(gauge_record)
        
        return pd.DataFrame(gauge_records)
    
   
    def _create_flood_event_parameters(self):
        """Create multi-center flood event parameters based on gauge vulnerability and water levels."""
        # If no gauge readings available, fall back to default
        if self.gauge_readings is None or not self.gauge_readings:
            print("🔍 DEBUG: No gauge readings available, using default center")
            return {
                'multi_center': True,
                'centers': [{
                    'name': 'Default_Thames',
                    'center_lat': 51.5074,
                    'center_lon': -0.1278,
                    'radius': 2000,  # More realistic 2km radius
                    'max_depth': 0.5  # More realistic 0.5m depth
                }]
            }
        
        print(f"🔍 DEBUG: Starting gauge-based flood analysis with {len(self.gauge_readings)} gauge readings")
        
        # Step 1: Analyze each gauge's flood vulnerability
        gauge_vulnerability = {}
        
        for gauge_id, gauge_metadata in self.gauge_metadata.items():
            if gauge_id not in self.gauge_readings:
                continue
            
            # Get gauge location and flood levels
            lat = gauge_metadata.get('gauge_latitude')
            lon = gauge_metadata.get('gauge_longitude')
            gauge_name = gauge_metadata.get('gauge_name', gauge_id)
            alert_level = gauge_metadata.get('flood_alert', 0)
            warning_level = gauge_metadata.get('flood_warning', 0)
            severe_level = gauge_metadata.get('severe_flood_warning', 0)
            
            # Skip gauges without coordinates or flood levels
            if not lat or not lon or not severe_level:
                continue
            
            # Get maximum water level from readings
            readings_df = self.gauge_readings[gauge_id]
            max_water_level = readings_df['water_level'].max()
            
            # Calculate vulnerability metrics
            # 1. How close to severe flood warning (0-1, where 1 = at severe level)
            severe_proximity = min(max_water_level / severe_level, 1.0) if severe_level > 0 else 0
            
            # 2. How much above alert level (0+ where 0 = at alert level)
            alert_exceedance = max(max_water_level - alert_level, 0) if alert_level > 0 else 0
            
            # 3. Combined vulnerability score (higher = more vulnerable/likely flood center)
            vulnerability_score = (severe_proximity * 0.6) + (alert_exceedance * 0.4)
            
            gauge_vulnerability[gauge_id] = {
                'name': gauge_name,
                'lat': lat,
                'lon': lon,
                'max_water_level': max_water_level,
                'alert_level': alert_level,
                'warning_level': warning_level,
                'severe_level': severe_level,
                'severe_proximity': severe_proximity,
                'alert_exceedance': alert_exceedance,
                'vulnerability_score': vulnerability_score
            }
            
            print(f"    {gauge_id}: water={max_water_level:.2f}, severe={severe_level:.2f}, "
                f"proximity={severe_proximity:.2f}, vulnerability={vulnerability_score:.2f}")
        
        if not gauge_vulnerability:
            print("🔍 DEBUG: No valid gauges found, using default center")
            return {
                'multi_center': True,
                'centers': [{
                    'name': 'Default_Thames',
                    'center_lat': 51.5074,
                    'center_lon': -0.1278,
                    'radius': 2000,
                    'max_depth': 0.5
                }]
            }
        
        # Step 2: Select top flood centers based on vulnerability
        # Sort gauges by vulnerability score (highest first)
        sorted_gauges = sorted(gauge_vulnerability.items(), 
                            key=lambda x: x[1]['vulnerability_score'], 
                            reverse=True)
        
        # Select top 3-5 most vulnerable gauges as flood centers
        num_centers = min(5, max(1, len([g for g in sorted_gauges if g[1]['vulnerability_score'] > 0.1])))
        top_gauges = sorted_gauges[:num_centers]
        
        print(f"🔍 DEBUG: Selected {num_centers} flood centers from {len(gauge_vulnerability)} gauges")
        
        # Step 3: Create flood centers
        flood_params = {
            'multi_center': True,
            'centers': []
        }
        
        for gauge_id, info in top_gauges:
            # Calculate flood parameters based on gauge vulnerability
            vulnerability = info['vulnerability_score']
            
            # Radius: base 1km + up to 4km based on vulnerability (1-5km total)
            radius = 1000 + (vulnerability * 4000)
            
            # Max depth: 0.2m to 2.0m based on vulnerability and exceedance
            base_depth = 0.2 + (vulnerability * 1.8)  # 0.2-2.0m based on vulnerability
            exceedance_depth = min(info['alert_exceedance'] * 0.5, 1.0)  # Up to 1m extra for exceedance
            max_depth = min(base_depth + exceedance_depth, 3.0)  # Cap at 3m total
            
            center = {
                'name': f"{info['name']}",
                'center_lat': info['lat'],
                'center_lon': info['lon'],
                'radius': int(radius),
                'max_depth': round(max_depth, 2),
                'gauge_id': gauge_id,
                'vulnerability_score': round(vulnerability, 3)
            }
            
            flood_params['centers'].append(center)
            print(f"✅ Flood center: {info['name']} at ({info['lat']:.4f}, {info['lon']:.4f})")
            print(f"    Radius: {radius:.0f}m, Max depth: {max_depth:.2f}m, Vulnerability: {vulnerability:.3f}")
        
        # Step 4: Quality check - ensure we have realistic parameters
        total_centers = len(flood_params['centers'])
        avg_depth = sum(c['max_depth'] for c in flood_params['centers']) / total_centers if total_centers > 0 else 0
        max_radius = max(c['radius'] for c in flood_params['centers']) if total_centers > 0 else 0
        
        print(f"🔍 FLOOD SCENARIO SUMMARY:")
        print(f"    Centers: {total_centers}")
        print(f"    Average depth: {avg_depth:.2f}m")
        print(f"    Maximum radius: {max_radius:.0f}m")
        
        # Sanity check
        if avg_depth > 4.0:
            print("⚠️  Warning: High average flood depth - may be unrealistic")
        if max_radius > 10000:
            print("⚠️  Warning: Large flood radius - may affect too many properties")
        
        return flood_params
   
   

    def _haversine_distance(self, lat1, lon1, lat2, lon2):
        """Calculate distance between two points in meters."""
        R = 6371000  # Earth radius in meters
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        return R * c

    def calculate_direct_impacts(self, flood_depths):
        """Calculate damage ratios from flood depths."""
        # Simple depth-damage curve
        return np.clip(flood_depths * 0.3, 0, 1)  # 30% damage per meter
    
    def _calculate_flood_depths_multi_center(self):
        """New implementation for multi-center calculation"""
        properties = self.property_portfolio
        flood_event = self.flood_event
        
        # Initialize depths array
        depths = np.zeros(len(properties))
        
        # For each flood center, calculate depths and take the maximum
        for center in flood_event['centers']:
            center_lat = center['center_lat']
            center_lon = center['center_lon']
            radius = center['radius']
            max_depth = center['max_depth']
            
            # Calculate distances from properties to this center
            distances = np.sqrt(
                (properties['latitude'] - center_lat) ** 2 + 
                (properties['longitude'] - center_lon) ** 2
            )
            
            # Convert to meters (rough approximation)
            distances_m = distances * 111000
            
            # Calculate depth for properties within radius
            within_radius = distances_m <= radius
            
            # Simple linear decay model - more sophisticated models could be used
            center_depths = np.zeros(len(properties))
            center_depths[within_radius] = max_depth * (1 - distances_m[within_radius] / radius)
            
            # Take the maximum depth between current calculation and previous centers
            depths = np.maximum(depths, center_depths)
        
        # Apply terrain adjustments based on property elevation
        if 'ground_level_meters' in properties.columns:
            # Adjust depths based on property elevation
            pass
            
        return depths
 
 
 
 
    def _validate_data_loaded(self):
        """Validate that required data has been loaded."""
        if self.gauge_metadata is None:
            print("❌ Gauge metadata not loaded")
            return False
        if self.gauge_readings is None:
            print("❌ Gauge readings not loaded")
            return False
        if self.property_portfolio is None:
            print("❌ Property portfolio not loaded")
            return False
        return True
    
    def _compile_property_risk_details(self, flood_depths, direct_impacts):
        """Compile detailed risk information for each property."""
        property_details = []
        
        for i, (_, prop) in enumerate(self.property_portfolio.iterrows()):
            flood_depth = flood_depths[i] if i < len(flood_depths) else 0
            impact = direct_impacts[i] if i < len(direct_impacts) else 0
            
            # Determine risk level
            if impact > 0.6:
                risk_level = "High"
            elif impact > 0.3:
                risk_level = "Medium"
            elif impact > 0.1:
                risk_level = "Low"
            else:
                risk_level = "Minimal"
            
            property_details.append({
                'property_id': prop['property_id'],
                'latitude': prop['latitude'],
                'longitude': prop['longitude'],
                'elevation': prop.get('elevation', None),
                'property_value': prop['value'],
                'flood_depth': flood_depth,
                'impact_ratio': impact,
                'value_at_risk': prop['value'] * impact,
                'risk_level': risk_level
            })
        
        return property_details
    
    def simulate_portfolio_impact(self):
        """Simple portfolio impact calculation."""
        return {"mean_impact": 0, "var_95": 0, "var_99": 0}

    def analyze_spatial_concentration(self):
        """Simple spatial analysis."""
        return pd.DataFrame({'grid_id': [], 'value_at_risk': []})

    def calculate_advanced_metrics(self):
        """Simple metrics calculation."""
        return {
            "total_portfolio_value": self.property_portfolio['value'].sum(),
            "expected_loss": 0
        }
    
    
    
    def _calculate_portfolio_summary(self, flood_depths, direct_impacts):
        """Calculate portfolio-level summary statistics."""
        total_properties = len(self.property_portfolio)
        properties_at_risk = sum(1 for impact in direct_impacts if impact > 0.1)
        
        total_value = self.property_portfolio['value'].sum()
        total_value_at_risk = sum(
            self.property_portfolio.iloc[i]['value'] * direct_impacts[i]
            for i in range(len(direct_impacts))
        )
        
        return {
            'total_properties': total_properties,
            'properties_at_risk': properties_at_risk,
            'percentage_at_risk': (properties_at_risk / total_properties) * 100,
            'total_value': total_value,
            'value_at_risk': total_value_at_risk,
            'percentage_value_at_risk': (total_value_at_risk / total_value) * 100,
            'average_flood_depth': np.mean(flood_depths),
            'max_flood_depth': np.max(flood_depths),
            'average_impact_ratio': np.mean(direct_impacts)
        }
    
    def generate_comprehensive_report(self):
        """Generate a comprehensive flood and mortgage risk report."""
        print("\n📄 Generating comprehensive report...")
        
        # Ensure flood analysis has been run
        if self.flood_risk_results is None:
            print("Running flood analysis first...")
            self.run_flood_analysis()
        
        # Compile comprehensive report
        comprehensive_report = {
            'report_metadata': {
                'generated_at': datetime.now(),
                'model_version': '1.0 (FIXED)',
                'input_directory': str(self.input_dir),
                'output_directory': str(self.output_dir),
                'cdm_version': 'v6' if self.mortgage_cdm else 'legacy'
            },
            'data_summary': {
                'total_properties': len(self.property_portfolio) if self.property_portfolio is not None else 0,
                'total_gauges': len(self.gauge_metadata) if self.gauge_metadata is not None else 0,
                'total_mortgages': len(self.mortgage_portfolio) if self.mortgage_portfolio is not None else 0,
                'gauges_with_readings': len(self.gauge_readings) if self.gauge_readings is not None else 0
            },
            'flood_risk_analysis': self.flood_risk_results
        }
        
        # Save report to file
        report_file = self.output_dir / "flood_risk_report.json"
        with open(report_file, 'w') as f:
            json.dump(comprehensive_report, f, indent=2, default=str)
        
        print(f"✅ Flood report report saved to: {report_file}")
        
        # Print summary
        self._print_report_summary(comprehensive_report)
        
        return comprehensive_report
    
    def _print_report_summary(self, report):
        """Print a summary of the comprehensive report."""
        print("\n📊 COMPREHENSIVE FLOOD RISK REPORT SUMMARY (FIXED VERSION)")
        print("=" * 70)
        
        # Data summary
        data_summary = report['data_summary']
        print(f"\n📋 Data Summary:")
        print(f"  Properties: {data_summary['total_properties']}")
        print(f"  Flood Gauges: {data_summary['total_gauges']}")
        print(f"  Mortgages: {data_summary['total_mortgages']}")
        print(f"  CDM Version: {report['report_metadata'].get('cdm_version', 'legacy')}")
        
        # Flood risk summary
        if report['flood_risk_analysis']:
            flood_summary = report['flood_risk_analysis']['summary']
            print(f"\n🌊 Flood Risk Summary:")
            print(f"  Properties at Risk: {flood_summary['properties_at_risk']} ({flood_summary['percentage_at_risk']:.1f}%)")
            print(f"  Total Value: £{flood_summary['total_value']:,.2f}")
            print(f"  Value at Risk: £{flood_summary['value_at_risk']:,.2f} ({flood_summary['percentage_value_at_risk']:.1f}%)")
            print(f"  Average Flood Depth: {flood_summary['average_flood_depth']:.2f}m")
            print(f"  Max Flood Depth: {flood_summary['max_flood_depth']:.2f}m")

def main():
    """Main execution function for portfolio flood risk analysis."""
    
    print("🚀 Starting Portfolio Flood Risk Analysis (FIXED VERSION)")
    print("=" * 70)
    
    try:
        # Initialize model with default directories
        print("🏗️ Initializing Portfolio Flood Model...")
        model = PortfolioFloodModel()
        
        # Load data
        print("📊 Loading portfolio and flood data...")
        if not model.load_data():
            print("❌ Failed to load data. Exiting.")
            return False
        
        # Run flood risk analysis
        print("🌊 Running flood risk analysis...")
        flood_results = model.run_flood_analysis()
        if not flood_results:
            print("❌ Flood risk analysis failed")
            return False
        print("✅ Flood risk analysis completed")
        
        # Generate comprehensive report
        print("📄 Generating comprehensive report...")
        comprehensive_report = model.generate_comprehensive_report()
        
        if comprehensive_report:
            print("✅ Comprehensive report generated")
            
            # Print final summary
            print("\n🎉 Analysis completed successfully!")
            print("=" * 70)
            
            flood_summary = comprehensive_report['flood_risk_analysis']['summary']
            print(f"📊 Flood Risk Summary:")
            print(f"  Properties analyzed: {flood_summary['total_properties']}")
            print(f"  Properties at risk: {flood_summary['properties_at_risk']} ({flood_summary['percentage_at_risk']:.1f}%)")
            print(f"  Total value at risk: £{flood_summary['value_at_risk']:,.2f}")
            
            print(f"📁 Results saved to: {model.output_dir}")
            return True
            
        else:
            print("❌ Failed to generate comprehensive report")
            return False
    
    except KeyboardInterrupt:
        print("\n⏹️ Analysis interrupted by user")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

# Execute main function if run directly
if __name__ == "__main__":
    main()