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
