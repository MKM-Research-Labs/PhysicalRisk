# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Tests for models.winddamage.cdm — property record navigation."""

from models.winddamage.cdm import (
    extract_bri_scores,
    extract_lon_lat,
    extract_property_id,
    extract_wind_threshold_kph,
    extract_wind_threshold_mps,
)


def _record(**overrides):
    """A property record shaped like data/input/<catch>/property.json entries."""
    base = {
        "PropertyHeader": {
            "Header": {"PropertyID": "PROP-test-001"},
        },
        "ProtectionMeasures": {
            "HazardProfile": {"WindThresholdKph": 120.0},
            "RiskAssessment": {
                "GoverningBodyRatings": {
                    "BRIWindScore": 0.6214,
                    "BRIScore": 0.6176,
                },
            },
        },
    }
    base.update(overrides)
    return base


class TestExtractPropertyId:

    def test_property_header_path(self):
        assert extract_property_id(_record()) == "PROP-test-001"

    def test_missing_returns_none(self):
        # Strip PropertyHeader entirely.
        rec = _record()
        rec.pop("PropertyHeader")
        assert extract_property_id(rec) is None

    def test_empty_dict_returns_none(self):
        assert extract_property_id({}) is None

    def test_fallback_to_top_level_header(self):
        # Commercial records sometimes carry Header directly at the top.
        rec = {"Header": {"PropertyID": "CPROP-abc"}}
        assert extract_property_id(rec) == "CPROP-abc"


class TestExtractWindThresholdKph:

    def test_present_returns_float(self):
        assert extract_wind_threshold_kph(_record()) == 120.0

    def test_missing_returns_none(self):
        rec = _record()
        rec["ProtectionMeasures"]["HazardProfile"].pop("WindThresholdKph")
        assert extract_wind_threshold_kph(rec) is None

    def test_int_value_cast_to_float(self):
        rec = _record()
        rec["ProtectionMeasures"]["HazardProfile"]["WindThresholdKph"] = 100
        assert extract_wind_threshold_kph(rec) == 100.0
        assert isinstance(extract_wind_threshold_kph(rec), float)

    def test_garbage_value_returns_none(self):
        rec = _record()
        rec["ProtectionMeasures"]["HazardProfile"]["WindThresholdKph"] = "not-a-number"
        assert extract_wind_threshold_kph(rec) is None

    def test_missing_protection_measures_returns_none(self):
        assert extract_wind_threshold_kph({}) is None


class TestExtractBriScores:

    def test_both_present(self):
        wind, comp = extract_bri_scores(_record())
        assert wind == 0.6214
        assert comp == 0.6176

    def test_only_wind_present(self):
        rec = _record()
        rec["ProtectionMeasures"]["RiskAssessment"]["GoverningBodyRatings"].pop("BRIScore")
        wind, comp = extract_bri_scores(rec)
        assert wind == 0.6214
        assert comp is None

    def test_only_composite_present(self):
        rec = _record()
        rec["ProtectionMeasures"]["RiskAssessment"]["GoverningBodyRatings"].pop("BRIWindScore")
        wind, comp = extract_bri_scores(rec)
        assert wind is None
        assert comp == 0.6176

    def test_missing_ratings_block_returns_none_none(self):
        rec = _record()
        rec["ProtectionMeasures"]["RiskAssessment"].pop("GoverningBodyRatings")
        wind, comp = extract_bri_scores(rec)
        assert (wind, comp) == (None, None)

    def test_garbage_score_value_becomes_none(self):
        rec = _record()
        rec["ProtectionMeasures"]["RiskAssessment"]["GoverningBodyRatings"]["BRIWindScore"] = "n/a"
        wind, comp = extract_bri_scores(rec)
        assert wind is None
        assert comp == 0.6176

    def test_empty_dict_returns_none_none(self):
        assert extract_bri_scores({}) == (None, None)


class TestExtractWindThresholdMps:

    def test_preferred_mps_field(self):
        rec = _record()
        rec["ProtectionMeasures"]["HazardProfile"]["WindThresholdMajorMps"] = 33.0
        assert extract_wind_threshold_mps(rec) == 33.0

    def test_mps_garbage_falls_through_to_kph(self):
        # mps present but non-numeric → except → fall to kph/3.6.
        rec = _record()
        rec["ProtectionMeasures"]["HazardProfile"]["WindThresholdMajorMps"] = "x"
        rec["ProtectionMeasures"]["HazardProfile"]["WindThresholdKph"] = 36.0
        assert extract_wind_threshold_mps(rec) == 10.0

    def test_legacy_kph_converted(self):
        rec = _record()  # only WindThresholdKph=120.0
        assert extract_wind_threshold_mps(rec) == 120.0 / 3.6

    def test_kph_garbage_returns_none(self):
        rec = _record()
        rec["ProtectionMeasures"]["HazardProfile"]["WindThresholdKph"] = "bad"
        assert extract_wind_threshold_mps(rec) is None

    def test_no_fields_returns_none(self):
        assert extract_wind_threshold_mps({}) is None


class TestExtractWindThresholdKphFallback:

    def test_falls_back_to_mps_times_3_6(self):
        rec = _record()
        rec["ProtectionMeasures"]["HazardProfile"].pop("WindThresholdKph")
        rec["ProtectionMeasures"]["HazardProfile"]["WindThresholdMajorMps"] = 10.0
        assert extract_wind_threshold_kph(rec) == 36.0

    def test_mps_fallback_garbage_returns_none(self):
        rec = _record()
        rec["ProtectionMeasures"]["HazardProfile"].pop("WindThresholdKph")
        rec["ProtectionMeasures"]["HazardProfile"]["WindThresholdMajorMps"] = "no"
        assert extract_wind_threshold_kph(rec) is None


class TestGetNestedNonDictSegment:

    def test_non_dict_intermediate_returns_none(self):
        # PropertyHeader is a string, not a dict → _get_nested line 52.
        assert extract_property_id({"PropertyHeader": "oops"}) is None


class TestExtractLonLat:

    def test_returns_lon_lat(self):
        rec = {"PropertyHeader": {"Location": {
            "LongitudeDegrees": -0.1, "LatitudeDegrees": 51.5}}}
        assert extract_lon_lat(rec) == (-0.1, 51.5)

    def test_missing_location_returns_none_none(self):
        assert extract_lon_lat({}) == (None, None)

    def test_location_not_dict_returns_none_none(self):
        assert extract_lon_lat({"PropertyHeader": {"Location": "x"}}) == (None, None)

    def test_garbage_coords_become_none(self):
        rec = {"PropertyHeader": {"Location": {
            "LongitudeDegrees": "bad", "LatitudeDegrees": None}}}
        assert extract_lon_lat(rec) == (None, None)
