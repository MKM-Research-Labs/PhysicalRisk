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

"""Shared fixtures for PDF generation tests."""

from typing import Any, Dict
import pytest


@pytest.fixture
def sample_property_data() -> Dict[str, Any]:
    """Property data in the CDM format expected by the report generator."""
    return {
        "PropertyHeader": {
            "Header": {
                "UPRN": "12345678",
                "PropertyID": "PROP-test0001",
                "CatchmentID": "thames",
                "propertyType": "residential",
                "propertyStatus": "active"
            },
            "Valuation": {
                "PropertyValue": 450000.00,
                "ValuationDate": "2025-01-15",
                "ValuationMethod": "Desktop valuation"
            },
            "PropertyAttributes": {
                "OccupancyType": "Residential owner-occupied",
                "PropertyAreaSqm": 95.0,
                "PropertyResi": "Semi-detached",
                "NumberOfStoreys": 2,
                "ConstructionYear": 1990,
                "PropertyPeriod": "1975-2000",
                "CouncilTaxBand": "D",
                "NumberBedrooms": 3,
                "NumberBathrooms": 1,
                "PropertyCondition": "Good",
                "PropertyID": "PROP-test0001",
                "CatchmentID": "thames"
            },
            "Construction": {
                "ConstructionType": "Traditional brick",
                "FoundationType": "Strip foundations",
                "FloorLevelMeters": 0.15,
                "BasementPresent": False
            },
            "Location": {
                "BuildingNumber": "42",
                "StreetName": "Test Road",
                "TownCity": "Richmond",
                "County": "Greater London",
                "Postcode": "TW9 1AA",
                "LocalAuthority": "Richmond upon Thames",
                "Country": "England",
                "Region": "London",
                "UrbanRuralClassification": "Urban",
                "LatitudeDegrees": 51.4613,
                "LongitudeDegrees": -0.3037
            },
            "RiskAssessment": {
                "EAFloodZone": "Zone 2",
                "OverallFloodRisk": "Medium",
                "FloodRiskType": "River",
                "GroundLevelMeters": 8.5,
                "RiverDistanceMeters": 350.0
            }
        },
        "ProtectionMeasures": {
            "RiskAssessment": {
                "InsurancePremium": 2500.00,
                "RiskRating": "Medium"
            },
            "ResilienceMeasures": {
                "FloodGates": True,
                "FloodBarriers": False,
                "SumpPump": True,
                "FloodWarningSystem": True
            }
        },
        "TransactionHistory": {
            "Purchase": {
                "PurchaseDate": "2020-06-15T10:00:00",
                "PurchasePriceGbp": 425000.00
            },
            "Rental": {
                "MonthlyRentGbp": 1800,
                "RentalYield": 4.8
            }
        }
    }


@pytest.fixture
def sample_mortgage_data() -> Dict[str, Any]:
    """Mortgage data in the CDM format expected by the report generator."""
    return {
        "RLoan": {
            "Header": {
                "RLoanID": "MORT-test0001",
                "CatchmentID": "thames",
                "PropertyID": "PROP-test0001",
                "UPRN": "UPRN-12345678"
            },
            "Application": {
                "MemberID": "MEMBER-test001",
                "MortgageProvider": "Test Bank",
                "ApplicationDate": "2020-05-01",
                "ApplicationChannel": "Retail",
                "LoanPurpose": "Purchase",
                "OccupancyType": "PrimaryResidence"
            },
            "FinancialTerms": {
                "currency": "GBP",
                "DisbursalDate": "2020-06-15",
                "PurchaseValue": 425000.00,
                "OriginalLoan": 340000.00,
                "OriginalTerm": 300,
                "OriginalLendingRate": 2.5,
                "OriginalRateType": "Fixed",
                "OriginalLTV": 80.0,
                "MaturityDate": "2045-06-15",
                "DebtToIncomeRatio": 0.28
            },
            "Features": {
                "MortgageType": "Residential",
                "RepaymentType": "Repayment",
                "FlexibleFeatures": "Overpayments"
            },
            "CurrentStatus": {
                "OutstandingBalance": 310000.00,
                "CurrentLTV": 68.89,
                "CurrentInterestRate": 2.5,
                "RemainingTerm": 240,
                "AccountStatus": "Active",
                "DefaultFlag": False,
                "ArrearsMonths": 0
            },
            "BorrowerDetails": {
                "BorrowerAge": 35,
                "BorrowerIncome": 85000.00,
                "BorrowerCreditScore": 750,
                "EmploymentType": "Employed",
                "NumberOfBorrowers": 2
            },
            "RiskAssessment": {
                "BehavioralScore": 85,
                "PrepaymentRisk": 3,
                "FloodRiskCategory": "Medium"
            }
        }
    }


@pytest.fixture
def sample_gauge_data() -> Dict[str, Any]:
    """Gauge data in the CDM format expected by the report generator."""
    return {
        "FloodGauge": {
            "Header": {
                "GaugeID": "GAUGE-test0001",
                "CatchmentID": "thames",
                "GaugeName": "Thames Test Gauge"
            },
            "SensorStats": {
                "HistoricalHighLevel": 6.85,
                "HistoricalHighDate": "2024-01-15",
                "LastDateLevelExceedLevel3": "2023-11-10",
                "FrequencyExceedLevel3": 2
            },
            "SensorDetails": {
                "GaugeInformation": {
                    "DataSourceType": "SensorGauge",
                    "GaugeOwner": "Environment Agency",
                    "GaugeType": "Pressure transducer",
                    "ManufacturerName": "OTT HydroMet",
                    "InstallationDate": "2015-03-20",
                    "LastInspectionDate": "2024-10-15",
                    "MaintenanceSchedule": "Quarterly",
                    "OperationalStatus": "Fully operational",
                    "CertificationStatus": "Fully certified",
                    "GaugeLatitude": 51.4613,
                    "GaugeLongitude": -0.3037,
                    "GroundLevelMeters": 7.5,
                    "elevation": 7.5
                },
                "Measurements": {
                    "MeasurementFrequency": "15 minutes",
                    "MeasurementMethod": "Automatic",
                    "DataTransmission": "Automatic",
                    "DataCurator": "Environment Agency",
                    "DataAccessMethod": "API"
                }
            },
            "FloodStage": {
                "UK": {
                    "DecisionBody": "Environment Agency",
                    "FloodAlert": 4.5,
                    "FloodWarning": 5.5,
                    "SevereFloodWarning": 6.5
                }
            },
            "NRFAMetadata": {
                "NRFAStationID": "NRFA-TEST-001",
                "GridReference": "TQ177746",
                "CatchmentArea": 9.8,
                "RecordStartDate": "2015-03-20",
                "RecordEndDate": "2024-12-31",
                "MeanFlow": 4.2,
                "MedianFlow": 3.8,
                "Q95Flow": 1.5,
                "Q5Flow": 8.9,
                "MaxRecordedFlow": 12.3,
                "MaxRecordedFlowDate": "2024-01-15",
                "HistoricalDataFile": "test_gauge_history.csv",
                "DatabaseSource": "NRFA",
                "FlowUnits": "m3/s",
                "DataQualityNotes": "Good quality"
            },
            "Location": {
                "GaugeLatitude": 51.4613,
                "GaugeLongitude": -0.3037,
                "GaugeElevation": 7.5
            },
            "FloodStages": {
                "FloodAlert": 4.5,
                "FloodWarning": 5.5,
                "SevereFloodWarning": 6.5,
                "HistoricalHighLevel": 6.85,
                "HistoricalHighDate": "2024-01-15"
            }
        }
    }
