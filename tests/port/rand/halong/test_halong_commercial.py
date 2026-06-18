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

"""Coverage smoke tests for port.rand.halong.commercial.commercial_random.*

Commercial generators delegate shared fields to the residential generator
via property_random. The halong copy imports from port.rand.halong.property
(the only line that differs from the thames copy).
"""

import random

import pytest


@pytest.fixture(autouse=True)
def _seeded():
    random.seed(20260527)


@pytest.fixture(autouse=True)
def _halong(monkeypatch):
    """Drive the halong profile through the shared commercial generators.

    Post-dedup the ``port.rand.halong.commercial`` tree is an alias of the
    shared engine, which reads the *active* catchment profile. These tests
    assert halong-specific behaviour, so activate the halong catchment.
    """
    from config import config
    monkeypatch.setattr(config, "_catchment_id", "halong")


# ---------------------------------------------------------------------------
# Module-load smoke
# ---------------------------------------------------------------------------

def test_import_commercial_subpackage():
    from port.rand.halong.commercial import commercial_random
    assert hasattr(commercial_random, "generate_field_value")


def test_import_all_modules():
    from port.rand.halong.commercial.commercial_random import (
        COMMERCIAL_TYPE_ALLOCATION, generators, metadata,
    )
    assert COMMERCIAL_TYPE_ALLOCATION
    assert hasattr(generators, "generate_field_value")
    assert hasattr(metadata, "generate_commercial_metadata")


# ---------------------------------------------------------------------------
# metadata.py
# ---------------------------------------------------------------------------

class TestGetCommercialType:
    def test_index_within_allocation(self):
        from port.rand.halong.commercial.commercial_random.metadata import get_commercial_type
        from port.rand.halong.commercial.commercial_random import COMMERCIAL_TYPE_ALLOCATION
        for i, expected in enumerate(COMMERCIAL_TYPE_ALLOCATION):
            assert get_commercial_type(i) == expected

    def test_index_past_allocation_cycles(self):
        from port.rand.halong.commercial.commercial_random.metadata import get_commercial_type
        from port.rand.halong.commercial.commercial_random import COMMERCIAL_TYPE_ALLOCATION
        n = len(COMMERCIAL_TYPE_ALLOCATION)
        assert get_commercial_type(n) == COMMERCIAL_TYPE_ALLOCATION[0]
        assert get_commercial_type(n + 3) == COMMERCIAL_TYPE_ALLOCATION[3]


class TestDeterministicCommercialId:
    def test_returns_cprop_prefix(self):
        from port.rand.halong.commercial.commercial_random.metadata import _deterministic_commercial_id
        cid = _deterministic_commercial_id({"name": "X", "vertical_offset": 0.5}, 0)
        assert cid.startswith("CPROP-")

    def test_stable_across_calls(self):
        from port.rand.halong.commercial.commercial_random.metadata import _deterministic_commercial_id
        loc = {"name": "Halong", "vertical_offset": 0.5}
        assert _deterministic_commercial_id(loc, 0) == _deterministic_commercial_id(loc, 0)


class TestPeriodFromYear:
    @pytest.mark.parametrize("year,expected", [
        (1970, "Pre-1980"),
        (1990, "1980-1994"),
        (2000, "1995-2004"),
        (2010, "2005-2014"),
        (2020, "2015-Present"),
    ])
    def test_all_year_branches(self, year, expected):
        from port.rand.halong.commercial.commercial_random.metadata import period_from_year
        assert period_from_year(year) == expected


class TestAnchorTenant:
    @pytest.mark.parametrize("ctype", [
        "Office", "MultiFamily", "Hotel", "Retail", "MixedUse",
    ])
    def test_known_types_return_str(self, ctype):
        from port.rand.halong.commercial.commercial_random.metadata import anchor_tenant
        assert isinstance(anchor_tenant(ctype), str)

    def test_unknown_type_falls_back(self):
        from port.rand.halong.commercial.commercial_random.metadata import anchor_tenant
        assert anchor_tenant("MysteryType") == "Multi-let"


