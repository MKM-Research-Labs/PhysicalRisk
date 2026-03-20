# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.
#
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Tests for _build_section, _set_specific_mortgage_values, _quality_consistency_check."""

from unittest.mock import MagicMock
import pytest

from tests.port.mortgage.conftest import make_generator


# ===========================================================================
# _build_section
# ===========================================================================

class TestBuildSection:
    """Schema-driven recursive section building."""

    def test_non_dict_schema_returns_empty_dict(self, tmp_path):
        assert make_generator(tmp_path)._build_section("not-a-dict", 0, {}) == {}

    def test_none_schema_returns_empty_dict(self, tmp_path):
        assert make_generator(tmp_path)._build_section(None, 0, {}) == {}

    def test_reserved_key_type_skipped(self, tmp_path):
        gen = make_generator(tmp_path)
        result = gen._build_section({"type": "object", "SomeField": {"type": "text"}}, 0, {})
        assert "type" not in result

    def test_reserved_key_options_skipped(self, tmp_path):
        assert "options" not in make_generator(tmp_path)._build_section({"options": ["A", "B"]}, 0, {})

    def test_reserved_key_description_skipped(self, tmp_path):
        assert "description" not in make_generator(tmp_path)._build_section({"description": "x"}, 0, {})

    def test_reserved_key_values_skipped(self, tmp_path):
        assert "values" not in make_generator(tmp_path)._build_section({"values": [1, 2]}, 0, {})

    def test_none_value_from_generate_field_value_excluded(self, tmp_path):
        gen = make_generator(tmp_path)
        orig = gen.random.generate_field_value
        gen.random.generate_field_value = lambda field, fd, idx, fdata: None
        result = gen._build_section({"AField": {"type": "text"}}, 0, {})
        assert "AField" not in result
        gen.random.generate_field_value = orig

    def test_nested_dict_without_type_recurses(self, tmp_path):
        gen = make_generator(tmp_path)
        orig = gen.random.generate_field_value
        gen.random.generate_field_value = lambda field, fd, idx, fdata: {"leaf": "hello"}.get(field, "value")
        schema = {"SubSection": {"leaf": {"type": "text"}}}
        result = gen._build_section(schema, 0, {})
        assert "SubSection" in result
        assert isinstance(result["SubSection"], dict)
        gen.random.generate_field_value = orig

    def test_empty_schema_returns_empty_dict(self, tmp_path):
        assert make_generator(tmp_path)._build_section({}, 0, {}) == {}


# ===========================================================================
# _set_specific_mortgage_values
# ===========================================================================

class TestSetSpecificMortgageValues:

    def _financial_data(self):
        return {"loan_amount": 320000, "current_balance": 305000,
                "interest_rate": 3.75, "loan_term": 25, "ltv": 80}

    def test_initialises_mortgage_key_when_absent(self, tmp_path):
        gen = make_generator(tmp_path)
        data = {}
        gen._set_specific_mortgage_values(data, "MORT-abc", 0, self._financial_data(), {"property_id": "PROP-001"})
        assert "Mortgage" in data

    def test_initialises_header_key_when_absent(self, tmp_path):
        gen = make_generator(tmp_path)
        data = {}
        gen._set_specific_mortgage_values(data, "MORT-abc", 0, self._financial_data(), {"property_id": "PROP-001"})
        assert "Header" in data["Mortgage"]

    def test_sets_mortgage_id(self, tmp_path):
        gen = make_generator(tmp_path)
        data = {}
        gen._set_specific_mortgage_values(data, "MORT-abc12", 0, self._financial_data(), {"property_id": "PROP-001"})
        assert data["Mortgage"]["Header"]["MortgageID"] == "MORT-abc12"

    def test_sets_property_id_in_header(self, tmp_path):
        gen = make_generator(tmp_path)
        data = {}
        gen._set_specific_mortgage_values(data, "MORT-abc", 0, self._financial_data(), {"property_id": "PROP-xyz"})
        assert data["Mortgage"]["Header"]["PropertyID"] == "PROP-xyz"

    def test_sets_catchment_id(self, tmp_path):
        gen = make_generator(tmp_path)
        data = {}
        gen._set_specific_mortgage_values(data, "MORT-abc", 0, self._financial_data(), {"property_id": "PROP-001"})
        assert data["Mortgage"]["Header"]["CatchmentID"] == "thames"

    def test_sets_loan_details_fields(self, tmp_path):
        gen = make_generator(tmp_path)
        data = {}
        fd = self._financial_data()
        gen._set_specific_mortgage_values(data, "MORT-abc", 0, fd, {"property_id": "PROP-001"})
        loan = data["Mortgage"]["LoanDetails"]
        assert loan["OriginalLoanAmount"] == fd["loan_amount"]
        assert loan["CurrentBalance"] == fd["current_balance"]
        assert loan["InterestRate"] == fd["interest_rate"]
        assert loan["LoanTerm"] == fd["loan_term"]
        assert loan["LTV"] == fd["ltv"]

    def test_existing_mortgage_dict_updated(self, tmp_path):
        gen = make_generator(tmp_path)
        data = {"Mortgage": {"Header": {"ExistingField": "keep"}}}
        gen._set_specific_mortgage_values(data, "MORT-new", 0, self._financial_data(), {"property_id": "P"})
        assert data["Mortgage"]["Header"]["ExistingField"] == "keep"
        assert data["Mortgage"]["Header"]["MortgageID"] == "MORT-new"

    def test_missing_property_id_key_defaults_empty_string(self, tmp_path):
        gen = make_generator(tmp_path)
        data = {}
        gen._set_specific_mortgage_values(data, "MORT-abc", 0, self._financial_data(), {})
        assert data["Mortgage"]["Header"]["PropertyID"] == ""


# ===========================================================================
# _quality_consistency_check (internal fallback path)
# ===========================================================================

class TestQualityConsistencyCheckFallback:

    def _data(self, original=400000, current=390000, ltv=80):
        return {"Mortgage": {"LoanDetails": {
            "OriginalLoanAmount": original, "CurrentBalance": current, "LTV": ltv,
        }}}

    def _strip_qcc(self, gen):
        """Remove quality_consistency_check from random module and return it."""
        qcc = getattr(gen.random, "quality_consistency_check", None)
        if qcc:
            del gen.random.quality_consistency_check
        return qcc

    def _restore_qcc(self, gen, qcc):
        if qcc:
            gen.random.quality_consistency_check = qcc

    def test_current_exceeds_original_is_capped_to_95pct(self, tmp_path):
        gen = make_generator(tmp_path)
        qcc = self._strip_qcc(gen)
        result = gen._quality_consistency_check(self._data(original=300000, current=400000), {})
        assert result["Mortgage"]["LoanDetails"]["CurrentBalance"] <= 300000
        self._restore_qcc(gen, qcc)

    def test_current_within_original_unchanged(self, tmp_path):
        gen = make_generator(tmp_path)
        qcc = self._strip_qcc(gen)
        result = gen._quality_consistency_check(self._data(original=400000, current=350000), {})
        assert result["Mortgage"]["LoanDetails"]["CurrentBalance"] == 350000
        self._restore_qcc(gen, qcc)

    def test_ltv_over_100_set_to_95(self, tmp_path):
        gen = make_generator(tmp_path)
        qcc = self._strip_qcc(gen)
        result = gen._quality_consistency_check(self._data(ltv=120), {})
        assert result["Mortgage"]["LoanDetails"]["LTV"] == 95
        self._restore_qcc(gen, qcc)

    def test_ltv_under_10_set_to_60(self, tmp_path):
        gen = make_generator(tmp_path)
        qcc = self._strip_qcc(gen)
        result = gen._quality_consistency_check(self._data(ltv=5), {})
        assert result["Mortgage"]["LoanDetails"]["LTV"] == 60
        self._restore_qcc(gen, qcc)

    def test_valid_ltv_unchanged(self, tmp_path):
        gen = make_generator(tmp_path)
        qcc = self._strip_qcc(gen)
        result = gen._quality_consistency_check(self._data(ltv=75), {})
        assert result["Mortgage"]["LoanDetails"]["LTV"] == 75
        self._restore_qcc(gen, qcc)

    def test_delegates_to_random_module_when_method_present(self, tmp_path):
        gen = make_generator(tmp_path)
        sentinel = {"sentinel": True}
        mock_qcc = MagicMock(return_value=sentinel)
        orig = getattr(gen.random, "quality_consistency_check", None)
        gen.random.quality_consistency_check = mock_qcc
        result = gen._quality_consistency_check(self._data(), {"x": 1})
        mock_qcc.assert_called_once()
        assert result is sentinel
        if orig:
            gen.random.quality_consistency_check = orig
        else:
            del gen.random.quality_consistency_check
