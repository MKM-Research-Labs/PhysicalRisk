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
Storm Time Series Common Data Model (CDM) implementation.

Provides standardized schema for storm event time series data
used in flood simulation and scenario analysis.
"""

from typing import Dict, List

from .base import BaseCDM


class StormTimeSeriesCDM(BaseCDM):
    """
    Storm Time Series Common Data Model (CDM) implementation.

    Provides schema for time-varying storm data during
    flood events and scenarios.
    """

    def __init__(self):
        """Initialize the Storm Time Series CDM with schema definition."""
        self._schema = {
            "StormTimeSeries": {
                "Header": {
                    "TimeSeriesID": {
                        "type": "text",
                        "description": "Unique identifier for the time series"
                    },
                    "CatchmentID": {
                        "type": "text",
                        "description": "Identifier for the river catchment"
                    },
                    "StormEventID": {
                        "type": "text",
                        "description": "Reference to parent storm event"
                    },
                    "SimulationName": {
                        "type": "text",
                        "description": "Name of the simulation scenario"
                    }
                },
                "Parameters": {
                    "StartDateTime": {
                        "type": "datetime",
                        "description": "Start of time series"
                    },
                    "EndDateTime": {
                        "type": "datetime",
                        "description": "End of time series"
                    },
                    "TimeStepMinutes": {
                        "type": "integer",
                        "description": "Time step interval in minutes"
                    },
                    "NumberOfSteps": {
                        "type": "integer",
                        "description": "Total number of time steps"
                    }
                },
                "Reading": {
                    "Timestamp": {
                        "type": "datetime",
                        "description": "Timestamp of the reading"
                    },
                    "RainfallMm": {
                        "type": "decimal",
                        "description": "Rainfall intensity in mm"
                    },
                    "WindSpeedKmh": {
                        "type": "decimal",
                        "description": "Wind speed in km/h"
                    },
                    "PressureMbar": {
                        "type": "decimal",
                        "description": "Atmospheric pressure in millibars"
                    },
                    "StormSurgeM": {
                        "type": "decimal",
                        "description": "Storm surge height in meters"
                    },
                    "AlertLevel": {
                        "type": "menu",
                        "options": ["Normal", "Alert", "Warning", "Severe"],
                        "description": "Current alert level"
                    }
                }
            }
        }

    @property
    def schema(self) -> Dict:
        """Return the CDM schema."""
        return self._schema

    def validate(self, ts_data: dict) -> Dict[str, List[str]]:
        """
        Validate storm time series data against the CDM schema.

        Args:
            ts_data: Storm time series data to validate

        Returns:
            Dictionary of validation errors by section
        """
        errors = {}

        try:
            header = ts_data.get("StormTimeSeries", {}).get("Header", {})
            header_errors = []

            if not header.get("TimeSeriesID"):
                header_errors.append("Missing required field: TimeSeriesID")

            if not header.get("CatchmentID"):
                header_errors.append("Missing recommended field: CatchmentID")

            if header_errors:
                errors["Header"] = header_errors

            return errors

        except Exception as e:
            return {"validation_error": [str(e)]}

    def create_mapping(self, ts: dict) -> dict:
        """
        Create a flat dictionary from nested CDM structure.

        Args:
            ts: Nested storm time series data in CDM format

        Returns:
            Flat dictionary with snake_case keys
        """
        try:
            sts = ts.get('StormTimeSeries', {})
            header = sts.get('Header', {})
            params = sts.get('Parameters', {})

            ts_data = {
                # Header
                'time_series_id': header.get('TimeSeriesID'),
                'catchment_id': header.get('CatchmentID'),
                'storm_event_id': header.get('StormEventID'),
                'simulation_name': header.get('SimulationName'),

                # Parameters
                'start_datetime': params.get('StartDateTime'),
                'end_datetime': params.get('EndDateTime'),
                'time_step_minutes': params.get('TimeStepMinutes'),
                'number_of_steps': params.get('NumberOfSteps')
            }

            # Remove None values
            return {k: v for k, v in ts_data.items() if v is not None}

        except Exception as e:
            raise ValueError(f"Error creating storm time series mapping: {str(e)}")

    def create_reading_mapping(self, reading: dict) -> dict:
        """
        Create a flat dictionary from a single reading.

        Args:
            reading: Single reading data

        Returns:
            Flat dictionary with snake_case keys
        """
        return {
            'timestamp': reading.get('Timestamp'),
            'rainfall_mm': reading.get('RainfallMm'),
            'wind_speed_kmh': reading.get('WindSpeedKmh'),
            'pressure_mbar': reading.get('PressureMbar'),
            'storm_surge_m': reading.get('StormSurgeM'),
            'alert_level': reading.get('AlertLevel')
        }

    def get_required_fields(self) -> List[str]:
        """Return list of required fields."""
        return [
            'StormTimeSeries.Header.TimeSeriesID',
            'StormTimeSeries.Header.CatchmentID'
        ]


# Backwards compatibility alias
TCEventTSCDM = StormTimeSeriesCDM
