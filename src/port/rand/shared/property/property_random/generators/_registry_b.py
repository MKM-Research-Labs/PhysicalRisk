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

"""Field generator registry (part B) for property randomisation."""

import random
from datetime import datetime, timedelta
from typing import Any, Callable, Dict

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


def field_generators_part_b():
    return {
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
