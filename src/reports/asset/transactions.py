# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Render the TransactionHistory section.

Sub-shape:
    TransactionHistory
      Purchase  { PurchaseDate, PurchasePriceGbp }
      Sales     { SalePriceGbp, SaleDate, PreviousOwner, MarketingDays }
      Rental    { MonthlyRentGbp, RentalYield, … }
      Insurance { InsurancePremium, ExcessAmount, … }
"""

from typing import Any, Dict, List

from reportlab.platypus import Paragraph

from ._helpers import auto_rows, section_block

_PURCHASE_FIELDS = [
    ("PurchaseDate",     "Purchase Date"),
    ("PurchasePriceGbp", "Purchase Price"),
]

_SALES_FIELDS = [
    ("SalePriceGbp",  "Sale Price"),
    ("SaleDate",      "Sale Date"),
    ("PreviousOwner", "Previous Owner"),
    ("MarketingDays", "Marketing Days"),
]

_RENTAL_FIELDS = [
    ("MonthlyRentGbp",    "Monthly Rent"),
    ("RentalYield",       "Rental Yield"),
    ("RentalHistory",     "Rental History"),
    ("VacancyCount",      "Vacancy Count"),
    ("TenancyDuration",   "Tenancy Duration"),
]

_INSURANCE_FIELDS = [
    ("InsurancePremium",  "Insurance Premium"),
    ("ExcessAmount",      "Excess Amount"),
    ("InsuranceStatus",   "Insurance Status"),
    ("FloodReEligible",   "Flood Re Eligible"),
    ("ClaimsHistory",     "Claims History"),
    ("LastClaimType",     "Last Claim Type"),
]


def render_transactions(transactions: Dict[str, Any], page) -> List:
    """Build the transaction history tables."""
    elements: List = [
        Paragraph("Transaction History", page.styles["SectionHeader"]),
    ]
    elements.extend(section_block(
        "Purchase",
        page,
        auto_rows(transactions.get("Purchase", {}) or {}, _PURCHASE_FIELDS),
        style="financial",
        header=("Field", "Value"),
    ))
    elements.extend(section_block(
        "Sales",
        page,
        auto_rows(transactions.get("Sales", {}) or {}, _SALES_FIELDS),
        style="financial",
        header=("Field", "Value"),
    ))
    elements.extend(section_block(
        "Rental",
        page,
        auto_rows(transactions.get("Rental", {}) or {}, _RENTAL_FIELDS),
        style="financial",
        header=("Field", "Value"),
    ))
    elements.extend(section_block(
        "Insurance",
        page,
        auto_rows(transactions.get("Insurance", {}) or {}, _INSURANCE_FIELDS),
        style="financial",
        header=("Field", "Value"),
    ))
    return elements
