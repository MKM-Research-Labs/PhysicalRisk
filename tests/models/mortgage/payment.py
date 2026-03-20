# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial 
# research and educational use only. Any commercial use, including 
# but not limited to use in or for products or services offered for sale, 
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Tests for monthly payment and total cost calculations."""

import pytest

from models.mortgage.pricer import MortgagePricer


class TestMonthlyPayment:
    """Tests for calculate_monthly_payment (static method)."""

    def test_standard_mortgage(self):
        """£200k at 3.5% over 25yr ≈ £1,001.25/month."""
        payment = MortgagePricer.calculate_monthly_payment(200_000, 0.035, 25)
        assert 995 < payment < 1010

    def test_zero_rate(self):
        """Zero-rate degenerate case: M = P / n."""
        payment = MortgagePricer.calculate_monthly_payment(120_000, 0.0, 10)
        assert payment == pytest.approx(1000.0)

    def test_higher_rate_higher_payment(self):
        low = MortgagePricer.calculate_monthly_payment(200_000, 0.03, 25)
        high = MortgagePricer.calculate_monthly_payment(200_000, 0.06, 25)
        assert high > low

    def test_shorter_term_higher_payment(self):
        long = MortgagePricer.calculate_monthly_payment(200_000, 0.04, 30)
        short = MortgagePricer.calculate_monthly_payment(200_000, 0.04, 15)
        assert short > long


class TestTotalCost:
    """Tests for calculate_total_cost (static method)."""

    def test_zero_rate_equals_principal(self):
        cost = MortgagePricer.calculate_total_cost(100_000, 0.0, 20)
        assert cost == pytest.approx(100_000.0)

    def test_positive_rate_exceeds_principal(self):
        cost = MortgagePricer.calculate_total_cost(200_000, 0.04, 25)
        assert cost > 200_000
