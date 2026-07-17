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

"""Tests that LoanCDM fields map correctly to generated loan JSON."""

import pytest

from config import config
from port.cdm import LoanCDM
from tests.port.cdm._mapping_helpers import run_cdm_mapping_test

_LOAN_SKIP = {
    "generation_metadata", "generated_at", "generator_version",
    "catchment", "total_loans_generated", "linked_properties",
    "CatchmentID", "RLoanID", "MortgageID", "PropertyID",
}

@pytest.fixture(scope="module")
def loan_mapping_summary():
    json_path = config.get_input_path("loan.json")
    return run_cdm_mapping_test(LoanCDM(), json_path, "loans", _LOAN_SKIP)


def test_all_cdm_fields_present(loan_mapping_summary):
    assert not loan_mapping_summary.missing_fields, (
        f"Unexpected missing CDM fields: {loan_mapping_summary.missing_fields}"
    )


def test_all_types_valid(loan_mapping_summary):
    assert loan_mapping_summary.fields_type_invalid == 0, "Type errors found"


def test_all_values_valid(loan_mapping_summary):
    assert loan_mapping_summary.fields_value_invalid == 0, "Value errors found"
