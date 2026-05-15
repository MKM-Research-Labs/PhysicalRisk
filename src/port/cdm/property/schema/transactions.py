# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""
TransactionHistory — commercial and financial information.

Covers §3 of the revised Property CDM (Purchase, Rental) plus three
extensions to re-home rand-registry lambdas that were previously orphan:

    Sales      — past-sale fields (SalePriceGbp, SaleDate, PreviousOwner,
                 MarketingDays). Distinct from Purchase (the current owner's
                 purchase) because Sales tracks the prior disposition.
    Rental     — extended with RentalHistory, VacancyCount, TenancyDuration.
    Insurance  — InsurancePremium (moved from ProtectionMeasures per revised
                 CDM) + ExcessAmount.
"""

TRANSACTION_HISTORY_SCHEMA = {
    "Purchase": {
        "PurchaseDate": {
            "type": "date",
            "description": "Date of purchase"
        },
        "PurchasePriceGbp": {
            "type": "decimal",
            "description": "Purchase price in GBP"
        }
    },
    "Sales": {
        "SalePriceGbp": {
            "type": "decimal",
            "description": "Most recent sale price in GBP"
        },
        "SaleDate": {
            "type": "date",
            "description": "Date of most recent sale"
        },
        "PreviousOwner": {
            "type": "string",
            "description": "Name of the previous owner"
        },
        "MarketingDays": {
            "type": "integer",
            "description": "Number of days on market before sale"
        }
    },
    "Rental": {
        "MonthlyRentGbp": {
            "type": "decimal",
            "description": "Monthly rent in GBP"
        },
        "RentalYield": {
            "type": "decimal",
            "description": "Annual rental yield percentage"
        },
        "RentalHistory": {
            "type": "menu",
            "options": [
                "Never rented", "Previously rented", "Currently rented",
                "Mixed use history",
            ],
            "description": "Rental history classification"
        },
        "VacancyCount": {
            "type": "integer",
            "description": "Number of vacancy periods recorded"
        },
        "TenancyDuration": {
            "type": "menu",
            "options": [
                "0-6 months", "6-12 months", "12-24 months",
                "24-36 months", "36+ months",
            ],
            "description": "Typical tenancy duration bucket"
        }
    },
    "Insurance": {
        "InsurancePremium": {
            "type": "decimal",
            "description": "Annual insurance premium in local currency"
        },
        "ExcessAmount": {
            "type": "integer",
            "description": "Insurance policy excess in local currency"
        },
        "InsuranceStatus": {
            "type": "menu",
            "options": [
                "Uninsured", "Standard cover", "Flood Re supported",
                "Specialist cover",
            ],
            "description": "Current insurance coverage type"
        },
        "FloodReEligible": {
            "type": "boolean",
            "description": "Eligibility for Flood Re scheme"
        },
        "ClaimsHistory": {
            "type": "integer",
            "description": "Number of historical insurance claims"
        },
        "LastClaimDate": {
            "type": "date",
            "description": "Date of most recent insurance claim"
        },
        "LastClaimType": {
            "type": "menu",
            "options": [
                "None", "Fire", "Flood damage", "Subsidence",
                "Domestic appliances",
            ],
            "description": "Nature of most recent claim"
        }
    }
}
