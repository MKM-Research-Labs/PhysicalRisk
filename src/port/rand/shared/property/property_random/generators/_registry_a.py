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

"""Field generator registry (part A) for property randomisation."""

import random
from datetime import datetime, timedelta
from typing import Any, Callable, Dict

from config.port import (
    DESIGN_WIND_SPEED_JITTER_KPH,
    DESIGN_WIND_SPEED_KPH_POINTS,
    DESIGN_WIND_SPEED_WEIGHTS,
)
from port.rand.profiles import active_profile as _profile

from ..helpers import (
    _deterministic_prop_id,
    _ea_zone_from_elevation,
    _flood_hazard_class_from_offset,
)
from ...property_energy import (
    calculate_annual_energy,
    calculate_carbon_emissions,
    calculate_energy_bill,
    calculate_gas_usage,
    calculate_grid_electricity,
    calculate_solar_generation,
)
from ...property_location import (
    calculate_purchase_price,
    generate_bathrooms,
    generate_bedrooms,
    generate_council_tax_band,
    generate_floor_level,
    generate_postcode_for_area,
    generate_street_name,
)
from ...property_utils import (
    generate_construction_year,
    generate_owner_name,
    generate_past_date,
    get_property_period,
)
from ...property_valuation import (
    calculate_insurance_premium,
    calculate_monthly_rent,
    calculate_property_area,
    calculate_property_value,
    calculate_sale_price,
)


