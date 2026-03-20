# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Thames mortgage constants — UK market specific."""

from config.port import MORTGAGE_TYPE_WEIGHTS, RATE_TYPE_WEIGHTS  # noqa: F401

UK_LENDERS = [
    "HSBC", "Barclays", "NatWest", "Lloyds", "Santander",
    "Nationwide", "Halifax", "Royal Bank of Scotland",
    "Yorkshire Building Society", "Coventry Building Society"
]

MORTGAGE_TYPES = [
    "Residential", "Buy-to-Let", "Second Home",
    "Holiday Home", "Shared Ownership"
]
# MORTGAGE_TYPE_WEIGHTS imported from config/port.py

RATE_TYPES = [
    "Fixed", "Variable", "Tracker", "Discount",
    "Capped", "Standard Variable Rate"
]
# RATE_TYPE_WEIGHTS imported from config/port.py

REPAYMENT_TYPES = ["Repayment", "Interest only", "Part and part"]
EMPLOYMENT_TYPES = ["Employed", "Self-employed", "Retired", "Unemployed", "Director", "Contractor"]
