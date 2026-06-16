# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Contract tests for the halong commercial BRI prototype catalogue.

Pins the wiring between port.rand.halong.commercial.bri_codes and the
halong commercial generators:

- Hotels get WD06 (wind) and FI09 (fire) — the hotel-only differentiators
- Tsunami codes are hotel-only
- Non-hotels carry the flash-flood code set and no tsunami codes
- Thresholds are populated from the SE-Asia prototype constants
- Thames commercial leaves every new field null / empty
"""

import pytest

from port.rand.halong.commercial import bri_codes
from port.rand.halong.commercial.commercial_random import (
    generate_commercial_metadata as halong_metadata,
    generate_field_value as halong_field,
)
from port.rand.thames.commercial.commercial_random import (
    generate_commercial_metadata as thames_metadata,
    generate_field_value as thames_field,
)


@pytest.fixture
def _halong(monkeypatch):
    """Activate the halong catchment so the shared commercial generators read
    the halong profile (BRI enabled). The ``port.rand.halong`` import path is a
    thin alias of the shared engine, which follows the *active* catchment."""
    from config import config
    monkeypatch.setattr(config, "_catchment_id", "halong")


_LOCATION = {
    "name": "Tuan Chau",
    "elevation": 6.0,
    "vertical_offset": 0.5,
    "value_factor": 1.0,
    "streets_data": {},
}


def _gen_halong(index: int) -> tuple[dict, callable]:
    md = halong_metadata(index, _LOCATION)
    return md, (lambda f: halong_field(f, {}, index, md))


@pytest.mark.usefixtures("_halong")
class TestHalongHotel:
    """Hotel (index 6) maps to the Bldg-3 prototype: Grade A everywhere."""

    def test_wind_codes_include_hotel_extra(self):
        md, get = _gen_halong(6)
        assert md["commercial_type"] == "Hotel"
        assert "WD06" in get("WindCodes"), "Hotel must carry the WD06 differentiator"

    def test_fire_codes_include_hotel_extra(self):
        _, get = _gen_halong(6)
        assert "FI09" in get("FireCodes"), "Hotel must carry the FI09 differentiator"

    def test_tsunami_codes_present(self):
        _, get = _gen_halong(6)
        codes = get("WaterCodes")
        assert codes, "Hotel must carry tsunami codes"
        assert set(codes) >= {"WT08", "WT13", "WT18", "WT19", "WT20", "WT09"}

    def test_water_threshold_populated(self):
        _, get = _gen_halong(6)
        assert get("WaterThresholdMajorM") == bri_codes.WATER_MAJOR_M
        assert get("WaterThresholdMinorM") == bri_codes.WATER_MINOR_M

    def test_grade_a_ratings(self):
        _, get = _gen_halong(6)
        assert get("BRIWaterRating") == "A"
        assert get("BRIFlashRating") == "A"


@pytest.mark.usefixtures("_halong")
class TestHalongMultiFamily:
    """MultiFamily (index 3) maps to the Bldg-2 apartment prototype."""

    def test_no_hotel_wind_extra(self):
        md, get = _gen_halong(3)
        assert md["commercial_type"] == "MultiFamily"
        assert "WD06" not in get("WindCodes"), "Non-hotel must not carry WD06"

    def test_no_tsunami_codes(self):
        _, get = _gen_halong(3)
        assert get("WaterCodes") == [], "Non-hotel must not carry tsunami codes"

    def test_water_threshold_blank(self):
        _, get = _gen_halong(3)
        assert get("WaterThresholdMajorM") is None
        assert get("WaterThresholdMinorM") is None
        assert get("BRIWaterRating") == "N/A"

    def test_flash_grade_a(self):
        _, get = _gen_halong(3)
        # Apartment prototype has the full FF/SS A-set ticked.
        assert get("BRIFlashRating") == "A"
        assert set(get("FlashCodes")) >= set(bri_codes.FLASH_A_CODES)


@pytest.mark.usefixtures("_halong")
class TestHalongOffice:
    """Office (index 0) falls back to the Bldg-1 mixed-use prototype."""

    def test_flash_grade_b(self):
        md, get = _gen_halong(0)
        assert md["commercial_type"] == "Office"
        assert get("BRIFlashRating") == "B"

    def test_flash_codes_partial(self):
        _, get = _gen_halong(0)
        codes = set(get("FlashCodes"))
        # Mixed-use prototype only ticks WT16 from the A set.
        assert codes == {"WT16", "WD03"}


@pytest.mark.usefixtures("_halong")
class TestHalongThresholdConstants:

    def test_wind_thresholds_in_mps(self):
        _, get = _gen_halong(0)
        # 250 km/h -> 69.44 m/s, 200 km/h -> 55.56 m/s (rounded to 2dp).
        assert get("WindThresholdMajorMps") == 69.44
        assert get("WindThresholdMinorMps") == 55.56

    def test_flash_thresholds_in_metres(self):
        _, get = _gen_halong(0)
        assert get("FlashThresholdMajorM") == 5.0
        assert get("FlashThresholdMinorM") == 3.0


class TestThamesEmpty:
    """Thames commercial must leave every new field null / empty."""

    def test_thresholds_null(self):
        md = thames_metadata(6, _LOCATION)
        get = lambda f: thames_field(f, {}, 6, md)
        for field in (
            "WindThresholdMajorMps", "WindThresholdMinorMps",
            "WaterThresholdMajorM", "WaterThresholdMinorM",
            "FlashThresholdMajorM", "FlashThresholdMinorM",
        ):
            assert get(field) is None, f"Thames must leave {field} null"

    def test_ratings_null(self):
        md = thames_metadata(6, _LOCATION)
        get = lambda f: thames_field(f, {}, 6, md)
        assert get("BRIWaterRating") is None
        assert get("BRIFlashRating") is None

    def test_industry_groups_empty(self):
        md = thames_metadata(6, _LOCATION)
        get = lambda f: thames_field(f, {}, 6, md)
        for field in ("WindCodes", "WaterCodes", "FlashCodes",
                      "FireCodes", "SeismicCodes"):
            assert get(field) == [], f"Thames must leave {field} as []"
