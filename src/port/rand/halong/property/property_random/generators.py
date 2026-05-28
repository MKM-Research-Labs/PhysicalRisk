# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Field generator registry and value generation."""

import random
from datetime import datetime, timedelta
from typing import Any, Callable, Dict

from .helpers import (
    _deterministic_prop_id,
    _ea_zone_from_elevation,
    _flood_hazard_class_from_offset,
)
from ..property_energy import (
    calculate_annual_energy,
    calculate_carbon_emissions,
    calculate_energy_bill,
    calculate_gas_usage,
    calculate_grid_electricity,
    calculate_solar_generation,
)
from ..property_location import (
    calculate_purchase_price,
    generate_bathrooms,
    generate_bedrooms,
    generate_council_tax_band,
    generate_floor_level,
    generate_postcode_for_area,
    generate_street_name,
)
from ..property_utils import (
    generate_construction_year,
    generate_owner_name,
    generate_past_date,
    get_property_period,
)
from ..property_valuation import (
    calculate_insurance_premium,
    calculate_monthly_rent,
    calculate_property_area,
    calculate_property_value,
    calculate_sale_price,
)


def generate_field_value(field_name: str, field_def: Dict, index: int, metadata: Dict[str, Any]) -> Any:
    """
    Generate a value for a specific field.

    Args:
        field_name: Name of the field
        field_def: Field definition from schema
        index: Property index
        metadata: Property metadata dictionary

    Returns:
        Generated value for the field
    """
    generators = get_field_generators()

    if field_name in generators:
        location_info = {
            'property_type': metadata.get('property_type'),
            'property_area': metadata.get('property_area'),
            'property_value': metadata.get('property_value'),
            'construction_year': metadata.get('construction_year'),
            'elevation': metadata.get('elevation'),
            'vertical_offset': metadata.get('vertical_offset', 0.5),
            'area_name': metadata.get('area_name'),
            'value_factor': metadata.get('value_factor', 1.0),
            'streets_data': metadata.get('streets_data', {})
        }

        try:
            return generators[field_name](location_info)
        except Exception:
            pass

    # Fallback to type-based generation
    field_type = field_def.get('type', 'string')

    if field_type in ('string', 'text'):
        options = field_def.get('options')
        if options:
            return random.choice(options)
        return ''
    elif field_type == 'number':
        return round(random.uniform(0, 1000), 2)
    elif field_type == 'integer':
        return random.randint(0, 100)
    elif field_type == 'boolean':
        return random.choice([True, False])
    elif field_type == 'date':
        days_ago = random.randint(0, 3650)
        return (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')

    return None


def get_field_generators() -> Dict[str, Callable]:
    """
    Return dictionary of field name to generator function mappings.

    Each generator takes a location_info dict and returns the field value.
    """
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
        # Water / Flash split-rating fields. The spreadsheet's prototypes are
        # commercial-only; for residential we leave them null and let the
        # BRI helper fall back to the legacy flat "Flood" rating.
        "BRIWaterRating":    lambda _: None,
        "BRIWaterScore":     lambda _: None,
        "BRIFlashRating":    lambda _: None,
        "BRIFlashScore":     lambda _: None,
        # HazardProfile split thresholds — populated by halong commercial
        # generators only. Residential keeps the legacy WindThresholdKph
        # path (when present) and leaves the new fields blank.
        "WindThresholdMajorMps": lambda _: None,
        "WindThresholdMinorMps": lambda _: None,
        "WaterThresholdMajorM":  lambda _: None,
        "WaterThresholdMinorM":  lambda _: None,
        "FlashThresholdMajorM":  lambda _: None,
        "FlashThresholdMinorM":  lambda _: None,
        # IndustryGroups BRI measure codes — populated for halong commercial
        # from the SE-Asia prototype catalogue. Empty list everywhere else.
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
            [80, 100, 120, 140, 160],
            weights=[0.05, 0.40, 0.35, 0.15, 0.05],
        )[0] + random.uniform(-5, 5), 0),
        "DesignFloodReturnYr": lambda _: random.choice([50, 100, 200, 500, 1000]),
        "DesignSeismicPGA":    lambda _: round(random.uniform(0.02, 0.08), 3),
        "WindHazardClass":    lambda _: random.choices(
            ["None", "Low", "Medium", "High", "Extreme"],
            weights=[0.05, 0.55, 0.30, 0.09, 0.01],
        )[0],
        "SeismicHazardClass": lambda _: random.choices(
            ["None", "Low", "Medium", "High", "Extreme"],
            weights=[0.70, 0.28, 0.02, 0.00, 0.00],
        )[0],
        "FireHazardClass":    lambda _: random.choices(
            ["None", "Low", "Medium", "High", "Extreme"],
            weights=[0.10, 0.55, 0.25, 0.08, 0.02],
        )[0],

        # Property attributes
        "NumberBedrooms": lambda info: generate_bedrooms(info),
        "NumberBathrooms": lambda info: generate_bathrooms(info),
        "FloorLevelMeters": lambda info: generate_floor_level(info),

        # PropertyAttributes — v10 fields restored
        "HousingAssociation":   lambda _: random.random() < 0.15,
        "PayingBusinessRates":  lambda info: info.get('property_type') in ('commercial', 'industrial') or random.random() < 0.05,
        "TotalRooms":           lambda _: random.randint(3, 12),
        "GardenAreaFront":      lambda _: round(random.uniform(0, 60), 1),
        "GardenAreaBack":       lambda _: round(random.uniform(0, 200), 1),
        "ParkingType":          lambda _: random.choices(
            ["None", "On-street only", "Driveway only", "Garage only",
             "Driveway and garage", "Allocated space"],
            weights=[0.20, 0.25, 0.20, 0.10, 0.15, 0.10],
        )[0],
        "AccessType":           lambda _: random.choices(
            ["Public road", "Private road", "Shared access", "Right of way"],
            weights=[0.75, 0.10, 0.10, 0.05],
        )[0],
        "LastMajorWorksDate":   lambda _: generate_past_date(days_range=(180, 365*15)),

        # Construction — v10 fields restored
        "FloorType":      lambda _: random.choice([
            "Suspended timber", "Solid concrete", "Suspended concrete",
            "Beam and block", "Mixed",
        ]),
        "StiltsHeight":   lambda _: 0 if random.random() < 0.95 else round(random.uniform(0.5, 2.5), 2),
        # PropertyHeight is reconciled with HeightMeters in the builder's
        # consistency post-step; this lambda is only a placeholder.
        "PropertyHeight": lambda info: round(random.uniform(4, 25), 1),

        # Address fields
        "StreetName": lambda info: generate_street_name(info),
        "BuildingNumber": lambda _: str(random.randint(1, 250)),
        "TownCity": lambda info: info.get('area_name', 'London'),
        "County": lambda _: 'Greater London',
        "LocalAuthority": lambda info: info.get('area_name', 'Westminster'),

        # Location — v10 fields restored
        "BuildingName":              lambda _: random.choice([
            "Rose Cottage", "The Old Mill", "Riverside House", "Oak Lodge",
            "The Granary", "Willow Cottage", None, None, None,  # often blank
        ]),
        "SubBuildingNumber":         lambda _: random.choice([None, None, None, "A", "B", "1", "2", "3"]),
        "SubBuildingName":           lambda _: random.choice([
            None, None, None, "Ground Floor Flat", "First Floor Flat",
            "Top Floor Flat", "Basement Flat",
        ]),
        "AddressLine2":              lambda _: random.choice([None, None, None, "Millbrook", "Riverside", "The Park"]),
        "USRN":                      lambda _: str(random.randint(8400000, 8499999)),
        "ElectoralWard":             lambda info: info.get('area_name', 'Westminster'),
        "ParliamentaryConstituency": lambda info: f"{info.get('area_name', 'London')} {random.choice(['North','South','East','West','Central'])}",
        "LocalDensityHectare":       lambda _: round(random.uniform(20, 150), 0),
        "BritishNationalGrid":       lambda _: f"{random.choice(['TQ','TL','SU','SP','SZ'])} {random.randint(100,999)} {random.randint(100,999)}",
        "What3Words":                lambda _: f"//{random.choice(['famous','honest','daily','quiet','sunny'])}.{random.choice(['rapid','quiet','silver','open','green'])}.{random.choice(['pizza','table','river','horse','garden'])}",

        # Transaction fields
        "PurchasePriceGbp": lambda info: calculate_purchase_price(info),
        "RentalYield": lambda info: round(random.uniform(3.5, 6.5), 2),
        "CouncilTaxBand": lambda info: generate_council_tax_band(info),
        "PropertyPeriod": lambda info: get_property_period(info.get('construction_year', 1980)),

        # Building Fabric
        "WallConstruction": lambda _: random.choice(['Solid brick', 'Cavity brick', 'Timber frame', 'Modern methods of construction', 'Stone', 'System build', 'Concrete']),
        "CavityInsulation": lambda _: random.choice([True, False]),
        "ThermalBridgeScore": lambda _: round(random.uniform(0.05, 0.8), 2),
        "LoftInsulationMm": lambda _: random.choice([0, 100, 150, 200, 250, 300, 350]),
        "RoofType": lambda _: random.choice(['Flat roof', 'Pitched with tiles', 'Pitched with slate', 'Pitched with other', 'Mansard', 'Barrel vault', 'Green roof', 'Mixed']),
        "FloorConstruction": lambda _: random.choice(['Solid concrete', 'Suspended timber', 'Suspended concrete', 'Beam and block', 'Mixed construction']),
        "FloorInsulation": lambda _: random.choice([True, False]),
        "HeatingSys": lambda _: random.choice(['Combi boiler', 'System boiler', 'Regular boiler', 'Electric storage heaters', 'Air source heat pump', 'Ground source heat pump', 'District heating', 'Biomass boiler', 'Direct electric', 'Hybrid system']),
        "WaterHeating": lambda _: random.choice(['Gas combi', 'Gas system with cylinder', 'Electric immersion', 'Heat pump', 'Solar thermal', 'District heating', 'Instant electric', 'Gas multipoint']),
        "LightingType": lambda _: random.choice(['LED', 'Compact fluorescent', 'Halogen', 'Mixed types', 'Traditional', 'Smart LED']),
        "AirTightnessScore": lambda _: round(random.uniform(3, 15), 1),
        "GlazingType": lambda _: random.choice(['Single', 'Double', 'Triple', 'Secondary glazing', 'Mixed types', 'Low-E coated', 'Solar control']),
        "WindowFrameType": lambda _: random.choice(['uPVC', 'Timber', 'Aluminum', 'Composite', 'Steel', 'Mixed materials']),
        "DoorType": lambda _: random.choice(['uPVC', 'Timber', 'Composite', 'Aluminum', 'Steel', 'Mixed materials', 'Traditional']),
        "SmartMeterType": lambda _: random.choice(['None', 'Basic meter', 'Smart meter', 'Smart meter with export capability', 'Smart prepayment']),

        # Protection Measures - Resilience
        # NB: the bulk of resilience checks are now generated by the
        # age/condition/zone-aware module in resilience.py and applied as a
        # builder post-step. Only the original four BRI-aligned flood booleans
        # remain here as a fallback for callers that hit the registry directly.
        "FloodGates": lambda _: random.choice([True, False]),
        "FloodBarriers": lambda _: random.choice([True, False]),
        "SumpPump": lambda _: random.choice([True, False]),
        "FloodWarningSystem": lambda _: random.choice([True, False]),

        # Number fields
        "PropertyValue": lambda info: calculate_property_value(info),
        "GroundLevelMeters": lambda info: round(info['elevation'], 2),
        "RiverDistanceMeters": lambda info: info.get('distance_to_thames', random.uniform(100, 5000)),

        # Integer fields
        # ConstructionYear must mirror metadata.construction_year so that
        # derived fields (PropertyPeriod, BRI scoring) stay consistent.
        "ConstructionYear": lambda info: info.get('construction_year', generate_construction_year()),
        "NumberOfStoreys": lambda info: 1 if info.get('property_type') == 'Flat' else random.randint(1, 4),

        # Energy Performance - Usage
        "TariffType": lambda _: random.choice(['Wood Fire', 'Gas', 'Electricity', 'Both']),
        "AnnualCarbonKgCO2e": lambda info: calculate_carbon_emissions(info),
        "HeatingSystem": lambda _: random.choice(['Gas central heating', 'Electric heating', 'Heat pump', 'Oil heating', 'Other']),
        "RenewableSystem": lambda _: random.choice(['None', 'Solar PV', 'Solar thermal', 'Heat pump', 'Multiple']),
        "AnnualEnergyKwh": lambda info: calculate_annual_energy(info),
        "GridElectricityKwh": lambda info: calculate_grid_electricity(info),
        "GasUsageKwh": lambda info: calculate_gas_usage(info),
        "SolarGenerationKwh": lambda info: calculate_solar_generation(info),
        "AnnualEnergyBill": lambda info: calculate_energy_bill(info),

        # Energy Performance - Ratings
        "EPCRating": lambda _: random.choice(['A', 'B', 'C', 'D', 'E', 'F', 'G']),
        "CarbonRating": lambda _: random.choice(['A+', 'A', 'B', 'C', 'D', 'E', 'F']),
        "EmissionsScore": lambda _: random.choice(['Excellent', 'Good', 'Fair', 'Poor', 'Very poor']),

        # History - Environmental Issues
        "AirQuality": lambda _: random.choice(['Low', 'Moderate', 'High', 'Very high', 'Exceeds limits']),
        "WaterQuality": lambda _: random.choice(['Excellent', 'Good', 'Fair', 'Poor', 'Very poor']),
        "NoisePollution": lambda _: random.choice(['None', 'Traffic', 'Planes', 'Train']),
        "LastEnvironmentalIssueDate": lambda _: generate_past_date(days_range=(365, 365*5)),

        # History - Fire Incidents
        "FireDamageSeverity": lambda _: random.choice(['None', 'Minor', 'Moderate', 'Severe', 'Total loss']),
        "LastFireDate": lambda _: generate_past_date(days_range=(365*2, 365*10)) if random.random() < 0.1 else None,

        # History - Flood Events
        "FloodReturnPeriod": lambda _: random.choice([50, 100, 200, 500, 1000]),
        "FloodDamageSeverity": lambda _: random.choice(['No damage', 'Minor damage', 'Moderate damage', 'Significant damage', 'Severe damage']),
        "LastFloodDateHistory": lambda _: generate_past_date(days_range=(365, 365*15)) if random.random() < 0.2 else None,

        # History - Ground Conditions
        "SubsidenceStatus": lambda _: random.choice(['No issues', 'Minor movement', 'Moderate subsidence', 'Severe subsidence', 'Under investigation']),
        "ContaminationStatus": lambda _: random.choice(['None detected', 'Historical industrial', 'Remediated', 'Current contamination', 'Under investigation']),
        "GroundStability": lambda _: random.choice(['Stable', 'Minor concerns', 'Moderate risk', 'High risk', 'Active movement']),
        "LastGroundIssueDate": lambda _: generate_past_date(days_range=(365*2, 365*20)) if random.random() < 0.05 else None,

        # Transaction History - Rental
        "RentalHistory": lambda _: random.choice(['Never rented', 'Previously rented', 'Currently rented', 'Mixed use history']),
        "MonthlyRentGbp": lambda info: calculate_monthly_rent(info),
        "VacancyCount": lambda _: random.randint(0, 5),
        "TenancyDuration": lambda _: random.choice(['0-6 months', '6-12 months', '12-24 months', '24-36 months', '36+ months']),

        # Transaction History - Sales
        "SalePriceGbp": lambda info: calculate_sale_price(info),
        "SaleDate": lambda _: generate_past_date(days_range=(30, 365*3)),
        "PreviousOwner": lambda _: generate_owner_name(),
        "MarketingDays": lambda _: random.randint(14, 365),

        # Contents
        "ContentsValue":            lambda info: round(info.get("property_value", 500000) * random.uniform(0.05, 0.25), 2),
        "ContentsMobility":         lambda _: random.choices(
            ["Fixed", "Moveable", "Mixed"],
            weights=[0.20, 0.50, 0.30],
        )[0],
        "ContentsStoredAboveFlood": lambda _: random.random() < 0.40,

        # Date fields
        "dateCreated": lambda _: datetime.now().strftime('%Y-%m-%d'),
        "lastUpdated": lambda _: datetime.now().strftime('%Y-%m-%d'),
        "ValuationDate": lambda _: (datetime.now() - timedelta(days=random.randint(0, 365))).strftime('%Y-%m-%d'),
    }
