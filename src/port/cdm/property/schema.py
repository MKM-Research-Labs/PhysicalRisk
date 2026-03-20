# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.
#
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
Property CDM schema definition.

Defines PROPERTY_SCHEMA (the canonical 136-field, 17-section schema based on
Property_CDM v10) and DEFAULT_ELEVATION used when GroundLevelMeters is absent.
"""

# Default elevation when not specified (prevents unrealistic flood calculations)
DEFAULT_ELEVATION: float = 12.0

PROPERTY_SCHEMA = {
    "PropertyHeader": {
        "Header": {
            "UPRN": {
                "type": "string",
                "description": "Unique Property Reference Number"
            },
            "PropertyID": {
                "type": "string",
                "description": "Unique identifier for the property"
            },
            "CatchmentID": {
                "type": "string",
                "description": "Identifier for the river catchment (e.g., 'thames', 'rhine')"
            },
            "propertyType": {
                "type": "menu",
                "options": ["residential", "commercial", "industrial"],
                "description": "Basic property type classification"
            },
            "propertyStatus": {
                "type": "menu",
                "options": ["active", "inactive", "under_construction"],
                "description": "Current status of property"
            }
        },
        "Valuation": {
            "PropertyValue": {
                "type": "decimal",
                "description": "Current market value of the property"
            },
            "ValuationDate": {
                "type": "date",
                "description": "Date of last valuation"
            },
            "ValuationMethod": {
                "type": "menu",
                "options": ["Market comparison", "Income approach", "Cost approach", "Automated valuation"],
                "description": "Method used for valuation"
            }
        },
        "PropertyAttributes": {
            "OccupancyType": {
                "type": "menu",
                "options": ["Residential owner-occupied", "Second home", "Static caravan", "Vacant"],
                "description": "Primary use classification"
            },
            "PropertyAreaSqm": {
                "type": "decimal",
                "description": "Total floor area in square meters"
            },
            "PropertyResi": {
                "type": "menu",
                "options": ["Detached", "Semi-detached", "Mid-terrace", "End-terrace", "Bungalow", "Flat"],
                "description": "Residential property type"
            },
            "NumberOfStoreys": {
                "type": "integer",
                "description": "Number of floors in property"
            },
            "ConstructionYear": {
                "type": "integer",
                "description": "Year property was built"
            },
            "PropertyPeriod": {
                "type": "menu",
                "options": ["Pre-1919", "1919-1944", "1945-1975", "1976-1999", "2000-2008", "2009-Present"],
                "description": "Construction period classification"
            },
            "CouncilTaxBand": {
                "type": "menu",
                "options": ["A", "B", "C", "D", "E", "F", "G", "H"],
                "description": "Council tax valuation band"
            },
            "NumberBedrooms": {
                "type": "integer",
                "description": "Total number of bedrooms"
            },
            "NumberBathrooms": {
                "type": "integer",
                "description": "Total number of bathrooms"
            },
            "PropertyCondition": {
                "type": "menu",
                "options": ["Excellent", "Good", "Fair", "Poor", "Very poor"],
                "description": "Overall condition of property"
            }
        },
        "Construction": {
            "ConstructionType": {
                "type": "menu",
                "options": ["Brick and block", "Timber frame", "Stone", "Modern methods", "Mixed construction"],
                "description": "Primary construction material/method"
            },
            "FoundationType": {
                "type": "menu",
                "options": ["Strip foundations", "Raft foundations", "Pile foundations", "Deep foundations", "Unknown"],
                "description": "Type of foundation system"
            },
            "FloorLevelMeters": {
                "type": "decimal",
                "description": "Height of ground floor above ground level in metres"
            },
            "BasementPresent": {
                "type": "boolean",
                "description": "Indicates presence of basement"
            }
        },
        "Location": {
            "BuildingNumber": {
                "type": "string",
                "description": "Street number of property"
            },
            "StreetName": {
                "type": "string",
                "description": "Name of street"
            },
            "TownCity": {
                "type": "string",
                "description": "Town or city name"
            },
            "County": {
                "type": "string",
                "description": "County name"
            },
            "Postcode": {
                "type": "string",
                "description": "Property postcode"
            },
            "LocalAuthority": {
                "type": "string",
                "description": "Governing local authority name"
            },
            "Country": {
                "type": "menu",
                "options": ["England", "Wales", "Scotland", "Northern Ireland"],
                "description": "Country location"
            },
            "Region": {
                "type": "menu",
                "options": [
                    "North East", "North West", "Yorkshire and The Humber",
                    "East Midlands", "West Midlands", "East of England",
                    "London", "South East", "South West", "Wales", "Scotland",
                ],
                "description": "Administrative region"
            },
            "UrbanRuralClassification": {
                "type": "menu",
                "options": ["Urban", "Suburban", "Rural"],
                "description": "Urban/rural classification"
            },
            "LatitudeDegrees": {
                "type": "decimal",
                "description": "Geographic latitude coordinate"
            },
            "LongitudeDegrees": {
                "type": "decimal",
                "description": "Geographic longitude coordinate"
            }
        },
        "RiskAssessment": {
            "EAFloodZone": {
                "type": "menu",
                "options": ["Zone 1", "Zone 2", "Zone 3a", "Zone 3b"],
                "description": "Environment Agency flood zone"
            },
            "OverallFloodRisk": {
                "type": "menu",
                "options": ["Very low", "Low", "Medium", "High", "Very high"],
                "description": "Overall flood risk assessment"
            },
            "FloodRiskType": {
                "type": "menu",
                "options": ["River", "Surface water", "Groundwater", "Coastal", "Multiple"],
                "description": "Primary type of flood risk"
            },
            "GroundLevelMeters": {
                "type": "decimal",
                "description": "Height above sea level in meters"
            },
            "RiverDistanceMeters": {
                "type": "decimal",
                "description": "Distance to nearest river in meters"
            }
        }
    },
    "ProtectionMeasures": {
        "RiskAssessment": {
            "InsurancePremium": {
                "type": "decimal",
                "description": "Annual insurance premium in local currency"
            },
            "RiskRating": {
                "type": "menu",
                "options": ["Very low", "Low", "Medium", "High", "Very high"],
                "description": "Overall risk rating"
            }
        },
        "ResilienceMeasures": {
            "FloodGates":          {"type": "boolean", "description": "Flood gates installed"},
            "FloodBarriers":       {"type": "boolean", "description": "Flood barriers installed"},
            "SumpPump":            {"type": "boolean", "description": "Sump pump installed"},
            "FloodWarningSystem":  {"type": "boolean", "description": "Flood warning system in place"}
        }
    },
    "TransactionHistory": {
        "Purchase": {
            "PurchaseDate":      {"type": "date",    "description": "Date of purchase"},
            "PurchasePriceGbp":  {"type": "decimal", "description": "Purchase price in GBP"}
        },
        "Rental": {
            "MonthlyRentGbp":  {"type": "decimal", "description": "Monthly rent in GBP"},
            "RentalYield":     {"type": "decimal", "description": "Annual rental yield percentage"}
        }
    }
}
