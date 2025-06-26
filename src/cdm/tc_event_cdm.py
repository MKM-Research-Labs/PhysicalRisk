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
Tropical Cyclone Event Common Data Model (CDM) implementation.
Based on TC_Event_CDM v1 specification.

This module provides a standardized data model for tropical cyclone events,
enabling consistent processing across different data sources and applications.
"""

from typing import Dict, List

class TCEventCDM:
    """
    Tropical Cyclone Event Common Data Model (CDM) implementation.
    Provides a standardized schema and data transformation methods
    for tropical cyclone event data.
    """
    def __init__(self):
        """Initialize the TC Event CDM with schema definition."""
        self.schema = {
            "TropicalCycloneEvent": {
                "Header": {
                    "TCEventID": {
                        "type": "text",
                        "description": "Unique identifier for a TC event"
                    },
                },
                "Attributes": {
                    "TCName": {
                        "type": "text",
                        "description": "Name of the TC"
                    },
                    "TCSize": {
                        "type": "integer",
                        "description": "Size of the TC (diameter) in km"
                    },
                    "TCWindSpeed": {
                        "type": "integer",
                        "description": "Wind speed in km/h"
                    },
                    "TCDuration": {
                        "type": "integer",
                        "description": "Number of days"
                    },
                    "TCPressure": {
                        "type": "integer",
                        "description": "Low atmospheric pressure at the centre in milibars"
                    },
                    "TCSurge": {
                        "type": "integer",
                        "description": "Elevated sea level rise above normal in m"
                    },
                    "DistanceEye": {
                        "type": "integer",
                        "description": "Distance from the eye of the storm in km"
                    },
                    "DistancePath": {
                        "type": "integer",
                        "description": "Distance from the expected path of the storm in km"
                    },
                    "StartDate": {
                        "type": "date",
                        "description": "Start date of the event"
                    },
                    "EndDate": {
                        "type": "date",
                        "description": "End date of the event"
                    }
                },
                "Alert": {
                    "WarningCentre": {
                        "type": "text",
                        "description": "Name of the Regional Specialized Meteorological Centre"
                    },
                    "CycloneAlert": {
                        "type": "date",
                        "description": "Date first warning received"
                    }
                },
                "Warning": {
                    "Date": {
                        "type": "date",
                        "description": "Date of warning update"
                    },
                    "Time": {
                        "type": "time",
                        "description": "Time of warning update"
                    },
                    "Position": {
                        "type": "text",
                        "description": "Location of TC"
                    },
                    "Intensity": {
                        "type": "integer",
                        "description": "Category of the TC"
                    },
                    "WindSpeeds": {
                        "type": "integer",
                        "description": "Wind speed at TC warning time in km/h"
                    },
                    "ExpectedTime": {
                        "type": "time",
                        "description": "Time of expected Landfall"
                    },
                    "ExpectedDate": {
                        "type": "date",
                        "description": "Date of expected Landfall"
                    },
                    "ExpectedLocation": {
                        "type": "text",
                        "description": "Description of location"
                    },
                    "AnticipatedStormSurgeHeight": {
                        "type": "decimal",
                        "description": "Expected storm surge height above normal in m"
                    },
                    "PotentialDamage": {
                        "type": "text",
                        "description": "Description of expected damage"
                    },
                    "SuggestedActions": {
                        "type": "text",
                        "description": "Recommended actions"
                    }
                },
                "Triggers": {
                    "currency": {
                        "type": "text",
                        "description": "Trigger Currency"
                    },
                    "EvacuationTrigger": {
                        "type": "decimal",
                        "description": "Costs to cover evacuation in specified currency"
                    },
                    "PropertyDamageTrigger": {
                        "type": "decimal",
                        "description": "Costs to cover property damage"
                    },
                    "BusinessInteruptionTrigger": {
                        "type": "decimal",
                        "description": "Costs to cover business interuption"
                    },
                    "AdditionalExpensesTrigger": {
                        "type": "decimal",
                        "description": "Operational expenses and other immediate costs"
                    }
                }
            }
        }

    def validate_tcevent(self, tcevent_data: dict) -> Dict[str, List[str]]:
        """
        Validates tropical cyclone event data against the CDM schema.
        Returns dictionary of validation errors by section.
        
        Args:
            tcevent_data: Tropical cyclone event data to validate
            
        Returns:
            Dictionary of validation errors by section
        """
        errors = {}
        try:
            header_errors = []
            header = tcevent_data.get("TropicalCycloneEvent", {}).get("Header", {})
            if not header.get("TCEventID"):
                header_errors.append("Missing required field: TCEventID")
            if header_errors:
                errors["Header"] = header_errors
            return errors
        except Exception as e:
            return {"validation_error": [str(e)]}

    def create_event_mapping(self, tcevent: dict) -> dict:
        """
        Creates a standardized tropical cyclone event dictionary based on the CDM schema.
        
        Args:
            tcevent: Raw tropical cyclone event data dictionary
            
        Returns:
            Structured tropical cyclone event data according to CDM schema
        """
        try:
            tcevent_data = {
                'tc_event_id': tcevent.get('TropicalCycloneEvent', {}).get('Header', {}).get('TCEventID'),
                
                # Attributes section
                'tc_name': tcevent.get('TropicalCycloneEvent', {}).get('Attributes', {}).get('TCName'),
                'tc_size': tcevent.get('TropicalCycloneEvent', {}).get('Attributes', {}).get('TCSize'),
                'tc_wind_speed': tcevent.get('TropicalCycloneEvent', {}).get('Attributes', {}).get('TCWindSpeed'),
                'tc_duration': tcevent.get('TropicalCycloneEvent', {}).get('Attributes', {}).get('TCDuration'),
                'tc_pressure': tcevent.get('TropicalCycloneEvent', {}).get('Attributes', {}).get('TCPressure'),
                'tc_surge': tcevent.get('TropicalCycloneEvent', {}).get('Attributes', {}).get('TCSurge'),
                'distance_eye': tcevent.get('TropicalCycloneEvent', {}).get('Attributes', {}).get('DistanceEye'),
                'distance_path': tcevent.get('TropicalCycloneEvent', {}).get('Attributes', {}).get('DistancePath'),
                'start_date': tcevent.get('TropicalCycloneEvent', {}).get('Attributes', {}).get('StartDate'),
                'end_date': tcevent.get('TropicalCycloneEvent', {}).get('Attributes', {}).get('EndDate'),
                
                # Alert section
                'warning_centre': tcevent.get('TropicalCycloneEvent', {}).get('Alert', {}).get('WarningCentre'),
                'cyclone_alert': tcevent.get('TropicalCycloneEvent', {}).get('Alert', {}).get('CycloneAlert'),
                
                # Warning section
                'warning_date': tcevent.get('TropicalCycloneEvent', {}).get('Warning', {}).get('Date'),
                'warning_time': tcevent.get('TropicalCycloneEvent', {}).get('Warning', {}).get('Time'),
                'position': tcevent.get('TropicalCycloneEvent', {}).get('Warning', {}).get('Position'),
                'intensity': tcevent.get('TropicalCycloneEvent', {}).get('Warning', {}).get('Intensity'),
                'wind_speeds': tcevent.get('TropicalCycloneEvent', {}).get('Warning', {}).get('WindSpeeds'),
                'expected_time': tcevent.get('TropicalCycloneEvent', {}).get('Warning', {}).get('ExpectedTime'),
                'expected_date': tcevent.get('TropicalCycloneEvent', {}).get('Warning', {}).get('ExpectedDate'),
                'expected_location': tcevent.get('TropicalCycloneEvent', {}).get('Warning', {}).get('ExpectedLocation'),
                'anticipated_surge_height': tcevent.get('TropicalCycloneEvent', {}).get('Warning', {}).get('AnticipatedStormSurgeHeight'),
                'potential_damage': tcevent.get('TropicalCycloneEvent', {}).get('Warning', {}).get('PotentialDamage'),
                'suggested_actions': tcevent.get('TropicalCycloneEvent', {}).get('Warning', {}).get('SuggestedActions'),
                
                # Triggers section
                'currency': tcevent.get('TropicalCycloneEvent', {}).get('Triggers', {}).get('currency'),
                'evacuation_trigger': tcevent.get('TropicalCycloneEvent', {}).get('Triggers', {}).get('EvacuationTrigger'),
                'property_damage_trigger': tcevent.get('TropicalCycloneEvent', {}).get('Triggers', {}).get('PropertyDamageTrigger'),
                'business_interruption_trigger': tcevent.get('TropicalCycloneEvent', {}).get('Triggers', {}).get('BusinessInteruptionTrigger'),
                'additional_expenses_trigger': tcevent.get('TropicalCycloneEvent', {}).get('Triggers', {}).get('AdditionalExpensesTrigger')
            }
            return {k: v for k, v in tcevent_data.items() if v is not None}
        except Exception as e:
            raise ValueError(f"Error creating event mapping: {str(e)}")
            
    def create_TCEvent_mapping(self, event_data: dict) -> dict:
        """
        Creates a standardized tropical cyclone event data structure based on the CDM schema.
        
        Args:
            event_data: Input TC event data (flat structure)
            
        Returns:
            Structured TC event data according to CDM schema (nested structure)
        """
        try:
            tcevent_data = {
                "TropicalCycloneEvent": {
                    "Header": {
                        "TCEventID": event_data.get('tc_event_id')
                    },
                    "Attributes": {
                        "TCName": event_data.get('tc_name'),
                        "TCSize": event_data.get('tc_size'),
                        "TCWindSpeed": event_data.get('tc_wind_speed'),
                        "TCDuration": event_data.get('tc_duration'),
                        "TCPressure": event_data.get('tc_pressure'),
                        "TCSurge": event_data.get('tc_surge'),
                        "DistanceEye": event_data.get('distance_eye'),
                        "DistancePath": event_data.get('distance_path'),
                        "StartDate": event_data.get('start_date'),
                        "EndDate": event_data.get('end_date')
                    },
                    "Alert": {
                        "WarningCentre": event_data.get('warning_centre'),
                        "CycloneAlert": event_data.get('cyclone_alert')
                    },
                    "Warning": {
                        "Date": event_data.get('warning_date'),
                        "Time": event_data.get('warning_time'),
                        "Position": event_data.get('position'),
                        "Intensity": event_data.get('intensity'),
                        "WindSpeeds": event_data.get('wind_speeds'),
                        "ExpectedTime": event_data.get('expected_time'),
                        "ExpectedDate": event_data.get('expected_date'),
                        "ExpectedLocation": event_data.get('expected_location'),
                        "AnticipatedStormSurgeHeight": event_data.get('anticipated_surge_height'),
                        "PotentialDamage": event_data.get('potential_damage'),
                        "SuggestedActions": event_data.get('suggested_actions')
                    },
                    "Triggers": {
                        "currency": event_data.get('currency'),
                        "EvacuationTrigger": event_data.get('evacuation_trigger'),
                        "PropertyDamageTrigger": event_data.get('property_damage_trigger'),
                        "BusinessInteruptionTrigger": event_data.get('business_interruption_trigger'),
                        "AdditionalExpensesTrigger": event_data.get('additional_expenses_trigger')
                    }
                }
            }
            
            # Remove None values recursively
            def remove_nones(d):
                if not isinstance(d, dict):
                    return d
                return {k: remove_nones(v) for k, v in d.items() if v is not None}
                
            return remove_nones(tcevent_data)
            
        except Exception as e:
            raise ValueError(f"Error creating TC event mapping: {str(e)}")
