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
"""The fair value counts each loss once, and the recovery never exceeds the property.

Benchmark v0.1 (MKM-MP-001_wolfram_benchmark) found the fair value deducting the
expected loss twice -- once inside the recovery, once as pv_losses -- and the
recovery taken a month late. These pin both against a value computed path by path.
"""

import numpy as np
import pytest

# Under water and a high spread, so that the loss given default is large.
UNDERWATER = dict(loan_amount=285_000, property_value=300_000, gross_annual_income=30_000,
                  interest_rate=0.06, insurance_rate=0.005, original_maturity=25,
                  current_term=2, recovery_haircut=0.4)


def _pathwise(result, recovery_value, monthly_rate):
    """Expected PV over the default month: payments before it, the recovery in it."""
    m, b = result["monthly_payment"], result["outstanding_balance"]
    h = result["hazard_rates"][1]
    n = len(b) - 1
    disc = (1 + monthly_rate) ** -np.arange(1, n + 1)
    total = (1 - h) ** n * m * disc.sum()
    for t in range(1, n + 1):
        path = m * disc[:t - 1].sum() + min(b[t - 1], recovery_value) * disc[t - 1]
        total += (1 - h) ** (t - 1) * h * path
    return total


def test_fair_value_is_the_pathwise_value(pricer):
    result = pricer.price_loan(**UNDERWATER)
    expected = _pathwise(result, 0.6 * 300_000, 0.06 / 12)
    assert result["mortgage_value"] == pytest.approx(expected, rel=1e-12)
    assert result["pv_losses"] > 0.05 * UNDERWATER["loan_amount"]


def test_fair_value_does_not_deduct_the_loss_again(pricer):
    result = pricer.price_loan(**UNDERWATER)
    assert result["mortgage_value"] == pytest.approx(result["pv_cashflows"], rel=1e-15)


def test_the_recovery_never_exceeds_the_recoverable_value(pricer):
    result = pricer.price_loan(**UNDERWATER)
    b, lgd = result["outstanding_balance"], result["lgds"]
    recovery = b[:-1] - lgd[1:]
    assert np.all(recovery <= 0.6 * 300_000 + 1e-6)
    assert np.allclose(lgd[1:], np.maximum(0, b[:-1] - 0.6 * 300_000))
