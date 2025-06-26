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
Flood Gauge Common Data Model (CDM) implementation.
Based on Flood_Gauge_CDM v2 specification.

This module provides a standardized data model for flood gauge data,
enabling consistent processing across different data sources.
"""

import pandas as pd
from typing import Dict, List, Optional

class FloodGaugeCDM:
    """
    Flood Gauge Common Data Model (CDM) implementation.
    Provides a standardized schema and data transformation methods
    for flood gauge data.
    """
    def __init__(self):
        """Initialize the Flood Gauge CDM with schema definition."""
        self.schema = {
            "FloodGauge": {
                "Header": {
                    "GaugeID": {
                        "type": "text",
                        "description": "Unique identifier for the sensor"
                    }
                },
                "SensorStats": {
                    "HistoricalHighLevel": {
                        "type": "decimal",
                        "description": "Measurement of highest level recorded"
                    },
                    "HistoricalHighDate": {
                        "type": "date",
                        "description": "Date of highest recorded level"
                    },
                    "LastDateLevelExceedLevel3": {
                        "type": "date",
                        "description": "Date the last time Level 3 was exceeded"
                    },
                    "FrequencyExceedLevel3": {
                        "type": "integer",
                        "description": "Number of times in past 5 years Level 3 exceeded"
                    }
                },
                "SensorDetails": {
                    "GaugeInformation": {
                        "DataSourceType": {
                            "type": "menu",
                            "options": ["SensorGauge", "Satellite", "WeatherStation"],
                            "description": "Type of data source"
                        },
                        "GaugeOwner": {
                            "type": "text",
                            "description": "Name of data provider"
                        },
                        "GaugeType": {
                            "type": "menu",
                            "options": ["Staff gauge", "Wire-weight gauge", "Shaft encoder", 
                                      "Bubbler system", "Pressure transducer", "Radar gauge", 
                                      "Ultrasonic gauge"],
                            "description": "Specific type of river gauge"
                        },
                        "ManufacturerName": {
                            "type": "text",
                            "description": "Manufacturer of sensor"
                        },
                        "InstallationDate": {
                            "type": "date",
                            "description": "Date sensor was installed"
                        },
                        "LastInspectionDate": {
                            "type": "date",
                            "description": "Date of last physical inspection"
                        },
                        "MaintenanceSchedule": {
                            "type": "menu",
                            "options": ["Monthly", "Quarterly", "Bi-annual", "Annual"],
                            "description": "Required frequency of inspections"
                        },
                        "OperationalStatus": {
                            "type": "menu",
                            "options": ["Fully operational", "Maintenance required", 
                                      "Temporarily offline", "Decommissioned"],
                            "description": "Current operational status"
                        },
                        "CertificationStatus": {
                            "type": "menu",
                            "options": ["Fully certified", "Provisional", 
                                      "Under review", "Non-certified"],
                            "description": "Current certification status"
                        },
                        "GaugeLatitude": {
                            "type": "decimal",
                            "description": "Latitude coordinate of gauge"
                        },
                        "GaugeLongitude": {
                            "type": "decimal",
                            "description": "Longitude coordinate of gauge"
                        },
                        "GroundLevelMeters": {
                            "type": "decimal",
                            "description": "Elevation above sea level in meters at gauge location"
                        },
                        "elevation": {
                            "type": "decimal",
                            "description": "Elevation above sea level in meters at gauge location"
                        }
                    },
                    "Measurements": {
                        "MeasurementFrequency": {
                            "type": "menu",
                            "options": ["5 minutes", "15 minutes", "30 minutes", "Hourly"],
                            "description": "How often measurements are taken"
                        },
                        "MeasurementMethod": {
                            "type": "menu",
                            "options": ["Automatic", "Manual", "Hybrid"],
                            "description": "How measurements are recorded"
                        },
                        "DataTransmission": {
                            "type": "menu",
                            "options": ["Manual", "Automatic"],
                            "description": "Type of data transmission"
                        },
                        "DataCurator": {
                            "type": "text",
                            "description": "Which agency collects and stores data"
                        },
                        "DataAccessMethod": {
                            "type": "menu",
                            "options": ["PublicAPI", "WebInterface", "Email/Other"],
                            "description": "How data can be accessed by the parties"
                        }
                    }
                },
                "FloodStage": {
                    "UK": {
                        "DecisionBody": {
                            "type": "text",
                            "description": "Governmental Bodies"
                        },
                        "FloodAlert": {
                            "type": "decimal",
                            "description": "Trigger Level"
                        },
                        "FloodWarning": {
                            "type": "decimal",
                            "description": "Trigger Level"
                        },
                        "SevereFloodWarning": {
                            "type": "decimal",
                            "description": "Trigger Level"
                        }
                    }
                }
            }
        }

    def validate_gauge(self, gauge_data: dict) -> Dict[str, List[str]]:
        """
        Validates flood gauge data against the CDM schema.
        Returns dictionary of validation errors by section.
        
        Args:
            gauge_data: Flood gauge data to validate
            
        Returns:
            Dictionary of validation errors by section
        """
        errors = {}
        
        try:
            # Validate Header section
            header_errors = []
            header = gauge_data.get("FloodGauge", {}).get("Header", {})
            if not header.get("GaugeID"):
                header_errors.append("Missing required field: GaugeID")
            if header_errors:
                errors["Header"] = header_errors
                
            # Validate SensorDetails section
            sensor_errors = []
            gauge_info = gauge_data.get("FloodGauge", {}).get("SensorDetails", {}).get("GaugeInformation", {})
            
            # Validate menu fields
            menu_fields = {
                "DataSourceType": ["SensorGauge", "Satellite", "WeatherStation"],
                "GaugeType": ["Staff gauge", "Wire-weight gauge", "Shaft encoder", 
                             "Bubbler system", "Pressure transducer", "Radar gauge", 
                             "Ultrasonic gauge"],
                "MaintenanceSchedule": ["Monthly", "Quarterly", "Bi-annual", "Annual"],
                "OperationalStatus": ["Fully operational", "Maintenance required", 
                                    "Temporarily offline", "Decommissioned"],
                "CertificationStatus": ["Fully certified", "Provisional", 
                                      "Under review", "Non-certified"]
            }
            
            for field, valid_options in menu_fields.items():
                if field in gauge_info and gauge_info[field] not in valid_options:
                    sensor_errors.append(f"Invalid value for {field}")
                    
            if sensor_errors:
                errors["SensorDetails"] = sensor_errors
                    
            return errors
            
        except Exception as e:
            return {"validation_error": [str(e)]}

    def create_gauge_mapping(self, gauge: dict) -> dict:
        """
        Creates a standardized flood gauge data dictionary based on the CDM schema.
        
        Args:
            gauge: Raw flood gauge data dictionary
            
        Returns:
            Structured flood gauge data according to CDM schema
        """
        try:
            gauge_data = {
                # Header section
                'gauge_id': gauge.get('FloodGauge', {}).get('Header', {}).get('GaugeID'),
                
                # SensorStats section
                'historical_high_level': gauge.get('FloodGauge', {}).get('SensorStats', {}).get('HistoricalHighLevel'),
                'historical_high_date': gauge.get('FloodGauge', {}).get('SensorStats', {}).get('HistoricalHighDate'),
                'last_date_level_exceed_level3': gauge.get('FloodGauge', {}).get('SensorStats', {}).get('LastDateLevelExceedLevel3'),
                'frequency_exceed_level3': gauge.get('FloodGauge', {}).get('SensorStats', {}).get('FrequencyExceedLevel3'),
                
                # SensorDetails.GaugeInformation section
                'data_source_type': gauge.get('FloodGauge', {}).get('SensorDetails', {}).get('GaugeInformation', {}).get('DataSourceType'),
                'gauge_owner': gauge.get('FloodGauge', {}).get('SensorDetails', {}).get('GaugeInformation', {}).get('GaugeOwner'),
                'gauge_type': gauge.get('FloodGauge', {}).get('SensorDetails', {}).get('GaugeInformation', {}).get('GaugeType'),
                'manufacturer_name': gauge.get('FloodGauge', {}).get('SensorDetails', {}).get('GaugeInformation', {}).get('ManufacturerName'),
                'installation_date': gauge.get('FloodGauge', {}).get('SensorDetails', {}).get('GaugeInformation', {}).get('InstallationDate'),
                'last_inspection_date': gauge.get('FloodGauge', {}).get('SensorDetails', {}).get('GaugeInformation', {}).get('LastInspectionDate'),
                'maintenance_schedule': gauge.get('FloodGauge', {}).get('SensorDetails', {}).get('GaugeInformation', {}).get('MaintenanceSchedule'),
                'operational_status': gauge.get('FloodGauge', {}).get('SensorDetails', {}).get('GaugeInformation', {}).get('OperationalStatus'),
                'certification_status': gauge.get('FloodGauge', {}).get('SensorDetails', {}).get('GaugeInformation', {}).get('CertificationStatus'),
                'gauge_latitude': gauge.get('FloodGauge', {}).get('SensorDetails', {}).get('GaugeInformation', {}).get('GaugeLatitude'),
                'gauge_longitude': gauge.get('FloodGauge', {}).get('SensorDetails', {}).get('GaugeInformation', {}).get('GaugeLongitude'),
                'ground_level_meters': gauge.get('FloodGauge', {}).get('SensorDetails', {}).get('GaugeInformation', {}).get('GroundLevelMeters'),
                
                # SensorDetails.Measurements section
                'measurement_frequency': gauge.get('FloodGauge', {}).get('SensorDetails', {}).get('Measurements', {}).get('MeasurementFrequency'),
                'measurement_method': gauge.get('FloodGauge', {}).get('SensorDetails', {}).get('Measurements', {}).get('MeasurementMethod'),
                'data_transmission': gauge.get('FloodGauge', {}).get('SensorDetails', {}).get('Measurements', {}).get('DataTransmission'),
                'data_curator': gauge.get('FloodGauge', {}).get('SensorDetails', {}).get('Measurements', {}).get('DataCurator'),
                'data_access_method': gauge.get('FloodGauge', {}).get('SensorDetails', {}).get('Measurements', {}).get('DataAccessMethod'),
                
                # FloodStage.UK section
                'decision_body': gauge.get('FloodGauge', {}).get('FloodStage', {}).get('UK', {}).get('DecisionBody'),
                'flood_alert': gauge.get('FloodGauge', {}).get('FloodStage', {}).get('UK', {}).get('FloodAlert'),
                'flood_warning': gauge.get('FloodGauge', {}).get('FloodStage', {}).get('UK', {}).get('FloodWarning'),
                'severe_flood_warning': gauge.get('FloodGauge', {}).get('FloodStage', {}).get('UK', {}).get('SevereFloodWarning')
            }
            
            # Remove None values from the dictionary
            return {k: v for k, v in gauge_data.items() if v is not None}
            
        except Exception as e:
            raise ValueError(f"Error creating gauge mapping: {str(e)}")