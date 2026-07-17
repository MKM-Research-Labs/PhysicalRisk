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
