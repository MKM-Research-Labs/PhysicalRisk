# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Field-value generators for commercial assets.

Holds the commercial-only lambdas keyed by CDM field name. Anything not
in the commercial table delegates to ``property_random.generate_field_value``
so shared fields (Location, RiskAssessment, Resilience, EnergyPerformance,
ratings) use the same logic across asset classes.
"""

import random
from typing import Any, Callable, Dict, Optional

from port.rand.halong.commercial import bri_codes as _bri_codes
from port.rand.halong.property import property_random as _resi_random

from .constants import (
    COMMERCIAL_CONSTRUCTION_TYPES,
    TYPE_BUSINESS_RATES,
    TYPE_LOADING_BAYS,
    TYPE_PARKING_SPACES,
    TYPE_STOREYS,
    TYPE_TOTAL_UNITS,
    TYPE_USE_CLASS,
)
from .metadata import anchor_tenant, period_from_year


def _bri(info: Dict[str, Any]) -> Dict[str, Any]:
    """Return the asset's BRI prototype record. Falls back to a fresh draw
    when missing (e.g. older test fixtures that bypass generate_commercial_metadata)."""
    proto = info.get("bri_prototype")
    if proto is None:
        proto = _bri_codes.for_commercial(info.get("commercial_type") or "MixedUse")
    return proto


def _grade_to_rating(grade: Optional[str]) -> str:
    """Map an internal grade ('A'/'B'/'N/A') to a CDM BRI letter rating."""
    if grade in (None, "N/A"):
        return "N/A"
    return grade


def _commercial_generators() -> Dict[str, Callable]:
    """Map of CDM field name → lambda(location_info). ``info`` is the
    location_info dict built inside ``generate_field_value`` (it includes
    ``commercial_type``)."""
    return {
        "CommercialType":         lambda info: info["commercial_type"],
        "UseClassUKO":            lambda info: TYPE_USE_CLASS[info["commercial_type"]],
        "BusinessRatesCategory":  lambda info: TYPE_BUSINESS_RATES[info["commercial_type"]],
        "OccupancyStatus":        lambda info: random.choices(
            ["Fully occupied", "Partially vacant", "Vacant"], weights=[0.7, 0.25, 0.05])[0],
        "PropertyAreaSqm":        lambda info: info["property_area"],
        "NetInternalAreaSqm":     lambda info: round(info["property_area"] * random.uniform(0.82, 0.92), 0),
        "NetLettableAreaSqm":     lambda info: round(info["property_area"] * random.uniform(0.80, 0.90), 0),
        "PropertyValue":          lambda info: info["property_value"],
        "NumberOfStoreys":        lambda info: random.randint(*TYPE_STOREYS[info["commercial_type"]]),
        "TotalUnits":             lambda info: random.randint(*TYPE_TOTAL_UNITS[info["commercial_type"]]),
        "ParkingSpaces":          lambda info: random.randint(*TYPE_PARKING_SPACES[info["commercial_type"]]),
        "LoadingBays":            lambda info: random.randint(*TYPE_LOADING_BAYS[info["commercial_type"]]),
        "PlantRoomLocation":      lambda info: random.choice(["Basement", "Ground floor", "Roof", "External"]),
        "ServiceCore":            lambda info: random.choice(
            ["Central core", "Multiple cores", "External core", "None"]),
        # SE-Asia commercial stock is reinforced concrete per the BRI-PRS
        # prototypes (all three sheet buildings are RC). Forced here so
        # halong commercials don't draw timber / brick alternatives that
        # don't fit the cyclone-resilience grading model.
        "ConstructionType":       lambda info: "Concrete frame",
        "ConstructionYear":       lambda info: info["construction_year"],
        "PropertyPeriod":         lambda info: period_from_year(info["construction_year"]),
        "PropertyCondition":      lambda info: random.choices(
            ["Excellent", "Good", "Fair", "Poor", "Very poor"],
            weights=[0.15, 0.45, 0.25, 0.10, 0.05])[0],

        # AccessibilityFeatures
        "DisabledAccess":         lambda info: random.random() < 0.85,
        "GoodsLiftCount":         lambda info: random.randint(0, 3),
        "GoodsLiftCapacityKg":    lambda info: float(random.choice([1000, 1600, 2500, 3500])),
        "EmergencyExits":         lambda info: max(2, int(info["property_area"] / 1500)),
        "DeliveryBays":           lambda info: random.randint(*TYPE_LOADING_BAYS[info["commercial_type"]]),

        # Tenancy
        "AnchorTenant":           lambda info: anchor_tenant(info["commercial_type"]),
        "WAULT":                  lambda info: round(random.uniform(2.0, 12.0), 1),
        "ServiceChargeGbpPerSqm": lambda info: round(random.uniform(40, 120), 2),
        "NetInitialYield":        lambda info: round(random.uniform(0.035, 0.085), 4),
        "EquivalentYield":        lambda info: round(random.uniform(0.040, 0.090), 4),
        "ReversionaryYield":      lambda info: round(random.uniform(0.045, 0.095), 4),
        "CovenantStrength":       lambda info: random.choices(
            ["AAA", "AA", "A", "BBB", "BB", "B", "Unrated"],
            weights=[0.05, 0.10, 0.30, 0.30, 0.15, 0.05, 0.05])[0],

        # HazardProfile thresholds — populated for halong commercial assets
        # from the BRI prototype. Wind / Flash always apply; Water (tsunami)
        # only when the prototype's water_grade is not "N/A" (i.e. coastal-
        # exposed buildings such as hotels in the source spreadsheet).
        "WindThresholdMajorMps": lambda info: _bri(info)["wind_threshold_major_mps"],
        "WindThresholdMinorMps": lambda info: _bri(info)["wind_threshold_minor_mps"],
        "FlashThresholdMajorM":  lambda info: _bri(info)["flash_threshold_major_m"],
        "FlashThresholdMinorM":  lambda info: _bri(info)["flash_threshold_minor_m"],
        "WaterThresholdMajorM":  lambda info: (
            _bri(info)["water_threshold_major_m"]
            if _bri(info)["water_grade"] not in (None, "N/A") else None
        ),
        "WaterThresholdMinorM":  lambda info: (
            _bri(info)["water_threshold_minor_m"]
            if _bri(info)["water_grade"] not in (None, "N/A") else None
        ),

        # BRI water / flash sub-ratings. The flat BRIFloodRating is left to
        # the BRI helper to compute as min(Water, Flash) post-build.
        "BRIWaterRating": lambda info: _grade_to_rating(_bri(info)["water_grade"]),
        "BRIFlashRating": lambda info: _grade_to_rating(_bri(info)["flash_grade"]),
        "BRIWaterScore":  lambda _: None,
        "BRIFlashScore":  lambda _: None,

        # IndustryGroups — free-string BRI measure code lists per hazard.
        "WindCodes":    lambda info: list(_bri(info)["wind_codes"]),
        "WaterCodes":   lambda info: list(_bri(info)["water_codes"]),
        "FlashCodes":   lambda info: list(_bri(info)["flash_codes"]),
        "FireCodes":    lambda info: list(_bri(info)["fire_codes"]),
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
        'commercial_type':  metadata.get('commercial_type'),
        'property_type':    metadata.get('commercial_type'),
        'property_area':    metadata.get('property_area'),
        'property_value':   metadata.get('property_value'),
        'construction_year': metadata.get('construction_year'),
        'elevation':        metadata.get('elevation'),
        'vertical_offset':  metadata.get('vertical_offset', 0.5),
        'area_name':        metadata.get('area_name'),
        'value_factor':     metadata.get('value_factor', 1.0),
        'streets_data':     metadata.get('streets_data', {}),
        'bri_prototype':    metadata.get('bri_prototype'),
    }

    commercial_gens = _commercial_generators()
    if field_name in commercial_gens:
        try:
            return commercial_gens[field_name](info)
        except Exception:
            pass

    # Delegate to residential generators for all shared fields.
    return _resi_random.generate_field_value(field_name, field_def, index, metadata)
