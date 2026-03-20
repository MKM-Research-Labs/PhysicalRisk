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

"""Tests that MortgageCDM fields map correctly to generated mortgage JSON."""

import pytest

from config import config
from port.cdm import MortgageCDM
from tests.port.cdm._mapping_helpers import run_cdm_mapping_test

_MORTGAGE_SKIP = {
    "generation_metadata", "generated_at", "generator_version",
    "catchment", "total_mortgages_generated", "linked_properties",
    "CatchmentID", "MortgageID", "PropertyID",
}


@pytest.fixture(scope="module")
def mortgage_mapping_summary():
    json_path = config.get_input_path("mortgage.json")
    return run_cdm_mapping_test(MortgageCDM(), json_path, "mortgages", _MORTGAGE_SKIP)


def test_all_cdm_fields_present(mortgage_mapping_summary):
    assert mortgage_mapping_summary.fields_missing == 0, (
        f"Missing fields: {mortgage_mapping_summary.missing_fields}"
    )


def test_all_types_valid(mortgage_mapping_summary):
    assert mortgage_mapping_summary.fields_type_invalid == 0, "Type errors found"


def test_all_values_valid(mortgage_mapping_summary):
    assert mortgage_mapping_summary.fields_value_invalid == 0, "Value errors found"
