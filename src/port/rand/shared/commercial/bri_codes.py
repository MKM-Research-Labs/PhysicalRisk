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

"""SE-Asia commercial BRI resilience catalogue.

Encodes the three prototype buildings from
``data/catch/halong/BRI-PRS Building Prototypes.xlsx`` so that randomly
generated halong commercial assets are recognisable against the source
spreadsheet. Each prototype carries:

- per-hazard letter grade (A or B)
- the literal BRI measure codes installed
- the operational thresholds the grade is designed to withstand

The catalogue is regional. Free-string codes; the CDM does not enforce
a registry today.
"""

from typing import Dict, List, Optional


# -- Thresholds (constants per the SE-Asia commercial prototype set) -------

# Wind (cyclone) — Grade A = 250 km/h, Grade B = 200 km/h. Stored in m/s.
WIND_MAJOR_KPH: float = 250.0
WIND_MINOR_KPH: float = 200.0
WIND_MAJOR_MPS: float = round(WIND_MAJOR_KPH / 3.6, 2)   # 69.44
WIND_MINOR_MPS: float = round(WIND_MINOR_KPH / 3.6, 2)   # 55.56

# Water (tsunami / storm-surge) — m above the gauge SevereFloodWarning level.
WATER_MAJOR_M: float = 10.0
WATER_MINOR_M: float = 5.0

# Flash flood / fluvial — m above the gauge SevereFloodWarning level.
FLASH_MAJOR_M: float = 5.0
FLASH_MINOR_M: float = 3.0


# -- Measure code lists (per the spreadsheet ticks) ------------------------

# Wind. WD06 is the hotel-only differentiator that elevates wind to Grade A.
WIND_A_CODES: List[str] = ["WD02", "WD04", "WD05", "WD08"]
WIND_B_CODES: List[str] = ["WD03"]
HOTEL_WIND_EXTRA: List[str] = ["WD06"]

# Water (tsunami / storm-surge). Only the hotel prototype carries any of
# these in the source spreadsheet.
WATER_TSUNAMI_A_CODES: List[str] = ["WT08", "WT13", "WT18", "WT19", "WT20"]
WATER_TSUNAMI_B_CODES: List[str] = ["WT09"]

# Flash flood / fluvial. WD03 sits in both wind-B and flash-B per the source.
FLASH_A_CODES: List[str] = ["WT05", "WT10", "WT13", "WT15", "WT16"]
FLASH_B_CODES: List[str] = ["WD03"]

# Fire. FI09 is the hotel-only differentiator that elevates fire to Grade A.
FIRE_A_CODES: List[str] = ["FI04", "FI12", "FI14", "FI16", "FI17", "FI21"]
FIRE_B_CODES: List[str] = ["FI05", "FI18", "FI20"]
HOTEL_FIRE_EXTRA: List[str] = ["FI09"]

# Seismic. All three prototypes carry both sets — every asset gets Grade A.
SEISMIC_A_CODES: List[str] = ["GS02", "GS08", "GS11", "GS15", "GS16"]
SEISMIC_B_CODES: List[str] = ["GS01", "GS09", "GS10", "GS14"]


# -- Prototype records (the three buildings from the spreadsheet) ---------

_PROTOTYPE_MIXED_USE: Dict[str, object] = {
    "name": "Mixed-use (Bldg 1)",
    "wind_grade": "B",
    "water_grade": "N/A",            # No tsunami / storm-surge exposure
    "flash_grade": "B",              # Only WT16 from A-set ticked + WD03
    "fire_grade": "B",
    "seismic_grade": "A",
    "overall_grade": "B",
    "wind_codes":    WIND_A_CODES + WIND_B_CODES,
    "water_codes":   [],
    "flash_codes":   ["WT16"] + FLASH_B_CODES,
    "fire_codes":    FIRE_A_CODES + FIRE_B_CODES,
    "seismic_codes": SEISMIC_A_CODES + SEISMIC_B_CODES,
}

