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

"""Tests that LoanCDM fields map correctly to generated mortgage JSON."""

import pytest

from config import config
from port.cdm import LoanCDM
from tests.port.cdm._mapping_helpers import run_cdm_mapping_test

_MORTGAGE_SKIP = {
    "generation_metadata", "generated_at", "generator_version",
    "catchment", "total_mortgages_generated", "linked_properties",
    "CatchmentID", "MortgageID", "PropertyID",
}

# Nullable CDM schema fields not yet present in the on-disk mortgage.json
# fixture. Listed so test_all_cdm_fields_present still catches NEW unmapped
# fields but tolerates these pre-existing intentional gaps. The generator
# now emits them; remove once the fixture is regenerated. Contract behaviour
# is exercised by tests/port/cdm/test_loan_to_pricer.py against in-memory
# records.
_KNOWN_OPTIONAL_MISSING = {
    "Mortgage.FinancialTerms.InsuranceRate",
    "Mortgage.RiskAssessment.RecoveryHaircut",
}


@pytest.fixture(scope="module")
def mortgage_mapping_summary():
    json_path = config.get_input_path("mortgage.json")
    return run_cdm_mapping_test(LoanCDM(), json_path, "mortgages", _MORTGAGE_SKIP)


def test_all_cdm_fields_present(mortgage_mapping_summary):
    unexpected = [
        f for f in mortgage_mapping_summary.missing_fields
        if f not in _KNOWN_OPTIONAL_MISSING
    ]
    assert not unexpected, f"Unexpected missing CDM fields: {unexpected}"


def test_known_optional_fields_actually_missing(mortgage_mapping_summary):
    fixed = [
        f for f in _KNOWN_OPTIONAL_MISSING
        if f not in mortgage_mapping_summary.missing_fields
    ]
    assert not fixed, (
        f"These fields are now populated and should be removed from "
        f"_KNOWN_OPTIONAL_MISSING: {fixed}"
    )


def test_all_types_valid(mortgage_mapping_summary):
    assert mortgage_mapping_summary.fields_type_invalid == 0, "Type errors found"


def test_all_values_valid(mortgage_mapping_summary):
    assert mortgage_mapping_summary.fields_value_invalid == 0, "Value errors found"
