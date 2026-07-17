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
