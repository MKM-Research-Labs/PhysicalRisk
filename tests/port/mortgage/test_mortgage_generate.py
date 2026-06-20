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

"""Tests for log(), generate() error paths, generate() full output, and generate_mortgages()."""

import json

import pytest

import database
from port.src.mortgage import generate_mortgages
from tests.port.mortgage.conftest import make_generator, write_property_portfolio
from db_helpers import tmp_catchment


@pytest.fixture(autouse=True)
def _iso_catchment(tmp_path):
    """Bind a tmp-rooted backend (catchment "thames") for every test in this module.

    The migrated mortgage generator reads the property portfolio and writes loans through
    ``database``; rooting the backend at ``tmp_path`` means ``write_property_portfolio``
    (and any direct ``property.json`` write) is read back, and loan writes are isolated."""
    with tmp_catchment(tmp_path):
        yield


# ===========================================================================
# log() method
# ===========================================================================

class TestLogMethod:

    def test_info_level_does_not_raise(self, tmp_path):
        make_generator(tmp_path).log("test info message", "INFO")

    def test_warning_level_does_not_raise(self, tmp_path):
        make_generator(tmp_path).log("test warning", "WARNING")

    def test_error_level_does_not_raise(self, tmp_path):
        make_generator(tmp_path).log("test error", "ERROR")

    def test_debug_level_does_not_raise(self, tmp_path):
        make_generator(tmp_path).log("test debug", "DEBUG")

    def test_unknown_level_falls_back_to_info(self, tmp_path):
        make_generator(tmp_path).log("unknown level message", "NOTAREAL")

    def test_success_level_falls_back_gracefully(self, tmp_path):
        make_generator(tmp_path).log("success message", "SUCCESS")


# ===========================================================================
# generate() — error paths
# ===========================================================================

class TestGenerateErrorPaths:

    def test_missing_property_file_raises_file_not_found(self, tmp_path):
        gen = make_generator(tmp_path)
        with pytest.raises(FileNotFoundError):
            gen.generate()

    def test_empty_property_list_returns_zero_mortgages(self, tmp_path):
        prop_path = tmp_path / "property.json"
        prop_path.write_text(json.dumps({"properties": []}))
        result = make_generator(tmp_path).generate()
        assert result["data"]["mortgages"] == []
        assert result["processing_stats"]["total_mortgages"] == 0


# ===========================================================================
# generate() — full output structure validation
# ===========================================================================

@pytest.mark.generator
class TestGenerateFullOutput:

    def test_output_contains_mortgages_key(self, tmp_path):
        write_property_portfolio(tmp_path, count=3)
        result = make_generator(tmp_path).generate()
        assert "loans" in database.get_loan_portfolio(result["catchment"])

    def test_output_contains_generation_metadata(self, tmp_path):
        write_property_portfolio(tmp_path, count=2)
        result = make_generator(tmp_path).generate()
        meta = database.get_loan_portfolio(result["catchment"])["generation_metadata"]
        assert "generated_at" in meta
        assert "catchment" in meta
        assert meta["total_mortgages_generated"] == 2

    def test_processing_stats_contain_timing(self, tmp_path):
        prop_path = write_property_portfolio(tmp_path, count=2)
        stats = make_generator(tmp_path).generate()["processing_stats"]
        assert stats["start_time"] is not None
        assert stats["end_time"] is not None

    def test_more_than_five_properties_uses_debug_linkage_log(self, tmp_path):
        """With >5 properties, the per-mortgage DEBUG linkage log (the else branch
        of the 'first five / every 50th' INFO condition) is exercised."""
        write_property_portfolio(tmp_path, count=6)
        result = make_generator(tmp_path).generate()
        assert len(result["data"]["mortgages"]) == 6

    def test_mortgage_data_key_is_list(self, tmp_path):
        prop_path = write_property_portfolio(tmp_path, count=3)
        result = make_generator(tmp_path).generate()
        assert isinstance(result["data"]["mortgages"], list)

    def test_mortgage_ids_key_is_list(self, tmp_path):
        prop_path = write_property_portfolio(tmp_path, count=3)
        result = make_generator(tmp_path).generate()
        assert isinstance(result["data"]["mortgage_ids"], list)

    def test_mortgage_data_structure_has_mortgage_key(self, tmp_path):
        prop_path = write_property_portfolio(tmp_path, count=2)
        result = make_generator(tmp_path).generate()
        for m in result["data"]["mortgages"]:
            assert "RLoan" in m

    def test_mortgage_header_has_required_fields(self, tmp_path):
        prop_path = write_property_portfolio(tmp_path, count=2)
        result = make_generator(tmp_path).generate()
        for m in result["data"]["mortgages"]:
            header = m["RLoan"]["Header"]
            assert "RLoanID" in header
            assert "PropertyID" in header
            assert "CatchmentID" in header

    def test_loan_values_are_positive(self, tmp_path):
        prop_path = write_property_portfolio(tmp_path, count=3)
        result = make_generator(tmp_path).generate()
        for m in result["data"]["mortgages"]:
            terms = m["RLoan"]["FinancialTerms"]
            status = m["RLoan"]["CurrentStatus"]
            assert terms["OriginalLoan"] > 0
            assert status["OutstandingBalance"] > 0
            assert status["CurrentInterestRate"] > 0
            assert terms["OriginalTerm"] > 0
            assert status["CurrentLTV"] > 0

    def test_current_balance_does_not_exceed_original_loan(self, tmp_path):
        prop_path = write_property_portfolio(tmp_path, count=5)
        result = make_generator(tmp_path).generate()
        for m in result["data"]["mortgages"]:
            assert (
                m["RLoan"]["CurrentStatus"]["OutstandingBalance"]
                <= m["RLoan"]["FinancialTerms"]["OriginalLoan"]
            )

    def test_ltv_within_valid_range(self, tmp_path):
        prop_path = write_property_portfolio(tmp_path, count=5)
        result = make_generator(tmp_path).generate()
        for m in result["data"]["mortgages"]:
            assert 10 <= m["RLoan"]["CurrentStatus"]["CurrentLTV"] <= 100

    def test_output_is_valid_portfolio(self, tmp_path):
        write_property_portfolio(tmp_path, count=2)
        result = make_generator(tmp_path).generate()
        assert isinstance(database.get_loan_portfolio(result["catchment"]), dict)


# ===========================================================================
# generate_mortgages convenience function
# ===========================================================================

class TestGenerateMortgagesFunction:

    def test_raises_without_property_portfolio(self, tmp_path):
        # No property portfolio persisted for the catchment → FileNotFoundError.
        with pytest.raises(FileNotFoundError):
            generate_mortgages()

    def test_returns_dict_when_property_portfolio_exists(self, tmp_path):
        write_property_portfolio(tmp_path, count=2)
        result = generate_mortgages()
        assert isinstance(result, dict)
        assert "data" in result
        assert "catchment" in result
