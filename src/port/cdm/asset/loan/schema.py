# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""
Loan CDM schema + wrapper helpers.

Holds the schema dict (``MORTGAGE_SCHEMA``) and the small unwrap/id helpers
shared by :class:`~port.cdm.asset.loan.cdm.LoanCDM`. The canonical residential
record is wrapped under the ``RLoan`` key with an ``RLoanID`` header field. To
stay backwards-compatible with commercial records (``CLoan``) and any legacy
data still on the older ``Mortgage`` shape, the unwrap helpers below accept all
three wrapper keys.
"""


def _unwrap_loan(record: dict) -> dict:
    """Return the inner loan dict from a CDM wrapper.

    Tolerates the residential (``RLoan``), commercial (``CLoan``) and legacy
    (``Mortgage``) top-level keys, or an already-unwrapped record.
    """
    if not isinstance(record, dict):
        return {}
    for key in ("RLoan", "CLoan", "Mortgage"):
        inner = record.get(key)
        if isinstance(inner, dict):
            return inner
    return record


def _loan_id(header: dict) -> str:
    """Read the loan id from a header, tolerating R/C/legacy field names."""
    return (header.get("RLoanID")
            or header.get("CLoanID")
            or header.get("MortgageID"))


MORTGAGE_SCHEMA = {
    "RLoan": {
        "Header": {
            "RLoanID": {
                "type": "text",
                "description": "Unique identifier for the residential loan"
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
            },
            "InsuranceRate": {
                "type": "decimal",
                "description": "Annual property insurance cost as a decimal of property value (e.g. 0.002 = 0.2%)"
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
            },
            "RecoveryHaircut": {
                "type": "decimal",
                "description": "Haircut applied to collateral recovery on default, as a decimal (e.g. 0.20 = 20%)"
            }
        }
    }
}
