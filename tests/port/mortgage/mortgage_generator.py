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
Unit tests for MortgagePortfolioGenerator.

Mortgage generation depends on an existing property portfolio file.
"""

import re

import pytest

import database
from port.cdm import LoanCDM
from port.src.mortgage import MortgagePortfolioGenerator
from port.src.property import PropertyPortfolioGenerator


@pytest.fixture
def property_portfolio_in_tmp(tmp_path):
    """Persist a small (5-property) portfolio under a tmp-rooted backend and keep it bound.

    Both writers now persist through ``database``; ``tmp_catchment`` roots the backend at
    ``tmp_path`` for the whole test, so the property write, the mortgage generator's
    property read, and the loan write all resolve there. Yields ``tmp_path``."""
    from db_helpers import tmp_catchment
    with tmp_catchment(tmp_path):
        PropertyPortfolioGenerator(verbose=False).generate(count=5)
        yield tmp_path


@pytest.mark.generator
class TestMortgageGeneratorOutput:

    def test_generate_returns_expected_keys(self, property_portfolio_in_tmp):
        gen = MortgagePortfolioGenerator(verbose=False)
        result = gen.generate()
        assert "data" in result
        assert "catchment" in result
        assert "processing_stats" in result

    def test_mortgage_count_matches_properties(self, property_portfolio_in_tmp):
        gen = MortgagePortfolioGenerator(verbose=False)
        result = gen.generate()
        assert len(result["data"]["mortgages"]) == 5

    def test_mortgage_ids_unique(self, property_portfolio_in_tmp):
        gen = MortgagePortfolioGenerator(verbose=False)
        result = gen.generate()
        ids = result["data"]["mortgage_ids"]
        assert len(ids) == len(set(ids))

    def test_mortgage_id_format(self, property_portfolio_in_tmp):
        gen = MortgagePortfolioGenerator(verbose=False)
        result = gen.generate()
        for mid in result["data"]["mortgage_ids"]:
            assert re.match(r"^MORT-[a-f0-9]{8}$", mid)


@pytest.mark.generator
class TestMortgageGeneratorFile:

    def test_output_persisted(self, property_portfolio_in_tmp):
        gen = MortgagePortfolioGenerator(verbose=False)
        result = gen.generate()
        assert database.get_loan_portfolio(result["catchment"]) is not None

    def test_output_is_valid_portfolio(self, property_portfolio_in_tmp):
        gen = MortgagePortfolioGenerator(verbose=False)
        result = gen.generate()
        data = database.get_loan_portfolio(result["catchment"])
        assert isinstance(data, dict)


@pytest.mark.generator
class TestMortgageGeneratorDataQuality:

    def test_each_mortgage_has_property_id(self, property_portfolio_in_tmp):
        gen = MortgagePortfolioGenerator(verbose=False)
        result = gen.generate()
        cdm = LoanCDM()
        for mortgage in result["data"]["mortgages"]:
            mapping = cdm.create_mapping(mortgage)
            assert mapping.get("property_id") is not None

    def test_processing_stats(self, property_portfolio_in_tmp):
        gen = MortgagePortfolioGenerator(verbose=False)
        result = gen.generate()
        stats = result["processing_stats"]
        assert stats["successful_mortgages"] == 5
        assert stats["failed_mortgages"] == 0
