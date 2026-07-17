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

"""Portfolio-level mortgage metrics aggregation."""

import logging
from typing import Any, Dict, List

import numpy as np

logger = logging.getLogger(__name__)


def calculate_portfolio_metrics(pricing_results: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Calculate portfolio-level metrics from individual mortgage pricing results.

    Args:
        pricing_results: List of mortgage pricing results

    Returns:
        Dictionary of portfolio metrics
    """
    # Filter out error results
    valid_results = [r for r in pricing_results if 'error' not in r]

    if not valid_results:
        return {'error': 'No valid pricing results'}

    # Extract values
    mortgage_values = [r['mortgage_value'] for r in valid_results]
    credit_spreads = [r['credit_spread'] for r in valid_results]
    discount_percentages = [r['discount_percentage'] for r in valid_results]
    ltv_ratios = [r['ltv_ratio'] for r in valid_results]

    return {
        'total_mortgage_value': sum(mortgage_values),
        'average_mortgage_value': np.mean(mortgage_values),
        'total_mortgages': len(valid_results),
        'average_credit_spread': np.mean(credit_spreads),
        'median_credit_spread': np.median(credit_spreads),
        'average_discount_percentage': np.mean(discount_percentages),
        'total_discount_amount': sum(r.get('discount_to_par', 0) for r in valid_results),
        'average_ltv': np.mean(ltv_ratios),
        'high_risk_mortgages': sum(1 for r in valid_results if r['credit_spread'] > 0.1),
        'error_count': len(pricing_results) - len(valid_results)
    }
