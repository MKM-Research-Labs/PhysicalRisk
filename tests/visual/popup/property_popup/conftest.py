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

"""Shared fixtures for PropertyPopupBuilder tests."""
import pytest
import folium
from visual.popups.property_popup.builder import PropertyPopupBuilder

@pytest.fixture
def builder():
    return PropertyPopupBuilder()

@pytest.fixture
def prop():
    return {
        'PropertyHeader': {
            'Header': {'PropertyID': 'PROP-aabbccdd', 'propertyType': 'Residential', 'propertyStatus': 'Active'},
            'PropertyAttributes': {'PropertyType': 'Terraced House', 'NumberOfStoreys': 2},
            'Construction': {'ConstructionType': 'Brick'},
        },
    }

@pytest.fixture
def address():
    return {'building_number': '42', 'street_name': 'Flood Lane', 'town_city': 'London', 'post_code': 'SW1A 2AA'}

@pytest.fixture
def address_no_postcode():
    return {'building_number': '1', 'street_name': 'River Road', 'town_city': 'Oxford'}

@pytest.fixture
def flood_info():
    return {
        'nearest_gauge': 'Chelsea Gauge', 'distance_to_gauge': 0.8,
        'water_level': 3.2, 'flood_depth': 0.5, 'risk_value': 0.45,
        'risk_level': 'High', 'value_at_risk': 250000,
    }

@pytest.fixture
def rloan_info():
    return {
        'Header': {'MortgageID': 'MTG-001'},
        'FinancialTerms': {'OriginalLoan': 300000, 'OriginalLendingRate': 0.04, 'TermYears': 25, 'LoanToValueRatio': 0.75},
        'Application': {'MortgageProvider': 'Thames Bank'},
    }

