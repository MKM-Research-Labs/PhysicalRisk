# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""Location section of the asset header schema."""

LOCATION = {
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
