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
Unit tests for MortgagePortfolioGenerator.

Mortgage generation depends on an existing property portfolio file.
"""

import json
import re

import pytest

from port.cdm import LoanCDM
from port.src.mortgage import MortgagePortfolioGenerator
from port.src.property import PropertyPortfolioGenerator


@pytest.fixture
def property_portfolio_in_tmp(tmp_path):
    """Generate a small property portfolio and return (tmp_path, property_file_path).

    The WP2.4 property writer persists through ``database``; ``tmp_catchment`` roots the
    backend at ``tmp_path`` so ``property.json`` lands there physically, where the
    still-directory-injected mortgage generator reads it by path."""
    from db_helpers import tmp_catchment
    with tmp_catchment(tmp_path):
        gen = PropertyPortfolioGenerator(verbose=False)
        gen.generate(count=5)
    return tmp_path, tmp_path / "property.json"


@pytest.mark.generator
class TestMortgageGeneratorOutput:

    def test_generate_returns_expected_keys(self, property_portfolio_in_tmp):
        tmp_dir, prop_path = property_portfolio_in_tmp
        gen = MortgagePortfolioGenerator(output_dir=tmp_dir, verbose=False)
        result = gen.generate(property_portfolio_path=prop_path)
        assert "data" in result
        assert "file_path" in result
        assert "processing_stats" in result

    def test_mortgage_count_matches_properties(self, property_portfolio_in_tmp):
        tmp_dir, prop_path = property_portfolio_in_tmp
        gen = MortgagePortfolioGenerator(output_dir=tmp_dir, verbose=False)
        result = gen.generate(property_portfolio_path=prop_path)
        assert len(result["data"]["mortgages"]) == 5

    def test_mortgage_ids_unique(self, property_portfolio_in_tmp):
        tmp_dir, prop_path = property_portfolio_in_tmp
        gen = MortgagePortfolioGenerator(output_dir=tmp_dir, verbose=False)
        result = gen.generate(property_portfolio_path=prop_path)
        ids = result["data"]["mortgage_ids"]
        assert len(ids) == len(set(ids))

    def test_mortgage_id_format(self, property_portfolio_in_tmp):
        tmp_dir, prop_path = property_portfolio_in_tmp
        gen = MortgagePortfolioGenerator(output_dir=tmp_dir, verbose=False)
        result = gen.generate(property_portfolio_path=prop_path)
        for mid in result["data"]["mortgage_ids"]:
            assert re.match(r"^MORT-[a-f0-9]{8}$", mid)


@pytest.mark.generator
class TestMortgageGeneratorFile:

    def test_output_file_exists(self, property_portfolio_in_tmp):
        tmp_dir, prop_path = property_portfolio_in_tmp
        gen = MortgagePortfolioGenerator(output_dir=tmp_dir, verbose=False)
        result = gen.generate(property_portfolio_path=prop_path)
        assert result["file_path"].exists()

    def test_output_file_is_valid_json(self, property_portfolio_in_tmp):
        tmp_dir, prop_path = property_portfolio_in_tmp
        gen = MortgagePortfolioGenerator(output_dir=tmp_dir, verbose=False)
        result = gen.generate(property_portfolio_path=prop_path)
        with open(result["file_path"]) as f:
            data = json.load(f)
        assert isinstance(data, dict)


@pytest.mark.generator
class TestMortgageGeneratorDataQuality:

    def test_each_mortgage_has_property_id(self, property_portfolio_in_tmp):
        tmp_dir, prop_path = property_portfolio_in_tmp
        gen = MortgagePortfolioGenerator(output_dir=tmp_dir, verbose=False)
        result = gen.generate(property_portfolio_path=prop_path)
        cdm = LoanCDM()
        for mortgage in result["data"]["mortgages"]:
            mapping = cdm.create_mapping(mortgage)
            assert mapping.get("property_id") is not None

    def test_processing_stats(self, property_portfolio_in_tmp):
        tmp_dir, prop_path = property_portfolio_in_tmp
        gen = MortgagePortfolioGenerator(output_dir=tmp_dir, verbose=False)
        result = gen.generate(property_portfolio_path=prop_path)
        stats = result["processing_stats"]
        assert stats["successful_mortgages"] == 5
        assert stats["failed_mortgages"] == 0