_PROTOTYPE_APARTMENT: Dict[str, object] = {
    "name": "Apartment (Bldg 2)",
    "wind_grade": "B",
    "water_grade": "N/A",            # No tsunami exposure
    "flash_grade": "A",              # Full A-set ticked for FF/SS
    "fire_grade": "B",
    "seismic_grade": "A",
    "overall_grade": "B",
    "wind_codes":    WIND_A_CODES + WIND_B_CODES,
    "water_codes":   [],
    "flash_codes":   FLASH_A_CODES + FLASH_B_CODES,
    "fire_codes":    FIRE_A_CODES + FIRE_B_CODES,
    "seismic_codes": SEISMIC_A_CODES + SEISMIC_B_CODES,
}

_PROTOTYPE_HOTEL: Dict[str, object] = {
    "name": "Hotel (Bldg 3)",
    "wind_grade": "A",
    "water_grade": "A",              # Tsunami exposure, full A + B set
    "flash_grade": "A",
    "fire_grade": "A",
    "seismic_grade": "A",
    "overall_grade": "A",
    "wind_codes":    WIND_A_CODES + WIND_B_CODES + HOTEL_WIND_EXTRA,
    "water_codes":   WATER_TSUNAMI_A_CODES + WATER_TSUNAMI_B_CODES,
    "flash_codes":   FLASH_A_CODES + FLASH_B_CODES,
    "fire_codes":    FIRE_A_CODES + FIRE_B_CODES + HOTEL_FIRE_EXTRA,
    "seismic_codes": SEISMIC_A_CODES + SEISMIC_B_CODES,
}


# Map every CommercialType to one of the three source prototypes. Office /
# Retail / MixedUse aren't explicit prototypes but read most naturally as
# the mixed-use baseline; MultiFamily reads as the apartment block.
_PROTOTYPE_BY_TYPE: Dict[str, Dict[str, object]] = {
    "Office":      _PROTOTYPE_MIXED_USE,
    "Retail":      _PROTOTYPE_MIXED_USE,
    "MixedUse":    _PROTOTYPE_MIXED_USE,
    "MultiFamily": _PROTOTYPE_APARTMENT,
    "Hotel":       _PROTOTYPE_HOTEL,
}


def for_commercial(commercial_type: str) -> Dict[str, object]:
    """Return the BRI resilience record for a commercial asset of the given type.

    The returned dict is a shallow copy of the prototype so callers can
    mutate freely (e.g. attach the per-asset BRI scores once they exist).
    """
    proto = _PROTOTYPE_BY_TYPE.get(commercial_type, _PROTOTYPE_MIXED_USE)
    return {
        "name":          proto["name"],
        "wind_grade":    proto["wind_grade"],
        "water_grade":   proto["water_grade"],
        "flash_grade":   proto["flash_grade"],
        "fire_grade":    proto["fire_grade"],
        "seismic_grade": proto["seismic_grade"],
        "overall_grade": proto["overall_grade"],
        "wind_codes":    list(proto["wind_codes"]),
        "water_codes":   list(proto["water_codes"]),
        "flash_codes":   list(proto["flash_codes"]),
        "fire_codes":    list(proto["fire_codes"]),
        "seismic_codes": list(proto["seismic_codes"]),
        # Operational thresholds are uniform across the prototype set;
        # the grade decides which one matters for the damage model.
        "wind_threshold_major_mps":  WIND_MAJOR_MPS,
        "wind_threshold_minor_mps":  WIND_MINOR_MPS,
        "water_threshold_major_m":   WATER_MAJOR_M,
        "water_threshold_minor_m":   WATER_MINOR_M,
        "flash_threshold_major_m":   FLASH_MAJOR_M,
        "flash_threshold_minor_m":   FLASH_MINOR_M,
    }


def water_threshold_for_grade(grade: Optional[str]) -> Optional[Dict[str, float]]:
    """Return the major/minor threshold pair when water exposure applies.

    Returns None for ``None`` / ``"N/A"`` (no tsunami / storm-surge exposure)
    so callers can leave the CDM water threshold fields blank for those
    assets.
    """
    if grade in (None, "N/A"):
        return None
    return {"major_m": WATER_MAJOR_M, "minor_m": WATER_MINOR_M}
