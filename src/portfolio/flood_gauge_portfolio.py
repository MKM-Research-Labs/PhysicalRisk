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
Enhanced Flood Gauge Portfolio Generator with detailed processing information.

This module generates synthetic flood gauge data based on the FloodGaugeCDM schema,
focusing on Thames river locations
"""

import os
import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
import random
import sys
import numpy as np


class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle datetime objects."""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)

# Fix the Python path to find project modules
current_file = Path(__file__).resolve()
# Navigate up to find project root (assuming we're in src/portfolio or similar)
project_root = current_file.parent.parent

# Add project root to Python's path
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Now import modules using absolute imports
from utilities.project_paths import ProjectPaths

paths = ProjectPaths(__file__)
paths.setup_import_paths()

from cdm.flood_gauge_cdm import FloodGaugeCDM

from utilities.elevation import init_elevation_data, get_elevation, THAMES_POINTS, LONDON_AREAS

# Initialize project paths
paths = ProjectPaths(__file__)

class FloodGaugePortfolioGenerator:
    """Enhanced Flood Gauge Portfolio Generator with detailed processing information."""
    
    def __init__(self, output_dir: Union[str, Path], verbose: bool = True):
        """
        Initialize the Enhanced Flood Gauge Portfolio Generator.
        
        Args:
            output_dir: Directory to save generated files
            verbose: Enable detailed processing information
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.flood_gauge_cdm = FloodGaugeCDM()
        self.verbose = verbose
        self.dem_data = None
        
        # Processing statistics
        self.processing_stats = {
            'total_gauges': 0,
            'successful_gauges': 0,
            'failed_gauges': 0,
            'elevation_successes': 0,
            'elevation_failures': 0,
            'coordinate_conversions': 0,
            'start_time': None,
            'end_time': None
        }
        
        # Gauge types with weights
        self.gauge_types = [
            "Staff gauge", "Wire-weight gauge", "Shaft encoder", 
            "Bubbler system", "Pressure transducer", "Radar gauge", 
            "Ultrasonic gauge"
        ]
        self.gauge_type_weights = [0.05, 0.05, 0.15, 0.1, 0.2, 0.25, 0.2]
        
        # Gauge owners
        self.gauge_owners = [
            "Environment Agency", "Thames Water", "Local Authority", 
            "Met Office", "Research Institution"
        ]
        
        # UK flood decision bodies
        self.uk_decision_bodies = [
            "Environment Agency", "Department for Environment, Food and Rural Affairs",
            "Natural Resources Wales", "Scottish Environment Protection Agency"
        ]
        
        # Data curators
        self.data_curators = [
            "Environment Agency", "Met Office", "CEDA Archive", 
            "British Hydrological Society", "Centre for Ecology & Hydrology"
        ]
        
        # Manufacturer names
        self.manufacturers = [
            "OTT HydroMet", "Campbell Scientific", "Vaisala", "Sutron", 
            "YSI", "In-Situ Inc.", "Stevens Water", "SEBA Hydrometrie"
        ]
        
    def log(self, message: str, level: str = "INFO"):
        """Log processing information if verbose mode is enabled."""
        if self.verbose:
            timestamp = datetime.now().strftime("%H:%M:%S")
            prefix = {
                "INFO": "ℹ️ ",
                "SUCCESS": "✅ ",
                "WARNING": "⚠️ ",
                "ERROR": "❌ ",
                "DEBUG": "🔍 "
            }.get(level, "📝 ")
            print(f"[{timestamp}] {prefix}{message}")
    
    def generate(self, count: int = 40) -> Dict:
        """
        Generate synthetic flood gauge data directly from Thames points.
        
        Args:
            count: Number of flood gauges to generate
            
        Returns:
            Dictionary containing generated data, file path, and processing information
        """
        self.processing_stats['start_time'] = datetime.now()
        self.processing_stats['total_gauges'] = count
        
        self.log("="*60, "INFO")
        self.log("🌊 ENHANCED FLOOD GAUGE PORTFOLIO GENERATOR", "INFO")
        self.log("="*60, "INFO")
        self.log(f"Target gauge count: {count}", "INFO")
        self.log(f"Output directory: {self.output_dir}", "INFO")
        
        # Validate gauge count against available Thames points
        max_gauges = len(THAMES_POINTS)
        if count < 1:
            self.log(f"Invalid gauge count: {count}. Must be at least 1.", "ERROR")
            raise ValueError(f"Gauge count must be at least 1, got {count}")
        
        if count > max_gauges:
            self.log(f"Requested {count} gauges but only {max_gauges} Thames points available", "WARNING")
            self.log(f"Reducing gauge count to {max_gauges}", "INFO")
            count = max_gauges
            self.processing_stats['total_gauges'] = count
        
        self.log(f"Generating {count} gauges from {max_gauges} available Thames points", "INFO")
        
        # Use Thames points directly for gauge locations
        self.log("Creating gauge locations from Thames points...", "INFO")
        selected_locations = []
        
        for i in range(count):
            lat, lon, elevation = THAMES_POINTS[i]
            area_index = i % len(LONDON_AREAS)
            area_name = LONDON_AREAS[area_index]
            
            location = {
                "lat": lat,
                "lon": lon,
                "name": f"{area_name}_Point_{i}",
                "distance_to_thames": 0,  # Always 0 for gauges on Thames
                "elevation": elevation    # Use elevation from THAMES_POINTS
            }
            selected_locations.append(location)
            
            if i < 5:  # Log first 5 coordinates
                self.log(f"Thames point {i}: {area_name} at ({lat:.5f}, {lon:.5f}), elevation: {elevation:.1f}m", "DEBUG")
        
        self.log(f"Selected {len(selected_locations)} gauge locations directly from Thames points", "SUCCESS")
        
        # Access the schema from the FloodGaugeCDM instance
        schema = self.flood_gauge_cdm.schema
        self.log("Schema loaded from FloodGaugeCDM", "DEBUG")
        
        # Generate gauges
        self.log("Starting gauge generation process...", "INFO")
        gauges = []
        gauge_ids = []
        
        for i, location in enumerate(selected_locations):
            self.log(f"Generating gauge {i+1}/{count} at {location['name']}", "INFO")
            try:
                # Generate gauge using helper methods
                gauge_data, gauge_id = self._generate_single_gauge(i, schema, location)
                gauges.append(gauge_data)
                gauge_ids.append(gauge_id)
                self.processing_stats['successful_gauges'] += 1
                
                # Log gauge details
                gauge_name = gauge_data.get('FloodGauge', {}).get('Header', {}).get('GaugeName', 'Unknown')
                elevation = location['elevation']
                self.log(f"✓ Gauge {i+1} created: {gauge_name} (ID: {gauge_id[:12]}...) at {elevation:.1f}m", "SUCCESS")
                
            except Exception as e:
                self.log(f"Failed to generate gauge {i+1}: {str(e)}", "ERROR")
                self.processing_stats['failed_gauges'] += 1
                continue
        
        # Save to JSON file
        self.log("Saving gauge data to JSON file...", "INFO")
        output_path = self.output_dir / "flood_gauge_portfolio.json"
        try:
            # Create processing stats copy with serializable datetime objects
            serializable_stats = self.processing_stats.copy()
            if serializable_stats.get('start_time'):
                serializable_stats['start_time'] = serializable_stats['start_time'].isoformat()
            if serializable_stats.get('end_time'):
                serializable_stats['end_time'] = serializable_stats['end_time'].isoformat()
            
            output_data = {
                "flood_gauges": gauges,
                "generation_metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "generator_version": "Simplified v2.0",
                    "total_gauges_generated": len(gauges),
                    "thames_points_used": len(selected_locations),
                    "processing_stats": serializable_stats
                }
            }
            
            with open(output_path, 'w') as f:
                json.dump(output_data, f, indent=2, cls=DateTimeEncoder)
                
            self.log(f"Gauge data saved successfully to: {output_path}", "SUCCESS")
            
        except Exception as e:
            self.log(f"Error saving gauge data: {str(e)}", "ERROR")
            raise
        
        # Update processing statistics
        self.processing_stats['end_time'] = datetime.now()
        processing_time = (self.processing_stats['end_time'] - self.processing_stats['start_time']).total_seconds()
        
        # Final summary
        self.log("="*60, "INFO")
        self.log("🎉 GENERATION COMPLETE", "SUCCESS")
        self.log("="*60, "INFO")
        self.log(f"Successfully generated: {self.processing_stats['successful_gauges']}/{self.processing_stats['total_gauges']} gauges", "SUCCESS")
        self.log(f"Failed generations: {self.processing_stats['failed_gauges']}", "INFO" if self.processing_stats['failed_gauges'] == 0 else "WARNING")
        self.log(f"Processing time: {processing_time:.2f} seconds", "INFO")
        self.log(f"Output file: {output_path}", "INFO")
        
        return {
            "data": {
                "flood_gauges": gauges,
                "gauge_ids": gauge_ids,
                "thames_locations": selected_locations
            },
            "file_path": output_path,
            "processing_stats": self.processing_stats
        }
   
   
    def _generate_single_gauge(self, index: int, schema: Dict, location: Dict) -> tuple:
        """Generate a single flood gauge data structure with detailed logging."""
        # Generate unique ID
        gauge_id = f"GAUGE-{str(uuid.uuid4())[:8]}"
        
        self.log(f"  Creating gauge {gauge_id} at location {location['name']}", "DEBUG")
        
        # Generate consistent historical high level
        historical_high_level = 5.0 + random.uniform(0, 3.0)
        
        # Calculate alert levels as percentages of historical high
        flood_alert = historical_high_level * 0.6
        flood_warning = historical_high_level * 0.8
        severe_flood_warning = historical_high_level * 0.95
        
        # Generate install date (between 2 and 15 years ago)
        years_ago = random.randint(2, 15)
        install_date = (datetime.now() - timedelta(days=365*years_ago)).strftime("%Y-%m-%d")
        
        # Generate historical high date (after install date)
        high_date_days = random.randint(30, years_ago * 365 - 30)
        historical_high_date = (datetime.now() - timedelta(days=high_date_days)).strftime("%Y-%m-%d")
        
        # Store gauge metadata for field generation
        metadata = {
            "gauge_id": gauge_id,
            "historical_high_level": historical_high_level,
            "historical_high_date": historical_high_date,
            "flood_alert": flood_alert,
            "flood_warning": flood_warning,
            "severe_flood_warning": severe_flood_warning,
            "install_date": install_date,
            "location": location
        }
        
        self.log(f"  Generated levels: Alert={flood_alert:.1f}m, Warning={flood_warning:.1f}m, Severe={severe_flood_warning:.1f}m", "DEBUG")
        
        # Build gauge data structure recursively based on schema
        gauge_data = self._build_section(schema, index, metadata)
        
        # Override specific important fields
        self._set_specific_gauge_values(gauge_data, gauge_id, index, metadata)
        
        return gauge_data, gauge_id

    def _build_section(self, section_schema: Dict, index: int, metadata: Dict) -> Dict:
        """
        Recursively build a section of flood gauge data based on the schema.
        
        Args:
            section_schema: Schema dictionary for this section
            index: Gauge index for deterministic random generation
            metadata: Dictionary containing gauge-specific information
            
        Returns:
            Dictionary containing generated data for this section
        """
        result = {}
        # Handle the case where schema is not a dictionary
        if not isinstance(section_schema, dict):
            return {}
    
        # Iterate through schema keys
        for field_name, field_def in section_schema.items():
            # Skip metadata fields in schema
            if field_name in ['type', 'options', 'description', 'values']:
                continue
                
            # If this is a nested section, recurse
            if isinstance(field_def, dict) and not field_def.get("type"):
                result[field_name] = self._build_section(field_def, index, metadata)
            else:
                # This is a leaf field, generate a value
                field_type = field_def.get("type", "text") if isinstance(field_def, dict) else None
                
                if field_type == "text":
                    value = self._generate_text_value(field_name, field_def, index, metadata)
                elif field_type == "decimal":
                    value = self._generate_decimal_value(field_name, field_def, index, metadata)
                elif field_type == "integer":
                    value = self._generate_integer_value(field_name, field_def, index, metadata)
                elif field_type == "date":
                    value = self._generate_date_value(field_name, field_def, index, metadata)
                elif field_type == "menu":
                    value = self._generate_menu_value(field_name, field_def, index, metadata)
                else:
                    value = field_def
                
                if value is not None:
                    result[field_name] = value
        
        return result

    def _generate_value(self, field_def, index, field_name=None, metadata=None):
        """
        Generate a value for a specific field based on its schema.

        Args:
            field_def: Schema definition for this field
            index: Gauge index for deterministic random generation
            field_name: Name of the field
            metadata: Dictionary containing gauge-specific information
    
        Returns:
            Generated value for the field
        """
        # Handle the case where field_def is not a dictionary
        if not isinstance(field_def, dict):
            # If it's a string, return as is, otherwise return a default empty string
            return field_def if isinstance(field_def, str) else ""

        # Determine field type
        field_type = field_def.get('type', 'text')

        # Handle different field types
        if field_type == 'text':
            return self._generate_text_value(field_name, field_def, index, metadata)
        elif field_type == 'decimal':
            return self._generate_decimal_value(field_name, field_def, index, metadata)
        elif field_type == 'integer':
            return self._generate_integer_value(field_name, field_def, index, metadata)
        elif field_type == 'date':
            return self._generate_date_value(field_name, field_def, index, metadata)
        elif field_type == 'menu':
            return self._generate_menu_value(field_name, field_def, index, metadata)
        else:
            # Default to empty string for unknown types
            return ""
    

    def _generate_text_value(self, field_name, field_def, index, metadata):
        """Generate a text value based on field name and schema"""
        if field_name == 'GaugeID':
            return metadata['gauge_id']
        elif field_name == 'GaugeOwner':
            return random.choice(self.gauge_owners)
        elif field_name == 'ManufacturerName':
            return random.choice(self.manufacturers)
        elif field_name == 'DecisionBody':
            return random.choice(self.uk_decision_bodies)
        elif field_name == 'DataCurator':
            return random.choice(self.data_curators)
        elif field_name == 'GaugeName':
            # Name the gauge based on Thames area
            area_index = index % len(LONDON_AREAS)
            return f"Thames {LONDON_AREAS[area_index]} Gauge {index+1}"
        return f"Text-{field_name}-{index}"
    
    def _generate_decimal_value(self, field_name, field_def, index, metadata):
        """Generate a decimal value based on field name and schema"""
        if field_name == 'HistoricalHighLevel':
            return metadata['historical_high_level']
        elif field_name == 'FloodAlert':
            return metadata['flood_alert']
        elif field_name == 'FloodWarning':
            return metadata['flood_warning']
        elif field_name == 'SevereFloodWarning':
            return metadata['severe_flood_warning']
        elif field_name == 'GaugeLatitude':
            return metadata['location']['lat']
        elif field_name == 'GaugeLongitude':
            return metadata['location']['lon']
        elif field_name == 'elevation':
            return metadata['location']['elevation']
        return round(random.uniform(0, 10), 2)
    
    def _generate_integer_value(self, field_name, field_def, index, metadata):
        """Generate an integer value based on field name and schema"""
        if field_name == 'FrequencyExceedLevel3':
            # Generate frequency exceeded Level 3 in past 5 years
            return random.choices(
                [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 
                weights=[0.3, 0.2, 0.15, 0.1, 0.07, 0.05, 0.05, 0.03, 0.02, 0.02, 0.01]
            )[0]
        return random.randint(1, 10)
    
    def _generate_date_value(self, field_name, field_def, index, metadata):
        """Generate a date value based on field name and schema"""
        if field_name == 'HistoricalHighDate':
            return metadata['historical_high_date']
        elif field_name == 'InstallationDate':
            return metadata['install_date']
        elif field_name == 'LastInspectionDate':
            # Generate last inspection date (within last 2 years)
            inspection_days = random.randint(0, 365*2)
            return (datetime.now() - timedelta(days=inspection_days)).strftime("%Y-%m-%d")
        elif field_name == 'LastDateLevelExceedLevel3':
            # Generate last date level exceeded Level 3 (within last 5 years)
            level3_days = random.randint(0, 365*5)
            return (datetime.now() - timedelta(days=level3_days)).strftime("%Y-%m-%d")
        
        # Default random date within past 5 years
        days_ago = random.randint(0, 365 * 5)
        return (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
    
    def _generate_menu_value(self, field_name, field_def, index, metadata):
        """Generate a menu value based on field name and schema"""
        options = field_def.get('options', [])
        if not options:
            return ""
        
        if field_name == 'DataSourceType':
            return "SensorGauge"  # Most common for Thames river gauges
        elif field_name == 'GaugeType':
            return random.choices(self.gauge_types, weights=self.gauge_type_weights)[0]
        elif field_name == 'MaintenanceSchedule':
            return random.choice(["Monthly", "Quarterly", "Bi-annual", "Annual"])
        elif field_name == 'OperationalStatus':
            return random.choices(
                ["Fully operational", "Maintenance required", "Temporarily offline", "Decommissioned"],
                weights=[0.8, 0.15, 0.04, 0.01]
            )[0]
        elif field_name == 'CertificationStatus':
            return random.choices(
                ["Fully certified", "Provisional", "Under review", "Non-certified"],
                weights=[0.85, 0.1, 0.03, 0.02]
            )[0]
        elif field_name == 'MeasurementFrequency':
            return random.choice(["5 minutes", "15 minutes", "30 minutes", "Hourly"])
        elif field_name == 'MeasurementMethod':
            return "Automatic"  # Most common
        elif field_name == 'DataTransmission':
            return "Automatic"  # Most common
        elif field_name == 'DataAccessMethod':
            return random.choices(
                ["PublicAPI", "WebInterface", "Email/Other"],
                weights=[0.4, 0.5, 0.1]
            )[0]
        
        # Default random from options
        return options[index % len(options)]
  
  
    def _set_specific_gauge_values(self, gauge_data, gauge_id, index, metadata):
        """
        Override specific important fields in the gauge data.
        
        Args:
            gauge_data: Gauge data dictionary to modify
            gauge_id: Gauge ID
            index: Gauge index
            metadata: Dictionary containing gauge-specific information
        """
        self.log(f"    Setting specific values for gauge {gauge_id}", "DEBUG")
        
        # Ensure gauge data has all required structures
        if 'FloodGauge' not in gauge_data:
            gauge_data['FloodGauge'] = {}
        
        if 'Header' not in gauge_data['FloodGauge']:
            gauge_data['FloodGauge']['Header'] = {}
        
        if 'SensorDetails' not in gauge_data['FloodGauge']:
            gauge_data['FloodGauge']['SensorDetails'] = {}
            
        if 'GaugeInformation' not in gauge_data['FloodGauge']['SensorDetails']:
            gauge_data['FloodGauge']['SensorDetails']['GaugeInformation'] = {}
        
        # Set key fields
        gauge_data['FloodGauge']['Header']['GaugeID'] = gauge_id
        
        # Add a descriptive gauge name based on Thames location
        area_index = index % len(LONDON_AREAS)
        gauge_name = f"Thames {LONDON_AREAS[area_index]} Gauge {index+1}"
        gauge_data['FloodGauge']['Header']['GaugeName'] = gauge_name
        
        self.log(f"    Gauge name: {gauge_name}", "DEBUG")
        
        # Ensure location is set to Thames coordinates
        lat = metadata['location']['lat']
        lon = metadata['location']['lon']
        elevation = metadata['location']['elevation']
        
        gauge_data['FloodGauge']['SensorDetails']['GaugeInformation']['GaugeLatitude'] = lat
        gauge_data['FloodGauge']['SensorDetails']['GaugeInformation']['GaugeLongitude'] = lon
        gauge_data['FloodGauge']['SensorDetails']['GaugeInformation']['GroundLevelMeters'] = elevation
        gauge_data['FloodGauge']['SensorDetails']['GaugeInformation']['elevation'] = elevation
        self.log(f"    Location: ({lat:.5f}, {lon:.5f}) at {elevation:.1f}m", "DEBUG")
        
        # Set Thames-specific data
        if 'SensorStats' not in gauge_data['FloodGauge']:
            gauge_data['FloodGauge']['SensorStats'] = {}
        
        # Ensure historical data matches Thames flood patterns
        gauge_data['FloodGauge']['SensorStats']['HistoricalHighLevel'] = metadata['historical_high_level']
        gauge_data['FloodGauge']['SensorStats']['HistoricalHighDate'] = metadata['historical_high_date']
        
        # Set Thames-specific flood levels
        if 'FloodStage' not in gauge_data['FloodGauge']:
            gauge_data['FloodGauge']['FloodStage'] = {}
        
        if 'UK' not in gauge_data['FloodGauge']['FloodStage']:
            gauge_data['FloodGauge']['FloodStage']['UK'] = {}
        
        gauge_data['FloodGauge']['FloodStage']['UK']['FloodAlert'] = metadata['flood_alert']
        gauge_data['FloodGauge']['FloodStage']['UK']['FloodWarning'] = metadata['flood_warning']
        gauge_data['FloodGauge']['FloodStage']['UK']['SevereFloodWarning'] = metadata['severe_flood_warning']
        
        # Add Thames proximity info and flood risk assessment
        flood_risk = self._get_random_flood_status(metadata['location'])
        gauge_data['FloodGauge']['ThamesInfo'] = {
            'DistanceToThamesMeters': 0,  # These are gauges directly on the Thames
            'FloodRiskAssessment': flood_risk
        }
        
        self.log(f"    Flood levels: Alert={metadata['flood_alert']:.1f}m, Warning={metadata['flood_warning']:.1f}m", "DEBUG")
        self.log(f"    Flood risk: {flood_risk['FloodRiskCategory']} (Score: {flood_risk['FloodRiskScore']})", "DEBUG")
  
    
    def _get_random_flood_status(self, location, distance_threshold=300):
        """
        Generate random flood status based on proximity to Thames.
        
        Args:
            location: Location dictionary
            distance_threshold: Distance in meters considered close to Thames
            
        Returns:
            Dictionary with flood status information
        """
        # Properties closer to Thames have higher flood risks
        distance_to_thames = location.get('distance_to_thames', 0)
        is_close_to_thames = distance_to_thames < distance_threshold
        
        if is_close_to_thames:
            risk_score = random.randint(7, 10)
            risk_category = random.choice(["High", "Very High"])
        else:
            risk_score = random.randint(2, 6)
            risk_category = random.choice(["Low", "Medium"])
        
        return {
            "FloodRiskScore": risk_score,
            "FloodRiskCategory": risk_category,
            "LastAssessmentDate": (datetime.now() - timedelta(days=random.randint(0, 365))).strftime("%Y-%m-%d")
        }


def main():
    """Main function to run the enhanced flood gauge generator with elevation testing."""
    print("🌊 Enhanced Flood Gauge Portfolio Generator")
    print("=" * 50)
    
    # Setup output directory
    output_dir = Path("input")
    
    # Create generator instance with verbose logging
    generator = FloodGaugePortfolioGenerator(output_dir, verbose=True)
    
    try:
        # Generate gauges with elevation testing
        result = generator.generate(
            count=40, 
        )
        
        print("\n" + "=" * 50)
        print("🎉 Generation completed successfully!")
        print(f"📁 Output file: {result['file_path']}")
        print(f"📊 Gauges generated: {result['processing_stats']['successful_gauges']}")
        
        
    except Exception as e:
        print(f"❌ Generation failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    main()