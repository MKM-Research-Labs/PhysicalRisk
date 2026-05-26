# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Tests for the commercial random value generators."""

import random
import re
from collections import Counter

import pytest

from port.rand.thames.commercial.commercial_random import (
    COMMERCIAL_TYPE_ALLOCATION,
    _ANCHOR_TENANT_POOL,
    _TYPE_AREA_RANGE,
    _TYPE_STOREYS,
    _TYPE_TOTAL_UNITS,
    _TYPE_VALUE_PER_SQM,
    _period_from_year,
    generate_commercial_metadata,
    generate_field_value,
    get_commercial_type,
)


# ---------------------------------------------------------------------------
# Type allocation
# ---------------------------------------------------------------------------


class TestTypeAllocation:

    def test_allocation_length_is_ten(self):
        assert len(COMMERCIAL_TYPE_ALLOCATION) == 10

    def test_allocation_mix_matches_user_spec(self):
        counts = Counter(COMMERCIAL_TYPE_ALLOCATION)
        assert counts == {
            "Office": 3, "MultiFamily": 3, "Hotel": 1,
            "Retail": 2, "MixedUse": 1,
        }

    @pytest.mark.parametrize("idx, expected", [
        (0, "Office"), (1, "Office"), (2, "Office"),
        (3, "MultiFamily"), (4, "MultiFamily"), (5, "MultiFamily"),
        (6, "Hotel"),
        (7, "Retail"), (8, "Retail"),
        (9, "MixedUse"),
    ])
    def test_get_commercial_type_per_index(self, idx, expected):
        assert get_commercial_type(idx) == expected

    def test_get_commercial_type_cycles_beyond_ten(self):
        assert get_commercial_type(10) == get_commercial_type(0)
        assert get_commercial_type(15) == get_commercial_type(5)


# ---------------------------------------------------------------------------
# Metadata
# ---------------------------------------------------------------------------


class TestGenerateCommercialMetadata:

    @pytest.fixture
    def location(self):
        return {"name": "Westminster", "elevation": 7.5,
                "vertical_offset": 1.5, "value_factor": 1.3}

    def test_returns_dict_with_required_keys(self, location):
        md = generate_commercial_metadata(0, location)
        for key in ("property_id", "commercial_type", "construction_year",
                    "property_area", "property_value", "elevation",
                    "vertical_offset", "area_name", "value_factor"):
            assert key in md

    def test_property_id_format(self, location):
        md = generate_commercial_metadata(0, location)
        assert re.match(r"^CPROP-[a-f0-9]{8}$", md["property_id"])

    def test_property_id_deterministic_for_same_input(self, location):
        a = generate_commercial_metadata(0, location)["property_id"]
        b = generate_commercial_metadata(0, location)["property_id"]
        assert a == b

    def test_property_id_differs_by_index(self, location):
        a = generate_commercial_metadata(0, location)["property_id"]
        b = generate_commercial_metadata(1, location)["property_id"]
        assert a != b

    @pytest.mark.parametrize("idx", range(10))
    def test_area_within_type_range(self, idx, location):
        md = generate_commercial_metadata(idx, location)
        ctype = md["commercial_type"]
        lo, hi = _TYPE_AREA_RANGE[ctype]
        assert lo <= md["property_area"] <= hi

    @pytest.mark.parametrize("idx", range(10))
    def test_value_uses_per_sqm_range(self, idx, location):
        md = generate_commercial_metadata(idx, location)
        ctype = md["commercial_type"]
        lo_psqm, hi_psqm = _TYPE_VALUE_PER_SQM[ctype]
        vf = location["value_factor"]
        # Value is rounded to nearest £1k, allow 10% tolerance for rounding.
        lo_val = md["property_area"] * lo_psqm * vf * 0.9
        hi_val = md["property_area"] * hi_psqm * vf * 1.1
        assert lo_val <= md["property_value"] <= hi_val

    def test_property_type_alias_present(self, location):
        # The 'property_type' alias is needed by the residential generators
        # we delegate to (they look up location_info['property_type']).
        md = generate_commercial_metadata(0, location)
        assert md["property_type"] == md["commercial_type"]


# ---------------------------------------------------------------------------
# Field-value generation
# ---------------------------------------------------------------------------


