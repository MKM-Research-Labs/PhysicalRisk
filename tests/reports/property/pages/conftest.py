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

"""Shared helpers for property report page tests."""


def _make_property():
    return {
        "PropertyHeader": {
            "PropertyID": "PROP-001",
            "Address": "1 Test Street",
            "RiskAssessment": {
                "OverallFloodRisk": "Medium",
                "EAFloodZone": "Zone 2",
                "FloodZoneType": "River",
                "ClimateChangeFloodRisk": "High",
                "FloodInsuranceAvailable": True,
                "FloodInsurancePremiumIndicative": 1200,
            },
            "Construction": {
                "ConstructionMethod": "Traditional Brick",
                "FoundationType": "Strip",
                "RoofType": "Pitched",
                "WallMaterial": "Brick",
                "FloorType": "Solid concrete",
                "NumberOfFloors": 2,
                "BasementPresent": False,
                "FloodAdaptations": ["Flood barriers"],
            },
            "Valuation": {
                "PropertyValue": 750_000,
                "PurchasePrice": 600_000,
                "PurchaseDate": "2015-06-01",
                "RentalYield": 0.045,
                "FloodRiskDiscount": 0.05,
            },
            "Protection": {
                "BuildingsInsuranceProvider": "Aviva",
                "BuildingsInsuranceCover": 800_000,
                "BuildingsInsurancePremium": 1_200,
                "ContentsInsuranceProvider": "Direct Line",
                "ContentsInsurancePremium": 400,
                "FloodInsuranceFlag": True,
                "SecuritySystem": "Alarm + CCTV",
                "SmokeCO2Detectors": True,
            },
            "PropertyAttributes": {
                "PropertyAreaSqm": 120,
                "PropertyType": "Semi-detached",
                "ConstructionYear": 1990,
            },
        },
        "Location": {
            "Latitude": 51.5,
            "Longitude": -0.1,
            "Elevation": 5.0,
            "DistanceToRiver": 150,
        },
        "FloodHistory": {
            "FloodEvents": [
                {"EventDate": "2014-02-10", "FloodDepth": 0.3, "FloodType": "Surface"},
            ],
            "PreviousFloodClaims": 1,
        },
        "TransactionHistory": {
            "Transactions": [
                {"TransactionDate": "2015-06-01", "TransactionType": "Purchase",
                 "TransactionPrice": 600_000, "TransactionStatus": "Completed"},
                {"TransactionDate": "2010-03-01", "TransactionType": "Sale",
                 "TransactionPrice": 480_000, "TransactionStatus": "Completed"},
            ]
        },
    }


def _make_mortgage():
    return {
        "RLoan": {
            "Header": {"RLoanID": "MORT-001"},
            "CurrentStatus": {
                "CurrentLTV": 0.65,
                "CurrentBalance": 400_000,
                "InArrearsFlag": False,
                "MissedPayments12M": 0,
                "MonthsInArrears": 0,
                "ArrearsAmount": 0,
            },
            "FinancialDetails": {
                "MonthlyPayment": 2_000,
                "InterestRate": 0.035,
                "RemainingTerm": 18,
                "OriginalBalance": 450_000,
                "ProductType": "Fixed",
                "ProductEndDate": "2028-01-01",
            },
            "BorrowerDetails": {
                "BorrowerAge": 42,
                "EmploymentStatus": "Employed",
                "AnnualIncome": 90_000,
                "CreditScore": 750,
            },
        }
    }


# ---------------------------------------------------------------------------
# Helpers for page_13_risk_analysis_part*.py
# ---------------------------------------------------------------------------

def make_property(flood_risk="Medium"):
    return {
        "PropertyHeader": {
            "RiskAssessment": {"OverallFloodRisk": flood_risk},
        }
    }


def make_mortgage(ltv=0.65, in_arrears=False, missed_payments=0,
                  credit_score=720, lending_rate=None,
                  income=80_000, current_payment=None):
    status = {
        "CurrentLTV": ltv,
        "InArrearsFlag": in_arrears,
        "MissedPayments12M": missed_payments,
    }
    if lending_rate is not None:
        status["CurrentLendingRate"] = lending_rate
    if current_payment is not None:
        status["CurrentPayment"] = current_payment
    return {
        "RLoan": {
            "CurrentStatus": status,
            "BorrowerDetails": {
                "BorrowerCreditScore": credit_score,
                "BorrowerIncome": income,
            },
        }
    }
