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

"""Tests that ResidentialAssetCDM fields map correctly to generated property JSON."""

import pytest

from config import config
from port.cdm import ResidentialAssetCDM
from tests.port.cdm._mapping_helpers import run_cdm_mapping_test

_PROPERTY_SKIP = {
    "generation_metadata", "generated_at", "generator_version",
    "catchment", "total_properties_generated", "CatchmentID",
}

# Nullable CDM schema fields that the random property generator does not
# populate. Listed here so test_all_cdm_fields_present catches NEW
# unmapped fields but tolerates these pre-existing intentional gaps.
# When the generator starts emitting one of these, remove it from the
# allowlist — otherwise the regression guard loosens silently.
_KNOWN_OPTIONAL_MISSING = {
    "PropertyHeader.Construction.RetrofitYear",
    "PropertyHeader.Location.BuildingName",
    "PropertyHeader.Location.SubBuildingName",
    "ProtectionMeasures.HazardProfile.WindThresholdKph",
    "HistoryAndIncidents.FloodEvents.LastFloodDateHistory",
    "HistoryAndIncidents.GroundConditions.LastGroundIssueDate",
}


@pytest.fixture(scope="module")
def property_mapping_summary():
    json_path = config.get_input_path("property.json")
    return run_cdm_mapping_test(ResidentialAssetCDM(), json_path, "properties", _PROPERTY_SKIP)


def test_all_cdm_fields_present(property_mapping_summary):
    """Every CDM field should be populated by the generator, EXCEPT the
    nullable fields listed in _KNOWN_OPTIONAL_MISSING. The allowlist
    intentionally pins the current gap set — any new missing field
    triggers a failure here so unmapped additions surface immediately."""
    unexpected = [
        f for f in property_mapping_summary.missing_fields
        if f not in _KNOWN_OPTIONAL_MISSING
    ]
    assert not unexpected, (
        f"Unexpected missing CDM fields (not in _KNOWN_OPTIONAL_MISSING): "
        f"{unexpected}"
    )


def test_known_optional_fields_actually_missing(property_mapping_summary):
    """If a field in _KNOWN_OPTIONAL_MISSING is now populated, take it
    out of the allowlist so the strict check on it resumes."""
    fixed = [
        f for f in _KNOWN_OPTIONAL_MISSING
        if f not in property_mapping_summary.missing_fields
    ]
    assert not fixed, (
        f"These fields are now populated and should be removed from "
        f"_KNOWN_OPTIONAL_MISSING: {fixed}"
    )


def test_all_types_valid(property_mapping_summary):
    assert property_mapping_summary.fields_type_invalid == 0, "Type errors found"


def test_all_values_valid(property_mapping_summary):
    assert property_mapping_summary.fields_value_invalid == 0, "Value errors found"
