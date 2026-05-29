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
Tests for visual.utils.data_extractors.rloan_extractor.

Covers: extract_rloan_info, _extract_term_years,
build_rloan_lookup, _normalize_rloan_list.
"""

import pytest

from visual.utils.data_extractors.rloan_extractor import (
    extract_rloan_info,
    build_rloan_lookup,
)


# ===========================================================================
# extract_rloan_info
# ===========================================================================

def _make_mortgage(mortgage_id="MORT-001", property_id="PROP-001",
                   original_loan=250_000, term_years=25):
    return {
        "Mortgage": {
            "Header": {
                "MortgageID": mortgage_id,
                "PropertyID": property_id,
                "UPRN": "12345",
            },
            "FinancialTerms": {
                "OriginalLoan": original_loan,
                "CurrentBalance": 220_000,
                "OriginalLendingRate": 0.035,
                "CurrentRate": 0.035,
                "LoanToValueRatio": 0.8,
                "TermYears": term_years,
                "MonthlyPayment": 1250.0,
            },
            "Application": {
                "MortgageProvider": "Halifax",
                "ApplicationDate": "2020-01-15",
                "CompletionDate": "2020-03-01",
            },
        }
    }


class TestExtractRLoanInfo:

    def test_returns_dict_for_valid_mortgage(self):
        result = extract_rloan_info(_make_mortgage())
        assert isinstance(result, dict)

    def test_extracts_mortgage_id(self):
        result = extract_rloan_info(_make_mortgage(mortgage_id="M-999"))
        assert result["mortgage_id"] == "M-999"

    def test_extracts_property_id(self):
        result = extract_rloan_info(_make_mortgage(property_id="PROP-XYZ"))
        assert result["property_id"] == "PROP-XYZ"

    def test_extracts_original_loan(self):
        result = extract_rloan_info(_make_mortgage(original_loan=300_000))
        assert result["original_loan"] == 300_000

    def test_extracts_term_years(self):
        result = extract_rloan_info(_make_mortgage(term_years=30))
        assert result["term_years"] == 30

    def test_extracts_provider(self):
        result = extract_rloan_info(_make_mortgage())
        assert result["mortgage_provider"] == "Halifax"

    def test_missing_property_id_returns_none(self):
        mort = {"Mortgage": {"Header": {"MortgageID": "M1"}, "FinancialTerms": {}, "Application": {}}}
        assert extract_rloan_info(mort) is None

    def test_none_values_removed(self):
        # Fields that are None should be removed from result
        mort = {
            "Mortgage": {
                "Header": {"MortgageID": "M1", "PropertyID": "P1"},
                "FinancialTerms": {},  # All None
                "Application": {},
            }
        }
        result = extract_rloan_info(mort)
        assert result is not None
        # None values should not be in result
        for v in result.values():
            assert v is not None

    def test_flat_dict_without_mortgage_wrapper(self):
        flat = {
            "Header": {"MortgageID": "M-FLAT", "PropertyID": "P-FLAT"},
            "FinancialTerms": {"OriginalLoan": 200_000, "TermYears": 20},
            "Application": {},
        }
        result = extract_rloan_info(flat)
        assert result is not None
        assert result["property_id"] == "P-FLAT"

    def test_original_term_in_months_converted(self):
        # OriginalTerm = 300 months → 25 years
        mort = {
            "Mortgage": {
                "Header": {"MortgageID": "M1", "PropertyID": "P1"},
                "FinancialTerms": {"OriginalTerm": 300},  # 300 months > 100
                "Application": {},
            }
        }
        result = extract_rloan_info(mort)
        assert result["term_years"] == pytest.approx(25.0)

    def test_original_term_not_converted_if_small(self):
        # OriginalTerm = 25 (interpreted as years)
        mort = {
            "Mortgage": {
                "Header": {"MortgageID": "M1", "PropertyID": "P1"},
                "FinancialTerms": {"OriginalTerm": 25},
                "Application": {},
            }
        }
        result = extract_rloan_info(mort)
        assert result["term_years"] == 25


# ===========================================================================
# build_rloan_lookup
# ===========================================================================

class TestBuildRLoanLookup:

    def test_list_input(self):
        mortgages = [_make_mortgage("M1", "P1"), _make_mortgage("M2", "P2")]
        result = build_rloan_lookup(mortgages)
        assert "P1" in result
        assert "P2" in result

    def test_dict_with_mortgages_key(self):
        data = {"mortgages": [_make_mortgage("M1", "P1")]}
        result = build_rloan_lookup(data)
        assert "P1" in result

    def test_dict_with_Mortgages_key(self):
        data = {"Mortgages": [_make_mortgage("M1", "P1")]}
        result = build_rloan_lookup(data)
        assert "P1" in result

    def test_dict_with_mortgage_portfolio_key(self):
        data = {"mortgage_portfolio": [_make_mortgage("M1", "P1")]}
        result = build_rloan_lookup(data)
        assert "P1" in result

    def test_single_mortgage_dict_wrapped(self):
        # Dict without known key — treated as single mortgage
        mort = _make_mortgage("M1", "P1")
        result = build_rloan_lookup(mort)
        assert "P1" in result

    def test_empty_list_returns_empty(self):
        assert build_rloan_lookup([]) == {}

    def test_mortgage_without_property_id_skipped(self):
        bad = {"Mortgage": {"Header": {"MortgageID": "M1"}, "FinancialTerms": {}, "Application": {}}}
        result = build_rloan_lookup([bad])
        assert result == {}
