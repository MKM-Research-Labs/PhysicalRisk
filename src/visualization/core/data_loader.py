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
Data loading and validation module for the visualization system.

This module provides centralized data loading, validation, and relationship analysis
for all data sources used in the tropical cyclone event visualization.
"""

import json
import sys
import warnings
from pathlib import Path
from typing import Optional, Union, Dict, List, Any, NamedTuple
from dataclasses import dataclass

# Fix the Python path to find project modules
current_file = Path(__file__).resolve()
# Navigate up to find project root (assuming we're in visualization/core)
project_root = current_file.parent.parent.parent

# Add project root to Python's path
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Now import modules using absolute imports
from utilities.project_paths import ProjectPaths

# Import from our utils (relative to visualization package)
try:
    from ..utils import DataExtractor
except ImportError:
    # Fallback for direct execution
    sys.path.insert(0, str(current_file.parent.parent))
    from utils import DataExtractor


@dataclass
class LoadedData:
    """Container for all loaded visualization data."""
    tc_data: Optional[Dict[str, Any]] = None
    gauge_data: Optional[Dict[str, Any]] = None
    property_data: Optional[Dict[str, Any]] = None
    mortgage_data: Optional[Dict[str, Any]] = None
    flood_risk_data: Optional[Dict[str, Any]] = None
    
    # Processed lookups
    mortgage_lookup: Optional[Dict[str, Dict]] = None
    gauge_flood_info: Optional[Dict[str, Dict]] = None
    property_flood_info: Optional[Dict[str, Dict]] = None
    mortgage_risk_info: Optional[Dict[str, Dict]] = None


class DataValidationResult(NamedTuple):
    """Result of data validation."""
    is_valid: bool
    warnings: List[str]
    errors: List[str]
    summary: Dict[str, Any]


class DataLoader:
    """
    Centralized data loading and validation for the visualization system.
    
    This class handles loading JSON files, validating their structure,
    building lookup tables, and analyzing relationships between datasets.
    """
    
    def __init__(self, input_dir: Optional[Union[str, Path]] = None):
        """
        Initialize the data loader.
        
        Args:
            input_dir: Directory containing input JSON files
        """
        self.input_dir = Path(input_dir) if input_dir else self._get_default_input_dir()
        self.loaded_data = LoadedData()
        self._validation_results = {}
        
        print(f"DataLoader initialized with input directory: {self.input_dir}")
    
    def load_all_data(self, ts_filename: str, gauge_filename: str,
                     property_filename: str, mortgage_filename: str,
                     flood_risk_filename: str) -> LoadedData:
        """
        Load all required data files and build lookup tables.
        
        Args:
            ts_filename: Tropical cyclone timeseries filename
            gauge_filename: Flood gauge data filename
            property_filename: Property portfolio filename
            mortgage_filename: Mortgage portfolio filename
            flood_risk_filename: Flood risk report filename
            
        Returns:
            LoadedData container with all loaded and processed data
        """
        print("\n=== Loading Data Files ===")
        
        # Load individual data files
        self.loaded_data.tc_data = self._load_and_validate_json(
            ts_filename, 'tropical_cyclone'
        )
        self.loaded_data.gauge_data = self._load_and_validate_json(
            gauge_filename, 'gauge'
        )
        self.loaded_data.property_data = self._load_and_validate_json(
            property_filename, 'property'
        )
        self.loaded_data.mortgage_data = self._load_and_validate_json(
            mortgage_filename, 'mortgage'
        )
        self.loaded_data.flood_risk_data = self._load_and_validate_json(
            flood_risk_filename, 'flood_risk'
        )
        
        # Build lookup tables and process relationships
        self._build_lookup_tables()
        
        # Analyze ID relationships for debugging
        self._analyze_id_relationships()
        
        # Print summary
        self._print_loading_summary()
        
        return self.loaded_data
    
    def _load_and_validate_json(self, filename: str, data_type: str) -> Optional[Dict[str, Any]]:
        """
        Load and validate a JSON file.
        
        Args:
            filename: Name of the file to load
            data_type: Type of data for validation
            
        Returns:
            Loaded and validated data or None if loading failed
        """
        try:
            data = self._load_json(filename)
            if data is not None:
                validation_result = self._validate_data(data, data_type)
                self._validation_results[data_type] = validation_result
                
                if validation_result.errors:
                    print(f"Validation errors for {filename}: {validation_result.errors}")
                    return None
                
                if validation_result.warnings:
                    for warning in validation_result.warnings:
                        warnings.warn(f"{filename}: {warning}")
                
                print(f"✓ Loaded {filename}: {validation_result.summary}")
                return data
            else:
                print(f"✗ Failed to load {filename}")
                return None
                
        except Exception as e:
            print(f"✗ Error loading {filename}: {str(e)}")
            return None
    
    def _load_json(self, filename: str) -> Optional[Dict[str, Any]]:
        """
        Load a JSON file from the input directory.
        
        Args:
            filename: Name of the file to load
            
        Returns:
            Loaded data or None if file doesn't exist or is invalid
        """
        file_path = self.input_dir / filename
        
        if not file_path.exists():
            print(f"File not found: {file_path}")
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data
        except json.JSONDecodeError as e:
            print(f"Invalid JSON in {file_path}: {str(e)}")
            return None
        except Exception as e:
            print(f"Error reading {file_path}: {str(e)}")
            return None
    
    def _validate_data(self, data: Dict[str, Any], data_type: str) -> DataValidationResult:
        """
        Validate the structure and content of loaded data.
        
        Args:
            data: Loaded data to validate
            data_type: Type of data being validated
            
        Returns:
            DataValidationResult with validation details
        """
        warnings_list = []
        errors = []
        summary = {}
        
        try:
            if data_type == 'tropical_cyclone':
                summary, warns, errs = self._validate_tc_data(data)
            elif data_type == 'gauge':
                summary, warns, errs = self._validate_gauge_data(data)
            elif data_type == 'property':
                summary, warns, errs = self._validate_property_data(data)
            elif data_type == 'mortgage':
                summary, warns, errs = self._validate_mortgage_data(data)
            elif data_type == 'flood_risk':
                summary, warns, errs = self._validate_flood_risk_data(data)
            else:
                summary = {"type": "unknown", "size": len(str(data))}
                warns = [f"Unknown data type: {data_type}"]
                errs = []
            
            warnings_list.extend(warns)
            errors.extend(errs)
            
        except Exception as e:
            errors.append(f"Validation failed: {str(e)}")
            summary = {"error": str(e)}
        
        is_valid = len(errors) == 0
        return DataValidationResult(is_valid, warnings_list, errors, summary)
    
    def _validate_tc_data(self, data: Dict[str, Any]) -> tuple:
        """Validate tropical cyclone data structure."""
        warnings_list = []
        errors = []
        
        if 'timeseries' not in data:
            errors.append("Missing 'timeseries' key in TC data")
            return {}, warnings_list, errors
        
        timeseries = data['timeseries']
        if not isinstance(timeseries, list):
            errors.append("'timeseries' should be a list")
            return {}, warnings_list, errors
        
        if len(timeseries) == 0:
            errors.append("Empty timeseries data")
            return {}, warnings_list, errors
        
        # Validate first entry structure
        first_entry = timeseries[0]
        required_keys = ['EventTimeseries']
        for key in required_keys:
            if key not in first_entry:
                errors.append(f"Missing '{key}' in timeseries entry")
        
        # Check for coordinate data
        coordinates_found = 0
        for ts in timeseries:
            if ('EventTimeseries' in ts and 
                'Dimensions' in ts['EventTimeseries'] and
                'lat' in ts['EventTimeseries']['Dimensions'] and
                'lon' in ts['EventTimeseries']['Dimensions']):
                coordinates_found += 1
        
        if coordinates_found == 0:
            errors.append("No coordinate data found in timeseries")
        elif coordinates_found < len(timeseries):
            warnings_list.append(f"Only {coordinates_found}/{len(timeseries)} entries have coordinates")
        
        summary = {
            "type": "tropical_cyclone",
            "entries": len(timeseries),
            "coordinates": coordinates_found
        }
        
        return summary, warnings_list, errors
    
    def _validate_gauge_data(self, data: Dict[str, Any]) -> tuple:
        """Validate gauge data structure."""
        warnings_list = []
        errors = []
        
        # Try different possible key names
        gauges = data.get('floodGauges') or data.get('flood_gauges') or []
        
        if not gauges:
            errors.append("No gauge data found (checked 'floodGauges' and 'flood_gauges')")
            return {}, warnings_list, errors
        
        if not isinstance(gauges, list):
            errors.append("Gauge data should be a list")
            return {}, warnings_list, errors
        
        coordinates_found = 0
        valid_gauges = 0
        
        for gauge in gauges:
            if 'FloodGauge' in gauge:
                valid_gauges += 1
                gauge_info = gauge.get('FloodGauge', {}).get('SensorDetails', {}).get('GaugeInformation', {})
                if gauge_info.get('GaugeLatitude') is not None and gauge_info.get('GaugeLongitude') is not None:
                    coordinates_found += 1
        
        if valid_gauges == 0:
            errors.append("No valid gauge entries found")
        
        if coordinates_found < valid_gauges:
            warnings_list.append(f"Only {coordinates_found}/{valid_gauges} gauges have coordinates")
        
        summary = {
            "type": "gauge",
            "total_entries": len(gauges),
            "valid_gauges": valid_gauges,
            "coordinates": coordinates_found
        }
        
        return summary, warnings_list, errors
    
    def _validate_property_data(self, data: Dict[str, Any]) -> tuple:
        """Validate property data structure."""
        warnings_list = []
        errors = []
        
        properties = data.get('properties', [])
        
        if not properties:
            errors.append("No property data found (checked 'properties' key)")
            return {}, warnings_list, errors
        
        if not isinstance(properties, list):
            errors.append("Property data should be a list")
            return {}, warnings_list, errors
        
        coordinates_found = 0
        valid_properties = 0
        property_ids = set()
        
        for prop in properties:
            if 'PropertyHeader' in prop:
                valid_properties += 1
                prop_id = prop.get('PropertyHeader', {}).get('Header', {}).get('PropertyID')
                if prop_id:
                    property_ids.add(prop_id)
                
                location = prop.get('PropertyHeader', {}).get('Location', {})
                lat = location.get('LatitudeDegrees') or location.get('Latitude')
                lon = location.get('LongitudeDegrees') or location.get('Longitude')
                
                if lat is not None and lon is not None:
                    coordinates_found += 1
        
        if valid_properties == 0:
            errors.append("No valid property entries found")
        
        if coordinates_found < valid_properties:
            warnings_list.append(f"Only {coordinates_found}/{valid_properties} properties have coordinates")
        
        summary = {
            "type": "property",
            "total_entries": len(properties),
            "valid_properties": valid_properties,
            "unique_ids": len(property_ids),
            "coordinates": coordinates_found
        }
        
        return summary, warnings_list, errors
    
    def _validate_mortgage_data(self, data: Dict[str, Any]) -> tuple:
        """Validate mortgage data structure."""
        warnings_list = []
        errors = []
        
        mortgages = data.get('mortgages', [])
        
        if not mortgages:
            errors.append("No mortgage data found (checked 'mortgages' key)")
            return {}, warnings_list, errors
        
        if not isinstance(mortgages, list):
            errors.append("Mortgage data should be a list")
            return {}, warnings_list, errors
        
        valid_mortgages = 0
        mortgage_ids = set()
        property_ids = set()
        
        for mortgage in mortgages:
            if 'Mortgage' in mortgage:
                valid_mortgages += 1
                header = mortgage.get('Mortgage', {}).get('Header', {})
                
                mortgage_id = header.get('MortgageID')
                property_id = header.get('PropertyID')
                
                if mortgage_id:
                    mortgage_ids.add(mortgage_id)
                if property_id:
                    property_ids.add(property_id)
        
        if valid_mortgages == 0:
            errors.append("No valid mortgage entries found")
        
        summary = {
            "type": "mortgage",
            "total_entries": len(mortgages),
            "valid_mortgages": valid_mortgages,
            "unique_mortgage_ids": len(mortgage_ids),
            "unique_property_ids": len(property_ids)
        }
        
        return summary, warnings_list, errors
    
    def _validate_flood_risk_data(self, data: Dict[str, Any]) -> tuple:
        """Validate flood risk data structure."""
        warnings_list = []
        errors = []
        
        gauge_data = data.get('gauge_data', {})
        property_risk = data.get('property_risk', {})
        mortgage_risk = data.get('mortgage_risk', {})
        
        if not any([gauge_data, property_risk, mortgage_risk]):
            errors.append("No flood risk data found (checked 'gauge_data', 'property_risk', 'mortgage_risk')")
            return {}, warnings_list, errors
        
        summary = {
            "type": "flood_risk",
            "gauge_entries": len(gauge_data),
            "property_risk_entries": len(property_risk),
            "mortgage_risk_entries": len(mortgage_risk)
        }
        
        return summary, warnings_list, errors
    
    def _build_lookup_tables(self):
        """Build lookup tables for efficient data access."""
        print("\n=== Building Lookup Tables ===")
        
        # Build mortgage lookup table
        if self.loaded_data.mortgage_data:
            self.loaded_data.mortgage_lookup = DataExtractor.build_mortgage_lookup(
                self.loaded_data.mortgage_data
            )
            print(f"✓ Built mortgage lookup: {len(self.loaded_data.mortgage_lookup)} entries")
        
        # Extract flood risk information
        if self.loaded_data.flood_risk_data:
            flood_data = DataExtractor.extract_flood_risk_data(self.loaded_data.flood_risk_data)
            self.loaded_data.gauge_flood_info = flood_data['gauge_flood_info']
            self.loaded_data.property_flood_info = flood_data['property_flood_info']
            self.loaded_data.mortgage_risk_info = flood_data['mortgage_risk_info']
            
            print(f"✓ Extracted flood risk data:")
            print(f"  - Gauge flood info: {len(self.loaded_data.gauge_flood_info)} entries")
            print(f"  - Property flood info: {len(self.loaded_data.property_flood_info)} entries")
            print(f"  - Mortgage risk info: {len(self.loaded_data.mortgage_risk_info['by_mortgage_id'])} entries")
    
    def _analyze_id_relationships(self):
        """Analyze relationships between IDs in different datasets."""
        print("\n=== Analyzing ID Relationships ===")
        
        # Extract IDs from each dataset
        property_ids = self._extract_property_ids()
        mortgage_property_ids = self._extract_mortgage_property_ids()
        mortgage_ids = self._extract_mortgage_ids()
        flood_risk_property_ids = self._extract_flood_risk_property_ids()
        flood_risk_mortgage_ids = self._extract_flood_risk_mortgage_ids()
        
        # Print statistics
        print(f"Property IDs: {len(property_ids)}")
        print(f"Mortgage property IDs: {len(mortgage_property_ids)}")
        print(f"Mortgage IDs: {len(mortgage_ids)}")
        print(f"Flood risk property IDs: {len(flood_risk_property_ids)}")
        print(f"Flood risk mortgage IDs: {len(flood_risk_mortgage_ids)}")
        
        # Check overlaps
        properties_with_mortgages = property_ids.intersection(mortgage_property_ids)
        properties_with_flood_risk = property_ids.intersection(flood_risk_property_ids)
        mortgages_with_flood_risk = mortgage_ids.intersection(flood_risk_mortgage_ids)
        
        print(f"\nOverlaps:")
        print(f"Properties with mortgages: {len(properties_with_mortgages)}/{len(property_ids)}")
        print(f"Properties with flood risk: {len(properties_with_flood_risk)}/{len(property_ids)}")
        print(f"Mortgages with flood risk: {len(mortgages_with_flood_risk)}/{len(mortgage_ids)}")
        
        # Sample ID formats for debugging
        self._print_sample_ids(property_ids, mortgage_ids, flood_risk_property_ids)
    
    def _extract_property_ids(self) -> set:
        """Extract all property IDs from property data."""
        property_ids = set()
        if self.loaded_data.property_data and 'properties' in self.loaded_data.property_data:
            for prop in self.loaded_data.property_data['properties']:
                prop_id = prop.get('PropertyHeader', {}).get('Header', {}).get('PropertyID')
                if prop_id:
                    property_ids.add(prop_id)
        return property_ids
    
    def _extract_mortgage_property_ids(self) -> set:
        """Extract property IDs from mortgage data."""
        property_ids = set()
        if self.loaded_data.mortgage_lookup:
            property_ids = set(self.loaded_data.mortgage_lookup.keys())
        return property_ids
    
    def _extract_mortgage_ids(self) -> set:
        """Extract mortgage IDs from mortgage data."""
        mortgage_ids = set()
        if self.loaded_data.mortgage_data and 'mortgages' in self.loaded_data.mortgage_data:
            for mortgage in self.loaded_data.mortgage_data['mortgages']:
                mortgage_id = mortgage.get('Mortgage', {}).get('Header', {}).get('MortgageID')
                if mortgage_id:
                    mortgage_ids.add(mortgage_id)
        return mortgage_ids
    
    def _extract_flood_risk_property_ids(self) -> set:
        """Extract property IDs from flood risk data."""
        property_ids = set()
        if self.loaded_data.property_flood_info:
            property_ids = set(self.loaded_data.property_flood_info.keys())
        return property_ids
    
    def _extract_flood_risk_mortgage_ids(self) -> set:
        """Extract mortgage IDs from flood risk data."""
        mortgage_ids = set()
        if self.loaded_data.mortgage_risk_info and 'by_mortgage_id' in self.loaded_data.mortgage_risk_info:
            mortgage_ids = set(self.loaded_data.mortgage_risk_info['by_mortgage_id'].keys())
        return mortgage_ids
    
    def _print_sample_ids(self, property_ids: set, mortgage_ids: set, flood_risk_property_ids: set):
        """Print sample IDs for format analysis."""
        print(f"\nSample ID formats:")
        
        if property_ids:
            sample_prop_id = next(iter(property_ids))
            print(f"Property ID: {sample_prop_id}")
        
        if mortgage_ids:
            sample_mortgage_id = next(iter(mortgage_ids))
            print(f"Mortgage ID: {sample_mortgage_id}")
        
        if flood_risk_property_ids:
            sample_flood_prop_id = next(iter(flood_risk_property_ids))
            print(f"Flood risk property ID: {sample_flood_prop_id}")
    
    def _print_loading_summary(self):
        """Print a summary of all loaded data."""
        print(f"\n=== Data Loading Summary ===")
        data_status = {
            "TC Data": "✓" if self.loaded_data.tc_data else "✗",
            "Gauge Data": "✓" if self.loaded_data.gauge_data else "✗",
            "Property Data": "✓" if self.loaded_data.property_data else "✗",
            "Mortgage Data": "✓" if self.loaded_data.mortgage_data else "✗",
            "Flood Risk Data": "✓" if self.loaded_data.flood_risk_data else "✗"
        }
        
        for data_type, status in data_status.items():
            print(f"{status} {data_type}")
    
    def _get_default_input_dir(self) -> Path:
        """Get default input directory."""
        try:
            # Use ProjectPaths for consistent directory resolution
            return ProjectPaths(__file__).input_dir
        except Exception as e:
            print(f"Warning: Could not use ProjectPaths ({e}), using fallback")
            # Fallback to relative path from project root
            return project_root / "input"
    
    def get_validation_summary(self) -> Dict[str, DataValidationResult]:
        """
        Get validation results for all loaded data.
        
        Returns:
            Dictionary mapping data types to validation results
        """
        return self._validation_results.copy()
    
    def is_data_complete(self) -> bool:
        """
        Check if all required data has been loaded successfully.
        
        Returns:
            True if TC data is loaded (minimum requirement)
        """
        return self.loaded_data.tc_data is not None
    
    def get_data_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all loaded data.
        
        Returns:
            Dictionary with data summary information
        """
        summary = {}
        
        for data_type, validation_result in self._validation_results.items():
            summary[data_type] = {
                'loaded': validation_result.is_valid,
                'summary': validation_result.summary,
                'warnings': len(validation_result.warnings),
                'errors': len(validation_result.errors)
            }
        
        return summary