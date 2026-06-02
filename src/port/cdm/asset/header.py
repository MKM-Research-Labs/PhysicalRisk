# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""
Asset header schema — identifiers, valuation, attributes, construction, location.

Carries the full PropertyHeader schema as it existed in the legacy
property/schema/header.py. The residential/commercial split (e.g.
moving NumberBedrooms/CouncilTaxBand into asset/residential/header.py)
will happen on a later pass — this file is currently asset-wide so
the legacy property pipeline keeps emitting byte-identical JSON.
"""

HEADER_SCHEMA = {
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
        },
        "HeightMeters": {
            "type": "decimal",
            "description": "Building height in metres"
        },
        "IncomeGenerating": {
            "type": "menu",
            "options": ["Yes", "No"],
            "description": "Whether the property generates rental or other income"
        },
        "BuildingResidency": {
            "type": "menu",
            "options": ["Single Family", "Multi Family", "Mixed Use"],
            "description": "Building residency classification"
        },
        "OccupancyResidency": {
            "type": "menu",
            "options": ["Family resident", "Unoccupied", "Single", "HMO", "Other"],
            "description": "Detailed occupancy residency classification"
        },
        "RenovationRequired": {
            "type": "boolean",
            "description": "Whether the property requires renovation"
        },
        "HousingAssociation": {
            "type": "boolean",
            "description": "Indicates if property is owned by housing association"
        },
        "PayingBusinessRates": {
            "type": "boolean",
            "description": "Indicates if property is subject to business rates"
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
            "options": [
                "None", "On-street only", "Driveway only", "Garage only",
                "Driveway and garage", "Allocated space",
            ],
            "description": "Available parking facilities"
        },
        "AccessType": {
            "type": "menu",
            "options": ["Public road", "Private road", "Shared access", "Right of way"],
            "description": "Type of access to property"
        },
        "LastMajorWorksDate": {
            "type": "date",
            "description": "Date of last significant renovation/works"
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
        "BRIAdjustedFloorLevelMeters": {
            "type": "decimal",
            "description": (
                "Effective flood-threshold floor level (m) = FloorLevelMeters "
                "plus a Building Resilience Index credit derived from the BRI "
                "flood sub-score. A highly resilient (AA) building floods only "
                "once water rises well above its nominal floor. Used by the PRS "
                "flood event filter; falls back to FloorLevelMeters + a credit "
                "computed from BRIFloodScore when absent."
            )
        },
        "BasementPresent": {
            "type": "boolean",
            "description": "Indicates presence of basement"
        },
        "FloorType": {
            "type": "menu",
            "options": [
                "Suspended timber", "Solid concrete", "Suspended concrete",
                "Beam and block", "Mixed",
            ],
            "description": "Ground floor construction type"
        },
        "StiltsHeight": {
            "type": "decimal",
            "description": "Height of any stilts/pillars supporting property"
        },
        "PropertyHeight": {
            "type": "decimal",
            "description": "Total height of property in metres"
        },
        "RoofDetails": {
            "RoofCover": {
                "type": "menu",
                "options": ["Slate", "Clay tile", "Concrete tile", "Metal", "Felt", "Thatch", "Green roof", "Other"],
                "description": "Primary roof covering material"
            },
            "RoofGeometry": {
                "type": "menu",
                "options": ["Flat", "Gabled", "Hip", "Mansard", "Complex", "Barrel vault"],
                "description": "Roof shape / geometry"
            },
            "RoofPitch": {
                "type": "menu",
                "options": ["Flat (<5°)", "Low (5-20°)", "Medium (20-35°)", "Steep (>35°)"],
                "description": "Roof pitch category"
            },
            "RoofFrame": {
                "type": "menu",
                "options": ["Timber truss", "Timber rafter", "Steel", "Concrete", "Unknown"],
                "description": "Roof structural frame type"
            },
            "RoofDeck": {
                "type": "menu",
                "options": ["Plywood", "OSB", "Metal deck", "Concrete", "Sarking board", "Unknown"],
                "description": "Roof deck/substrate material"
            },
            "RoofYearReplaced": {
                "type": "integer",
                "description": "Year roof was last replaced (may differ from build year)"
            },
        },
        "SoftStory": {
            "type": "boolean",
            "description": "Ground floor structurally weaker than storeys above (OED SoftStory)"
        },
        "ShapeIrregularity": {
            "type": "menu",
            "options": ["None", "Plan", "Vertical", "Both"],
            "description": "Structural shape irregularity type (OED ShapeIrregularity)"
        },
        "BrickVeneer": {
            "type": "boolean",
            "description": "Non-structural masonry cladding over frame"
        },
        "GlassType": {
            "type": "menu",
            "options": ["Standard", "Laminated", "Tempered", "Impact resistant", "Unknown"],
            "description": "Structural glazing type (wind/impact resistance)"
        },
        "RetrofitYear": {
            "type": "integer",
            "description": "Year of last structural retrofit or seismic strengthening"
        },
        "HasCrippleWall": {
            "type": "boolean",
            "description": "Short wood-framed wall between foundation and first floor"
        },
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
        },
        "BuildingName": {
            "type": "string",
            "description": "Name of building if applicable"
        },
        "SubBuildingNumber": {
            "type": "string",
            "description": "Sub-unit number if applicable"
        },
        "SubBuildingName": {
            "type": "string",
            "description": "Name of sub-unit if applicable"
        },
        "AddressLine2": {
            "type": "string",
            "description": "Secondary address line"
        },
        "USRN": {
            "type": "string",
            "description": "Unique Street Reference Number"
        },
        "ElectoralWard": {
            "type": "string",
            "description": "Electoral ward name"
        },
        "ParliamentaryConstituency": {
            "type": "string",
            "description": "Parliamentary constituency name"
        },
        "LocalDensityHectare": {
            "type": "decimal",
            "description": "Number of properties per hectare"
        },
        "BritishNationalGrid": {
            "type": "string",
            "description": "OS National Grid reference"
        },
        "What3Words": {
            "type": "string",
            "description": "What3Words location identifier"
        }
    }
}