class TestGenerateCommercialMetadata:
    @pytest.mark.parametrize("index", [0, 3, 6, 9, 15])
    def test_returns_required_keys(self, index):
        from port.rand.halong.commercial.commercial_random.metadata import generate_commercial_metadata
        loc = {"elevation": 5.0, "name": "Bai Chay", "vertical_offset": 0.5}
        meta = generate_commercial_metadata(index, loc)
        for k in ("property_id", "commercial_type", "property_type",
                  "construction_year", "property_area", "property_value",
                  "elevation"):
            assert k in meta
        assert meta["property_id"].startswith("CPROP-")
        assert meta["property_area"] > 0
        assert meta["property_value"] > 0


# ---------------------------------------------------------------------------
# generators.py
# ---------------------------------------------------------------------------

@pytest.fixture
def commercial_metadata():
    """Realistic commercial metadata as built by generate_commercial_metadata."""
    return {
        "commercial_type": "Office",
        "property_type": "Office",
        "property_area": 5000.0,
        "property_value": 50_000_000,
        "construction_year": 1995,
        "elevation": 5.0,
        "vertical_offset": 0.5,
        "area_name": "Bai Chay",
        "value_factor": 1.0,
        "streets_data": {},
    }


class TestCommercialGenerators:
    """generate_field_value covers commercial-only fields, then delegates
    everything else to the residential property_random generator."""

    @pytest.mark.parametrize("field", [
        "CommercialType", "UseClassUKO", "BusinessRatesCategory",
        "OccupancyStatus", "PropertyAreaSqm", "NetInternalAreaSqm",
        "NetLettableAreaSqm", "PropertyValue", "NumberOfStoreys",
        "TotalUnits", "ParkingSpaces", "LoadingBays",
        "PlantRoomLocation", "ServiceCore", "ConstructionType",
        "ConstructionYear", "PropertyPeriod", "PropertyCondition",
        "DisabledAccess", "GoodsLiftCount", "GoodsLiftCapacityKg",
        "EmergencyExits", "DeliveryBays", "AnchorTenant", "WAULT",
        "ServiceChargeGbpPerSqm", "NetInitialYield", "EquivalentYield",
        "ReversionaryYield", "CovenantStrength",
    ])
    def test_commercial_only_fields(self, field, commercial_metadata):
        from port.rand.halong.commercial.commercial_random.generators import generate_field_value
        v = generate_field_value(field, {}, 0, commercial_metadata)
        assert v is not None

    def test_commercial_type_returns_metadata_value(self, commercial_metadata):
        from port.rand.halong.commercial.commercial_random.generators import generate_field_value
        commercial_metadata["commercial_type"] = "Hotel"
        assert generate_field_value("CommercialType", {}, 0, commercial_metadata) == "Hotel"

    def test_use_class_dispatches_by_type(self, commercial_metadata):
        from port.rand.halong.commercial.commercial_random.generators import generate_field_value
        commercial_metadata["commercial_type"] = "Retail"
        # halong uses Vietnam-local use-class labels (not UK O-classes): Retail -> "Retail"
        assert generate_field_value("UseClassUKO", {}, 0, commercial_metadata) == "Retail"

    def test_unknown_field_delegates_to_residential(self, commercial_metadata):
        from port.rand.halong.commercial.commercial_random.generators import generate_field_value
        # Unknown commercial field falls through to property_random — should not raise
        v = generate_field_value("UnknownField", {"type": "text"}, 0, commercial_metadata)
        # Returns something (may be empty string or generated value)
        assert v is not None or v == ""

    def test_exception_in_commercial_generator_falls_through(self, commercial_metadata):
        from port.rand.halong.commercial.commercial_random.generators import generate_field_value
        # Force exception: UseClassUKO indexes a TYPE_USE_CLASS dict by commercial_type
        commercial_metadata["commercial_type"] = "UnknownType"
        # Should not raise — exception is caught and falls through to residential
        v = generate_field_value("UseClassUKO", {"type": "text"}, 0, commercial_metadata)
        # The residential generator likely returns something or empty
        assert v is not None or v == ""
