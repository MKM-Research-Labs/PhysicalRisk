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

#
# This software is provided under license by MKM Research Labs.
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Mortgage CDM schema definition.

Extracted from mortgage.py. Based on Mortgage_CDM v6 specification.
Includes CatchmentID for multi-catchment support.
"""

MORTGAGE_SCHEMA = {
    "Mortgage": {
        "Header": {
            "MortgageID": {
                "type": "text",
                "description": "Unique identifier for the mortgage loan"
            },
            "CatchmentID": {
                "type": "text",
                "description": "Identifier for the river catchment (e.g., 'thames', 'rhine')"
            },
            "PropertyID": {
                "type": "text",
                "description": "Unique identifier for the property"
            },
            "UPRN": {
                "type": "text",
                "description": "Unique Property Reference Number"
            }
        },
        "Application": {
            "MemberID": {
                "type": "text",
                "description": "Unique identifier for the borrower"
            },
            "MortgageProvider": {
                "type": "text",
                "description": "Financial institution providing the mortgage"
            },
            "ApplicationDate": {
                "type": "date",
                "description": "Date when the mortgage application was submitted"
            },
            "ApplicationChannel": {
                "type": "menu",
                "options": ["Retail", "Broker", "Correspondent"],
                "description": "Channel through which the application was submitted"
            },
            "LoanPurpose": {
                "type": "menu",
                "options": ["Purchase", "Refinancing", "Home Improvement", "Other"],
                "description": "Primary purpose of the mortgage loan"
            },
            "OccupancyType": {
                "type": "menu",
                "options": ["PrimaryResidence", "SecondResidence", "Investment"],
                "description": "Intended occupancy status of the property"
            }
        },
        "FinancialTerms": {
            "currency": {
                "type": "text",
                "description": "Currency code for the mortgage transaction"
            },
            "DisbursalDate": {
                "type": "date",
                "description": "Date when mortgage funds were released"
            },
            "PurchaseValue": {
                "type": "decimal",
                "description": "Agreed purchase price of the property"
            },
            "OriginalLoan": {
                "type": "decimal",
                "description": "Initial amount borrowed"
            },
            "OriginalTerm": {
                "type": "integer",
                "description": "Initial length of mortgage in months"
            },
            "OriginalLendingRate": {
                "type": "decimal",
                "description": "Initial interest rate of the mortgage"
            },
            "OriginalRateType": {
                "type": "menu",
                "options": ["Fixed", "Variable", "Tracker", "Discount", "Capped", "Standard Variable Rate"],
                "description": "Type of interest rate structure"
            },
            "OriginalLTV": {
                "type": "decimal",
                "description": "Initial loan-to-value ratio"
            },
            "MaturityDate": {
                "type": "date",
                "description": "Scheduled date for final loan payment"
            },
            "DebtToIncomeRatio": {
                "type": "decimal",
                "description": "Ratio of total debt payments to income"
            }
        },
        "Features": {
            "MortgageType": {
                "type": "menu",
                "options": ["Residential", "Buy-to-Let", "Second Home", "Holiday Home", "Shared Ownership"],
                "description": "Primary classification of mortgage type"
            },
            "RepaymentType": {
                "type": "menu",
                "options": ["Repayment", "Interest only", "Part and part"],
                "description": "Type of repayment structure"
            },
            "FlexibleFeatures": {
                "type": "menu",
                "options": ["Overpayments", "Payment holidays", "Drawdown", "None"],
                "description": "Flexible mortgage features available"
            }
        },
        "CurrentStatus": {
            "OutstandingBalance": {
                "type": "decimal",
                "description": "Current amount owed on the mortgage"
            },
            "CurrentLTV": {
                "type": "decimal",
                "description": "Current loan-to-value ratio"
            },
            "CurrentInterestRate": {
                "type": "decimal",
                "description": "Current interest rate being charged"
            },
            "RemainingTerm": {
                "type": "integer",
                "description": "Remaining months on the mortgage"
            },
            "AccountStatus": {
                "type": "menu",
                "options": ["Current", "Arrears", "Default", "Closed"],
                "description": "Current status of the mortgage account"
            },
            "DefaultFlag": {
                "type": "boolean",
                "description": "Indicates if mortgage is in default"
            },
            "ArrearsMonths": {
                "type": "integer",
                "description": "Number of months in arrears"
            }
        },
        "BorrowerDetails": {
            "BorrowerAge": {
                "type": "integer",
                "description": "Age of the primary borrower"
            },
            "BorrowerIncome": {
                "type": "decimal",
                "description": "Annual income of the borrower"
            },
            "BorrowerCreditScore": {
                "type": "integer",
                "description": "Credit score of the borrower"
            },
            "EmploymentType": {
                "type": "menu",
                "options": ["Employed", "Self-employed", "Retired", "Contractor", "Other"],
                "description": "Employment status of the borrower"
            },
            "NumberOfBorrowers": {
                "type": "integer",
                "description": "Total number of borrowers on the mortgage"
            }
        },
        "RiskAssessment": {
            "BehavioralScore": {
                "type": "integer",
                "description": "Behavioral risk score"
            },
            "PrepaymentRisk": {
                "type": "integer",
                "description": "Risk score for early repayment"
            },
            "FloodRiskCategory": {
                "type": "menu",
                "options": ["Very low", "Low", "Medium", "High", "Very high"],
                "description": "Flood risk category for the property"
            }
        }
    }
}
