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
