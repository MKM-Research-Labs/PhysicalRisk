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

"""
Thames-specific property random value generators.

Contains the field generator registry and metadata generation.
Delegates to submodules for specific calculation domains:
  - property_utils: dates, names, construction years
  - property_location: postcodes, streets, bedrooms, floor levels, council tax
  - property_valuation: property value, area, sale price, rent, insurance
  - property_energy: carbon, energy, electricity, gas, solar, bills

Usage:
    from port.rand.thames import property_random

    generators = property_random.get_field_generators()
    value = generators['PropertyValue'](location_info)
"""

import random
from datetime import datetime, timedelta
from typing import Any, Callable, Dict

from .property_energy import (
    calculate_annual_energy,
    calculate_carbon_emissions,
    calculate_energy_bill,
    calculate_gas_usage,
    calculate_grid_electricity,
    calculate_solar_generation,
)
from .property_location import (
    calculate_purchase_price,
    generate_bathrooms,
    generate_bedrooms,
    generate_council_tax_band,
    generate_floor_level,
    generate_postcode_for_area,
    generate_street_name,
)
from .property_utils import (
    generate_construction_year,
    generate_owner_name,
    generate_past_date,
    generate_postcode,  # noqa: F401 — used via module attribute in tests
    get_property_period,
)
from .property_valuation import (
    calculate_insurance_premium,
    calculate_monthly_rent,
    calculate_property_area,
    calculate_property_value,
    calculate_sale_price,
)

# =============================================================================
# METADATA GENERATION
# =============================================================================

def _deterministic_prop_id(location: Dict, index: int) -> str:
    """Generate a stable property ID from location + index."""
    import hashlib
    loc_key = f"{location['lat']:.6f}:{location['lon']:.6f}:{index}"
    return f"PROP-{hashlib.sha256(loc_key.encode()).hexdigest()[:8]}"


