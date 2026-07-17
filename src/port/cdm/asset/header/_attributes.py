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

"""Property attributes section of the asset header schema."""

PROPERTY_ATTRIBUTES = {
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
}
