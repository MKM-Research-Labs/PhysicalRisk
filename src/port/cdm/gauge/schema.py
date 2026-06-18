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

"""Flood Gauge CDM schema definition."""

GAUGE_SCHEMA = {
    "FloodGauge": {
        "Header": {
            "GaugeID": {
                "type": "text",
                "description": "Unique identifier for the sensor"
            },
            "CatchmentID": {
                "type": "text",
                "description": "Identifier for the river catchment (e.g., 'thames', 'rhine')"
            },
            "GaugeName": {
                "type": "text",
                "description": "Human-readable name for the gauge"
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
                    "options": [
                        "Staff gauge", "Wire-weight gauge", "Shaft encoder",
                        "Bubbler system", "Pressure transducer", "Radar gauge",
                        "Ultrasonic gauge"
                    ],
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
                    "options": [
                        "Fully operational", "Maintenance required",
                        "Temporarily offline", "Decommissioned"
                    ],
                    "description": "Current operational status"
                },
                "CertificationStatus": {
                    "type": "menu",
                    "options": [
                        "Fully certified", "Provisional",
                        "Under review", "Non-certified"
                    ],
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
                    "description": "Elevation above sea level in meters"
                },
                "elevation": {
                    "type": "decimal",
                    "description": "Elevation above sea level (alias for GroundLevelMeters)"
                },
                "TidalInfluence": {
                    "type": "menu",
                    "options": ["Non-tidal", "Tidal", "Partially tidal"],
                    "description": "Whether the gauge is influenced by tidal cycles"
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
                    "description": "How data can be accessed"
                }
            }
        },
        "FloodStage": {
            "UK": {
                "DecisionBody": {
                    "type": "text",
                    "description": "Governmental body responsible for flood decisions"
                },
                "FloodAlert": {
                    "type": "decimal",
                    "description": "Water level that triggers flood alert"
                },
                "FloodWarning": {
                    "type": "decimal",
                    "description": "Water level that triggers flood warning"
                },
                "SevereFloodWarning": {
                    "type": "decimal",
                    "description": "Water level that triggers severe flood warning"
                },
                "FlashMinor": {
                    "type": "decimal",
                    "description": "Minor flash-flood / storm-surge stage (gauge level, m). "
                                   "Computed as SevereFloodWarning + 3 m at generation time. "
                                   "Above this stage, properties whose Flash protection is "
                                   "graded only B are exposed."
                },
                "FlashMajor": {
                    "type": "decimal",
                    "description": "Major flash-flood / storm-surge stage (gauge level, m). "
                                   "Computed as SevereFloodWarning + 5 m at generation time. "
                                   "Above this stage, even Grade-A flash protection is overtopped."
                },
                "TsunamiMinor": {
                    "type": "decimal",
                    "description": "Minor tsunami stage (gauge level, m). Computed as "
                                   "SevereFloodWarning + 5 m at generation time. Properties "
                                   "with only Grade-B water (tsunami) protection are exposed "
                                   "above this stage."
                },
                "TsunamiMajor": {
                    "type": "decimal",
                    "description": "Major tsunami stage (gauge level, m). Computed as "
                                   "SevereFloodWarning + 10 m at generation time. Even "
                                   "Grade-A water (tsunami) protection is overtopped above this."
                }
            }
        },
        "NRFAMetadata": {
            "NRFAStationID": {
                "type": "text",
                "description": "NRFA station identifier linking to historical data (e.g., '39001')"
            },
            "GridReference": {
                "type": "text",
                "description": "UK National Grid Reference (e.g., 'TQ17786985')"
            },
            "CatchmentArea": {
                "type": "decimal",
                "description": "Upstream catchment area in km²"
            },
            "RecordStartDate": {
                "type": "date",
                "description": "Start date of historical flow record"
            },
            "RecordEndDate": {
                "type": "date",
                "description": "End date of historical flow record"
            },
            "MeanFlow": {
                "type": "decimal",
                "description": "Long-term mean daily flow (m³/s)"
            },
            "MedianFlow": {
                "type": "decimal",
                "description": "Long-term median daily flow (m³/s)"
            },
            "Q95Flow": {
                "type": "decimal",
                "description": "95th percentile flow - exceeded 5% of time (m³/s)"
            },
            "Q5Flow": {
                "type": "decimal",
                "description": "5th percentile flow - exceeded 95% of time (m³/s)"
            },
            "MaxRecordedFlow": {
                "type": "decimal",
                "description": "Maximum recorded daily mean flow (m³/s)"
            },
            "MaxRecordedFlowDate": {
                "type": "date",
                "description": "Date of maximum recorded flow"
            },
            "HistoricalDataFile": {
                "type": "text",
                "description": "Filename of associated historical data JSON (e.g., 'gaugehd_39001.json')"
            },
            "DatabaseSource": {
                "type": "text",
                "description": "Source database (e.g., 'UK National River Flow Archive')"
            },
            "FlowUnits": {
                "type": "text",
                "description": "Units for flow measurements (typically 'm3/s')"
            },
            "DataQualityNotes": {
                "type": "text",
                "description": "Notes on data quality or measurement issues"
            }
        }
    }
}
