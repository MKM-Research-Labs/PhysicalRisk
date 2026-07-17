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
Storm Event Common Data Model (CDM) implementation.
Based on Storm_Event_CDM v1 specification.

Includes CatchmentID for multi-catchment support.
"""

from typing import Dict, List

from .base import BaseCDM


class StormEventCDM(BaseCDM):
    """
    Storm Event Common Data Model (CDM) implementation.

    Provides a standardized schema and data transformation methods
    for storm event data (including tropical cyclones).
    """

    def __init__(self):
        """Initialize the Storm Event CDM with schema definition."""
        self._schema = {
            "StormEvent": {
                "Header": {
                    "StormEventID": {
                        "type": "text",
                        "description": "Unique identifier for a storm event"
                    },
                    "CatchmentID": {
                        "type": "text",
                        "description": "Identifier for the river catchment (e.g., 'thames', 'rhine')"
                    }
                },
                "Attributes": {
                    "StormName": {
                        "type": "text",
                        "description": "Name of the storm"
                    },
                    "StormSize": {
                        "type": "integer",
                        "description": "Size of the storm (diameter) in km"
                    },
                    "StormWindSpeed": {
                        "type": "integer",
                        "description": "Wind speed in km/h"
                    },
                    "StormDuration": {
                        "type": "integer",
                        "description": "Number of days"
                    },
                    "StormPressure": {
                        "type": "integer",
                        "description": "Low atmospheric pressure at the centre in millibars"
                    },
                    "StormSurge": {
                        "type": "integer",
                        "description": "Elevated sea level rise above normal in m"
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
                    "StormAlert": {
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
                        "description": "Location of storm"
                    },
                    "Intensity": {
                        "type": "integer",
                        "description": "Category of the storm"
                    },
                    "WindSpeeds": {
                        "type": "integer",
                        "description": "Wind speed at storm warning time in km/h"
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
                        "description": "Description of expected landfall location"
                    },
                    "AnticipatedStormSurgeHeight": {
                        "type": "decimal",
                        "description": "Expected storm surge height above normal in m"
                    },
                    "PotentialDamage": {
                        "type": "text",
                        "description": "Description of expected damage"
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
                    "BusinessInterruptionTrigger": {
                        "type": "decimal",
                        "description": "Costs to cover business interruption"
                    },
                    "AdditionalExpensesTrigger": {
                        "type": "decimal",
                        "description": "Operational expenses and other immediate costs"
                    }
                }
            }
        }

    @property
    def schema(self) -> Dict:
        """Return the CDM schema."""
        return self._schema

    def validate(self, event_data: dict) -> Dict[str, List[str]]:
        """
        Validate storm event data against the CDM schema.

        Args:
            event_data: Storm event data to validate

        Returns:
            Dictionary of validation errors by section
        """
        errors = {}

        try:
            header = event_data.get("StormEvent", {}).get("Header", {})
            header_errors = []

            if not header.get("StormEventID"):
                header_errors.append("Missing required field: StormEventID")

            if not header.get("CatchmentID"):
                header_errors.append("Missing recommended field: CatchmentID")

            if header_errors:
                errors["Header"] = header_errors

            return errors

        except Exception as e:
            return {"validation_error": [str(e)]}

    def create_mapping(self, event: dict) -> dict:
        """
        Create a flat dictionary from nested CDM structure.

        Args:
            event: Nested storm event data in CDM format

        Returns:
            Flat dictionary with snake_case keys
        """
        try:
            se = event.get('StormEvent', {})
            header = se.get('Header', {})
            attrs = se.get('Attributes', {})
            alert = se.get('Alert', {})
            warning = se.get('Warning', {})
            triggers = se.get('Triggers', {})

            event_data = {
                # Header
                'storm_event_id': header.get('StormEventID'),
                'catchment_id': header.get('CatchmentID'),

                # Attributes
                'storm_name': attrs.get('StormName'),
                'storm_size': attrs.get('StormSize'),
                'storm_wind_speed': attrs.get('StormWindSpeed'),
                'storm_duration': attrs.get('StormDuration'),
                'storm_pressure': attrs.get('StormPressure'),
                'storm_surge': attrs.get('StormSurge'),
                'start_date': attrs.get('StartDate'),
                'end_date': attrs.get('EndDate'),

                # Alert
                'warning_centre': alert.get('WarningCentre'),
                'storm_alert': alert.get('StormAlert'),

                # Warning
                'warning_date': warning.get('Date'),
                'warning_time': warning.get('Time'),
                'position': warning.get('Position'),
                'intensity': warning.get('Intensity'),
                'wind_speeds': warning.get('WindSpeeds'),
                'expected_time': warning.get('ExpectedTime'),
                'expected_date': warning.get('ExpectedDate'),
                'expected_location': warning.get('ExpectedLocation'),
                'anticipated_surge_height': warning.get('AnticipatedStormSurgeHeight'),
                'potential_damage': warning.get('PotentialDamage'),

                # Triggers
                'currency': triggers.get('currency'),
                'evacuation_trigger': triggers.get('EvacuationTrigger'),
                'property_damage_trigger': triggers.get('PropertyDamageTrigger'),
                'business_interruption_trigger': triggers.get('BusinessInterruptionTrigger'),
                'additional_expenses_trigger': triggers.get('AdditionalExpensesTrigger')
            }

            # Remove None values
            return {k: v for k, v in event_data.items() if v is not None}

        except Exception as e:
            raise ValueError(f"Error creating storm event mapping: {str(e)}")

    def get_required_fields(self) -> List[str]:
        """Return list of required fields."""
        return ['StormEvent.Header.StormEventID', 'StormEvent.Header.CatchmentID']


# Backwards compatibility alias
TCEventCDM = StormEventCDM
