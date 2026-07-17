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

"""Branch coverage for rloan_extractor + smoke tests for the storm
portfolio table JS fragment generators (sp_table_basis / sp_table_trades)."""

import pytest

from visual.utils.data_extractors import rloan_extractor as rx


# ---------------------------------------------------------------------------
# extract_rloan_info
# ---------------------------------------------------------------------------

def test_extract_unwraps_rloan_and_drops_none():
    out = rx.extract_rloan_info({"RLoan": {
        "Header": {"PropertyID": "PROP-1", "RLoanID": "RLOAN-1"},
        "FinancialTerms": {"OriginalLoan": 100000, "TermYears": 25},
        "Application": {"MortgageProvider": "BankCo"},
    }})
    assert out["property_id"] == "PROP-1"
    assert out["mortgage_id"] == "RLOAN-1"
    assert out["term_years"] == 25
    assert out["mortgage_provider"] == "BankCo"
    assert "uprn" not in out  # None values stripped


def test_extract_missing_property_id_returns_none():
    assert rx.extract_rloan_info({"Header": {}}) is None


def test_extract_exception_returns_none():
    # A list has no .get → AttributeError caught → None (covers 105-107)
    assert rx.extract_rloan_info(["not", "a", "dict"]) is None


# ---------------------------------------------------------------------------
# _extract_term_years
# ---------------------------------------------------------------------------

def test_term_years_original_term_months_converted():
    assert rx._extract_term_years({"OriginalTerm": 240}) == 20  # 240/12


def test_term_years_direct_value():
    assert rx._extract_term_years({"TermYears": 30}) == 30


def test_term_years_absent_returns_none():
    assert rx._extract_term_years({}) is None


# ---------------------------------------------------------------------------
# build_rloan_lookup
# ---------------------------------------------------------------------------

def test_build_lookup_from_loans_key():
    data = {"loans": [{"RLoan": {
        "Header": {"PropertyID": "PROP-1", "RLoanID": "RLOAN-1"},
        "FinancialTerms": {}, "Application": {}}}]}
    lookup = rx.build_rloan_lookup(data)
    assert "PROP-1" in lookup


def test_build_lookup_handles_extract_exception(monkeypatch):
    # Force extract_rloan_info to raise so the inner except (149-150) runs.
    def boom(_):
        raise RuntimeError("kaboom")
    monkeypatch.setattr(rx, "extract_rloan_info", boom)
    lookup = rx.build_rloan_lookup([{"anything": 1}])
    assert lookup == {}


# ---------------------------------------------------------------------------
# _normalize_rloan_list
# ---------------------------------------------------------------------------

def test_normalize_mortgages_key():
    assert rx._normalize_rloan_list({"Mortgages": [1, 2]}) == [1, 2]


def test_normalize_portfolio_key():
    assert rx._normalize_rloan_list({"mortgage_portfolio": [3]}) == [3]


def test_normalize_single_dict_wrapped():
    assert rx._normalize_rloan_list({"Header": {}}) == [{"Header": {}}]


def test_normalize_list_passthrough():
    assert rx._normalize_rloan_list([1, 2]) == [1, 2]


def test_normalize_unexpected_type_returns_empty():
    # int is neither dict nor list (covers 171-172)
    assert rx._normalize_rloan_list(42) == []


# ---------------------------------------------------------------------------
# sp_table_basis / sp_table_trades JS fragment generators
# ---------------------------------------------------------------------------

def test_sp_table_basis_get_js():
    from visual.interactivity.storm import sp_table_basis
    js = sp_table_basis.get_js()
    assert isinstance(js, str)
    assert "loadBasisData" in js


def test_sp_table_trades_get_js():
    from visual.interactivity.storm import sp_table_trades
    js = sp_table_trades.get_js()
    assert isinstance(js, str)
    assert len(js) > 0
