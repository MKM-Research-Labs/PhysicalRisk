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

"""Tests for models.winddamage.cdm — property record navigation."""

import pytest

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

    def test_commercial_asset_header_path(self):
        # Commercial records nest the id under CommercialAsset/Header.
        rec = {"CommercialAsset": {"Header": {"PropertyID": "CPROP-08ac3589"}}}
        assert extract_property_id(rec) == "CPROP-08ac3589"

    def test_property_header_preferred_over_commercial_asset(self):
        # When both shapes are present, the residential PropertyHeader wins.
        rec = _record()
        rec["CommercialAsset"] = {"Header": {"PropertyID": "CPROP-should-not-win"}}
        assert extract_property_id(rec) == "PROP-test-001"


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

    def test_minor_preferred_over_major(self):
        # Damage-onset: when both Minor and Major are published, Minor wins.
        rec = _record()
        hp = rec["ProtectionMeasures"]["HazardProfile"]
        hp["WindThresholdMinorMps"] = 55.56
        hp["WindThresholdMajorMps"] = 69.44
        assert extract_wind_threshold_mps(rec) == 55.56

    def test_minor_garbage_falls_through_to_major(self):
        rec = _record()
        hp = rec["ProtectionMeasures"]["HazardProfile"]
        hp["WindThresholdMinorMps"] = "x"
        hp["WindThresholdMajorMps"] = 69.44
        assert extract_wind_threshold_mps(rec) == 69.44

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

    def test_commercial_asset_location_fallback(self):
        # Commercial records carry coords under CommercialAsset.Location.
        rec = {"CommercialAsset": {"Location": {
            "LongitudeDegrees": 105.837, "LatitudeDegrees": 21.067}}}
        assert extract_lon_lat(rec) == (105.837, 21.067)

    def test_property_header_location_preferred_over_commercial(self):
        rec = {
            "PropertyHeader": {"Location": {
                "LongitudeDegrees": -0.1, "LatitudeDegrees": 51.5}},
            "CommercialAsset": {"Location": {
                "LongitudeDegrees": 999.0, "LatitudeDegrees": 999.0}},
        }
        assert extract_lon_lat(rec) == (-0.1, 51.5)

    def test_missing_location_returns_none_none(self):
        assert extract_lon_lat({}) == (None, None)

    def test_location_not_dict_returns_none_none(self):
        assert extract_lon_lat({"PropertyHeader": {"Location": "x"}}) == (None, None)

    def test_garbage_coords_become_none(self):
        rec = {"PropertyHeader": {"Location": {
            "LongitudeDegrees": "bad", "LatitudeDegrees": None}}}
        assert extract_lon_lat(rec) == (None, None)


class TestDesignSpeedPrecedence:
    """DesignWindSpeedKmh drives the damage-onset threshold.

    The BRI WindThreshold* fields are uniform across the prototype catalogue,
    so keying off them gave every asset in a portfolio an identical trigger:
    on halong all ten commercial assets fired on the same five events out of a
    thousand. The design speed is the only per-asset quantity available.
    """

    @staticmethod
    def _record(**hazard):
        return {"ProtectionMeasures": {"HazardProfile": dict(hazard)}}

    def test_design_speed_wins_over_the_published_threshold(self):
        from models.winddamage.cdm import extract_wind_threshold_mps
        rec = self._record(DesignWindSpeedKmh=120.0, WindThresholdMinorMps=41.67)
        assert extract_wind_threshold_mps(rec) == pytest.approx(120 / 3.6)

    def test_two_assets_with_different_design_speeds_differ(self):
        """The whole point: a portfolio must not share one trigger."""
        from models.winddamage.cdm import extract_wind_threshold_mps
        weak = extract_wind_threshold_mps(self._record(DesignWindSpeedKmh=77.0))
        strong = extract_wind_threshold_mps(self._record(DesignWindSpeedKmh=140.0))
        assert weak < strong

    def test_falls_back_to_the_published_threshold_without_a_design_speed(self):
        from models.winddamage.cdm import extract_wind_threshold_mps
        rec = self._record(WindThresholdMinorMps=41.67)
        assert extract_wind_threshold_mps(rec) == pytest.approx(41.67)

    def test_an_unusable_design_speed_falls_through(self):
        from models.winddamage.cdm import extract_wind_threshold_mps
        for bad in ("not-a-number", 0, -5):
            rec = self._record(DesignWindSpeedKmh=bad, WindThresholdMinorMps=41.67)
            assert extract_wind_threshold_mps(rec) == pytest.approx(41.67), bad

    def test_the_minor_threshold_comes_from_config(self):
        """R1: the km/h levels are parameters and live in the config package."""
        from config.damage import COMMERCIAL_WIND_MINOR_KPH
        from port.rand.shared.commercial.bri_codes import WIND_MINOR_MPS
        assert WIND_MINOR_MPS == pytest.approx(COMMERCIAL_WIND_MINOR_KPH / 3.6, abs=0.01)
