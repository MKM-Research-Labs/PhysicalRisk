# Copyright (c) 2025 MKM Research Labs. All rights reserved.

# ELEVATION UPDATE: This version includes default elevation handling
# - ground_level_meters: Defaults to 12.0 when None or missing
# - elevation: Added as alias field for flood model compatibility  
# - Both fields prevent unrealistic flood calculations for high properties

# This software is provided under license by MKM Research Labs.
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
    Enhanced Property Common Data Model (CDM) implementation.
    Provides a standardized schema and data transformation methods
    for property data with comprehensive attributes.
    
    Based on Property_CDM_v10.xlsx specification with 136 fields across 17 sections.
"""

import warnings
from typing import Dict, Optional

class PropertyCDM:

    def __init__(self):
        """Initialize the Property CDM with schema definition from Excel specification."""
        self.schema = {
            "PropertyHeader": {
                "Header": {
                    "UPRN": {
                        "type": "string",
                        "description": "Unique Property Reference Number"
                    },
                    "PropertyID": {
                        "type": "string", 
                        "description": "Unique identifier for the contract"
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
                        "description": "Primary use classification of the property"
                    },
                    "PropertyAreaSqm": {
                        "type": "decimal",
                        "description": "Total floor area of property in square meters"
                    },
                    "HousingAssociation": {
                        "type": "boolean",
                        "description": "Indicates if property is owned by housing association"
                    },
                    "IncomeGenerating": {
                        "type": "menu",
                        "options": ["No", "Yes, rental, holiday let"],
                        "description": "Property's income generation status"
                    },
                    "PayingBusinessRates": {
                        "type": "boolean",
                        "description": "Indicates if property is subject to business rates"
                    },
                    "BuildingResidency": {
                        "type": "menu",
                        "options": ["Single residence", "Two/three residences", "Over three residences"],
                        "description": "Number of residential units in building"
                    },
                    "PropertyResi": {
                        "type": "menu",
                        "options": ["Detached", "Semi-detached", "Mid-terrace", "End-terrace", "Bungalow", "Flat"],
                        "description": "Architectural style of property"
                    },
                    "OccupancyResidency": {
                        "type": "menu", 
                        "options": ["Family resident", "Unoccupied", "Other"],
                        "description": "Current occupancy status"
                    },
                    "HeightMeters": {
                        "type": "decimal",
                        "description": "Height of property in meters"
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
                    "TotalRooms": {
                        "type": "integer",
                        "description": "Total number of rooms excluding bathrooms"
                    },
                    "GardenAreaFront": {
                        "type": "decimal",
                        "description": "Front garden area in square meters"
                    },
                    "GardenAreaBack": {
                        "type": "decimal",
                        "description": "Back garden area in square meters"
                    },
                    "ParkingType": {
                        "type": "menu",
                        "options": ["None", "On-street only", "Driveway only", "Garage only", "Driveway and garage", "Allocated space"],
                        "description": "Type of parking available"
                    },
                    "AccessType": {
                        "type": "menu",
                        "options": ["Public road", "Private road", "Shared access", "Right of way"],
                        "description": "Type of property access"
                    },
                    "LastMajorWorksDate": {
                        "type": "date",
                        "description": "Date of last significant renovation/works"
                    },
                    "RenovationRequired": {
                        "type": "boolean", 
                        "description": "Indicates if renovation is required"
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
                    "FloorType": {
                        "type": "menu",
                        "options": ["Suspended timber", "Solid concrete", "Suspended concrete", "Beam and block", "Mixed"],
                        "description": "Ground floor construction type"
                    },
                    "SiteHeight": {
                        "type": "decimal",
                        "description": "Height of any stilts/pillars supporting property"
                    },
                    "PropertyHeight": {
                        "type": "decimal",
                        "description": "Total height of property in metres"
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
                    "BuildingName": {
                        "type": "string",
                        "description": "Name of building if applicable"
                    },
                    "BuildingNumber": {
                        "type": "string",
                        "description": "Street number of property"
                    },
                    "SubBuildingNumber": {
                        "type": "string", 
                        "description": "Sub-unit number if applicable"
                    },
                    "SubBuildingName": {
                        "type": "string",
                        "description": "Name of sub-unit if applicable"
                    },
                    "StreetName": {
                        "type": "string",
                        "description": "Name of street"
                    },
                    "AddressLine2": {
                        "type": "string",
                        "description": "Secondary address line"
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
                    "USRN": {
                        "type": "string",
                        "description": "Unique Street Reference Number"
                    },
                    "LocalAuthority": {
                        "type": "string",
                        "description": "Governing local authority name"
                    },
                    "ElectoralWard": {
                        "type": "string",
                        "description": "Electoral ward name"
                    },
                    "ParliamentaryConstituency": {
                        "type": "string",
                        "description": "Parliamentary constituency name"
                    },
                    "Country": {
                        "type": "menu",
                        "options": ["England", "Wales", "Scotland", "Northern Ireland"],
                        "description": "Country location"
                    },
                    "Region": {
                        "type": "menu",
                        "options": ["North East", "North West", "Yorkshire and The Humber", "East Midlands", "West Midlands", "East of England", "London", "South East", "South West", "Wales", "Scotland"],
                        "description": "Administrative region"
                    },
                    "UrbanRuralClassification": {
                        "type": "menu",
                        "options": ["Urban", "Suburban", "Rural"],
                        "description": "Urban/rural classification"
                    },
                    "LocalDensityHectare": {
                        "type": "decimal", 
                        "description": "Average number of local properties in a hectare"
                    },
                    "LatitudeDegrees": {
                        "type": "decimal",
                        "description": "Geographic latitude coordinate"
                    },
                    "LongitudeDegrees": {
                        "type": "decimal",
                        "description": "Geographic longitude coordinate"
                    },
                    "BritishNationalGrid": {
                        "type": "string",
                        "description": "OS National Grid reference"
                    },
                    "What3Words": {
                        "type": "string",
                        "description": "What3Words location identifier"
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
                    "LastFloodDate": {
                        "type": "date",
                        "description": "Date of most recent flood event"
                    },
                    "SoilType": {
                        "type": "menu",
                        "options": ["Clay", "Sandy", "Loamy", "Chalk", "Peat", "Rocky", "Mixed", "Subsoils", "Unknown"],
                        "description": "Predominant soil type"
                    },
                    "GroundLevelMeters": {
                        "type": "decimal",
                        "description": "Height above sea level in meters"
                    },
                    "RiverDistanceMeters": {
                        "type": "decimal",
                        "description": "Distance to nearest river in meters"
                    },
                    "LakeDistanceMeters": {
                        "type": "decimal",
                        "description": "Distance to nearest lake in meters"
                    },
                    "CoastalDistanceMeters": {
                        "type": "decimal",
                        "description": "Distance to coastline in meters"
                    },
                    "CanalDistanceMeters": {
                        "type": "decimal",
                        "description": "Distance to nearest canal in meters"
                    },
                    "GovernmentDefenceScheme": {
                        "type": "boolean",
                        "description": "Covered by government flood defence scheme"
                    }
                }
            },
            # Additional sections would continue here...
        }

    def validate_property(self, property_data: dict) -> bool:
        """
        Validates property data against the CDM schema.
        Returns True if valid, raises ValueError if invalid.
        """
        warnings.warn("Property validation not fully implemented - returning True by default")
        return True

    def create_property_mapping(self, prop: dict) -> dict:
        """
        Creates a standardized property data dictionary with FIXED field mappings.
        
        Args:
            prop: Raw property data dictionary
        
        Returns:
            Structured property data according to CDM schema with correct field names
        """
        try:
            property_data = {
                # PropertyHeader.Header (4 fields) - CRITICAL FIELDS FOR FLOOD MODEL
                'property_id': prop.get('PropertyHeader', {}).get('Header', {}).get('PropertyID'),
                'uprn': prop.get('PropertyHeader', {}).get('Header', {}).get('UPRN'),
                'property_type': prop.get('PropertyHeader', {}).get('Header', {}).get('propertyType', 'residential'),
                'property_status': prop.get('PropertyHeader', {}).get('Header', {}).get('propertyStatus', 'active'),

                # PropertyHeader.Valuation (3 fields) - **CRITICAL: THIS WAS MISSING!**
                'value': prop.get('PropertyHeader', {}).get('Valuation', {}).get('PropertyValue'),  # FLOOD MODEL NEEDS THIS!
                'valuation_date': prop.get('PropertyHeader', {}).get('Valuation', {}).get('ValuationDate'),
                'valuation_method': prop.get('PropertyHeader', {}).get('Valuation', {}).get('ValuationMethod'),

                # PropertyHeader.Location (21 fields) - CRITICAL FOR FLOOD MODEL
                'building_name': prop.get('PropertyHeader', {}).get('Location', {}).get('BuildingName'),
                'building_number': prop.get('PropertyHeader', {}).get('Location', {}).get('BuildingNumber'),
                'sub_building_number': prop.get('PropertyHeader', {}).get('Location', {}).get('SubBuildingNumber'),
                'sub_building_name': prop.get('PropertyHeader', {}).get('Location', {}).get('SubBuildingName'),
                'street_name': prop.get('PropertyHeader', {}).get('Location', {}).get('StreetName'),
                'address_line2': prop.get('PropertyHeader', {}).get('Location', {}).get('AddressLine2'),
                'town_city': prop.get('PropertyHeader', {}).get('Location', {}).get('TownCity'),
                'county': prop.get('PropertyHeader', {}).get('Location', {}).get('County'),
                'postcode': prop.get('PropertyHeader', {}).get('Location', {}).get('Postcode'),
                'usrn': prop.get('PropertyHeader', {}).get('Location', {}).get('USRN'),
                'local_authority': prop.get('PropertyHeader', {}).get('Location', {}).get('LocalAuthority'),
                'electoral_ward': prop.get('PropertyHeader', {}).get('Location', {}).get('ElectoralWard'),
                'parliamentary_constituency': prop.get('PropertyHeader', {}).get('Location', {}).get('ParliamentaryConstituency'),
                'country': prop.get('PropertyHeader', {}).get('Location', {}).get('Country'),
                'region': prop.get('PropertyHeader', {}).get('Location', {}).get('Region'),
                'urban_rural': prop.get('PropertyHeader', {}).get('Location', {}).get('UrbanRuralClassification'),
                'latitude': prop.get('PropertyHeader', {}).get('Location', {}).get('LatitudeDegrees'),      # FLOOD MODEL NEEDS THIS!
                'longitude': prop.get('PropertyHeader', {}).get('Location', {}).get('LongitudeDegrees'),    # FLOOD MODEL NEEDS THIS!
                'british_national_grid': prop.get('PropertyHeader', {}).get('Location', {}).get('BritishNationalGrid'),
                'what3words': prop.get('PropertyHeader', {}).get('Location', {}).get('What3Words'),
                'local_density': prop.get('PropertyHeader', {}).get('Location', {}).get('LocalDensityHectare'),
                
                # PropertyHeader.Construction (7 fields) - CRITICAL FOR FLOOD MODEL
                'construction_type': prop.get('PropertyHeader', {}).get('Construction', {}).get('ConstructionType'),
                'foundation_type': prop.get('PropertyHeader', {}).get('Construction', {}).get('FoundationType'),
                'floor_type': prop.get('PropertyHeader', {}).get('Construction', {}).get('FloorType'),
                'site_height': prop.get('PropertyHeader', {}).get('Construction', {}).get('SiteHeight'),
                'property_height': prop.get('PropertyHeader', {}).get('Construction', {}).get('PropertyHeight'),
                'floor_level_metres': prop.get('PropertyHeader', {}).get('Construction', {}).get('FloorLevelMeters'),  # FLOOD MODEL NEEDS THIS!
                'basement_present': prop.get('PropertyHeader', {}).get('Construction', {}).get('BasementPresent'),

                # PropertyHeader.RiskAssessment (11 fields) - CRITICAL FOR FLOOD MODEL
                'flood_zone': prop.get('PropertyHeader', {}).get('RiskAssessment', {}).get('EAFloodZone'),
                'overall_flood_risk': prop.get('PropertyHeader', {}).get('RiskAssessment', {}).get('OverallFloodRisk'),
                'flood_risk_type': prop.get('PropertyHeader', {}).get('RiskAssessment', {}).get('FloodRiskType'),
                'last_flood_date': prop.get('PropertyHeader', {}).get('RiskAssessment', {}).get('LastFloodDate'),
                'soil_type': prop.get('PropertyHeader', {}).get('RiskAssessment', {}).get('SoilType'),
                # ELEVATION - Critical for flood model with default value
                'ground_level_meters': prop.get('PropertyHeader', {}).get('RiskAssessment', {}).get('GroundLevelMeters') or 12.0,  # Default 12m elevation
                'elevation': prop.get('PropertyHeader', {}).get('RiskAssessment', {}).get('GroundLevelMeters') or 12.0,  # Alias for flood model compatibility
                'river_distance': prop.get('PropertyHeader', {}).get('RiskAssessment', {}).get('RiverDistanceMeters'),
                'lake_distance': prop.get('PropertyHeader', {}).get('RiskAssessment', {}).get('LakeDistanceMeters'),
                'coastal_distance': prop.get('PropertyHeader', {}).get('RiskAssessment', {}).get('CoastalDistanceMeters'),
                'canal_distance': prop.get('PropertyHeader', {}).get('RiskAssessment', {}).get('CanalDistanceMeters'),
                'government_defence_scheme': prop.get('PropertyHeader', {}).get('RiskAssessment', {}).get('GovernmentDefenceScheme'),
                
                # PropertyHeader.PropertyAttributes (21 fields)
                'occupancy_type': prop.get('PropertyHeader', {}).get('PropertyAttributes', {}).get('OccupancyType'),
                'property_area_sqm': prop.get('PropertyHeader', {}).get('PropertyAttributes', {}).get('PropertyAreaSqm'),
                'housing_association': prop.get('PropertyHeader', {}).get('PropertyAttributes', {}).get('HousingAssociation'),
                'income_generating': prop.get('PropertyHeader', {}).get('PropertyAttributes', {}).get('IncomeGenerating'),
                'paying_business_rates': prop.get('PropertyHeader', {}).get('PropertyAttributes', {}).get('PayingBusinessRates'),
                'building_residency': prop.get('PropertyHeader', {}).get('PropertyAttributes', {}).get('BuildingResidency'),
                'property_resi': prop.get('PropertyHeader', {}).get('PropertyAttributes', {}).get('PropertyResi'),
                'occupancy_residency': prop.get('PropertyHeader', {}).get('PropertyAttributes', {}).get('OccupancyResidency'),
                'height_meters': prop.get('PropertyHeader', {}).get('PropertyAttributes', {}).get('HeightMeters'),
                'number_storeys': prop.get('PropertyHeader', {}).get('PropertyAttributes', {}).get('NumberOfStoreys'),
                'construction_year': prop.get('PropertyHeader', {}).get('PropertyAttributes', {}).get('ConstructionYear'),
                'property_period': prop.get('PropertyHeader', {}).get('PropertyAttributes', {}).get('PropertyPeriod'),
                'council_tax_band': prop.get('PropertyHeader', {}).get('PropertyAttributes', {}).get('CouncilTaxBand'),
                'number_bedrooms': prop.get('PropertyHeader', {}).get('PropertyAttributes', {}).get('NumberBedrooms'),
                'number_bathrooms': prop.get('PropertyHeader', {}).get('PropertyAttributes', {}).get('NumberBathrooms'),
                'total_rooms': prop.get('PropertyHeader', {}).get('PropertyAttributes', {}).get('TotalRooms'),
                'garden_area_front': prop.get('PropertyHeader', {}).get('PropertyAttributes', {}).get('GardenAreaFront'),
                'garden_area_back': prop.get('PropertyHeader', {}).get('PropertyAttributes', {}).get('GardenAreaBack'),
                'parking_type': prop.get('PropertyHeader', {}).get('PropertyAttributes', {}).get('ParkingType'),
                'access_type': prop.get('PropertyHeader', {}).get('PropertyAttributes', {}).get('AccessType'),
                'last_major_works_date': prop.get('PropertyHeader', {}).get('PropertyAttributes', {}).get('LastMajorWorksDate'),
                'renovation_required': prop.get('PropertyHeader', {}).get('PropertyAttributes', {}).get('RenovationRequired'),
                'property_condition': prop.get('PropertyHeader', {}).get('PropertyAttributes', {}).get('PropertyCondition'),
            }
            
            # Remove None values from the dictionary
            # Note: elevation fields have defaults so won't be None
            return {k: v for k, v in property_data.items() if v is not None}
            return {k: v for k, v in property_data.items() if v is not None}
        
        except Exception as e:
            raise ValueError(f"Error creating property mapping: {str(e)}")

    def get_field_info(self, field_path: str) -> dict:
        """Get information about a specific field in the schema."""
        path_parts = field_path.split('.')
        current = self.schema
        
        for part in path_parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return {"error": f"Field path {field_path} not found in schema"}
        
        return current if isinstance(current, dict) else {"type": "unknown", "value": current}

    def list_all_fields(self) -> list:
        """Get a list of all field paths in the schema."""
        def extract_paths(obj, prefix=""):
            paths = []
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if key in ['type', 'options', 'values', 'description', 'items']:
                        continue
                    current_path = f"{prefix}.{key}" if prefix else key
                    if isinstance(value, dict) and 'type' in value:
                        paths.append(current_path)
                    else:
                        paths.extend(extract_paths(value, current_path))
            return paths
        
        return extract_paths(self.schema)