# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Field-value generators for commercial assets."""

import random
from typing import Any, Callable, Dict, Optional

from port.rand.halong.commercial import bri_codes as _bri_codes
from port.rand.halong.property import property_random as _resi_random

from .constants import (
    TYPE_BUSINESS_RATES,
    TYPE_LOADING_BAYS,
    TYPE_PARKING_SPACES,
    TYPE_STOREYS,
    TYPE_TOTAL_UNITS,
    TYPE_USE_CLASS,
)

from .metadata import anchor_tenant, period_from_year

def _bri(info: Dict[str, Any]) -> Dict[str, Any]:
    """Return the asset's BRI prototype record."""
    proto = info.get("bri_prototype")
    if proto is None:
        proto = _bri_codes.for_commercial(info.get("commercial_type") or "MixedUse")
    return proto

def _grade_to_rating(grade: Optional[str]) -> str:
    """Map an internal grade ('A'/'B'/'N/A') to a CDM BRI letter rating."""
    if grade in (None, "N/A"):
        return "N/A"
    return grade

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
    ctype = info["commercial_type"]
    if ctype in ("MultiFamily", "MixedUse"):
        return random.choice(["Unrated", "Local", "Regional", "Institutional"])
    if ctype == "Hotel":
        return random.choice(["Unrated", "Local", "Regional", "International"])
    return random.choice(["Unrated", "Local", "Regional", "Institutional", "Government"])

def _commercial_generators() -> Dict[str, Callable]:
    return {
        "CommercialType": lambda info: info["commercial_type"],
        "UseClassUKO": lambda info: TYPE_USE_CLASS[info["commercial_type"]],
        "BusinessRatesCategory": lambda info: TYPE_BUSINESS_RATES[info["commercial_type"]],
        "OccupancyStatus": _occupancy_status,
        "PropertyAreaSqm": lambda info: info["property_area"],
        "NetInternalAreaSqm": lambda info: round(info["property_area"] * random.uniform(0.82, 0.92), 0),
        "NetLettableAreaSqm": lambda info: round(info["property_area"] * random.uniform(0.78, 0.90), 0),
        "PropertyValue": lambda info: info["property_value"],
        "NumberOfStoreys": lambda info: random.randint(*TYPE_STOREYS[info["commercial_type"]]),
        "TotalUnits": lambda info: random.randint(*TYPE_TOTAL_UNITS[info["commercial_type"]]),
        "ParkingSpaces": lambda info: random.randint(*TYPE_PARKING_SPACES[info["commercial_type"]]),
        "LoadingBays": lambda info: random.randint(*TYPE_LOADING_BAYS[info["commercial_type"]]),
        "PlantRoomLocation": _plant_room_location,
        "ServiceCore": _service_core,
        "ConstructionType": lambda info: random.choice(
            ["Concrete frame", "Reinforced concrete", "Concrete frame", "Mixed construction"]
        ),
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
        "DeliveryBays": lambda info: random.randint(*TYPE_LOADING_BAYS[info["commercial_type"]]),

        # Tenancy / Investment
        "AnchorTenant": lambda info: anchor_tenant(info["commercial_type"]),
        "WAULT": lambda info: round(random.uniform(1.5, 8.0), 1),
        "ServiceChargeUSDPerSqm": lambda info: 0.0,
        "NetInitialYield": lambda info: round(random.uniform(0.045, 0.090), 4),
        "EquivalentYield": lambda info: round(random.uniform(0.050, 0.095), 4),
        "ReversionaryYield": lambda info: round(random.uniform(0.055, 0.100), 4),
        "CovenantStrength": _covenant_strength,

        # HazardProfile thresholds
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

        "BRIWaterRating": lambda info: _grade_to_rating(_bri(info)["water_grade"]),
        "BRIFlashRating": lambda info: _grade_to_rating(_bri(info)["flash_grade"]),
        "BRIWaterScore": lambda _: None,
        "BRIFlashScore": lambda _: None,

        "WindCodes": lambda info: list(_bri(info)["wind_codes"]),
        "WaterCodes": lambda info: list(_bri(info)["water_codes"]),
        "FlashCodes": lambda info: list(_bri(info)["flash_codes"]),
        "FireCodes": lambda info: list(_bri(info)["fire_codes"]),
        "SeismicCodes": lambda info: list(_bri(info)["seismic_codes"]),
    }

def generate_field_value(field_name: str, field_def: Dict, index: int,
                         metadata: Dict[str, Any]) -> Any:
    """Generate a value for a commercial schema field."""
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

    return _resi_random.generate_field_value(field_name, field_def, index, metadata)
