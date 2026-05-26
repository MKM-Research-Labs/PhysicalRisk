# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Tests for CommercialAssetCDM and the standalone commercial validator."""

import pytest

from port.cdm import CommercialAssetCDM
from port.cdm.asset.commercial.validator import (
    get_required_fields,
    validate,
)


# ---------------------------------------------------------------------------
# Standalone validate()
# ---------------------------------------------------------------------------


class TestCommercialValidator:

    def _valid_record(self):
        return {
            "CommercialAsset": {
                "Header": {"PropertyID": "CPROP-test1234", "CatchmentID": "thames"},
                "CommercialAttributes": {"CommercialType": "Office"},
                "Location": {"LatitudeDegrees": 51.5, "LongitudeDegrees": -0.1},
            }
        }

    def test_valid_returns_empty(self):
        assert validate(self._valid_record()) == {}

    def test_missing_property_id_detected(self):
        d = self._valid_record()
        del d["CommercialAsset"]["Header"]["PropertyID"]
        errors = validate(d)
        assert "Header" in errors
        assert any("PropertyID" in e for e in errors["Header"])

    def test_missing_catchment_id_recommended(self):
        d = self._valid_record()
        del d["CommercialAsset"]["Header"]["CatchmentID"]
        errors = validate(d)
        assert "Header" in errors
        assert any("CatchmentID" in e for e in errors["Header"])

    def test_missing_commercial_type_detected(self):
        d = self._valid_record()
        del d["CommercialAsset"]["CommercialAttributes"]["CommercialType"]
        errors = validate(d)
        assert "CommercialAttributes" in errors
        assert any("CommercialType" in e for e in errors["CommercialAttributes"])

    def test_missing_latitude_detected(self):
        d = self._valid_record()
        del d["CommercialAsset"]["Location"]["LatitudeDegrees"]
        errors = validate(d)
        assert "Location" in errors
        assert any("LatitudeDegrees" in e for e in errors["Location"])

    def test_missing_longitude_detected(self):
        d = self._valid_record()
        del d["CommercialAsset"]["Location"]["LongitudeDegrees"]
        errors = validate(d)
        assert "Location" in errors
        assert any("LongitudeDegrees" in e for e in errors["Location"])

    def test_exception_returns_validation_error(self):
        result = validate(None)
        assert "validation_error" in result
        assert isinstance(result["validation_error"], list)


class TestGetRequiredFields:

    def test_returns_five_paths(self):
        fields = get_required_fields()
        assert len(fields) == 5

    def test_includes_expected_paths(self):
        fields = get_required_fields()
        assert "CommercialAsset.Header.PropertyID" in fields
        assert "CommercialAsset.Header.CatchmentID" in fields
        assert "CommercialAsset.CommercialAttributes.CommercialType" in fields
        assert "CommercialAsset.Location.LatitudeDegrees" in fields
        assert "CommercialAsset.Location.LongitudeDegrees" in fields


# ---------------------------------------------------------------------------
# CommercialAssetCDM class
# ---------------------------------------------------------------------------


class TestCommercialAssetCDM:

    @pytest.fixture
    def cdm(self):
        return CommercialAssetCDM()

    def test_instantiates(self, cdm):
        assert cdm is not None

    def test_schema_top_keys(self, cdm):
        assert set(cdm.schema) == {
            "CommercialAsset", "ProtectionMeasures", "EnergyPerformance",
            "HistoryAndIncidents", "TransactionHistory",
        }

    def test_default_elevation_class_attr(self, cdm):
        assert cdm.DEFAULT_ELEVATION > 0

    def test_validate_delegates(self, cdm):
        d = {"CommercialAsset": {
            "Header": {"PropertyID": "CPROP-1", "CatchmentID": "thames"},
            "CommercialAttributes": {"CommercialType": "Office"},
            "Location": {"LatitudeDegrees": 51.5, "LongitudeDegrees": -0.1},
        }}
        assert cdm.validate(d) == {}

    def test_create_mapping_returns_dict(self, cdm):
        d = {"CommercialAsset": {
            "Header": {"PropertyID": "CPROP-1", "CatchmentID": "thames"},
            "CommercialAttributes": {"CommercialType": "Office",
                                     "PropertyAreaSqm": 5000,
                                     "NetInternalAreaSqm": 4400,
                                     "UseClassUKO": "E(g)(i)"},
            "Location": {"LatitudeDegrees": 51.5, "LongitudeDegrees": -0.1},
        }}
        out = cdm.create_mapping(d)
        assert isinstance(out, dict)
        assert out["property_id"] == "CPROP-1"
        assert out["commercial_type"] == "Office"
        assert out["latitude"] == 51.5
        assert out["longitude"] == -0.1
        assert out["property_area_sqm"] == 5000

    def test_create_mapping_skips_nones(self, cdm):
        # Empty record produces an empty flat mapping (no None values leak).
        assert cdm.create_mapping({"CommercialAsset": {}}) == {}

    def test_required_fields_from_class(self, cdm):
        assert cdm.get_required_fields() == get_required_fields()

    def test_repr_contains_class_name(self, cdm):
        assert "CommercialAssetCDM" in repr(cdm)