def generate_property_metadata(index: int, location: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate property metadata including ID, type, and other core attributes.

    Args:
        index: Property index in the portfolio
        location: Location dictionary with lat, lon, elevation, name, etc.

    Returns:
        Dictionary containing property metadata
    """
    property_type = random.choice([
        'Flat', 'Mid-terrace', 'End-terrace',
        'Semi-detached', 'Detached', 'Bungalow'
    ])

    construction_year = generate_construction_year()
    property_area = calculate_property_area({'property_type': property_type})

    property_value = calculate_property_value({
        'property_type': property_type,
        'property_area': property_area,
        'construction_year': construction_year,
        'elevation': location['elevation'],
        'value_factor': location.get('value_factor', 1.0)
    })

    return {
        'property_id': _deterministic_prop_id(location, index),
        'property_type': property_type,
        'construction_year': construction_year,
        'property_area': property_area,
        'property_value': property_value,
        'elevation': location['elevation'],
        'area_name': location.get('name', 'Unknown'),
        'value_factor': location.get('value_factor', 1.0),
        'streets_data': location.get('streets_data', {})
    }


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
        return (datetime.now() - timedelta(days=days_ago)).isoformat()

    return None


# =============================================================================
# FIELD GENERATORS
# =============================================================================

def get_field_generators() -> Dict[str, Callable]:
    """
    Return dictionary of field name to generator function mappings.

    Each generator takes a location_info dict and returns the field value.
    """
    return {
        # String fields
        "PropertyID": lambda info: _deterministic_prop_id(info, info.get('index', 0)),
        "UPRN": lambda _: str(random.randint(10000000, 99999999)),
        "PostCode": lambda info: generate_postcode_for_area(info),
        "Postcode": lambda info: generate_postcode_for_area(info),
        "OccupancyType": lambda _: random.choice(['Residential owner-occupied', 'Second home', 'Static caravan', 'Vacant']),
        "IncomeGenerating": lambda _: random.choice(['Yes', 'No']),
        "BuildingResidency": lambda _: random.choice(['Single Family', 'Multi Family', 'Mixed Use']),
        "propertyType": lambda _: random.choice(['residential', 'commercial', 'industrial']),
        "propertyStatus": lambda _: random.choice(['active', 'inactive', 'under_construction']),
        "FloodRisk": lambda _: random.choice(['Very low', 'Low', 'Medium', 'High', 'Very high']),
        "ConstructionType": lambda _: random.choice(['Brick and block', 'Timber frame', 'Stone', 'Modern methods', 'Mixed construction']),
        "FoundationType": lambda _: random.choice(['Strip foundations', 'Raft foundations', 'Pile foundations', 'Deep foundations', 'Unknown']),
        "ValuationMethod": lambda _: random.choice(['Market comparison', 'Income approach', 'Cost approach', 'Automated valuation']),
        "Country": lambda _: 'England',
        "Region": lambda _: random.choice(['London', 'South East', 'East of England']),
        "UrbanRuralClassification": lambda _: random.choice(['Urban', 'Suburban', 'Rural']),
        "EAFloodZone": lambda _: random.choice(['Zone 1', 'Zone 2', 'Zone 3a', 'Zone 3b']),
        "FloodRiskType": lambda _: random.choice(['River', 'Surface water', 'Groundwater', 'Coastal', 'Multiple']),

        "PropertyResi": lambda info: info.get('property_type', 'Flat'),
        "OccupancyResidency": lambda _: random.choice(['Family resident', 'Unoccupied', 'Single', 'HMO', 'Other']),
        "HeightMeters": lambda info: round(random.uniform(6, 25), 1),

        "PropertyAreaSqm": lambda info: calculate_property_area(info),

        "RenovationRequired": lambda _: random.choice([True, False]),
        "PropertyCondition": lambda _: random.choice(['Excellent', 'Good', 'Fair', 'Poor', 'Very poor']),
        "InsurancePremium": lambda info: calculate_insurance_premium(info),
        "ExcessAmount": lambda _: random.randint(250, 2500),
        "RiskRating": lambda _: random.choice(['Very low', 'Low', 'Medium', 'High', 'Very high']),
        "OverallFloodRisk": lambda _: random.choice(['Very low', 'Low', 'Medium', 'High', 'Very high']),

        # Property attributes
        "NumberBedrooms": lambda info: generate_bedrooms(info),
        "NumberBathrooms": lambda info: generate_bathrooms(info),
        "FloorLevelMeters": lambda info: generate_floor_level(info),

        # Address fields
        "StreetName": lambda info: generate_street_name(info),
        "BuildingNumber": lambda _: str(random.randint(1, 250)),
        "TownCity": lambda info: info.get('area_name', 'London'),
        "County": lambda _: 'Greater London',
        "LocalAuthority": lambda info: info.get('area_name', 'Westminster'),

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
        "FloodGates": lambda _: random.choice([True, False]),
        "FloodBarriers": lambda _: random.choice([True, False]),
        "SumpPump": lambda _: random.choice([True, False]),
        "NonReturnValves": lambda _: random.choice([True, False]),
        "WaterproofFlooring": lambda _: random.choice([True, False]),
        "RaisedElectricals": lambda _: random.choice([True, False]),
        "WaterproofPlaster": lambda _: random.choice([True, False]),
        "FloodWarningSystem": lambda _: random.choice([True, False]),
        "DrainageImprovement": lambda _: random.choice([True, False]),
        "SandBags": lambda _: random.choice([True, False]),
        "WaterButts": lambda _: random.choice([True, False]),
        "PermeablePaving": lambda _: random.choice([True, False]),
        "FloodProofDoors": lambda _: random.choice([True, False]),
        "FloodProofWindows": lambda _: random.choice([True, False]),
        "EmergencyKit": lambda _: random.choice([True, False]),

        # Protection Measures - Natural
        "TreePlanting": lambda _: random.choice([True, False]),
        "RainGarden": lambda _: random.choice([True, False]),
        "GreenRoof": lambda _: random.choice([True, False]),
        "Wetlands": lambda _: random.choice([True, False]),
        "NaturalDrainage": lambda _: random.choice([True, False]),
        "VegetationManagement": lambda _: random.choice([True, False]),

        # Number fields
        "PropertyValue": lambda info: calculate_property_value(info),
        "GroundLevelMeters": lambda info: info['elevation'],
        "elevation": lambda info: info['elevation'],
        "RiverDistanceMeters": lambda info: info.get('distance_to_thames', random.uniform(100, 5000)),

        # Integer fields
        "ConstructionYear": lambda _: generate_construction_year(),
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

        # Date fields
        "dateCreated": lambda _: datetime.now().strftime('%Y-%m-%d'),
        "lastUpdated": lambda _: datetime.now().strftime('%Y-%m-%d'),
        "ValuationDate": lambda _: (datetime.now() - timedelta(days=random.randint(0, 365))).strftime('%Y-%m-%d'),
    }
