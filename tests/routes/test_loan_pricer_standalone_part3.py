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

"""Tests for the standalone Loan Calculator endpoint + pricing helper (part 3).

The standalone calculator is launched from the asset right-click menu but is
asset-independent: the client supplies every pricing input and POSTs to
``/api/v1/loan-pricer`` (no property/loan id). It is backed by
``routes._loan_pricing.compute_standalone_pricing``.
"""

import pytest


# ===========================================================================
# _coerce_number helper
# ===========================================================================

class TestCoerceNumber:

    def test_bool_passes_through_untouched(self):
        from routes._loan_pricing import _coerce_number
        # bool is an int subclass — must NOT be cast to 1.0/0.0
        assert _coerce_number(True) is True
        assert _coerce_number(False) is False

    def test_int_and_float_become_float(self):
        from routes._loan_pricing import _coerce_number
        assert _coerce_number(5) == 5.0
        assert isinstance(_coerce_number(5), float)
        assert _coerce_number(2.5) == 2.5

    def test_numeric_string_becomes_float(self):
        from routes._loan_pricing import _coerce_number
        assert _coerce_number("3.5") == 3.5
        assert isinstance(_coerce_number("3.5"), float)

    def test_non_numeric_string_unchanged(self):
        from routes._loan_pricing import _coerce_number
        assert _coerce_number("High") == "High"

    def test_other_types_unchanged(self):
        from routes._loan_pricing import _coerce_number
        assert _coerce_number(None) is None
        sentinel = {"a": 1}
        assert _coerce_number(sentinel) is sentinel


# ===========================================================================
# compute_loan_pricing helper (asset-linked / CDM path)
# ===========================================================================

def _record(**overrides):
    """Build a nested CDM loan dict for compute_loan_pricing."""
    rec = {
        "Mortgage": {
            "Header": {"MortgageID": "MORT-1", "PropertyID": "PROP-1"},
            "FinancialTerms": {
                "OriginalLoan": 400000,
                "OriginalTerm": 300,
                "OriginalLendingRate": 3.5,
                "InsuranceRate": 0.0025,
            },
            "CurrentStatus": {
                "OutstandingBalance": 350000,
                "CurrentLTV": 70.0,
                "CurrentInterestRate": 5.0,
                "RemainingTerm": 240,
            },
            "BorrowerDetails": {"BorrowerIncome": 90000},
            "RiskAssessment": {
                "FloodRiskCategory": "High",
                "RecoveryHaircut": 0.25,
            },
        }
    }
    rec["Mortgage"].update(overrides)
    return rec


class TestComputeLoanPricing:

    def test_echoes_ids_and_prices(self):
        from routes._loan_pricing import compute_loan_pricing
        res = compute_loan_pricing(_record())
        assert res["mortgage_id"] == "MORT-1"
        assert res["property_id"] == "PROP-1"
        assert "mortgage_value" in res["pricing"]
        assert "inputs" in res

    def test_overrides_applied(self):
        from routes._loan_pricing import compute_loan_pricing
        res = compute_loan_pricing(_record(), overrides={"loan_amount": 123456})
        assert res["inputs"]["loan_amount"] == 123456

    def test_missing_value_raises(self):
        from routes._loan_pricing import compute_loan_pricing
        # Strip out the financials so loan amount / property value can't resolve.
        bad = _record()
        bad["Mortgage"]["FinancialTerms"] = {}
        bad["Mortgage"]["CurrentStatus"] = {}
        with pytest.raises(ValueError):
            compute_loan_pricing(bad)
