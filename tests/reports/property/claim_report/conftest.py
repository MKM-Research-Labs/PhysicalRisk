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

"""Shared fixtures for claim report tests."""
from datetime import datetime
import pytest

@pytest.fixture
def styles():
    from reports.property.claim.styles import setup_styles
    return setup_styles()

@pytest.fixture
def sequence_lookup():
    return {
        'SEQ-001': {'sequence_type': 'doublet',    'num_storms': 2},
        'SEQ-002': {'sequence_type': 'cluster',    'num_storms': 3},
        'SEQ-003': {'sequence_type': 'persistent', 'num_storms': 5},
    }

@pytest.fixture
def flood_events():
    return [
        {'storm_id': 'STORM-001', 'sequence_id': 'SEQ-001', 'flood_depth_m': 0.42,
         'damage_ratio': 0.08, 'flooded': True, 'arrival_time_hrs': 12.0, 'peak_time_hrs': 18.5},
        {'storm_id': 'STORM-002', 'sequence_id': 'SEQ-001', 'flood_depth_m': 0.71,
         'damage_ratio': 0.15, 'flooded': True, 'arrival_time_hrs': 36.0, 'peak_time_hrs': 44.0},
        {'storm_id': 'STORM-003', 'sequence_id': 'SEQ-002', 'flood_depth_m': 0.18,
         'damage_ratio': 0.02, 'flooded': True, 'arrival_time_hrs': 8.0, 'peak_time_hrs': 14.0},
        {'storm_id': 'STORM-004', 'sequence_id': None, 'flood_depth_m': 0.0,
         'damage_ratio': 0.0, 'flooded': False, 'arrival_time_hrs': 20.0, 'peak_time_hrs': 26.0},
    ]

@pytest.fixture
def prop_data(flood_events):
    return {
        'property_id': 'PROP-00001234', 'property_type': 'residential',
        'construction_year': 1985, 'flood_zone': 'Zone 2', 'elevation_m': 8.5,
        'floor_level_m': 0.15,
        'location': {'latitude': 51.431, 'longitude': -0.321},
        'flood_events': flood_events,
    }

@pytest.fixture
def prop_record():
    return {
        'Header': {'PropertyID': 'PROP-00001234', 'catchment': 'Thames'},
        'Valuation': {'PropertyValue': 650000},
        'PropertyAttributes': {'PropertyType': 'Residential'},
        'Construction': {'ConstructionYear': 1985},
    }

@pytest.fixture
def rloan_record():
    return {
        'FinancialTerms': {'OriginalBalance': 400000},
        'CurrentStatus': {'OutstandingBalance': 320000},
    }

@pytest.fixture
def claim_ref():
    return 'CLM-00001234-20260312'

@pytest.fixture
def today():
    return datetime(2026, 3, 12, 10, 0, 0)
