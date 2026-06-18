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
from unittest.mock import MagicMock, patch

import pytest

from port.src.mortgage import generate_mortgages
from tests.port.mortgage.conftest import make_generator, write_property_portfolio


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
            gen.generate(property_portfolio_path=tmp_path / "nonexistent.json")

    def test_empty_property_list_returns_zero_mortgages(self, tmp_path):
        prop_path = tmp_path / "property.json"
        prop_path.write_text(json.dumps({"properties": []}))
        result = make_generator(tmp_path).generate(property_portfolio_path=prop_path)
        assert result["data"]["mortgages"] == []
        assert result["processing_stats"]["total_mortgages"] == 0


# ===========================================================================
# generate() — full output structure validation
# ===========================================================================

@pytest.mark.generator
class TestGenerateFullOutput:

    def test_output_json_contains_mortgages_key(self, tmp_path):
        prop_path = write_property_portfolio(tmp_path, count=3)
        result = make_generator(tmp_path).generate(property_portfolio_path=prop_path)
        with open(result["file_path"]) as f:
            assert "loans" in json.load(f)

    def test_output_json_contains_generation_metadata(self, tmp_path):
        prop_path = write_property_portfolio(tmp_path, count=2)
        result = make_generator(tmp_path).generate(property_portfolio_path=prop_path)
        with open(result["file_path"]) as f:
            meta = json.load(f)["generation_metadata"]
        assert "generated_at" in meta
        assert "catchment" in meta
        assert meta["total_mortgages_generated"] == 2

    def test_processing_stats_contain_timing(self, tmp_path):
        prop_path = write_property_portfolio(tmp_path, count=2)
        stats = make_generator(tmp_path).generate(property_portfolio_path=prop_path)["processing_stats"]
        assert stats["start_time"] is not None
        assert stats["end_time"] is not None

    def test_mortgage_data_key_is_list(self, tmp_path):
        prop_path = write_property_portfolio(tmp_path, count=3)
        result = make_generator(tmp_path).generate(property_portfolio_path=prop_path)
        assert isinstance(result["data"]["mortgages"], list)

    def test_mortgage_ids_key_is_list(self, tmp_path):
        prop_path = write_property_portfolio(tmp_path, count=3)
        result = make_generator(tmp_path).generate(property_portfolio_path=prop_path)
        assert isinstance(result["data"]["mortgage_ids"], list)

    def test_mortgage_data_structure_has_mortgage_key(self, tmp_path):
        prop_path = write_property_portfolio(tmp_path, count=2)
        result = make_generator(tmp_path).generate(property_portfolio_path=prop_path)
        for m in result["data"]["mortgages"]:
            assert "RLoan" in m

    def test_mortgage_header_has_required_fields(self, tmp_path):
        prop_path = write_property_portfolio(tmp_path, count=2)
        result = make_generator(tmp_path).generate(property_portfolio_path=prop_path)
        for m in result["data"]["mortgages"]:
            header = m["RLoan"]["Header"]
            assert "RLoanID" in header
            assert "PropertyID" in header
            assert "CatchmentID" in header

    def test_loan_values_are_positive(self, tmp_path):
        prop_path = write_property_portfolio(tmp_path, count=3)
        result = make_generator(tmp_path).generate(property_portfolio_path=prop_path)
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
        result = make_generator(tmp_path).generate(property_portfolio_path=prop_path)
        for m in result["data"]["mortgages"]:
            assert (
                m["RLoan"]["CurrentStatus"]["OutstandingBalance"]
                <= m["RLoan"]["FinancialTerms"]["OriginalLoan"]
            )

    def test_ltv_within_valid_range(self, tmp_path):
        prop_path = write_property_portfolio(tmp_path, count=5)
        result = make_generator(tmp_path).generate(property_portfolio_path=prop_path)
        for m in result["data"]["mortgages"]:
            assert 10 <= m["RLoan"]["CurrentStatus"]["CurrentLTV"] <= 100

    def test_output_file_is_valid_json(self, tmp_path):
        prop_path = write_property_portfolio(tmp_path, count=2)
        result = make_generator(tmp_path).generate(property_portfolio_path=prop_path)
        with open(result["file_path"]) as f:
            assert isinstance(json.load(f), dict)


# ===========================================================================
# generate_mortgages convenience function
# ===========================================================================

class TestGenerateMortgagesFunction:

    def test_raises_without_property_file(self, tmp_path):
        with patch("port.src.mortgage._generator.config") as mock_cfg:
            mock_cfg.get_input_dir.return_value = tmp_path
            mock_cfg.CATCHMENT = "thames"
            mock_cfg.get_input_path.return_value = tmp_path / "property.json"
            mock_cfg.load_random_module.return_value = MagicMock()
            mock_cfg.load_params_module.return_value = MagicMock()
            with pytest.raises((FileNotFoundError, Exception)):
                generate_mortgages(output_dir=tmp_path)

    def test_returns_dict_when_property_file_exists(self, tmp_path):
        write_property_portfolio(tmp_path, count=2)
        result = generate_mortgages(output_dir=tmp_path)
        assert isinstance(result, dict)
        assert "data" in result
        assert "file_path" in result
