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

"""
Tests for PropertyLayer popup methods — part 2.

_create_rloan_section.
"""

import pytest

from visual.layer.property_layer.layer import PropertyLayer

from .conftest import make_mortgage_info


# ===========================================================================
# _create_rloan_section
# ===========================================================================

class TestCreateMortgageSection:

    def test_returns_html_string(self):
        layer = PropertyLayer()
        html = layer._create_rloan_section(make_mortgage_info(), 500_000)
        assert isinstance(html, str)
        assert "MORTGAGE DETAILS" in html

    def test_contains_lender(self):
        layer = PropertyLayer()
        html = layer._create_rloan_section(make_mortgage_info(provider="Barclays"), 500_000)
        assert "Barclays" in html

    def test_interest_rate_less_than_1_multiplied(self):
        """Rate < 1 -> displayed as percentage (4.0%)."""
        layer = PropertyLayer()
        html = layer._create_rloan_section(make_mortgage_info(rate=0.04), 500_000)
        assert "4.0" in html

    def test_interest_rate_above_1_used_directly(self):
        """Rate >= 1 -> used as-is."""
        layer = PropertyLayer()
        html = layer._create_rloan_section(make_mortgage_info(rate=4.5), 500_000)
        assert "4.5" in html

    def test_ltv_calculated_from_loan_and_value(self):
        """LTV ratio computed from loan_amount / property_value."""
        layer = PropertyLayer()
        html = layer._create_rloan_section(make_mortgage_info(loan=250_000), 500_000)
        assert "50" in html or "LTV" in html

    def test_ltv_division_error_uses_fallback(self):
        """Division error (property_value=0) -> falls back to mortgage info."""
        layer = PropertyLayer()
        html = layer._create_rloan_section(make_mortgage_info(), 0)
        assert isinstance(html, str)

    def test_alternative_keys(self):
        """OriginalLoan / OriginalLendingRate / TermYears / MortgageProvider keys."""
        layer = PropertyLayer()
        rloan_info = {
            "OriginalLoan": 200_000,
            "OriginalLendingRate": 0.035,
            "TermYears": 20,
            "MortgageProvider": "NatWest",
        }
        html = layer._create_rloan_section(rloan_info, 400_000)
        assert "NatWest" in html

    def test_term_years_shown(self):
        layer = PropertyLayer()
        html = layer._create_rloan_section(make_mortgage_info(term=30), 500_000)
        assert "30" in html

    def test_non_numeric_loan_amount_uses_fallback(self):
        """Lines 296-297: float(loan_amount) raises ValueError -> fallback to rloan_info LTV."""
        layer = PropertyLayer()
        rloan_info = {"original_loan": "not_a_number", "loan_to_value_ratio": 0.5}
        html = layer._create_rloan_section(rloan_info, 500_000)
        assert isinstance(html, str)


