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
Tropical Cyclone Event Time Series Common Data Model (CDM) implementation.
Based on TCEventTS_CDM v1 and v2 specifications.

This module provides a standardized data model for tropical cyclone event time series data,
enabling consistent processing across different data sources and applications.
"""

import pandas as pd
from typing import Dict, List, Optional, Any

class TCEventTSCDM:
    """
    Tropical Cyclone Event Time Series Common Data Model (CDM) implementation.
    Provides a standardized schema and data transformation methods
    for tropical cyclone event time series data.
    """
    def __init__(self, yaml_config: Optional[Dict[str, Any]] = None):
        """
        Initialize the TC Event Time Series CDM with schema definition.
        
        Args:
            yaml_config: Optional configuration for GEFS-HRRR integration
        """
        self.yaml_config = yaml_config or {
            'input_surface_variables': ["u10m", "v10m", "t2m", "q2m", "sp", "msl", "precipitable_water"],
            'input_isobaric_variables': ['u1000', 'u925', 'u850', 'u700', 'u500', 'u250',
                                       'v1000', 'v925', 'v850', 'v700', 'v500', 'v250',
                                       'z1000', 'z925', 'z850', 'z700', 'z500', 'z200',
                                       't1000', 't925', 't850', 't700', 't500', 't100',
                                       'r1000', 'r925', 'r850', 'r700', 'r500', 'r100'],
            'output_variables': ["u10m", "v10m", "t2m", "precip", "cat_snow", "cat_ice",
                               "cat_freez", "cat_rain", "cat_none"]
        }
        
        self.schema = {
            "EventTimeseries": {
                "Header": {
                    "event_id": {"type": "text", "description": "Unique identifier for TC event"},
                    "time": {"type": "datetime", "description": "UTC time"},
                    "lead_time": {"type": "integer", "description": "Forecast lead time", "units": "h"}
                },
                "Dimensions": {
                    "lat": {"type": "decimal", "description": "Latitude", "units": "degrees_north"},
                    "lon": {"type": "decimal", "description": "Longitude", "units": "degrees_east"},
                    "mrr": {"type": "decimal", "description": "Radius of maximum winds", "units": "km"}
                },
                "CycloneParameters": {
                    "direction": {"type": "decimal", "description": "Storm movement direction", "units": "degrees"},
                    "storm_size": {"type": "decimal", "description": "Radius of 34kt winds", "units": "km"},
                    "intensity_change": {"type": "decimal", "description": "24h intensity change", "units": "kt"},
                    "pressure_change": {"type": "decimal", "description": "24h pressure change", "units": "hPa"}
                },
                "SurfaceNearSurface": {
                    "t2m": {"type": "decimal", "description": "2m temperature", "units": "K"},
                    "sp": {"type": "decimal", "description": "Surface pressure", "units": "Pa"},
                    "msl": {"type": "decimal", "description": "Mean sea level pressure", "units": "Pa"},
                    "tcwv": {"type": "decimal", "description": "Total column water vapor", "units": "kg/m^2"},
                    "u10m": {"type": "decimal", "description": "10m u-wind component", "units": "m/s"},
                    "v10m": {"type": "decimal", "description": "10m v-wind component", "units": "m/s"},
                    "u100m": {"type": "decimal", "description": "100m u-wind component", "units": "m/s"},
                    "v100m": {"type": "decimal", "description": "100m v-wind component", "units": "m/s"},
                    "tp": {"type": "decimal", "description": "Total precipitation", "units": "m"},
                    "csnow": {"type": "decimal", "description": "Convective snow", "units": "kg/m^2"},
                    "cicep": {"type": "decimal", "description": "Convective ice precipitation", "units": "kg/m^2"},
                    "cfrzr": {"type": "decimal", "description": "Convective freezing rain", "units": "kg/m^2"},
                    "crain": {"type": "decimal", "description": "Convective rain", "units": "kg/m^2"}
                },
                "PressureLevels": {
                    "1000hPa": {
                        "u1000": {"type": "decimal", "description": "1000hPa u-wind component", "units": "m/s"},
                        "v1000": {"type": "decimal", "description": "1000hPa v-wind component", "units": "m/s"},
                        "z1000": {"type": "decimal", "description": "1000hPa geopotential height", "units": "m"}
                    },
                    "850hPa": {
                        "t850": {"type": "decimal", "description": "850hPa temperature", "units": "K"},
                        "u850": {"type": "decimal", "description": "850hPa u-wind component", "units": "m/s"},
                        "v850": {"type": "decimal", "description": "850hPa v-wind component", "units": "m/s"},
                        "z850": {"type": "decimal", "description": "850hPa geopotential height", "units": "m"},
                        "r850": {"type": "decimal", "description": "850hPa relative humidity", "units": "%"}
                    },
                    "500hPa": {
                        "t500": {"type": "decimal", "description": "500hPa temperature", "units": "K"},
                        "u500": {"type": "decimal", "description": "500hPa u-wind component", "units": "m/s"},
                        "v500": {"type": "decimal", "description": "500hPa v-wind component", "units": "m/s"},
                        "z500": {"type": "decimal", "description": "500hPa geopotential height", "units": "m"},
                        "r500": {"type": "decimal", "description": "500hPa relative humidity", "units": "%"}
                    },
                    "250hPa": {
                        "t250": {"type": "decimal", "description": "250hPa temperature", "units": "K"},
                        "u250": {"type": "decimal", "description": "250hPa u-wind component", "units": "m/s"},
                        "v250": {"type": "decimal", "description": "250hPa v-wind component", "units": "m/s"},
                        "z250": {"type": "decimal", "description": "250hPa geopotential height", "units": "m"}
                    },
                    "50hPa": {
                        "z50": {"type": "decimal", "description": "50hPa geopotential height", "units": "m"}
                    }
                },
                "SurfaceVariables": {var: {"type": "decimal"} for var in yaml_config['input_surface_variables']} 
                if yaml_config else {},
                "IsobaricVariables": {var: {"type": "decimal"} for var in yaml_config['input_isobaric_variables']}
                if yaml_config else {},
                "OutputVariables": {var: {"type": "decimal"} for var in yaml_config['output_variables']}
                if yaml_config else {}
            }
        }

    def validate_tceventts(self, tceventts_data: dict) -> Dict[str, List[str]]:
        """
        Validates tropical cyclone event timeseries data against the CDM schema.
        Returns dictionary of validation errors by section.
        
        Args:
            tceventts_data: Tropical cyclone event timeseries data to validate
            
        Returns:
            Dictionary of validation errors by section
        """
        errors = {}
        try:
            # Validate Header
            header_errors = []
            header = tceventts_data.get("EventTimeseries", {}).get("Header", {})
            if not header.get("event_id"):
                header_errors.append("Missing required field: event_id")
            if header_errors:
                errors["Header"] = header_errors
                
            # Validate required variables from YAML config
            if self.yaml_config:
                surface_errors = []
                isobaric_errors = []
                output_errors = []
                
                surface_data = tceventts_data.get("EventTimeseries", {}).get("SurfaceNearSurface", {})
                for var in self.yaml_config['input_surface_variables']:
                    if var not in surface_data:
                        surface_errors.append(f"Missing required surface variable: {var}")
                
                pressure_data = tceventts_data.get("EventTimeseries", {}).get("PressureLevels", {})
                for var in self.yaml_config['input_isobaric_variables']:
                    found = False
                    for level in pressure_data:
                        if var in pressure_data[level]:
                            found = True
                            break
                    if not found:
                        isobaric_errors.append(f"Missing required isobaric variable: {var}")
                
                if surface_errors:
                    errors["SurfaceVariables"] = surface_errors
                if isobaric_errors:
                    errors["IsobaricVariables"] = isobaric_errors
                if output_errors:
                    errors["OutputVariables"] = output_errors
                    
            return errors
        except Exception as e:
            return {"validation_error": [str(e)]}

    def create_tceventts_mapping(self, tceventts: dict) -> dict:
        """
        Creates a standardized tropical cyclone event timeseries dictionary based on the CDM schema.
        
        Args:
            tceventts: Raw tropical cyclone event timeseries data dictionary
            
        Returns:
            Structured tropical cyclone event timeseries data according to CDM schema
        """
        try:
            tceventts_data = {
                'event_id': tceventts.get('EventTimeseries', {}).get('Header', {}).get('event_id'),
                'time': tceventts.get('EventTimeseries', {}).get('Header', {}).get('time'),
                'lead_time': tceventts.get('EventTimeseries', {}).get('Header', {}).get('lead_time'),
                
                # Dimensions
                'lat': tceventts.get('EventTimeseries', {}).get('Dimensions', {}).get('lat'),
                'lon': tceventts.get('EventTimeseries', {}).get('Dimensions', {}).get('lon'),
                'mrr': tceventts.get('EventTimeseries', {}).get('Dimensions', {}).get('mrr'),
                
                # CycloneParameters
                'direction': tceventts.get('EventTimeseries', {}).get('CycloneParameters', {}).get('direction'),
                'storm_size': tceventts.get('EventTimeseries', {}).get('CycloneParameters', {}).get('storm_size'),
                'intensity_change': tceventts.get('EventTimeseries', {}).get('CycloneParameters', {}).get('intensity_change'),
                'pressure_change': tceventts.get('EventTimeseries', {}).get('CycloneParameters', {}).get('pressure_change'),
                
                # SurfaceNearSurface
                't2m': tceventts.get('EventTimeseries', {}).get('SurfaceNearSurface', {}).get('t2m'),
                'sp': tceventts.get('EventTimeseries', {}).get('SurfaceNearSurface', {}).get('sp'),
                'msl': tceventts.get('EventTimeseries', {}).get('SurfaceNearSurface', {}).get('msl'),
                'tcwv': tceventts.get('EventTimeseries', {}).get('SurfaceNearSurface', {}).get('tcwv'),
                'u10m': tceventts.get('EventTimeseries', {}).get('SurfaceNearSurface', {}).get('u10m'),
                'v10m': tceventts.get('EventTimeseries', {}).get('SurfaceNearSurface', {}).get('v10m'),
                'u100m': tceventts.get('EventTimeseries', {}).get('SurfaceNearSurface', {}).get('u100m'),
                'v100m': tceventts.get('EventTimeseries', {}).get('SurfaceNearSurface', {}).get('v100m'),
                'tp': tceventts.get('EventTimeseries', {}).get('SurfaceNearSurface', {}).get('tp'),
                'csnow': tceventts.get('EventTimeseries', {}).get('SurfaceNearSurface', {}).get('csnow'),
                'cicep': tceventts.get('EventTimeseries', {}).get('SurfaceNearSurface', {}).get('cicep'),
                'cfrzr': tceventts.get('EventTimeseries', {}).get('SurfaceNearSurface', {}).get('cfrzr'),
                'crain': tceventts.get('EventTimeseries', {}).get('SurfaceNearSurface', {}).get('crain'),
                
                # PressureLevels - flattening the nested structure for easier access
                'u1000': tceventts.get('EventTimeseries', {}).get('PressureLevels', {}).get('1000hPa', {}).get('u1000'),
                'v1000': tceventts.get('EventTimeseries', {}).get('PressureLevels', {}).get('1000hPa', {}).get('v1000'),
                'z1000': tceventts.get('EventTimeseries', {}).get('PressureLevels', {}).get('1000hPa', {}).get('z1000'),
                't850': tceventts.get('EventTimeseries', {}).get('PressureLevels', {}).get('850hPa', {}).get('t850'),
                'u850': tceventts.get('EventTimeseries', {}).get('PressureLevels', {}).get('850hPa', {}).get('u850'),
                'v850': tceventts.get('EventTimeseries', {}).get('PressureLevels', {}).get('850hPa', {}).get('v850'),
                'z850': tceventts.get('EventTimeseries', {}).get('PressureLevels', {}).get('850hPa', {}).get('z850'),
                'r850': tceventts.get('EventTimeseries', {}).get('PressureLevels', {}).get('850hPa', {}).get('r850'),
                't500': tceventts.get('EventTimeseries', {}).get('PressureLevels', {}).get('500hPa', {}).get('t500'),
                'u500': tceventts.get('EventTimeseries', {}).get('PressureLevels', {}).get('500hPa', {}).get('u500'),
                'v500': tceventts.get('EventTimeseries', {}).get('PressureLevels', {}).get('500hPa', {}).get('v500'),
                'z500': tceventts.get('EventTimeseries', {}).get('PressureLevels', {}).get('500hPa', {}).get('z500'),
                'r500': tceventts.get('EventTimeseries', {}).get('PressureLevels', {}).get('500hPa', {}).get('r500'),
                't250': tceventts.get('EventTimeseries', {}).get('PressureLevels', {}).get('250hPa', {}).get('t250'),
                'u250': tceventts.get('EventTimeseries', {}).get('PressureLevels', {}).get('250hPa', {}).get('u250'),
                'v250': tceventts.get('EventTimeseries', {}).get('PressureLevels', {}).get('250hPa', {}).get('v250'),
                'z250': tceventts.get('EventTimeseries', {}).get('PressureLevels', {}).get('250hPa', {}).get('z250'),
                'z50': tceventts.get('EventTimeseries', {}).get('PressureLevels', {}).get('50hPa', {}).get('z50')
            }
            
            return {k: v for k, v in tceventts_data.items() if v is not None}
        except Exception as e:
            raise ValueError(f"Error creating TC event timeseries mapping: {str(e)}")

    def to_dataframe(self, tceventts_data: List[dict]) -> pd.DataFrame:
        """
        Convert list of TC event timeseries data to pandas DataFrame.
        
        Args:
            tceventts_data: List of TC event timeseries dictionaries
            
        Returns:
            DataFrame containing the timeseries data
        """
        try:
            # Flatten nested dictionaries for DataFrame conversion
            flattened_data = []
            for entry in tceventts_data:
                flat_entry = {}
                for category, values in entry.items():
                    if isinstance(values, dict):
                        for key, value in values.items():
                            flat_entry[f"{category}_{key}"] = value
                    else:
                        flat_entry[category] = values
                flattened_data.append(flat_entry)
            
            return pd.DataFrame(flattened_data)
        except Exception as e:
            raise ValueError(f"Error converting to DataFrame: {str(e)}")
