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

"""Tests for build_mortgage_lookup + build_all_lookups."""

import pytest

from loaders.lookups import (
    build_mortgage_lookup,
    build_all_lookups,
)


# ===========================================================================
# build_mortgage_lookup
# ===========================================================================

class TestBuildMortgageLookup:

    def test_none_returns_empty(self):
        assert build_mortgage_lookup(None) == {}

    def test_empty_dict_returns_empty(self):
        assert build_mortgage_lookup({}) == {}

    def test_no_items_key_returns_empty(self):
        assert build_mortgage_lookup({"other": []}) == {}

    def test_single_mortgage(self):
        data = {
            "items": [{
                "Mortgage": {
                    "Header": {
                        "MortgageID": "MORT-001",
                        "PropertyID": "PROP-001",
                        "UPRN": "12345",
                    },
                    "FinancialTerms": {
                        "OriginalLoan": 250_000,
                        "OriginalLTV": 0.8,
                        "OriginalLendingRate": 0.035,
                        "OriginalTerm": 25,
                    },
                    "CurrentStatus": {
                        "OutstandingBalance": 220_000,
                        "CurrentLTV": 0.73,
                        "CurrentInterestRate": 0.035,
                    },
                    "LoanDetails": {},
                    "Application": {},
                }
            }]
        }
        result = build_mortgage_lookup(data)
        assert "PROP-001" in result
        assert result["PROP-001"]["mortgage_id"] == "MORT-001"
        assert result["PROP-001"]["OriginalLoan"] == 250_000
        assert result["PROP-001"]["OriginalLTV"] == pytest.approx(0.8)
        assert result["PROP-001"]["CurrentBalance"] == 220_000

    def test_mortgage_without_property_id_skipped(self):
        data = {
            "items": [{
                "Mortgage": {
                    "Header": {"MortgageID": "MORT-X"},
                    "FinancialTerms": {},
                    "CurrentStatus": {},
                    "LoanDetails": {},
                }
            }]
        }
        assert build_mortgage_lookup(data) == {}

    def test_loan_from_loan_details_fallback(self):
        data = {
            "items": [{
                "Mortgage": {
                    "Header": {"MortgageID": "MORT-002", "PropertyID": "PROP-002"},
                    "FinancialTerms": {},  # No OriginalLoan here
                    "CurrentStatus": {},
                    "LoanDetails": {"OriginalLoanAmount": 300_000},
                    "Application": {},
                }
            }]
        }
        result = build_mortgage_lookup(data)
        assert result["PROP-002"]["OriginalLoan"] == 300_000

    def test_multiple_mortgages(self):
        def _make_item(mid, pid):
            return {
                "Mortgage": {
                    "Header": {"MortgageID": mid, "PropertyID": pid},
                    "FinancialTerms": {},
                    "CurrentStatus": {},
                    "LoanDetails": {},
                    "Application": {},
                }
            }
        data = {"items": [_make_item("M1", "P1"), _make_item("M2", "P2")]}
        result = build_mortgage_lookup(data)
        assert set(result.keys()) == {"P1", "P2"}


# ===========================================================================
# build_all_lookups
# ===========================================================================

class TestBuildAllLookups:

    def test_all_none_returns_three_keys(self):
        result = build_all_lookups()
        assert set(result.keys()) == {
            "mortgage_lookup", "gauge_flood_info", "property_flood_info",
        }

    def test_all_none_returns_empty_dicts(self):
        result = build_all_lookups()
        assert result["mortgage_lookup"] == {}
        assert result["gauge_flood_info"] == {}
        assert result["property_flood_info"] == {}

    def test_with_data_populates_lookups(self):
        mortgage_data = {
            "items": [{
                "Mortgage": {
                    "Header": {"MortgageID": "M1", "PropertyID": "P1"},
                    "FinancialTerms": {"OriginalLoan": 150_000},
                    "CurrentStatus": {},
                    "LoanDetails": {},
                    "Application": {},
                }
            }]
        }
        result = build_all_lookups(mortgage_data=mortgage_data)
        assert "P1" in result["mortgage_lookup"]
