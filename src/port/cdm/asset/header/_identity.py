# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""Header identifiers and valuation sections of the asset header schema."""

HEADER = {
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
}

VALUATION = {
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
}
