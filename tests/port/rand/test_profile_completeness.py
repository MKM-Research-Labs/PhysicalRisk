# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Profile completeness contract for the catchment rand de-duplication.

The shared generators (``port.rand.shared.*``) read every per-catchment value
from the active catchment's profile (``port.rand.profiles.<id>``). This module
pins the profile CONTRACT so that adding a catchment can't silently ship a
profile with a missing or malformed key — which would otherwise surface as an
``AttributeError`` / ``KeyError`` deep inside generation.

It discovers every profile module under ``port.rand.profiles`` automatically, so
a new catchment is covered the moment its profile file exists.
"""

import importlib
import pkgutil

import pytest

import port.rand.profiles as _profiles_pkg


# ---------------------------------------------------------------------------
# Contract
# ---------------------------------------------------------------------------

# Scalars / collections every profile MUST define (read by the shared engine
# with no getattr default).
REQUIRED_BOOL_TOGGLES = (
    "PUBLISH_BRI_LETTER_RATINGS",
    "BRI_SCORES_ENABLED",
    "COMMERCIAL_BRI_ENABLED",
)

REQUIRED_ATTRS = (
    "SEISMIC_PGA_RANGE",
    "SEISMIC_HAZARD_CLASS_WEIGHTS",
    "COMMERCIAL_TYPE_ALLOCATION",
    "COMMERCIAL_CONSTRUCTION_TYPES",
    "COMMERCIAL_ANCHOR_TENANT_POOL",
    "COMMERCIAL_PERIOD_BUCKETS",
    "COMMERCIAL_CONSTRUCTION_YEAR_RANGE",
)

# Per-type tables that MUST have an entry for every type in the allocation
# (the shared code indexes them by commercial_type → KeyError if missing).
REQUIRED_PER_TYPE_DICTS = (
    "COMMERCIAL_TYPE_AREA_RANGE",
    "COMMERCIAL_TYPE_VALUE_PER_SQM",
    "COMMERCIAL_TYPE_USE_CLASS",
    "COMMERCIAL_TYPE_BUSINESS_RATES",
    "COMMERCIAL_TYPE_STOREYS",
    "COMMERCIAL_TYPE_TOTAL_UNITS",
    "COMMERCIAL_TYPE_PARKING_SPACES",
    "COMMERCIAL_TYPE_LOADING_BAYS",
)

# The five-level hazard scale SEISMIC_HAZARD_CLASS_WEIGHTS weights (see
# property_random/generators/_registry_a.py SeismicHazardClass).
_HAZARD_CLASS_COUNT = 5


def _discover_catchments():
    """Every profile module under port.rand.profiles (excludes private/dunder)."""
    return sorted(
        name for _, name, ispkg in pkgutil.iter_modules(_profiles_pkg.__path__)
        if not ispkg and not name.startswith("_")
    )


_CATCHMENTS = _discover_catchments()


def _profile(catchment):
    return importlib.import_module(f"port.rand.profiles.{catchment}")


@pytest.fixture
def _active(monkeypatch):
    """Return a helper that activates a catchment for the shared generators."""
    from config import config

    def activate(catchment):
        monkeypatch.setattr(config, "_catchment_id", catchment)
    return activate


def test_at_least_one_catchment_discovered():
    assert _CATCHMENTS, "no catchment profiles found under port.rand.profiles"


@pytest.mark.parametrize("catchment", _CATCHMENTS)
class TestProfileContract:
    """Static shape checks — every profile satisfies the read contract."""

    def test_bool_toggles_present_and_bool(self, catchment):
        p = _profile(catchment)
        for attr in REQUIRED_BOOL_TOGGLES:
            assert hasattr(p, attr), f"{catchment}: missing {attr}"
            assert isinstance(getattr(p, attr), bool), f"{catchment}.{attr} not bool"

    def test_required_attrs_present(self, catchment):
        p = _profile(catchment)
        for attr in REQUIRED_ATTRS + REQUIRED_PER_TYPE_DICTS:
            assert hasattr(p, attr), f"{catchment}: missing {attr}"

    def test_seismic_pga_range_shape(self, catchment):
        lo, hi = _profile(catchment).SEISMIC_PGA_RANGE
        assert 0 <= lo <= hi, f"{catchment}: SEISMIC_PGA_RANGE not 0<=lo<=hi"

    def test_seismic_hazard_weights_shape(self, catchment):
        w = _profile(catchment).SEISMIC_HAZARD_CLASS_WEIGHTS
        assert len(w) == _HAZARD_CLASS_COUNT, (
            f"{catchment}: SEISMIC_HAZARD_CLASS_WEIGHTS must have "
            f"{_HAZARD_CLASS_COUNT} weights (None/Low/Medium/High/Extreme)")
        assert abs(sum(w) - 1.0) < 1e-6, f"{catchment}: seismic weights must sum to 1.0"

    def test_allocation_non_empty(self, catchment):
        alloc = _profile(catchment).COMMERCIAL_TYPE_ALLOCATION
        assert alloc, f"{catchment}: COMMERCIAL_TYPE_ALLOCATION is empty"

    def test_construction_types_non_empty(self, catchment):
        assert _profile(catchment).COMMERCIAL_CONSTRUCTION_TYPES, (
            f"{catchment}: COMMERCIAL_CONSTRUCTION_TYPES is empty")

    def test_per_type_dicts_cover_every_allocated_type(self, catchment):
        p = _profile(catchment)
        types = set(p.COMMERCIAL_TYPE_ALLOCATION)
        for attr in REQUIRED_PER_TYPE_DICTS:
            table = getattr(p, attr)
            missing = types - set(table)
            assert not missing, f"{catchment}.{attr} missing types: {sorted(missing)}"

    def test_anchor_tenant_pool_covers_every_allocated_type(self, catchment):
        p = _profile(catchment)
        missing = set(p.COMMERCIAL_TYPE_ALLOCATION) - set(p.COMMERCIAL_ANCHOR_TENANT_POOL)
        assert not missing, (
            f"{catchment}.COMMERCIAL_ANCHOR_TENANT_POOL missing types: {sorted(missing)}")

    def test_period_buckets_have_open_ended_terminator(self, catchment):
        buckets = _profile(catchment).COMMERCIAL_PERIOD_BUCKETS
        assert buckets, f"{catchment}: COMMERCIAL_PERIOD_BUCKETS empty"
        assert buckets[-1][0] is None, (
            f"{catchment}: COMMERCIAL_PERIOD_BUCKETS last cutoff must be None "
            "(open-ended catch-all)")

    def test_construction_year_range_shape(self, catchment):
        lo, hi = _profile(catchment).COMMERCIAL_CONSTRUCTION_YEAR_RANGE
        assert isinstance(lo, int), f"{catchment}: construction-year lo must be int"
        assert hi is None or (isinstance(hi, int) and hi >= lo), (
            f"{catchment}: construction-year hi must be None or int >= lo")


@pytest.mark.parametrize("catchment", _CATCHMENTS)
class TestProfileDrivesGeneration:
    """Functional smoke — every profile drives the shared generators end-to-end
    without raising (the real protection against a malformed profile)."""

    _LOC = {"name": "Reach", "elevation": 8.0, "vertical_offset": 0.5,
            "value_factor": 1.0, "streets_data": {}}

    def test_commercial_metadata_and_fields(self, catchment, _active):
        _active(catchment)
        from port.rand.shared.commercial.commercial_random import (
            generate_commercial_metadata, generate_field_value,
        )
        # One asset of every allocated type, exercising the per-type tables.
        n = len(_profile(catchment).COMMERCIAL_TYPE_ALLOCATION)
        for i in range(n):
            md = generate_commercial_metadata(i, dict(self._LOC))
            for field in ("UseClassUKO", "BusinessRatesCategory", "NumberOfStoreys",
                          "TotalUnits", "ParkingSpaces", "LoadingBays",
                          "ConstructionType", "PropertyPeriod", "AnchorTenant",
                          "BRIWaterRating", "WindCodes"):
                generate_field_value(field, {}, i, md)

    def test_property_seismic_fields(self, catchment, _active):
        _active(catchment)
        from port.rand.shared.property.property_random.generators import (
            generate_field_value,
        )
        info = {"property_type": "Detached", "property_area": 120.0,
                "elevation": 8.0, "area_name": "Reach", "value_factor": 1.0}
        pga = generate_field_value("DesignSeismicPGA", {}, 0, dict(info))
        assert pga is not None
        hazard = generate_field_value("SeismicHazardClass", {}, 0, dict(info))
        assert hazard in ("None", "Low", "Medium", "High", "Extreme")

    def test_resilience_toggles_resolve(self, catchment, _active):
        _active(catchment)
        from config import config
        mod = config.load_random_module("property.property_random.resilience")
        assert isinstance(mod.PUBLISH_BRI_LETTER_RATINGS, bool)
        assert isinstance(mod.BRI_SCORES_ENABLED, bool)