def field_generators_part_a():
    return {
        # String fields
        "PropertyID": lambda info: _deterministic_prop_id(info, info.get('index', 0)),
        "UPRN": lambda _: str(random.randint(10000000, 99999999)),
        "Postcode": lambda info: generate_postcode_for_area(info),
        "OccupancyType": lambda _: random.choice(['Residential owner-occupied', 'Second home', 'Static caravan', 'Vacant']),
        "IncomeGenerating": lambda _: random.choice(['Yes', 'No']),
        "BuildingResidency": lambda _: random.choice(['Single Family', 'Multi Family', 'Mixed Use']),
        "propertyType": lambda _: random.choice(['residential', 'commercial', 'industrial']),
        "propertyStatus": lambda _: random.choice(['active', 'inactive', 'under_construction']),
        "ConstructionType": lambda _: random.choice(['Brick and block', 'Timber frame', 'Stone', 'Modern methods', 'Mixed construction']),
        "FoundationType": lambda _: random.choice(['Strip foundations', 'Raft foundations', 'Pile foundations', 'Deep foundations', 'Unknown']),

        # Construction — RoofDetails
        "RoofCover":      lambda _: random.choice(["Slate", "Clay tile", "Concrete tile", "Metal", "Felt", "Thatch", "Green roof", "Other"]),
        "RoofGeometry":   lambda _: random.choices(
            ["Flat", "Gabled", "Hip", "Mansard", "Complex", "Barrel vault"],
            weights=[0.10, 0.35, 0.30, 0.10, 0.10, 0.05],
        )[0],
        "RoofPitch":      lambda _: random.choices(
            ["Flat (<5°)", "Low (5-20°)", "Medium (20-35°)", "Steep (>35°)"],
            weights=[0.10, 0.25, 0.50, 0.15],
        )[0],
        "RoofFrame":      lambda _: random.choices(
            ["Timber truss", "Timber rafter", "Steel", "Concrete", "Unknown"],
            weights=[0.45, 0.25, 0.10, 0.10, 0.10],
        )[0],
        "RoofDeck":       lambda _: random.choices(
            ["Plywood", "OSB", "Metal deck", "Concrete", "Sarking board", "Unknown"],
            weights=[0.20, 0.25, 0.10, 0.15, 0.20, 0.10],
        )[0],
        "RoofYearReplaced": lambda info: (
            info.get("construction_year", 1980) + random.randint(0, 30)
        ),

        # Construction — structural characteristics
        "SoftStory":         lambda _: random.random() < 0.08,
        "ShapeIrregularity": lambda _: random.choices(
            ["None", "Plan", "Vertical", "Both"],
            weights=[0.65, 0.20, 0.10, 0.05],
        )[0],
        "BrickVeneer":   lambda _: random.random() < 0.20,
        "GlassType":     lambda _: random.choices(
            ["Standard", "Laminated", "Tempered", "Impact resistant", "Unknown"],
            weights=[0.55, 0.15, 0.15, 0.05, 0.10],
        )[0],
        "RetrofitYear":  lambda info: (
            info.get("construction_year", 1980) + random.randint(10, 40)
            if random.random() < 0.15 else None
        ),
        "HasCrippleWall": lambda info: (
            random.random() < 0.25
            if (info.get("construction_year") or 1980) < 1980 else False
        ),
        "ValuationMethod": lambda _: random.choice(['Market comparison', 'Income approach', 'Cost approach', 'Automated valuation']),
        "Country": lambda _: 'England',
        "Region": lambda _: random.choice(['London', 'South East', 'East of England']),
        "UrbanRuralClassification": lambda _: random.choice(['Urban', 'Suburban', 'Rural']),
        "EAFloodZone": lambda info: _ea_zone_from_elevation(info),
        "FloodRiskType": lambda _: random.choice(['Fluvial', 'Pluvial', 'GroundWater', 'Coastal', 'Multiple']),

        "PropertyResi": lambda info: info.get('property_type', 'Flat'),
        "OccupancyResidency": lambda _: random.choice(['Family resident', 'Unoccupied', 'Single', 'HMO', 'Other']),
        "HeightMeters": lambda info: round(random.uniform(6, 25), 1),

        "PropertyAreaSqm": lambda info: calculate_property_area(info),

        "RenovationRequired": lambda _: random.choice([True, False]),
        "PropertyCondition": lambda _: random.choice(['Excellent', 'Good', 'Fair', 'Poor', 'Very poor']),
        "InsurancePremium": lambda info: calculate_insurance_premium(info),
        "ExcessAmount": lambda _: random.randint(250, 2500),
        "OverallFloodRisk": lambda _: random.choice(['Very low', 'Low', 'Medium', 'High', 'Very high']),

        # RiskAssessment — v10 fields restored. LastFloodDate is nullable
        # (most properties never flooded); distances reflect Thames-context
        # geography (London is inland, no coast, scattered lakes/canals).
        "LastFloodDate":             lambda _: generate_past_date(days_range=(365*2, 365*30)) if random.random() < 0.15 else None,

        # RiskAssessment — flood geometry and geotechnical
        "BaseFloodElevationMeters": lambda info: round(info.get("elevation", 12.0) - random.uniform(0.5, 3.0), 2),
        "VerticalDatum":            lambda _: "AOD",
        "SoilVs30Mps":             lambda _: round(random.choices(
            [800, 500, 350, 250, 180, 120],
            weights=[0.05, 0.10, 0.20, 0.35, 0.20, 0.10],
        )[0] + random.uniform(-20, 20), 0),
        "FloodDebrisPresent":       lambda info: (info.get("vertical_offset", 999) < 2.0) and (random.random() < 0.4),

        "SoilType":                  lambda _: random.choices(
            ["Clay", "Sandy", "Loamy", "Chalk", "Peat", "Rocky", "Mixed", "Saltpans", "Unknown"],
            weights=[0.35, 0.10, 0.15, 0.10, 0.05, 0.05, 0.15, 0.00, 0.05],
        )[0],
        "LakeDistanceMeters":        lambda _: round(random.uniform(500, 8000), 0),
        "CoastalDistanceMeters":     lambda _: round(random.uniform(40000, 120000), 0),  # London is far from coast
        "CanalDistanceMeters":       lambda _: round(random.uniform(200, 5000), 0),
        "GovernmentalDefenceScheme": lambda info: (info.get('vertical_offset', 999) < 3.0) and (random.random() < 0.4),

        # TransactionHistory.Insurance — v10 policy fields parked here as financial info.
        "InsuranceStatus":  lambda info: random.choices(
            ["Uninsured", "Standard cover", "Flood Re supported", "Specialist cover"],
            weights=[0.05, 0.65, 0.20, 0.10],
        )[0],
        "FloodReEligible":  lambda info: (info.get('vertical_offset', 999) < 3.0) and (random.random() < 0.7),
        "ClaimsHistory":    lambda _: random.choices([0, 1, 2, 3, 4], weights=[0.55, 0.25, 0.12, 0.06, 0.02])[0],
        "LastClaimDate":    lambda _: generate_past_date(days_range=(180, 365*10)) if random.random() < 0.45 else None,
        "LastClaimType":    lambda _: random.choices(
            ["None", "Fire", "Flood damage", "Subsidence", "Domestic appliances"],
            weights=[0.45, 0.05, 0.20, 0.10, 0.20],
        )[0],

        # GoverningBodyRatings — letter ratings are stamped by the BRI helper
        # in the builder post-step. The *score* fields are left blank pending
        # a forthcoming methodology model that will populate them.
        "BRIScore":          lambda _: None,
        "BRIFloodScore":     lambda _: None,
        "BRIWindScore":      lambda _: None,
        "BRIFireScore":      lambda _: None,
        "BRISeismicScore":   lambda _: None,
        # Water / Flash split-rating fields — populated by halong commercial
        # only. Thames leaves them blank.
        "BRIWaterRating":    lambda _: None,
        "BRIWaterScore":     lambda _: None,
        "BRIFlashRating":    lambda _: None,
        "BRIFlashScore":     lambda _: None,
        # HazardProfile split thresholds — populated by halong commercial only.
        "WindThresholdMajorMps": lambda _: None,
        "WindThresholdMinorMps": lambda _: None,
        "WaterThresholdMajorM":  lambda _: None,
        "WaterThresholdMinorM":  lambda _: None,
        "FlashThresholdMajorM":  lambda _: None,
        "FlashThresholdMinorM":  lambda _: None,
        # IndustryGroups — empty everywhere except halong commercial.
        "WindCodes":    lambda _: [],
        "WaterCodes":   lambda _: [],
        "FlashCodes":   lambda _: [],
        "FireCodes":    lambda _: [],
        "SeismicCodes": lambda _: [],

        # Insurance body ratings (was previously named RiskRating).
        "InsuranceRating":        lambda _: random.choice(['Very low', 'Low', 'Medium', 'High', 'Very high']),
        "InsuranceRatingBody":    lambda _: random.choice(['Aviva', 'Direct Line', 'AXA', 'Zurich', 'RSA', 'LV=']),
        "InsuranceRatingVersion": lambda _: random.choice(['v1.0', 'v1.5', 'v2.0', 'v2.1']),
        "InsuranceDate":          lambda _: generate_past_date(days_range=(30, 730)),

        # Normalised hazard classes for downstream resilience scoring.
        # FloodHazardClass is derived from vertical offset to stay consistent
        # with EAFloodZone; the other three are Thames-context weighted random
        # (UK is low-seismic, urban-low-wind, urban-low-fire).
        "FloodHazardClass":   lambda info: _flood_hazard_class_from_offset(info),

        # HazardProfile — design intensities
        "DesignWindSpeedKmh":  lambda _: round(random.choices(
            DESIGN_WIND_SPEED_KPH_POINTS,
            weights=DESIGN_WIND_SPEED_WEIGHTS,
        )[0] + random.uniform(
            -DESIGN_WIND_SPEED_JITTER_KPH, DESIGN_WIND_SPEED_JITTER_KPH), 0),
        "DesignFloodReturnYr": lambda _: random.choice([50, 100, 200, 500, 1000]),
        "DesignSeismicPGA":    lambda _: round(random.uniform(*_profile().SEISMIC_PGA_RANGE), 3),
        "WindHazardClass":    lambda _: random.choices(
            ["None", "Low", "Medium", "High", "Extreme"],
            weights=[0.05, 0.55, 0.30, 0.09, 0.01],
        )[0],
        "SeismicHazardClass": lambda _: random.choices(
            ["None", "Low", "Medium", "High", "Extreme"],
            weights=_profile().SEISMIC_HAZARD_CLASS_WEIGHTS,
        )[0],
        "FireHazardClass":    lambda _: random.choices(
            ["None", "Low", "Medium", "High", "Extreme"],
            weights=[0.10, 0.55, 0.25, 0.08, 0.02],
        )[0],

    }
