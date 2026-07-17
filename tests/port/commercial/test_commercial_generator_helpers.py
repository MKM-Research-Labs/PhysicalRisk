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

"""Branch coverage for the lightweight helper methods of
CommercialPortfolioGenerator. Uses ``__new__`` to bypass the heavy
CDM/random-module loading in ``__init__`` — these helpers only depend on
the class-level _RATING_ORDER and their dict arguments.
"""

import pytest

from port.src.commercial.main.generator import CommercialPortfolioGenerator as G


@pytest.fixture
def gen():
    # Bypass __init__ (no CDM / random module load needed for helpers).
    return G.__new__(G)


# ---------------------------------------------------------------------------
# _flood_rating_envelope
# ---------------------------------------------------------------------------

def test_envelope_uses_existing_rating(gen):
    assert gen._flood_rating_envelope({"BRIFloodRating": "A"}) == "A"


def test_envelope_no_grades_returns_none(gen):
    assert gen._flood_rating_envelope({}) is None
    assert gen._flood_rating_envelope(
        {"BRIWaterRating": "N/A", "BRIFlashRating": None}) is None


def test_envelope_picks_weakest_grade(gen):
    # _RATING_ORDER = ("AA", "A", "B", "NR"); max by index = weakest
    assert gen._flood_rating_envelope(
        {"BRIWaterRating": "AA", "BRIFlashRating": "B"}) == "B"


def test_envelope_ignores_invalid_existing(gen):
    # Existing rating not in order → fall through to grade pair
    assert gen._flood_rating_envelope(
        {"BRIFloodRating": "ZZ", "BRIWaterRating": "A"}) == "A"


# ---------------------------------------------------------------------------
# _stamp_bri_adjusted_floor
# ---------------------------------------------------------------------------

def test_stamp_floor_noop_when_floor_missing(gen):
    asset = {"CommercialAsset": {"Construction": {}}}
    gen._stamp_bri_adjusted_floor(asset)
    assert "BRIAdjustedFloorLevelMeters" not in asset["CommercialAsset"]["Construction"]


def test_stamp_floor_noop_when_no_flood_grade(gen):
    asset = {"CommercialAsset": {"Construction": {"FloorLevelMeters": 0.3}}}
    gen._stamp_bri_adjusted_floor(asset)
    assert "BRIAdjustedFloorLevelMeters" not in asset["CommercialAsset"]["Construction"]


def test_stamp_floor_success(gen):
    asset = {
        "CommercialAsset": {"Construction": {"FloorLevelMeters": 0.3}},
        "ProtectionMeasures": {"RiskAssessment": {"GoverningBodyRatings": {
            "BRIWaterRating": "AA"}}},
    }
    gen._stamp_bri_adjusted_floor(asset)
    adj = asset["CommercialAsset"]["Construction"].get("BRIAdjustedFloorLevelMeters")
    assert adj is not None
    assert adj >= 0.3  # floor raised by the resilience credit


def test_stamp_floor_handles_bad_floor_type(gen):
    asset = {
        "CommercialAsset": {"Construction": {"FloorLevelMeters": "not-a-number"}},
        "ProtectionMeasures": {"RiskAssessment": {"GoverningBodyRatings": {
            "BRIWaterRating": "AA"}}},
    }
    gen._stamp_bri_adjusted_floor(asset)  # should not raise
    assert "BRIAdjustedFloorLevelMeters" not in asset["CommercialAsset"]["Construction"]


# ---------------------------------------------------------------------------
# _set_specific_values
# ---------------------------------------------------------------------------

def test_set_specific_values_stamps_identifiers(gen):
    asset = {}
    metadata = {"property_id": "CPROP-0001", "commercial_type": "Office",
                "property_area": 500, "construction_year": 2005,
                "property_value": 2_000_000}
    location = {"lat": 1.0, "lon": 2.0, "postcode": "AB1 2CD",
                "name": "Town", "elevation": 12.0}
    gen._set_specific_values(asset, metadata, location)
    ca = asset["CommercialAsset"]
    assert ca["Header"]["PropertyID"] == "CPROP-0001"
    assert ca["Header"]["propertyType"] == "commercial"
    assert ca["Location"]["Postcode"] == "AB1 2CD"
    assert ca["Location"]["TownCity"] == "Town"
    assert ca["Valuation"]["PropertyValue"] == 2_000_000
    assert ca["RiskAssessment"]["GroundLevelMeters"] == 12.0


# ---------------------------------------------------------------------------
# _type_mix_summary
# ---------------------------------------------------------------------------

def test_type_mix_summary(gen):
    records = [
        {"CommercialAsset": {"CommercialAttributes": {"CommercialType": "Office"}}},
        {"CommercialAsset": {"CommercialAttributes": {"CommercialType": "Office"}}},
        {"CommercialAsset": {"CommercialAttributes": {"CommercialType": "Retail"}}},
        {"CommercialAsset": {}},  # → Unknown
    ]
    out = gen._type_mix_summary(records)
    assert out["Office"] == 2
    assert out["Retail"] == 1
    assert out["Unknown"] == 1
