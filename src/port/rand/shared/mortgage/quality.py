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

"""Quality and consistency checks for generated mortgage data."""

from typing import Dict


def quality_consistency_check(mortgage_data: Dict, financial_data: Dict) -> Dict:
    """Perform quality and consistency checks on generated mortgage data.

    Clamps the canonical CDM fields (FinancialTerms / CurrentStatus) so the
    constraints apply to the data downstream consumers actually read.
    """
    mortgage = mortgage_data.get('RLoan', {})
    terms = mortgage.get('FinancialTerms', {})
    status = mortgage.get('CurrentStatus', {})

    original = terms.get('OriginalLoan')
    current = status.get('OutstandingBalance')
    if original is not None and current is not None and current > original:
        status['OutstandingBalance'] = original * 0.95

    for section, key in ((status, 'CurrentLTV'), (terms, 'OriginalLTV')):
        ltv = section.get(key)
        if ltv is None:
            continue
        if ltv > 100:
            section[key] = 95
        elif ltv < 10:
            section[key] = 60

    for section, key in ((status, 'CurrentInterestRate'), (terms, 'OriginalLendingRate')):
        rate = section.get(key)
        if rate is None:
            continue
        if rate > 15:
            section[key] = 12.0
        elif rate < 1:
            section[key] = 2.0

    return mortgage_data
