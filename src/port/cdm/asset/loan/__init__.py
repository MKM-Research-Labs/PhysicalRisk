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

"""
Loan/mortgage asset CDM package.

Splits the former single ``asset/loan.py`` module into focused sub-modules:

- schema:  ``MORTGAGE_SCHEMA`` dict + ``_unwrap_loan`` / ``_loan_id`` helpers
- cdm:     ``LoanCDM`` class (validate / create_mapping / to_pricer_inputs)

The public names are re-exported here so existing imports
(``from port.cdm.asset.loan import LoanCDM`` /
``from port.cdm.asset.loan import MORTGAGE_SCHEMA``) keep working unchanged.
"""

from .cdm import LoanCDM
from .schema import MORTGAGE_SCHEMA, _loan_id, _unwrap_loan

__all__ = [
    "LoanCDM",
    "MORTGAGE_SCHEMA",
    "_loan_id",
    "_unwrap_loan",
]
