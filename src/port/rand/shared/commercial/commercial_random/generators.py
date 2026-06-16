# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Field-value generators for commercial assets.

Catchment-agnostic. The commercial-only lambdas (keyed by CDM field name)
read every per-catchment value from the active profile
(``port.rand.profiles.active_profile()``); anything not in the commercial
table delegates to ``property_random.generate_field_value`` so shared fields
(Location, RiskAssessment, Resilience, EnergyPerformance) use the same logic
across asset classes.

BRI commercial coding (the HazardProfile thresholds, BRI ratings and measure
codes) is gated on ``COMMERCIAL_BRI_ENABLED``. Catchments without a BRI regime
leave those fields blank (``None`` ratings/thresholds, empty code lists).
"""

import random
from typing import Any, Callable, Dict, Optional

from port.rand.profiles import active_profile
from port.rand.shared.commercial import bri_codes as _bri_codes
from port.rand.shared.property.property_random import generators as _resi_random

from .metadata import anchor_tenant, period_from_year  # noqa: F401


# A neutral prototype used when the active profile disables commercial BRI
# coding: every hazard threshold and code list reads empty.
_BLANK_PROTOTYPE: Dict[str, Any] = {
    "name": None,
    "wind_grade": None, "water_grade": None, "flash_grade": None,
    "fire_grade": None, "seismic_grade": None, "overall_grade": None,
    "wind_codes": [], "water_codes": [], "flash_codes": [],
    "fire_codes": [], "seismic_codes": [],
    "wind_threshold_major_mps": None, "wind_threshold_minor_mps": None,
    "water_threshold_major_m": None, "water_threshold_minor_m": None,
    "flash_threshold_major_m": None, "flash_threshold_minor_m": None,
}


def _bri(info: Dict[str, Any]) -> Dict[str, Any]:
    """Return the asset's BRI prototype record.

    When the active profile disables commercial BRI coding a blank prototype
    is returned (so thresholds/codes read empty). Otherwise the prototype
    carried on the metadata is used, or one is built from the commercial type.
    """
    if not active_profile().COMMERCIAL_BRI_ENABLED:
        return dict(_BLANK_PROTOTYPE)
    proto = info.get("bri_prototype")
    if proto is None:
        proto = _bri_codes.for_commercial(info.get("commercial_type") or "MixedUse")
    return proto


def _grade_to_rating(grade: Optional[str]) -> str:
    """Map an internal grade ('A'/'B'/'N/A'/None) to a CDM BRI letter rating."""
    if grade in (None, "N/A"):
        return "N/A"
    return grade


def _bri_rating(info: Dict[str, Any], grade_key: str) -> Optional[str]:
    """BRI letter rating for a hazard, or ``None`` when BRI coding is off.

    Distinct from ``_grade_to_rating(None)`` (which is 'N/A'): a catchment with
    no BRI regime leaves the rating field null rather than stamping 'N/A'.
    """
    if not active_profile().COMMERCIAL_BRI_ENABLED:
        return None
    return _grade_to_rating(_bri(info)[grade_key])


def _occupancy_status(info: Dict[str, Any]) -> str:
    weights = {
        "Office": [0.62, 0.28, 0.10],
        "MultiFamily": [0.82, 0.15, 0.03],
        "Hotel": [0.72, 0.22, 0.06],
        "Retail": [0.68, 0.24, 0.08],
        "MixedUse": [0.70, 0.24, 0.06],
    }.get(info["commercial_type"], [0.70, 0.25, 0.05])

    return random.choices(
        ["Fully occupied", "Partially vacant", "Vacant"],
        weights=weights,
        k=1,
    )[0]


def _plant_room_location(info: Dict[str, Any]) -> str:
    options = {
        "Office": ["Roof", "Ground floor", "Basement", "External"],
        "MultiFamily": ["Roof", "Ground floor", "External"],
        "Hotel": ["Roof", "Ground floor", "Basement", "External"],
        "Retail": ["Ground floor", "Roof", "External"],
        "MixedUse": ["Roof", "Ground floor", "External", "Basement"],
    }
    return random.choice(options.get(info["commercial_type"], ["Ground floor"]))


def _service_core(info: Dict[str, Any]) -> str:
    ctype = info["commercial_type"]
    if ctype == "Retail":
        return random.choice(["None", "Central core", "External core"])
    if ctype == "MixedUse":
        return random.choice(["Central core", "Multiple cores"])
    return random.choice(["Central core", "Multiple cores", "External core"])


def _goods_lift_count(info: Dict[str, Any]) -> int:
    ctype = info["commercial_type"]
    if ctype == "Retail":
        return random.randint(0, 2)
    if ctype == "Hotel":
        return random.randint(1, 3)
    if ctype == "MixedUse":
        return random.randint(1, 3)
    return random.randint(0, 2)


def _covenant_strength(info: Dict[str, Any]) -> str:
    """Aggregate tenant covenant strength.

    Drawn from the CDM ``CovenantStrength`` menu (credit-rating buckets) so the
    value is always schema-valid regardless of catchment.
    """
    return random.choices(
        ["AAA", "AA", "A", "BBB", "BB", "B", "Unrated"],
        weights=[0.05, 0.10, 0.30, 0.30, 0.15, 0.05, 0.05],
        k=1,
    )[0]


def _commercial_generators() -> Dict[str, Callable]:
    """Map of CDM field name -> lambda(info). ``info`` is the location_info
    dict built inside ``generate_field_value`` (it includes
    ``commercial_type``). Per-type tables are resolved once from the active
    profile so the closures pick up the right catchment's values."""
    profile = active_profile()
    use_class = profile.COMMERCIAL_TYPE_USE_CLASS
    business_rates = profile.COMMERCIAL_TYPE_BUSINESS_RATES
    storeys = profile.COMMERCIAL_TYPE_STOREYS
    total_units = profile.COMMERCIAL_TYPE_TOTAL_UNITS
    parking = profile.COMMERCIAL_TYPE_PARKING_SPACES
    loading = profile.COMMERCIAL_TYPE_LOADING_BAYS
    construction_types = profile.COMMERCIAL_CONSTRUCTION_TYPES

    return {
        "CommercialType": lambda info: info["commercial_type"],
        "UseClassUKO": lambda info: use_class[info["commercial_type"]],
        "BusinessRatesCategory": lambda info: business_rates[info["commercial_type"]],
        "OccupancyStatus": _occupancy_status,
        "PropertyAreaSqm": lambda info: info["property_area"],
        "NetInternalAreaSqm": lambda info: round(info["property_area"] * random.uniform(0.82, 0.92), 0),
        "NetLettableAreaSqm": lambda info: round(info["property_area"] * random.uniform(0.78, 0.90), 0),
        "PropertyValue": lambda info: info["property_value"],
        "NumberOfStoreys": lambda info: random.randint(*storeys[info["commercial_type"]]),
        "TotalUnits": lambda info: random.randint(*total_units[info["commercial_type"]]),
        "ParkingSpaces": lambda info: random.randint(*parking[info["commercial_type"]]),
        "LoadingBays": lambda info: random.randint(*loading[info["commercial_type"]]),
        "PlantRoomLocation": _plant_room_location,
        "ServiceCore": _service_core,
        "ConstructionType": lambda info: random.choice(construction_types),
        "ConstructionYear": lambda info: info["construction_year"],
        "PropertyPeriod": lambda info: period_from_year(info["construction_year"]),
        "PropertyCondition": lambda info: random.choices(
            ["Excellent", "Good", "Fair", "Poor", "Very poor"],
            weights=[0.12, 0.46, 0.28, 0.10, 0.04],
            k=1,
        )[0],

        # AccessibilityFeatures
        "DisabledAccess": lambda info: random.random() < 0.80,
        "GoodsLiftCount": _goods_lift_count,
        "GoodsLiftCapacityKg": lambda info: float(random.choice([1000, 1600, 2500, 3500])),
        "EmergencyExits": lambda info: max(2, int(info["property_area"] / 1800)),
        "DeliveryBays": lambda info: random.randint(*loading[info["commercial_type"]]),

        # Tenancy / Investment
        "AnchorTenant": lambda info: anchor_tenant(info["commercial_type"]),
        "WAULT": lambda info: round(random.uniform(1.5, 8.0), 1),
        "ServiceChargeGbpPerSqm": lambda info: 0.0,
        "NetInitialYield": lambda info: round(random.uniform(0.045, 0.090), 4),
        "EquivalentYield": lambda info: round(random.uniform(0.050, 0.095), 4),
        "ReversionaryYield": lambda info: round(random.uniform(0.055, 0.100), 4),
        "CovenantStrength": _covenant_strength,

        # HazardProfile thresholds (blank unless the profile enables BRI)
        "WindThresholdMajorMps": lambda info: _bri(info)["wind_threshold_major_mps"],
        "WindThresholdMinorMps": lambda info: _bri(info)["wind_threshold_minor_mps"],
        "FlashThresholdMajorM": lambda info: _bri(info)["flash_threshold_major_m"],
        "FlashThresholdMinorM": lambda info: _bri(info)["flash_threshold_minor_m"],
        "WaterThresholdMajorM": lambda info: (
            _bri(info)["water_threshold_major_m"]
            if _bri(info)["water_grade"] not in (None, "N/A") else None
        ),
        "WaterThresholdMinorM": lambda info: (
            _bri(info)["water_threshold_minor_m"]
            if _bri(info)["water_grade"] not in (None, "N/A") else None
        ),

        # BRI ratings (null when BRI coding is off; 'N/A' for an unexposed hazard)
        "BRIWaterRating": lambda info: _bri_rating(info, "water_grade"),
        "BRIFlashRating": lambda info: _bri_rating(info, "flash_grade"),
        "BRIWaterScore": lambda _: None,
        "BRIFlashScore": lambda _: None,

        # BRI measure codes (empty unless the profile enables BRI)
        "WindCodes": lambda info: list(_bri(info)["wind_codes"]),
        "WaterCodes": lambda info: list(_bri(info)["water_codes"]),
        "FlashCodes": lambda info: list(_bri(info)["flash_codes"]),
        "FireCodes": lambda info: list(_bri(info)["fire_codes"]),
        "SeismicCodes": lambda info: list(_bri(info)["seismic_codes"]),
    }


def generate_field_value(field_name: str, field_def: Dict, index: int,
                         metadata: Dict[str, Any]) -> Any:
    """Generate a value for a commercial schema field.

    Order of resolution:
      1. Commercial-only generators (this module)
      2. Residential generators (delegation to property_random)
      3. Type-based default (handled inside property_random)
    """
    info = {
        "commercial_type": metadata.get("commercial_type"),
        "property_type": metadata.get("commercial_type"),
        "property_area": metadata.get("property_area"),
        "property_value": metadata.get("property_value"),
        "construction_year": metadata.get("construction_year"),
        "elevation": metadata.get("elevation"),
        "vertical_offset": metadata.get("vertical_offset", 0.5),
        "area_name": metadata.get("area_name"),
        "value_factor": metadata.get("value_factor", 1.0),
        "streets_data": metadata.get("streets_data", {}),
        "bri_prototype": metadata.get("bri_prototype"),
    }

    commercial_gens = _commercial_generators()
    if field_name in commercial_gens:
        try:
            return commercial_gens[field_name](info)
        except Exception:
            pass

    # Delegate to residential generators for all shared fields.
    return _resi_random.generate_field_value(field_name, field_def, index, metadata)