class TestGenerateFieldValue:

    @pytest.fixture
    def metadata(self):
        return generate_commercial_metadata(0, {
            "name": "Westminster", "elevation": 7.5,
            "vertical_offset": 1.5, "value_factor": 1.3,
        })

    def test_commercial_type_returns_metadata_value(self, metadata):
        v = generate_field_value("CommercialType", {}, 0, metadata)
        assert v == metadata["commercial_type"]

    def test_use_class_derived_from_type(self):
        # Office → E(g)(i)
        md = generate_commercial_metadata(0, {"name": "x", "elevation": 5,
                                              "vertical_offset": 1, "value_factor": 1})
        assert generate_field_value("UseClassUKO", {}, 0, md) == "E(g)(i)"
        # Hotel → C1
        md_h = generate_commercial_metadata(6, {"name": "x", "elevation": 5,
                                                "vertical_offset": 1, "value_factor": 1})
        assert generate_field_value("UseClassUKO", {}, 6, md_h) == "C1"

    def test_business_rates_derived_from_type(self):
        # Office → "Office", Hotel → "Hotel", Retail → "Shop and Premises"
        for idx, expected in [(0, "Office"), (6, "Hotel"), (7, "Shop and Premises")]:
            md = generate_commercial_metadata(idx, {"name": "x", "elevation": 5,
                                                    "vertical_offset": 1, "value_factor": 1})
            assert generate_field_value("BusinessRatesCategory", {}, idx, md) == expected

    def test_total_units_within_type_range(self, metadata):
        v = generate_field_value("TotalUnits", {}, 0, metadata)
        lo, hi = _TYPE_TOTAL_UNITS[metadata["commercial_type"]]
        assert lo <= v <= hi

    def test_number_of_storeys_within_range(self, metadata):
        v = generate_field_value("NumberOfStoreys", {}, 0, metadata)
        lo, hi = _TYPE_STOREYS[metadata["commercial_type"]]
        assert lo <= v <= hi

    def test_yields_are_decimal_in_range(self, metadata):
        for field in ("NetInitialYield", "EquivalentYield", "ReversionaryYield"):
            v = generate_field_value(field, {}, 0, metadata)
            assert isinstance(v, float)
            assert 0.03 <= v <= 0.10

    def test_wault_in_expected_range(self, metadata):
        v = generate_field_value("WAULT", {}, 0, metadata)
        assert 2.0 <= v <= 12.0

    def test_anchor_tenant_office_pool(self):
        md = generate_commercial_metadata(0, {"name": "x", "elevation": 5,
                                              "vertical_offset": 1, "value_factor": 1})
        v = generate_field_value("AnchorTenant", {}, 0, md)
        assert v in _ANCHOR_TENANT_POOL["Office"]

    def test_anchor_tenant_hotel_pool(self):
        md = generate_commercial_metadata(6, {"name": "x", "elevation": 5,
                                              "vertical_offset": 1, "value_factor": 1})
        v = generate_field_value("AnchorTenant", {}, 6, md)
        assert v in _ANCHOR_TENANT_POOL["Hotel"]

    def test_delegates_to_residential_for_shared_fields(self, metadata):
        # EAFloodZone is a residential generator — it must produce a valid
        # menu value when called via the commercial dispatcher.
        v = generate_field_value("EAFloodZone", {}, 0, metadata)
        assert v in {"Zone 1", "Zone 2", "Zone 3a", "Zone 3b"}

    def test_unknown_field_falls_back_to_type_default(self, metadata):
        # Unknown name + integer type → falls back to property_random's
        # type-based default (random int 0..100).
        v = generate_field_value("MysteriousField", {"type": "integer"}, 0, metadata)
        assert isinstance(v, int)
        assert 0 <= v <= 100


# ---------------------------------------------------------------------------
# Helper: period mapping
# ---------------------------------------------------------------------------


class TestPeriodFromYear:

    @pytest.mark.parametrize("year, expected", [
        (1850, "Pre-1919"),
        (1918, "Pre-1919"),
        (1919, "1919-1944"),
        (1944, "1919-1944"),
        (1945, "1945-1975"),
        (1975, "1945-1975"),
        (1976, "1976-1999"),
        (1999, "1976-1999"),
        (2000, "2000-2008"),
        (2008, "2000-2008"),
        (2009, "2009-Present"),
        (2026, "2009-Present"),
    ])
    def test_boundary_cases(self, year, expected):
        assert _period_from_year(year) == expected
