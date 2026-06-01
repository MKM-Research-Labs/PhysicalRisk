# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Shared fixtures for visual.popups.popup_builder tests."""

import pytest

from visual.popups.popup_builder import PopupBuilder


@pytest.fixture
def builder():
    return PopupBuilder()


# ---------------------------------------------------------------------------
# Synthetic data fixtures (shared across popup_integration parts)
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_property():
    return {
        'PropertyHeader': {
            'Header': {
                'PropertyID': 'PROP-INTG-001',
                'propertyType': 'Residential',
                'propertyStatus': 'Active',
            },
            'PropertyAttributes': {
                'PropertyType': 'Terraced House',
                'NumberOfStoreys': 2,
                'ConstructionYear': 1985,
            },
            'Construction': {'ConstructionType': 'Brick'},
            'Location': {
                'LatitudeDegrees': 51.5074,
                'LongitudeDegrees': -0.1278,
                'BuildingNumber': '123',
                'StreetName': 'Test Street',
                'TownCity': 'London',
                'Postcode': 'SW1A 1AA',
            },
        },
        'FloodRisk': 'Medium',
        'ThamesProximity': 'Close',
        'GroundElevation': 10.0,
        'ElevationEstimated': False,
        'PropertyValue': 500000,
    }


@pytest.fixture
def sample_address():
    return {
        'building_number': '123',
        'street_name': 'Test Street',
        'town_city': 'London',
        'post_code': 'SW1A 1AA',
    }


@pytest.fixture
def sample_mortgage():
    return {
        'Header': {'RLoanID': 'MTG-INTG-001'},
        'FinancialTerms': {
            'OriginalLoan': 400000,
            'OriginalLendingRate': 0.035,
            'TermYears': 25,
            'LoanToValueRatio': 0.8,
        },
        'Application': {'MortgageProvider': 'Test Bank Ltd'},
    }


@pytest.fixture
def sample_flood_info():
    return {
        'nearest_gauge': 'Test Thames Gauge',
        'distance_to_gauge': 0.5,
        'water_level': 3.0,
        'flood_depth': 0.0,
        'risk_value': 0.3,
        'risk_level': 'Medium',
        'value_at_risk': 150000,
    }


@pytest.fixture
def sample_gauge_info():
    return {
        'Header': {
            'GaugeID': 'GAUGE-INTG-001',
            'GaugeName': 'Test Thames Gauge',
        },
        'SensorDetails': {
            'GaugeInformation': {
                'GaugeLatitude': 51.5074,
                'GaugeLongitude': -0.1278,
                'GaugeOwner': 'Environment Agency',
                'GaugeType': 'Water Level',
                'OperationalStatus': 'Fully operational',
                'DataSourceType': 'Telemetry',
                'InstallationDate': '2020-01-01',
                'CertificationStatus': 'Certified',
            },
            'Measurements': {
                'MeasurementFrequency': '15 minutes',
                'MeasurementMethod': 'Pressure sensor',
                'DataTransmission': 'Real-time',
            },
        },
        'SensorStats': {
            'HistoricalHighLevel': 5.2,
            'HistoricalHighDate': '2020-02-09',
            'LastDateLevelExceedLevel3': '2024-11-15',
            'FrequencyExceedLevel3': 3,
        },
        'FloodStage': {
            'UK': {
                'FloodAlert': 2.5,
                'FloodWarning': 3.5,
                'SevereFloodWarning': 4.5,
            }
        },
    }
