# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.
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
def mortgage_info():
    return {
        'Header': {'MortgageID': 'MTG-001'},
        'FinancialTerms': {'OriginalLoan': 300000, 'OriginalLendingRate': 0.04, 'TermYears': 25, 'LoanToValueRatio': 0.75},
        'Application': {'MortgageProvider': 'Thames Bank'},
    }

@pytest.fixture
def mortgage_risk_info():
    return {
        'MortgageID': 'MTG-001', 'loan_amount': 300000, 'interest_rate': 0.04,
        'monthly_payment': 1582.0, 'annual_payment': 18984.0, 'credit_spread': 0.015,
        'recovery_haircut': 0.1, 'mortgage_value': 285000.0, 'mortgage_value_at_risk': 12000.0,
        'flood_risk_level': 'Medium', 'flood_risk_value': 0.3, 'flood_depth': 0.2, 'property_value': 400000,
    }
