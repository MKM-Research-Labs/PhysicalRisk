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

"""Tests for the commercial random value generators."""

import random
import re
from collections import Counter

import pytest

from port.rand.thames.commercial.commercial_random import (
    ANCHOR_TENANT_POOL,
    COMMERCIAL_TYPE_ALLOCATION,
    TYPE_AREA_RANGE,
    TYPE_STOREYS,
    TYPE_TOTAL_UNITS,
    TYPE_VALUE_PER_SQM,
    generate_commercial_metadata,
    generate_field_value,
    get_commercial_type,
    period_from_year,
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
        lo, hi = TYPE_AREA_RANGE[ctype]
        assert lo <= md["property_area"] <= hi

    @pytest.mark.parametrize("idx", range(10))
    def test_value_uses_per_sqm_range(self, idx, location):
        md = generate_commercial_metadata(idx, location)
        ctype = md["commercial_type"]
        lo_psqm, hi_psqm = TYPE_VALUE_PER_SQM[ctype]
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
        lo, hi = TYPE_TOTAL_UNITS[metadata["commercial_type"]]
        assert lo <= v <= hi

    def test_number_of_storeys_within_range(self, metadata):
        v = generate_field_value("NumberOfStoreys", {}, 0, metadata)
        lo, hi = TYPE_STOREYS[metadata["commercial_type"]]
        assert lo <= v <= hi

    def test_yields_are_decimal_in_range(self, metadata):
        for field in ("NetInitialYield", "EquivalentYield", "ReversionaryYield"):
            v = generate_field_value(field, {}, 0, metadata)
            assert isinstance(v, float)
            assert 0.03 <= v <= 0.10

    def test_wault_in_expected_range(self, metadata):
        v = generate_field_value("WAULT", {}, 0, metadata)
        assert 1.5 <= v <= 8.0

    def test_anchor_tenant_office_pool(self):
        md = generate_commercial_metadata(0, {"name": "x", "elevation": 5,
                                              "vertical_offset": 1, "value_factor": 1})
        v = generate_field_value("AnchorTenant", {}, 0, md)
        assert v in ANCHOR_TENANT_POOL["Office"]

    def test_anchor_tenant_hotel_pool(self):
        md = generate_commercial_metadata(6, {"name": "x", "elevation": 5,
                                              "vertical_offset": 1, "value_factor": 1})
        v = generate_field_value("AnchorTenant", {}, 6, md)
        assert v in ANCHOR_TENANT_POOL["Hotel"]

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
        assert period_from_year(year) == expected


class TestBriRatingCompleteness:
    """Every BRI sub-rating the CDM defines must actually be published.

    Regression for a silent omission: the prototype set computed six grades,
    the CDM schema defined six rating fields, and the generator wrote two. Wind,
    fire, seismic and the overall rating were dropped, so the wind damage model
    had no grade to read while water and flash sat published beside it.

    Asserted against the schema rather than a hand-written list, so a rating
    added to the CDM later fails here until the generator publishes it too.
    """

    @staticmethod
    def _schema_rating_fields():
        from port.cdm.asset.resilience._ratings import RATINGS_SCHEMA
        block = RATINGS_SCHEMA["GoverningBodyRatings"]
        return {k for k in block if k.startswith("BRI") and k.endswith("Rating")}

    def test_generator_publishes_every_schema_rating(self):
        from port.rand.shared.commercial.commercial_random.generators import (
            _commercial_generators,
        )
        published = set(_commercial_generators())
        missing = self._schema_rating_fields() - published
        assert not missing, f"CDM defines these ratings but the generator omits them: {sorted(missing)}"

    def test_wind_rating_is_published(self):
        """Named separately because the wind damage model reads it."""
        from port.rand.shared.commercial.commercial_random.generators import (
            _commercial_generators,
        )
        assert "BRIWindRating" in _commercial_generators()

    def test_wind_rating_varies_by_asset_type(self):
        """A rating identical across every prototype would be no better than the
        omission it replaced. The hotel prototype carries the WD06 differentiator
        and must grade above the rest.

        Reads the grade from the prototype set directly rather than through the
        generator, because the generator gates every BRI field on the active
        catchment profile's ``COMMERCIAL_BRI_ENABLED`` and the default test
        profile has no BRI regime — which would make this pass vacuously on a
        column of nulls.
        """
        from port.rand.shared.commercial.bri_codes import for_commercial

        grades = {
            t: (for_commercial(t) or {}).get("wind_grade")
            for t in ("Hotel", "Office", "Retail", "MultiFamily", "MixedUse")
        }
        assert grades["Hotel"] == "A", grades
        assert len(set(grades.values())) > 1, grades


class TestFloodEnvelopeRating:
    """BRIFloodRating is the water envelope: the weaker of Water and Flash.

    The subtlety is what "N/A" means. For commercial it is a *value* meaning the
    asset has no exposure to that hazard, not a bad score. Treating it as the
    weakest letter would report an asset with genuine flash exposure as having
    no flood exposure at all.

    Every test here forces ``COMMERCIAL_BRI_ENABLED``. Without it the function
    returns None before reaching its body, and an assertion that tolerated that
    None would pass while testing nothing.
    """

    @staticmethod
    def _envelope(monkeypatch, water, flash):
        """Evaluate the envelope for a given (water, flash) grade pair."""
        import port.rand.shared.commercial.commercial_random.generators as gen

        class _Profile:
            COMMERCIAL_BRI_ENABLED = True

        monkeypatch.setattr(gen, "active_profile", lambda: _Profile())
        monkeypatch.setattr(
            gen, "_bri",
            lambda info: {"water_grade": water, "flash_grade": flash})
        return gen._flood_envelope_rating({"commercial_type": "Office"})

    def test_the_weaker_of_two_applicable_ratings_wins(self, monkeypatch):
        assert self._envelope(monkeypatch, "A", "B") == "B"
        assert self._envelope(monkeypatch, "B", "A") == "B"
        assert self._envelope(monkeypatch, "AA", "A") == "A"

    def test_equal_ratings_return_that_rating(self, monkeypatch):
        assert self._envelope(monkeypatch, "A", "A") == "A"

    def test_an_unexposed_hazard_is_excluded_not_treated_as_weakest(self, monkeypatch):
        """The point of the whole function. An asset with no tsunami exposure
        but real flash exposure must report the flash rating, not N/A."""
        assert self._envelope(monkeypatch, "N/A", "B") == "B"
        assert self._envelope(monkeypatch, "A", "N/A") == "A"

    def test_na_only_when_nothing_is_applicable(self, monkeypatch):
        assert self._envelope(monkeypatch, "N/A", "N/A") == "N/A"

    def test_none_grades_are_treated_as_unexposed(self, monkeypatch):
        assert self._envelope(monkeypatch, None, "B") == "B"
        assert self._envelope(monkeypatch, None, None) == "N/A"

    def test_returns_none_when_the_catchment_has_no_bri_regime(self, monkeypatch):
        """A catchment without a BRI regime leaves the field null rather than
        stamping N/A — the same distinction _bri_rating draws."""
        import port.rand.shared.commercial.commercial_random.generators as gen

        class _Profile:
            COMMERCIAL_BRI_ENABLED = False

        monkeypatch.setattr(gen, "active_profile", lambda: _Profile())
        assert gen._flood_envelope_rating({"commercial_type": "Office"}) is None

    def test_the_office_prototype_really_has_this_shape(self):
        """Guards the premise: if the prototype set changed so that Office had
        tsunami exposure, the tests above would still pass but would no longer
        describe the case that motivated the function."""
        from port.rand.shared.commercial.bri_codes import for_commercial

        proto = for_commercial("Office")
        assert proto["water_grade"] in (None, "N/A")
        assert proto["flash_grade"] not in (None, "N/A")
