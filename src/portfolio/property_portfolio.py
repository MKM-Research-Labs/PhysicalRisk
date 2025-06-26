# Copyright (c) 2025 MKM Research Labs. All rights reserved.
# 
# This software is provided under license by MKM Research Labs. 
# Use, reproduction, distribution, or modification of this code is subject to the 
# terms and conditions of the license agreement provided with this software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Property Portfolio Generator.

This module generates synthetic property data based on the PropertyCDM schema.
"""

import os
import json
import uuid 
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
import random
import numpy as np
import sys


# Fix the Python path to find project modules
current_file = Path(__file__).resolve()
# Navigate up to find project root (assuming we're in src/portfolio or similar)
project_root = current_file.parent.parent

# Add project root to Python's path
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Now import modules using absolute imports
from utilities.project_paths import ProjectPaths

paths = ProjectPaths(__file__)
paths.setup_import_paths()

# Import CDM classes
sys.path.insert(0, str(project_root / 'src' / 'cdm'))
from property_cdm import PropertyCDM

sys.path.insert(0, str(project_root / 'src' / 'utilities'))
from elevation import init_elevation_data, get_elevation, LONDON_AREAS, LONDON_STREETS, AREA_VALUE_FACTORS, generate_synchronized_locations

# Initialize project paths
paths = ProjectPaths(__file__)

class PropertyPortfolioGenerator:
    """Generates synthetic property data based on the PropertyCDM schema."""
  
  
    def __init__(self, output_dir):
        """Initialize the Property Portfolio Generator."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.property_cdm = PropertyCDM()

        
        # London areas with value factors for property pricing
        self.london_areas = LONDON_AREAS
        self.london_streets = LONDON_STREETS
        
        # Property types with distribution weights
        self.property_types = ["Detached", "Semi-detached", "Mid-terrace", "End-terrace", "Bungalow", "Flat"]
        self.property_type_weights = [0.05, 0.1, 0.25, 0.15, 0.05, 0.4]  # More flats in London
        
        # Field value generators map
        self.field_generators = {
            # String fields
            "PropertyID": lambda _: f"PROP-{str(uuid.uuid4())[:8]}",
            "UPRN": lambda _: str(random.randint(10000000, 99999999)),
            "PostCode": lambda _: self._generate_postcode(),
            "OccupancyType": lambda _: random.choice(['Owner Occupied', 'Rented', 'Vacant']),
            "IncomeGenerating": lambda _: random.choice(['Yes', 'No']),
            "BuildingResidency": lambda _: random.choice(['Single Family', 'Multi Family', 'Mixed Use']),
            "propertyType": lambda _: 'Residential',
            "propertyStatus": lambda _: 'Active',
            "FloodRisk": lambda _: random.choice(['Very Low', 'Low', 'Medium', 'High', 'Very High']),
            "ConstructionType": lambda _: random.choice(['Brick', 'Timber Frame', 'Stone', 'Concrete']),
        
            "PropertyResi": lambda info: info.get('property_type', 'Flat'),  # Maps to same as PropertyType
            "OccupancyResidency": lambda _: random.choice(['Family resident', 'Unoccupied', 'Single','HMO','Other']),
            "HeightMeters": lambda info: round(random.uniform(6, 25), 1),  # Building height in meters
            
            "PropertyAreaSqm": lambda info: self._calculate_property_area(info),
            
            
            "RenovationRequired": lambda _: random.choice([True, False]),
            "PropertyCondition": lambda _: random.choice(['Excellent', 'Good', 'Fair', 'Poor', 'Very poor']),
            "InsurancePremium": lambda info: self._calculate_insurance_premium(info),
            "ExcessAmount": lambda _: random.randint(250, 2500),  # £250-£2500
            "RiskRating": lambda _: random.choice(['Very low', 'Low', 'Medium', 'High', 'Very high']),
            "OverallFloodRisk": lambda _: random.choice(['Very Low', 'Low', 'Medium', 'High', 'Very High']),
            
            "WallConstruction": lambda _: random.choice(['Solid brick', 'Cavity brick', 'Timber frame', 'Modern methods of construction', 'Stone', 'System build', 'Concrete']),
            "CavityInsulation": lambda _: random.choice([True, False]),
            "ThermalBridgeScore": lambda _: round(random.uniform(0.05, 0.8), 2),  # W/m²K
            "LoftInsulationMm": lambda _: random.choice([0, 100, 150, 200, 250, 300, 350]),
            "RoofType": lambda _: random.choice(['Flat roof', 'Pitched with tiles', 'Pitched with slate', 'Pitched with other', 'Mansard', 'Barrel vault', 'Green roof', 'Mixed']),
            "FloorConstruction": lambda _: random.choice(['Solid concrete', 'Suspended timber', 'Suspended concrete', 'Beam and block', 'Mixed construction']),
            "FloorInsulation": lambda _: random.choice([True, False]),
            "HeatingSys": lambda _: random.choice(['Combi boiler', 'System boiler', 'Regular boiler', 'Electric storage heaters', 'Air source heat pump', 'Ground source heat pump', 'District heating', 'Biomass boiler', 'Direct electric', 'Hybrid system']),
            "WaterHeating": lambda _: random.choice(['Gas combi', 'Gas system with cylinder', 'Electric immersion', 'Heat pump', 'Solar thermal', 'District heating', 'Instant electric', 'Gas multipoint']),
            "LightingType": lambda _: random.choice(['LED', 'Compact fluorescent', 'Halogen', 'Mixed types', 'Traditional', 'Smart LED']),
            "AirTightnessScore": lambda _: round(random.uniform(3, 15), 1),  # m³/h/m² at 50Pa
            "GlazingType": lambda _: random.choice(['Single', 'Double', 'Triple', 'Secondary glazing', 'Mixed types', 'Low-E coated', 'Solar control']),
            "WindowFrameType": lambda _: random.choice(['uPVC', 'Timber', 'Aluminum', 'Composite', 'Steel', 'Mixed materials']),
            "DoorType": lambda _: random.choice(['uPVC', 'Timber', 'Composite', 'Aluminum', 'Steel', 'Mixed materials', 'Traditional']),
            "SmartMeterType": lambda _: random.choice(['None', 'Basic meter', 'Smart meter', 'Smart meter with export capability', 'Smart prepayment']),
        
            # ProtectionMeasures.ResilienceMeasures (15 boolean fields)
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
            
            # ProtectionMeasures.NaturalMeasures (6 boolean fields)
            "TreePlanting": lambda _: random.choice([True, False]),
            "RainGarden": lambda _: random.choice([True, False]),
            "GreenRoof": lambda _: random.choice([True, False]),
            "Wetlands": lambda _: random.choice([True, False]),
            "NaturalDrainage": lambda _: random.choice([True, False]),
            "VegetationManagement": lambda _: random.choice([True, False]),
            
            # Number fields
            "PropertyValue": lambda info: self._calculate_property_value(info),
            "GroundLevelMeters": lambda info: info['elevation'],  # Always use actual elevation
            "elevation": lambda info: info['elevation'],
            "RiverDistanceMeters": lambda info: info.get('distance_to_thames', random.uniform(100, 5000)),
            
            # Integer fields
            "ConstructionYear": lambda _: self._generate_construction_year(),
            "NumberOfStoreys": lambda info: 1 if info.get('property_type') == 'Flat' else random.randint(1, 4),
            
            # EnergyPerformance.EnergyUsage (9 fields)
            "TariffType": lambda _: random.choice(['Wood Fire', 'Gas', 'Electricity', 'Both']),
            "AnnualCarbonKgCO2e": lambda info: self._calculate_carbon_emissions(info),
            "HeatingSystem": lambda _: random.choice(['Gas central heating', 'Electric heating', 'Heat pump', 'Oil heating', 'Other']),
            "RenewableSystem": lambda _: random.choice(['None', 'Solar PV', 'Solar thermal', 'Heat pump', 'Multiple']),
            "AnnualEnergyKwh": lambda info: self._calculate_annual_energy(info),
            "GridElectricityKwh": lambda info: self._calculate_grid_electricity(info),
            "GasUsageKwh": lambda info: self._calculate_gas_usage(info),
            "SolarGenerationKwh": lambda info: self._calculate_solar_generation(info),
            "AnnualEnergyBill": lambda info: self._calculate_energy_bill(info),
            
            # EnergyPerformance.Ratings (3 fields)
            "EPCRating": lambda _: random.choice(['A', 'B', 'C', 'D', 'E', 'F', 'G']),
            "CarbonRating": lambda _: random.choice(['A+', 'A', 'B', 'C', 'D', 'E', 'F']),
            "EmissionsScore": lambda _: random.choice(['Excellent', 'Good', 'Fair', 'Poor', 'Very poor']),
            
            # History.EnvironmentalIssues (4 fields)
            "AirQuality": lambda _: random.choice(['Low', 'Moderate', 'High', 'Very high', 'Exceeds limits']),
            "WaterQuality": lambda _: random.choice(['Excellent', 'Good', 'Fair', 'Poor', 'Very poor']),
            "NoisePollution": lambda _: random.choice(['None', 'Traffic', 'Planes', 'Train']),
            "LastEnvironmentalIssueDate": lambda _: self._generate_past_date(days_range=(365, 365*5)),
            
            # History.FireIncidents (2 fields)
            "FireDamageSeverity": lambda _: random.choice(['None', 'Minor', 'Moderate', 'Severe', 'Total loss']),
            "LastFireDate": lambda _: self._generate_past_date(days_range=(365*2, 365*10)) if random.random() < 0.1 else None,
            
            # History.FloodEvents (3 fields)
            "FloodReturnPeriod": lambda _: random.choice([50, 100, 200, 500, 1000]),
            "FloodDamageSeverity": lambda _: random.choice(['No damage', 'Minor damage', 'Moderate damage', 'Significant damage', 'Severe damage']),
            "LastFloodDateHistory": lambda _: self._generate_past_date(days_range=(365, 365*15)) if random.random() < 0.2 else None,
            
            # History.GroundConditions (4 fields)
            "SubsidenceStatus": lambda _: random.choice(['No issues', 'Minor movement', 'Moderate subsidence', 'Severe subsidence', 'Under investigation']),
            "ContaminationStatus": lambda _: random.choice(['None detected', 'Historical industrial', 'Remediated', 'Current contamination', 'Under investigation']),
            "GroundStability": lambda _: random.choice(['Stable', 'Minor concerns', 'Moderate risk', 'High risk', 'Active movement']),
            "LastGroundIssueDate": lambda _: self._generate_past_date(days_range=(365*2, 365*20)) if random.random() < 0.05 else None,
            
            # TransactionHistory.Rental (4 fields)
            "RentalHistory": lambda _: random.choice(['Never rented', 'Previously rented', 'Currently rented', 'Mixed use history']),
            "MonthlyRentGbp": lambda info: self._calculate_monthly_rent(info),
            "VacancyCount": lambda _: random.randint(0, 5),
            "TenancyDuration": lambda _: random.choice(['0-6 months', '6-12 months', '12-24 months', '24-36 months', '36+ months']),
            
            # TransactionHistory.Sales (4 fields)
            "SalePriceGbp": lambda info: self._calculate_sale_price(info),
            "SaleDate": lambda _: self._generate_past_date(days_range=(30, 365*3)),
            "PreviousOwner": lambda _: self._generate_owner_name(),
            "MarketingDays": lambda _: random.randint(14, 365),
            
            # Date fields
            "PropertyValue": lambda info: self._calculate_property_value(info),
            "dateCreated": lambda _: datetime.now().strftime('%Y-%m-%d'),
            "lastUpdated": lambda _: datetime.now().strftime('%Y-%m-%d'),
            "ValuationDate": lambda _: (datetime.now() - timedelta(days=random.randint(0, 365))).strftime('%Y-%m-%d'),
        }


    # Small utility functions
    def _generate_postcode(self):
        """Generate a UK-style postcode."""
        area_code = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=2))
        district = random.randint(1, 99)
        sector = random.randint(1, 9)
        unit = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=2))
        return f"{area_code}{district} {sector}{unit}"
    
    def _generate_construction_year(self):
        """Generate a realistic construction year based on era distribution."""
        era = random.choices(
            ['pre-1900', '1900-1950', '1950-1980', '1980-2000', 'post-2000'],
            weights=[0.1, 0.2, 0.3, 0.25, 0.15]
        )[0]
        
        if era == 'pre-1900':
            return random.randint(1800, 1900)
        elif era == '1900-1950':
            return random.randint(1900, 1950)
        elif era == '1950-1980':
            return random.randint(1950, 1980)
        elif era == '1980-2000':
            return random.randint(1980, 2000)
        else:  # post-2000
            return random.randint(2000, 2022)
    
    def _calculate_property_value(self, location_info):
        """Calculate property value based on location, property type, area, and other factors."""
        
        # Get basic property characteristics
        property_type = location_info.get('property_type', 'Flat')
        area = location_info.get('property_area', None)
        value_factor = location_info.get('value_factor', 1.0)
        
        # If area not yet calculated, calculate it first
        if area is None:
            area = self._calculate_property_area(location_info)
            location_info['property_area'] = area
        
        # Base price per square meter by property type (London averages)
        price_per_sqm = {
            'Detached': random.uniform(8000, 15000),      # £8k-15k per m²
            'Semi-detached': random.uniform(6500, 12000), # £6.5k-12k per m²
            'Mid-terrace': random.uniform(6000, 11000),   # £6k-11k per m²
            'End-terrace': random.uniform(6200, 11500),   # £6.2k-11.5k per m²
            'Bungalow': random.uniform(7000, 13000),      # £7k-13k per m²
            'Flat': random.uniform(5500, 10000)           # £5.5k-10k per m²
        }
        
        base_price_per_sqm = price_per_sqm.get(property_type, 7000)
        
        # Calculate base value from area
        base_value = area * base_price_per_sqm
        
        # Apply location value factor (area premium/discount)
        location_adjusted_value = base_value * value_factor
        
        # Additional factors affecting property value
        
        # Age factor (newer and period properties can command premium)
        construction_year = location_info.get('construction_year', random.randint(1950, 2020))
        current_year = 2025
        age = current_year - construction_year
        
        if age < 10:  # New build premium
            age_factor = random.uniform(1.05, 1.15)
        elif age < 25:  # Modern property
            age_factor = random.uniform(0.95, 1.05)
        elif age < 50:  # Established property
            age_factor = random.uniform(0.90, 1.0)
        elif age < 100:  # Older property
            age_factor = random.uniform(0.85, 0.95)
        else:  # Period property (can be premium or discount)
            age_factor = random.uniform(0.8, 1.2)  # Wide range for period properties
        
        # Condition factor
        condition = location_info.get('property_condition', random.choice(['Excellent', 'Good', 'Fair', 'Poor', 'Very poor']))
        condition_factors = {
            'Excellent': random.uniform(1.1, 1.2),
            'Good': random.uniform(1.0, 1.1),
            'Fair': random.uniform(0.9, 1.0),
            'Poor': random.uniform(0.7, 0.9),
            'Very poor': random.uniform(0.5, 0.7)
        }
        condition_factor = condition_factors.get(condition, 1.0)
        
        # Flood risk factor (affects value negatively)
        flood_risk = location_info.get('flood_risk', random.choice(['Very Low', 'Low', 'Medium', 'High', 'Very High']))
        flood_risk_factors = {
            'Very Low': random.uniform(1.0, 1.02),
            'Low': random.uniform(0.98, 1.0),
            'Medium': random.uniform(0.92, 0.98),
            'High': random.uniform(0.85, 0.92),
            'Very High': random.uniform(0.75, 0.85)
        }
        flood_risk_factor = flood_risk_factors.get(flood_risk, 1.0)
        
        # Energy efficiency factor (EPC rating affects value)
        epc_rating = location_info.get('epc_rating', random.choice(['A', 'B', 'C', 'D', 'E', 'F', 'G']))
        epc_factors = {
            'A': random.uniform(1.05, 1.1),
            'B': random.uniform(1.02, 1.05),
            'C': random.uniform(1.0, 1.02),
            'D': random.uniform(0.98, 1.0),
            'E': random.uniform(0.95, 0.98),
            'F': random.uniform(0.90, 0.95),
            'G': random.uniform(0.85, 0.90)
        }
        epc_factor = epc_factors.get(epc_rating, 1.0)
        
        # Thames proximity factor (closer to river can be premium but also flood risk)
        thames_distance = location_info.get('distance_to_thames', 1000)
        if thames_distance < 200:  # Very close to Thames
            if flood_risk in ['Very Low', 'Low']:
                proximity_factor = random.uniform(1.05, 1.15)  # River view premium
            else:
                proximity_factor = random.uniform(0.90, 1.05)  # Flood risk concern
        elif thames_distance < 500:  # Close to Thames
            proximity_factor = random.uniform(0.95, 1.1)
        else:  # Further from Thames
            proximity_factor = random.uniform(0.98, 1.02)
        
        # Calculate final value
        final_value = (location_adjusted_value * 
                    age_factor * 
                    condition_factor * 
                    flood_risk_factor * 
                    epc_factor * 
                    proximity_factor)
        
        # Add some random variation (±5%)
        final_value *= random.uniform(0.95, 1.05)
        
        # Ensure reasonable bounds (London property values)
        final_value = max(150000, min(5000000, final_value))
        
        return round(final_value, 2)

    def _calculate_sale_price(self, location_info):
        """Calculate historical sale price based on current value and market conditions."""
        current_value = location_info.get('property_value')
        
        if current_value is None:
            current_value = self._calculate_property_value(location_info)
        
        # Historical price factor based on how long ago it was sold
        sale_date_str = location_info.get('sale_date')
        if sale_date_str:
            try:
                sale_date = datetime.strptime(sale_date_str, '%Y-%m-%d')
                years_ago = (datetime.now() - sale_date).days / 365.25
            except:
                years_ago = random.uniform(0.5, 3.0)
        else:
            years_ago = random.uniform(0.5, 3.0)
        
        # UK property price appreciation (average 3-7% per year, but volatile)
        if years_ago < 1:
            # Very recent sale, similar to current value
            historical_factor = random.uniform(0.95, 1.05)
        elif years_ago < 2:
            # 1-2 years ago, modest appreciation
            annual_growth = random.uniform(0.02, 0.08)
            historical_factor = (1 + annual_growth) ** (-years_ago)
        else:
            # Older sale, more significant appreciation but also more volatile
            annual_growth = random.uniform(-0.05, 0.12)  # Can include market downturns
            historical_factor = (1 + annual_growth) ** (-years_ago)
        
        # Market conditions factor (boom/bust cycles)
        market_condition = random.choice(['boom', 'normal', 'recession'])
        if market_condition == 'boom':
            market_factor = random.uniform(0.85, 0.95)  # Sold before boom
        elif market_condition == 'recession':
            market_factor = random.uniform(1.05, 1.25)  # Sold before recession
        else:
            market_factor = random.uniform(0.95, 1.05)  # Normal market
        
        historical_price = current_value * historical_factor * market_factor
        
        # Ensure reasonable bounds
        historical_price = max(50000, min(8000000, historical_price))
        
        return round(historical_price, 2)

    def _calculate_monthly_rent(self, location_info):
        """Calculate monthly rent based on property value, area, and local factors."""
        property_value = location_info.get('property_value')
        area = location_info.get('property_area')
        property_type = location_info.get('property_type', 'Flat')
        
        if property_value is None:
            property_value = self._calculate_property_value(location_info)
        
        if area is None:
            area = self._calculate_property_area(location_info)
        
        # Calculate rent using multiple approaches and average them
        
        # Approach 1: Rental yield method (4-8% annual yield)
        base_yield = {
            'Flat': random.uniform(0.04, 0.07),           # 4-7% yield
            'Mid-terrace': random.uniform(0.045, 0.065),  # 4.5-6.5% yield
            'End-terrace': random.uniform(0.045, 0.065),  # 4.5-6.5% yield
            'Semi-detached': random.uniform(0.04, 0.06),  # 4-6% yield
            'Detached': random.uniform(0.035, 0.055),     # 3.5-5.5% yield
            'Bungalow': random.uniform(0.04, 0.06)        # 4-6% yield
        }
        
        yield_rate = base_yield.get(property_type, 0.05)
        rent_from_yield = (property_value * yield_rate) / 12
        
        # Approach 2: Price per square meter method
        rent_per_sqm = {
            'Flat': random.uniform(25, 50),           # £25-50 per m² per month
            'Mid-terrace': random.uniform(20, 40),    # £20-40 per m² per month
            'End-terrace': random.uniform(22, 42),    # £22-42 per m² per month
            'Semi-detached': random.uniform(18, 35),  # £18-35 per m² per month
            'Detached': random.uniform(15, 30),       # £15-30 per m² per month
            'Bungalow': random.uniform(18, 35)        # £18-35 per m² per month
        }
        
        sqm_rate = rent_per_sqm.get(property_type, 30)
        rent_from_area = area * sqm_rate
        
        # Average the two approaches
        base_rent = (rent_from_yield + rent_from_area) / 2
        
        # Apply local factors
        value_factor = location_info.get('value_factor', 1.0)
        base_rent *= value_factor
        
        # Transport links factor (London-specific)
        transport_factor = random.uniform(0.9, 1.2)  # Varies by transport accessibility
        base_rent *= transport_factor
        
        # Property condition factor
        condition = location_info.get('property_condition', 'Good')
        condition_factors = {
            'Excellent': random.uniform(1.1, 1.2),
            'Good': random.uniform(1.0, 1.1),
            'Fair': random.uniform(0.9, 1.0),
            'Poor': random.uniform(0.7, 0.9),
            'Very poor': random.uniform(0.5, 0.7)
        }
        condition_factor = condition_factors.get(condition, 1.0)
        base_rent *= condition_factor
        
        # Furnished/unfurnished factor (assume some are furnished)
        if random.random() < 0.3:  # 30% furnished
            furnished_factor = random.uniform(1.1, 1.3)
        else:
            furnished_factor = 1.0
        base_rent *= furnished_factor
        
        # Market demand factor
        demand_factor = random.uniform(0.9, 1.15)
        base_rent *= demand_factor
        
        # Ensure reasonable bounds for London
        base_rent = max(800, min(15000, base_rent))  # £800-£15k per month
        
        return round(base_rent, 2)

    def _calculate_insurance_premium(self, location_info):
        """Calculate insurance premium based on property value, risk factors, and characteristics."""
        property_value = location_info.get('property_value')
        area = location_info.get('property_area')
        property_type = location_info.get('property_type', 'Flat')
        
        if property_value is None:
            property_value = self._calculate_property_value(location_info)
        
        if area is None:
            area = self._calculate_property_area(location_info)
        
        # Base premium calculation (buildings insurance)
        # Typical rate: £1.50-£4.00 per £1000 of property value
        base_rate_per_1000 = random.uniform(1.5, 4.0)
        base_premium = (property_value / 1000) * base_rate_per_1000
        
        # Property type factor
        type_factors = {
            'Flat': random.uniform(0.8, 1.0),         # Lower risk (shared structure)
            'Mid-terrace': random.uniform(0.9, 1.1),  # Average risk
            'End-terrace': random.uniform(1.0, 1.2),  # Slightly higher (exposed wall)
            'Semi-detached': random.uniform(1.1, 1.3), # Higher risk
            'Detached': random.uniform(1.2, 1.5),     # Highest risk (standalone)
            'Bungalow': random.uniform(1.0, 1.2)      # Moderate risk
        }
        type_factor = type_factors.get(property_type, 1.0)
        
        # Flood risk factor (major impact on premiums)
        flood_risk = location_info.get('flood_risk', 'Low')
        flood_risk_factors = {
            'Very Low': random.uniform(0.9, 1.0),
            'Low': random.uniform(1.0, 1.2),
            'Medium': random.uniform(1.3, 1.8),
            'High': random.uniform(1.8, 2.5),
            'Very High': random.uniform(2.5, 4.0)
        }
        flood_factor = flood_risk_factors.get(flood_risk, 1.0)
        
        # Construction age factor
        construction_year = location_info.get('construction_year', 1980)
        current_year = 2025
        age = current_year - construction_year
        
        if age < 10:  # New build
            age_factor = random.uniform(0.8, 0.9)
        elif age < 30:  # Modern
            age_factor = random.uniform(0.9, 1.0)
        elif age < 100:  # Older
            age_factor = random.uniform(1.0, 1.3)
        else:  # Period property
            age_factor = random.uniform(1.2, 1.8)
        
        # Construction type factor
        construction_type = location_info.get('construction_type', 'Brick')
        construction_factors = {
            'Brick': random.uniform(0.9, 1.0),
            'Stone': random.uniform(0.9, 1.0),
            'Concrete': random.uniform(0.95, 1.05),
            'Timber Frame': random.uniform(1.1, 1.3),
            'Modern methods': random.uniform(0.85, 0.95)
        }
        construction_factor = construction_factors.get(construction_type, 1.0)
        
        # Area factor (larger properties cost more to rebuild)
        if area < 50:
            area_factor = random.uniform(0.9, 1.0)
        elif area < 100:
            area_factor = random.uniform(1.0, 1.1)
        elif area < 200:
            area_factor = random.uniform(1.1, 1.2)
        else:
            area_factor = random.uniform(1.2, 1.4)
        
        # Security features factor (assume some properties have better security)
        if random.random() < 0.3:  # 30% have good security
            security_factor = random.uniform(0.85, 0.95)
        else:
            security_factor = 1.0
        
        # Claims history factor (random previous claims)
        if random.random() < 0.15:  # 15% have previous claims
            claims_factor = random.uniform(1.2, 1.8)
        else:
            claims_factor = random.uniform(0.95, 1.05)
        
        # Calculate final premium
        final_premium = (base_premium * 
                        type_factor * 
                        flood_factor * 
                        age_factor * 
                        construction_factor * 
                        area_factor * 
                        security_factor * 
                        claims_factor)
        
        # Add contents insurance (optional, ~30% of buildings insurance)
        if random.random() < 0.8:  # 80% include contents
            contents_premium = final_premium * random.uniform(0.2, 0.4)
            final_premium += contents_premium
        
        # Ensure reasonable bounds
        final_premium = max(200, min(20000, final_premium))  # £200-£20k per year
        
        return round(final_premium, 2)

    def generate_location_data(self, count=100):
        """Generate Thames-aligned property locations."""
        try:
            return generate_synchronized_locations(count)
        except Exception as e:
            print(f"Warning: Could not use Thames-aligned locations: {e}")
            return self._generate_simple_locations(count)
    
    def _generate_simple_locations(self, count):
        """Generate simple London locations if generate_synchronized_locations is not available."""
        locations = []
        
        for i in range(count):
            # Select a random London area
            area_name = random.choice(LONDON_AREAS)
            
            # Generate coordinates around London
            # Central London: roughly 51.48-51.52°N, 0.12°W-0.15°E
            lat = random.uniform(51.48, 51.52)
            lon = random.uniform(-0.12, 0.15)
            
            # Simulate distance to Thames (closer for areas known to be riverside)
            riverside_areas = ["Chelsea", "Westminster", "Tower Hamlets", "Southwark", "Lambeth"]
            if area_name in riverside_areas:
                distance_to_thames = random.uniform(50, 500)
            else:
                distance_to_thames = random.uniform(500, 3000)
            
            # Simulate elevation (lower near the river)
            if distance_to_thames < 200:
                elevation = random.uniform(4, 8)
            elif distance_to_thames < 500:
                elevation = random.uniform(8, 15)
            else:
                elevation = random.uniform(15, 50)
            
            # Select a street in this area
            street = random.choice(LONDON_STREETS.get(area_name, ["High Street"]))
            
            # Get value factor for this area
            value_factor = AREA_VALUE_FACTORS.get(area_name, 1.0)
            
            locations.append({
                "name": area_name,
                "lat": lat,
                "lon": lon,
                "value_factor": value_factor,
                "distance_to_thames": distance_to_thames,
                "elevation": elevation,
                "street": street
            })
        
        return locations
    
    def get_location_info(self, location_data):
        """Enhance location data with property type and elevation."""
        location_info = location_data.copy()
        
        # Add property type
        location_info["property_type"] = random.choices(
            self.property_types, 
            weights=self.property_type_weights
        )[0]
        
        # Get elevation - now simple!
        elevation = get_elevation(location_info['lat'], location_info['lon'])
        if elevation is None:
            # Fallback calculation based on distance from Thames
            distance = location_info.get('distance_to_thames', 1000)
            elevation = 5.0 + (distance / 1000) * 10  # Simple linear increase
        
        location_info['elevation'] = elevation
        location_info['ground_level_meters'] = elevation  # Same as elevation for ground level
        return location_info

    # Schema population functions
    def generate_random_value(self, field_name, field_type, location_info):
        """Generate a random value based on field name and type."""
        # Check if we have a specific generator for this field
        if field_name in self.field_generators:
            return self.field_generators[field_name](location_info)
        
        # Handle special fields
        if field_name == "StreetName" and "street" in location_info:
            return location_info["street"]
        elif field_name == "BuildingNumber":
            return str(random.randint(1, 200))
        elif field_name == "TownCity" and "name" in location_info:
            return location_info["name"]
        elif field_name == "LatitudeDegrees" and "lat" in location_info:
            return location_info["lat"]
        elif field_name == "LongitudeDegrees" and "lon" in location_info:
            return location_info["lon"]
        elif field_name == "PropertyType" and "property_type" in location_info:
            return location_info["property_type"]
        elif field_name == "ThamesProximityMeters" and "distance_to_thames" in location_info:
            return location_info["distance_to_thames"]
        elif field_name == "GroundLevelMeters" in location_info:
            return location_info["GroundLevelMeters"]
        elif field_name == "elevation" in location_info:
            return location_info["elevation"]
        
        # Generic random values based on type
        if field_type == "string":
            return ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=8))
        elif field_type == "number":
            return random.uniform(0, 100)
        elif field_type == "integer":
            return random.randint(1, 100)
        elif field_type == "boolean":
            return random.choice([True, False])
        elif field_type == "date":
            days_ago = random.randint(0, 365 * 3)
            random_date = datetime.now() - timedelta(days=days_ago)
            return random_date.strftime('%Y-%m-%d')
        elif field_type == "array":
            # Return a small array with random strings
            return [''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=5)) for _ in range(random.randint(0, 3))]
        else:
            return None
    
    def populate_schema(self, schema, location_info):
        """Recursively populate the schema with random data."""
        if not isinstance(schema, dict):
            return {}
        
        result = {}
        
        for key, value in schema.items():
            # Skip metadata fields
            if key in ['type', 'options', 'description', 'values']:
                continue
            
            # Handle nested objects
            if isinstance(value, dict) and 'type' not in value:
                result[key] = self.populate_schema(value, location_info)
            # Handle fields with type
            elif isinstance(value, dict) and 'type' in value:
                field_type = value['type']
                result[key] = self.generate_random_value(key, field_type, location_info)
            # Handle arrays
            elif isinstance(value, dict) and key == 'items' and 'type' in value:
                # Generate 0-3 items for array
                num_items = random.randint(0, 3)
                items = []
                for _ in range(num_items):
                    items.append(self.generate_random_value(key, value['type'], location_info))
                result = items
            
        return result
    
    def ensure_required_fields(self, property_data, location_info):
        """Ensure all required fields are set correctly for complete CDM compliance."""
        
        # Initialize all nested structures
        if 'PropertyHeader' not in property_data:
            property_data['PropertyHeader'] = {}
        
        sections = ['Header', 'PropertyAttributes', 'Construction', 'Location', 'RiskAssessment']
        for section in sections:
            if section not in property_data['PropertyHeader']:
                property_data['PropertyHeader'][section] = {}
        
        if 'ProtectionMeasures' not in property_data:
            property_data['ProtectionMeasures'] = {}
        
        protection_sections = ['RiskAssessment', 'ResilienceMeasures', 'NaturalMeasures']
        for section in protection_sections:
            if section not in property_data['ProtectionMeasures']:
                property_data['ProtectionMeasures'][section] = {}
        
        if 'EnergyPerformance' not in property_data:
            property_data['EnergyPerformance'] = {}
        
        energy_sections = ['BuildingFabric', 'EnergyUsage', 'Ratings']
        for section in energy_sections:
            if section not in property_data['EnergyPerformance']:
                property_data['EnergyPerformance'][section] = {}
        
        if 'History' not in property_data:
            property_data['History'] = {}
        
        history_sections = ['EnvironmentalIssues', 'FireIncidents', 'FloodEvents', 'GroundConditions']
        for section in history_sections:
            if section not in property_data['History']:
                property_data['History'][section] = {}
        
        if 'TransactionHistory' not in property_data:
            property_data['TransactionHistory'] = {}
        
        transaction_sections = ['Rental', 'Sales']
        for section in transaction_sections:
            if section not in property_data['TransactionHistory']:
                property_data['TransactionHistory'][section] = {}

        # Calculate basic properties first (dependencies for other calculations)
        location_info['property_area'] = self.field_generators['PropertyAreaSqm'](location_info)
        location_info['construction_year'] = self._generate_construction_year()
        location_info['property_condition'] = self.field_generators['PropertyCondition'](location_info)
        location_info['flood_risk'] = self.field_generators['OverallFloodRisk'](location_info)
        location_info['epc_rating'] = self.field_generators['EPCRating'](location_info)
        location_info['construction_type'] = self.field_generators['ConstructionType'](location_info)

        # Calculate dependent values
        location_info['property_value'] = self.field_generators['PropertyValue'](location_info)

        # PropertyHeader.Header
        property_data['PropertyHeader']['Header']['PropertyID'] = location_info['prop_id']
        property_data['PropertyHeader']['Header']['UPRN'] = self.field_generators['UPRN'](location_info)
        property_data['PropertyHeader']['Header']['propertyType'] = 'Residential'
        property_data['PropertyHeader']['Header']['propertyStatus'] = 'Active'
        property_data['PropertyHeader']['Header']['dateCreated'] = self.field_generators['dateCreated'](location_info)
        property_data['PropertyHeader']['Header']['lastUpdated'] = self.field_generators['lastUpdated'](location_info)
        # Add to PropertyHeader.PropertyAttributes section
        property_data['PropertyHeader']['PropertyAttributes']['PropertyResi'] = self.field_generators['PropertyResi'](location_info)
        property_data['PropertyHeader']['PropertyAttributes']['OccupancyResidency'] = self.field_generators['OccupancyResidency'](location_info)  
        property_data['PropertyHeader']['PropertyAttributes']['HeightMeters'] = self.field_generators['HeightMeters'](location_info)

        # PropertyHeader.PropertyAttributes
        property_data['PropertyHeader']['PropertyAttributes']['PropertyAreaSqm'] = location_info['property_area']
        property_data['PropertyHeader']['PropertyAttributes']['PropertyType'] = location_info['property_type']
        property_data['PropertyHeader']['PropertyAttributes']['OccupancyType'] = self.field_generators['OccupancyType'](location_info)
        property_data['PropertyHeader']['PropertyAttributes']['RenovationRequired'] = self.field_generators['RenovationRequired'](location_info)
        property_data['PropertyHeader']['PropertyAttributes']['PropertyCondition'] = location_info['property_condition']
        property_data['PropertyHeader']['PropertyAttributes']['HousingAssociation'] = random.choice([True, False])
        property_data['PropertyHeader']['PropertyAttributes']['IncomeGenerating'] = self.field_generators['IncomeGenerating'](location_info)
        property_data['PropertyHeader']['PropertyAttributes']['PayingBusinessRates'] = random.choice([True, False])
        property_data['PropertyHeader']['PropertyAttributes']['BuildingResidency'] = self.field_generators['BuildingResidency'](location_info)
        property_data['PropertyHeader']['PropertyAttributes']['NumberBedrooms'] = random.randint(1, 6)
        property_data['PropertyHeader']['PropertyAttributes']['NumberBathrooms'] = random.randint(1, 4)
        property_data['PropertyHeader']['PropertyAttributes']['TotalRooms'] = random.randint(3, 12)
        property_data['PropertyHeader']['PropertyAttributes']['NumberOfStoreys'] = random.randint(1, 4)
        property_data['PropertyHeader']['PropertyAttributes']['ConstructionYear'] = location_info['construction_year']
        property_data['PropertyHeader']['PropertyAttributes']['PropertyPeriod'] = self._get_property_period(location_info['construction_year'])
        property_data['PropertyHeader']['PropertyAttributes']['CouncilTaxBand'] = random.choice(['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'])
        property_data['PropertyHeader']['PropertyAttributes']['GardenAreaFront'] = random.uniform(0, 100) if random.random() < 0.6 else None
        property_data['PropertyHeader']['PropertyAttributes']['GardenAreaBack'] = random.uniform(0, 200) if random.random() < 0.7 else None
        property_data['PropertyHeader']['PropertyAttributes']['ParkingType'] = random.choice(['None', 'On-street only', 'Driveway only', 'Garage only', 'Driveway and garage', 'Allocated space'])
        property_data['PropertyHeader']['PropertyAttributes']['AccessType'] = random.choice(['Public road', 'Private road', 'Shared access', 'Right of way'])
        property_data['PropertyHeader']['PropertyAttributes']['LastMajorWorksDate'] = self._generate_past_date(days_range=(365, 365*10))

        # PropertyHeader.Construction
        property_data['PropertyHeader']['Construction']['ConstructionType'] = location_info['construction_type']
        property_data['PropertyHeader']['Construction']['ConstructionYear'] = location_info['construction_year']
        property_data['PropertyHeader']['Construction']['FoundationType'] = random.choice(['Strip foundations', 'Raft foundations', 'Pile foundations', 'Deep foundations', 'Unknown'])
        property_data['PropertyHeader']['Construction']['FloorType'] = random.choice(['Suspended timber', 'Solid concrete', 'Suspended concrete', 'Beam and block', 'Mixed'])
        property_data['PropertyHeader']['Construction']['SiteHeight'] = random.uniform(0, 5) if random.random() < 0.1 else None
        property_data['PropertyHeader']['Construction']['PropertyHeight'] = random.uniform(6, 25)
        property_data['PropertyHeader']['Construction']['FloorLevelMeters'] = random.uniform(0.1, 2.0)
        property_data['PropertyHeader']['Construction']['BasementPresent'] = random.choice([True, False])

        # PropertyHeader.Location
        property_data['PropertyHeader']['Location']['BuildingName'] = None  # Mostly houses don't have building names
        property_data['PropertyHeader']['Location']['BuildingNumber'] = str(random.randint(1, 200))
        property_data['PropertyHeader']['Location']['SubBuildingNumber'] = None
        property_data['PropertyHeader']['Location']['SubBuildingName'] = None
        property_data['PropertyHeader']['Location']['StreetName'] = location_info.get('street', 'High Street')
        property_data['PropertyHeader']['Location']['AddressLine2'] = None
        property_data['PropertyHeader']['Location']['TownCity'] = location_info['name']
        property_data['PropertyHeader']['Location']['County'] = 'Greater London'
        property_data['PropertyHeader']['Location']['Postcode'] = self._generate_postcode()
        property_data['PropertyHeader']['Location']['USRN'] = str(random.randint(10000000, 99999999))
        property_data['PropertyHeader']['Location']['LocalAuthority'] = location_info['name'] + ' Council'
        property_data['PropertyHeader']['Location']['ElectoralWard'] = location_info['name'] + ' Ward'
        property_data['PropertyHeader']['Location']['ParliamentaryConstituency'] = location_info['name'] + ' and ' + random.choice(['North', 'South', 'East', 'West'])
        property_data['PropertyHeader']['Location']['Country'] = 'England'
        property_data['PropertyHeader']['Location']['Region'] = 'London'
        property_data['PropertyHeader']['Location']['UrbanRuralClassification'] = 'Urban'
        property_data['PropertyHeader']['Location']['LocalDensityHectare'] = random.uniform(50, 200)
        property_data['PropertyHeader']['Location']['LatitudeDegrees'] = location_info['lat']
        property_data['PropertyHeader']['Location']['LongitudeDegrees'] = location_info['lon']
        property_data['PropertyHeader']['Location']['BritishNationalGrid'] = self._generate_grid_reference(location_info['lat'], location_info['lon'])
        property_data['PropertyHeader']['Location']['What3Words'] = f"{random.choice(['happy', 'sunny', 'bright'])}.{random.choice(['river', 'street', 'park'])}.{random.choice(['home', 'place', 'spot'])}"

        # PropertyHeader.RiskAssessment
        property_data['PropertyHeader']['RiskAssessment']['EAFloodZone'] = random.choice(['Zone 1', 'Zone 2', 'Zone 3a', 'Zone 3b'])
        property_data['PropertyHeader']['RiskAssessment']['OverallFloodRisk'] = location_info['flood_risk']
        property_data['PropertyHeader']['RiskAssessment']['FloodRiskType'] = random.choice(['River', 'Surface water', 'Groundwater', 'Coastal', 'Multiple'])
        property_data['PropertyHeader']['RiskAssessment']['LastFloodDate'] = self._generate_past_date(days_range=(365*2, 365*20)) if random.random() < 0.15 else None
        property_data['PropertyHeader']['RiskAssessment']['SoilType'] = random.choice(['Clay', 'Sandy', 'Loamy', 'Chalk', 'Peat', 'Rocky', 'Mixed', 'Subsoils', 'Unknown'])
        property_data['PropertyHeader']['RiskAssessment']['elevation'] = location_info['elevation']
        property_data['PropertyHeader']['RiskAssessment']['GroundLevelMeters'] = location_info['ground_level_meters']
        property_data['PropertyHeader']['RiskAssessment']['elevation'] = location_info['elevation']
        property_data['PropertyHeader']['RiskAssessment']['RiverDistanceMeters'] = location_info.get('distance_to_thames', 1000)
        property_data['PropertyHeader']['RiskAssessment']['LakeDistanceMeters'] = random.uniform(500, 5000) if random.random() < 0.3 else None
        property_data['PropertyHeader']['RiskAssessment']['CoastalDistanceMeters'] = random.uniform(20000, 100000)  # London is inland
        property_data['PropertyHeader']['RiskAssessment']['CanalDistanceMeters'] = random.uniform(100, 2000) if random.random() < 0.4 else None
        property_data['PropertyHeader']['RiskAssessment']['GovernmentDefenceScheme'] = random.choice([True, False])

        # Valuation section
        if 'Valuation' not in property_data['PropertyHeader']:
            property_data['PropertyHeader']['Valuation'] = {}
        property_data['PropertyHeader']['Valuation']['PropertyValue'] = location_info['property_value']

        # ProtectionMeasures.RiskAssessment
        property_data['ProtectionMeasures']['RiskAssessment']['InsuranceStatus'] = random.choice(['Uninsured', 'Standard cover', 'Flood Re supported', 'Specialist cover'])
        property_data['ProtectionMeasures']['RiskAssessment']['FloodReEligible'] = random.choice([True, False])
        property_data['ProtectionMeasures']['RiskAssessment']['InsurancePremium'] = self.field_generators['InsurancePremium'](location_info)
        property_data['ProtectionMeasures']['RiskAssessment']['ExcessAmount'] = self.field_generators['ExcessAmount'](location_info)
        property_data['ProtectionMeasures']['RiskAssessment']['RiskRating'] = self.field_generators['RiskRating'](location_info)

        # ProtectionMeasures.ResilienceMeasures (15 boolean fields)
        resilience_fields = [
            'FloodGates', 'FloodBarriers', 'SumpPump', 'NonReturnValves', 'WaterproofFlooring',
            'RaisedElectricals', 'WaterproofPlaster', 'FloodWarningSystem', 'DrainageImprovement',
            'SandBags', 'WaterButts', 'PermeablePaving', 'FloodProofDoors', 'FloodProofWindows', 'EmergencyKit'
        ]
        for field in resilience_fields:
            property_data['ProtectionMeasures']['ResilienceMeasures'][field] = self.field_generators[field](location_info)

        # ProtectionMeasures.NaturalMeasures (6 boolean fields)
        natural_fields = ['TreePlanting', 'RainGarden', 'GreenRoof', 'Wetlands', 'NaturalDrainage', 'VegetationManagement']
        for field in natural_fields:
            property_data['ProtectionMeasures']['NaturalMeasures'][field] = self.field_generators[field](location_info)

        # EnergyPerformance.BuildingFabric (15 fields)
        fabric_fields = [
            'WallConstruction', 'CavityInsulation', 'ThermalBridgeScore', 'LoftInsulationMm', 'RoofType',
            'FloorConstruction', 'FloorInsulation', 'HeatingSys', 'WaterHeating', 'LightingType',
            'AirTightnessScore', 'GlazingType', 'WindowFrameType', 'DoorType', 'SmartMeterType'
        ]
        for field in fabric_fields:
            property_data['EnergyPerformance']['BuildingFabric'][field] = self.field_generators[field](location_info)

        # EnergyPerformance.EnergyUsage (9 fields) - Calculate in dependency order
        location_info['renewable_system'] = self.field_generators['RenewableSystem'](location_info)
        location_info['annual_energy'] = self.field_generators['AnnualEnergyKwh'](location_info)
        location_info['grid_electricity'] = self.field_generators['GridElectricityKwh'](location_info)
        location_info['gas_usage'] = self.field_generators['GasUsageKwh'](location_info)
        location_info['solar_generation'] = self.field_generators['SolarGenerationKwh'](location_info)
        
        property_data['EnergyPerformance']['EnergyUsage']['TariffType'] = self.field_generators['TariffType'](location_info)
        property_data['EnergyPerformance']['EnergyUsage']['AnnualCarbonKgCO2e'] = self.field_generators['AnnualCarbonKgCO2e'](location_info)
        property_data['EnergyPerformance']['EnergyUsage']['HeatingSystem'] = self.field_generators['HeatingSystem'](location_info)
        property_data['EnergyPerformance']['EnergyUsage']['RenewableSystem'] = location_info['renewable_system']
        property_data['EnergyPerformance']['EnergyUsage']['AnnualEnergyKwh'] = location_info['annual_energy']
        property_data['EnergyPerformance']['EnergyUsage']['GridElectricityKwh'] = location_info['grid_electricity']
        property_data['EnergyPerformance']['EnergyUsage']['GasUsageKwh'] = location_info['gas_usage']
        property_data['EnergyPerformance']['EnergyUsage']['SolarGenerationKwh'] = location_info['solar_generation']
        property_data['EnergyPerformance']['EnergyUsage']['AnnualEnergyBill'] = self.field_generators['AnnualEnergyBill'](location_info)

        # EnergyPerformance.Ratings (3 fields)
        property_data['EnergyPerformance']['Ratings']['EPCRating'] = location_info['epc_rating']
        property_data['EnergyPerformance']['Ratings']['CarbonRating'] = self.field_generators['CarbonRating'](location_info)
        property_data['EnergyPerformance']['Ratings']['EmissionsScore'] = self.field_generators['EmissionsScore'](location_info)

        # History.EnvironmentalIssues (4 fields)
        property_data['History']['EnvironmentalIssues']['AirQuality'] = self.field_generators['AirQuality'](location_info)
        property_data['History']['EnvironmentalIssues']['WaterQuality'] = self.field_generators['WaterQuality'](location_info)
        property_data['History']['EnvironmentalIssues']['NoisePollution'] = self.field_generators['NoisePollution'](location_info)
        property_data['History']['EnvironmentalIssues']['LastEnvironmentalIssueDate'] = self.field_generators['LastEnvironmentalIssueDate'](location_info)

        # History.FireIncidents (2 fields)
        property_data['History']['FireIncidents']['FireDamageSeverity'] = self.field_generators['FireDamageSeverity'](location_info)
        property_data['History']['FireIncidents']['LastFireDate'] = self.field_generators['LastFireDate'](location_info)

        # History.FloodEvents (3 fields)
        property_data['History']['FloodEvents']['FloodReturnPeriod'] = self.field_generators['FloodReturnPeriod'](location_info)
        property_data['History']['FloodEvents']['FloodDamageSeverity'] = self.field_generators['FloodDamageSeverity'](location_info)
        property_data['History']['FloodEvents']['LastFloodDate'] = self.field_generators['LastFloodDateHistory'](location_info)

        # History.GroundConditions (4 fields)
        property_data['History']['GroundConditions']['SubsidenceStatus'] = self.field_generators['SubsidenceStatus'](location_info)
        property_data['History']['GroundConditions']['ContaminationStatus'] = self.field_generators['ContaminationStatus'](location_info)
        property_data['History']['GroundConditions']['GroundStability'] = self.field_generators['GroundStability'](location_info)
        property_data['History']['GroundConditions']['LastGroundIssueDate'] = self.field_generators['LastGroundIssueDate'](location_info)

        # TransactionHistory.Rental (4 fields)
        property_data['TransactionHistory']['Rental']['RentalHistory'] = self.field_generators['RentalHistory'](location_info)
        property_data['TransactionHistory']['Rental']['MonthlyRentGbp'] = self.field_generators['MonthlyRentGbp'](location_info)
        property_data['TransactionHistory']['Rental']['VacancyCount'] = self.field_generators['VacancyCount'](location_info)
        property_data['TransactionHistory']['Rental']['TenancyDuration'] = self.field_generators['TenancyDuration'](location_info)

        # TransactionHistory.Sales (4 fields)
        location_info['sale_date'] = self.field_generators['SaleDate'](location_info)
        property_data['TransactionHistory']['Sales']['SalePriceGbp'] = self.field_generators['SalePriceGbp'](location_info)
        property_data['TransactionHistory']['Sales']['SaleDate'] = location_info['sale_date']
        property_data['TransactionHistory']['Sales']['PreviousOwner'] = self.field_generators['PreviousOwner'](location_info)
        property_data['TransactionHistory']['Sales']['MarketingDays'] = self.field_generators['MarketingDays'](location_info)

    # Helper methods to add to your PropertyPortfolioGenerator class

    def _get_property_period(self, construction_year):
        """Get property period classification based on construction year"""
        if construction_year < 1919:
            return "Pre-1919"
        elif construction_year < 1945:
            return "1919-1944"
        elif construction_year < 1976:
            return "1945-1975"
        elif construction_year < 2000:
            return "1976-1999"
        elif construction_year < 2009:
            return "2000-2008"
        else:
            return "2009-Present"

    def _generate_grid_reference(self, lat, lon):
        """Generate a simplified OS Grid Reference"""
        # This is a simplified version - real OS grid refs are more complex
        letters = ['TQ', 'TL', 'SU', 'SK', 'SP', 'SZ']
        numbers = f"{random.randint(10000, 99999)}{random.randint(10000, 99999)}"
        return f"{random.choice(letters)}{numbers}"
    
    
    def validate_property(self, property_data):
        """Ensure all required fields are filled."""
        required_fields = [
            ('PropertyHeader', 'Header', 'PropertyID'),
            ('PropertyHeader', 'Location', 'TownCity'),
            ('PropertyHeader', 'PropertyAttributes', 'PropertyType'),
            ('PropertyHeader', 'Valuation', 'PropertyValue')
        ]

        for field_path in required_fields:
            value = property_data
            for key in field_path:
                value = value.get(key, {})
            if not value and not isinstance(value, (int, float, bool)):
                print(f"Warning: Missing required field: {'.'.join(field_path)}")

    def _calculate_property_area(self, location_info):
        """Calculate property floor area based on type and value"""
        property_type = location_info.get('property_type', 'Flat')
        base_areas = {
            'Flat': (35, 120),
            'Mid-terrace': (60, 180),
            'End-terrace': (70, 200),
            'Semi-detached': (80, 250),
            'Detached': (120, 400),
            'Bungalow': (80, 200)
        }
        min_area, max_area = base_areas.get(property_type, (50, 150))
        return round(random.uniform(min_area, max_area), 1)

    def _calculate_carbon_emissions(self, location_info):
        """Calculate annual carbon emissions based on property characteristics"""
        area = location_info.get('property_area', 100)
        base_emissions = area * random.uniform(25, 80)  # kg CO2e per m²
        return round(base_emissions, 1)

    def _calculate_annual_energy(self, location_info):
        """Calculate total annual energy consumption"""
        area = location_info.get('property_area', 100)
        base_consumption = area * random.uniform(120, 250)  # kWh per m²
        return round(base_consumption, 0)

    def _calculate_grid_electricity(self, location_info):
        """Calculate grid electricity usage"""
        total_energy = location_info.get('annual_energy', 15000)
        electricity_proportion = random.uniform(0.3, 0.8)
        return round(total_energy * electricity_proportion, 0)

    def _calculate_gas_usage(self, location_info):
        """Calculate gas usage"""
        total_energy = location_info.get('annual_energy', 15000)
        grid_electricity = location_info.get('grid_electricity', 6000)
        remaining = total_energy - grid_electricity
        return max(0, round(remaining * random.uniform(0.6, 1.0), 0))

    def _calculate_solar_generation(self, location_info):
        """Calculate solar generation if renewable system present"""
        renewable_system = location_info.get('renewable_system', 'None')
        if renewable_system in ['Solar PV', 'Multiple']:
            area = location_info.get('property_area', 100)
            # Assume 10-30% of roof area for solar panels
            solar_capacity = area * random.uniform(0.1, 0.3) * 150  # 150 kWh/m²/year
            return round(solar_capacity, 0)
        return 0

    def _calculate_energy_bill(self, location_info):
        """Calculate annual energy bill"""
        grid_electricity = location_info.get('grid_electricity', 6000)
        gas_usage = location_info.get('gas_usage', 9000)
        
        # UK average rates (approximate)
        electricity_rate = 0.30  # £/kWh
        gas_rate = 0.07  # £/kWh
        
        bill = (grid_electricity * electricity_rate) + (gas_usage * gas_rate)
        return round(bill, 2)

    def _generate_owner_name(self):
        """Generate a realistic previous owner name"""
        first_names = ['John', 'Jane', 'David', 'Johnny', 'Fearghal','Sarah', 'Michael', 'Emma', 'James', 'Lisa', 'Robert', 'Anna']
        last_names = ['Smith', 'Johnson', 'Mattimore','Kelly','Mcgoveran','Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez']
        return f"{random.choice(first_names)} {random.choice(last_names)}"

    def _generate_past_date(self, days_range=(30, 365)):
        """Generate a past date within specified range"""
        days_ago = random.randint(days_range[0], days_range[1])
        past_date = datetime.now() - timedelta(days=days_ago)
        return past_date.strftime('%Y-%m-%d')


    def quality_consistency_check(self, property_data, location_info):
        """
        Perform comprehensive quality and consistency checks on property data.
        Fixes logical inconsistencies to ensure realistic property data.
        
        Args:
            property_data: The property data dictionary to validate and fix
            location_info: Location information for context-aware fixes
            
        Returns:
            dict: The corrected property data
        """
        
        # 1. Fix Property Condition vs Renovation Required
        condition = property_data.get('PropertyHeader', {}).get('PropertyAttributes', {}).get('PropertyCondition')
        if condition in ['Excellent', 'Good']:
            # Properties in excellent/good condition rarely need renovation
            property_data['PropertyHeader']['PropertyAttributes']['RenovationRequired'] = False
        elif condition in ['Poor', 'Very poor']:
            # Poor condition properties usually need renovation
            property_data['PropertyHeader']['PropertyAttributes']['RenovationRequired'] = True
        # Fair condition can go either way - leave as randomly generated
        
        # 2. Fix Garden Areas for Flats
        property_type = property_data.get('PropertyHeader', {}).get('PropertyAttributes', {}).get('PropertyResi')
        if property_type == 'Flat':
            # Most flats don't have gardens unless ground floor
            if random.random() < 0.85:  # 85% of flats have no gardens
                property_data['PropertyHeader']['PropertyAttributes']['GardenAreaFront'] = None
                property_data['PropertyHeader']['PropertyAttributes']['GardenAreaBack'] = None
            else:
                # Ground floor flats might have small gardens
                if property_data['PropertyHeader']['PropertyAttributes']['GardenAreaFront']:
                    property_data['PropertyHeader']['PropertyAttributes']['GardenAreaFront'] = round(random.uniform(5, 25), 1)
                if property_data['PropertyHeader']['PropertyAttributes']['GardenAreaBack']:
                    property_data['PropertyHeader']['PropertyAttributes']['GardenAreaBack'] = round(random.uniform(10, 50), 1)
        
        # 3. Fix Energy Performance Consistency
        epc_rating = property_data.get('EnergyPerformance', {}).get('Ratings', {}).get('EPCRating')
        building_fabric = property_data.get('EnergyPerformance', {}).get('BuildingFabric', {})
        
        if epc_rating:
            # Align energy features with EPC rating
            if epc_rating in ['A', 'B']:  # Excellent efficiency
                building_fabric['LoftInsulationMm'] = random.choice([250, 300, 350])
                building_fabric['CavityInsulation'] = True
                building_fabric['GlazingType'] = random.choice(['Triple', 'Low-E coated'])
                building_fabric['LightingType'] = random.choice(['LED', 'Smart LED'])
                building_fabric['FloorInsulation'] = True
                
            elif epc_rating in ['C', 'D']:  # Good to average efficiency
                building_fabric['LoftInsulationMm'] = random.choice([150, 200, 250])
                building_fabric['CavityInsulation'] = random.choice([True, False])
                building_fabric['GlazingType'] = random.choice(['Double', 'Triple', 'Low-E coated'])
                building_fabric['LightingType'] = random.choice(['LED', 'Compact fluorescent'])
                building_fabric['FloorInsulation'] = random.choice([True, False])
                
            elif epc_rating == 'E':  # Below average efficiency
                building_fabric['LoftInsulationMm'] = random.choice([100, 150, 200])
                building_fabric['CavityInsulation'] = random.choice([True, False])
                building_fabric['GlazingType'] = random.choice(['Double', 'Single', 'Secondary glazing'])
                building_fabric['LightingType'] = random.choice(['Compact fluorescent', 'Halogen', 'Mixed types'])
                building_fabric['FloorInsulation'] = random.choice([True, False])
                
            else:  # F, G - Poor efficiency
                building_fabric['LoftInsulationMm'] = random.choice([0, 100])
                building_fabric['CavityInsulation'] = False
                building_fabric['GlazingType'] = random.choice(['Single', 'Double'])
                building_fabric['LightingType'] = random.choice(['Halogen', 'Traditional'])
                building_fabric['FloorInsulation'] = False
        
        # 4. Fix Energy Tariff vs Usage Consistency
        tariff_type = property_data.get('EnergyPerformance', {}).get('EnergyUsage', {}).get('TariffType')
        energy_usage = property_data.get('EnergyPerformance', {}).get('EnergyUsage', {})
        
        if tariff_type == 'Electricity':
            # Electricity-only tariff should have minimal or no gas usage
            energy_usage['GasUsageKwh'] = 0
            energy_usage['HeatingSystem'] = random.choice(['Electric heating', 'Heat pump'])
            # Recalculate total energy without gas
            grid_electricity = energy_usage.get('GridElectricityKwh', 6000)
            energy_usage['AnnualEnergyKwh'] = grid_electricity
            
        elif tariff_type == 'Gas':
            # Gas-only tariff (rare) - minimal electricity for lighting/appliances
            gas_usage = energy_usage.get('GasUsageKwh', 8000)
            energy_usage['GridElectricityKwh'] = round(gas_usage * random.uniform(0.3, 0.5))  # Electricity ~30-50% of gas
            energy_usage['AnnualEnergyKwh'] = energy_usage['GridElectricityKwh'] + gas_usage
            energy_usage['HeatingSystem'] = 'Gas central heating'
            
        elif tariff_type == 'Both':
            # Mixed tariff - ensure both gas and electricity usage
            total_energy = energy_usage.get('AnnualEnergyKwh', 15000)
            # Typical split: 40-60% electricity, 40-60% gas
            electricity_ratio = random.uniform(0.4, 0.6)
            energy_usage['GridElectricityKwh'] = round(total_energy * electricity_ratio)
            energy_usage['GasUsageKwh'] = round(total_energy * (1 - electricity_ratio))
            energy_usage['HeatingSystem'] = 'Gas central heating'
        
        # 5. Fix Location Coordinates for Chelsea
        if location_info.get('name') == 'Chelsea':
            # Ensure coordinates are within actual Chelsea bounds
            # Real Chelsea: roughly 51.48-51.50°N, 0.15-0.18°W
            property_data['PropertyHeader']['Location']['LatitudeDegrees'] = random.uniform(51.48, 51.50)
            property_data['PropertyHeader']['Location']['LongitudeDegrees'] = random.uniform(-0.18, -0.15)
        
        # 6. Fix Council Tax Band vs Property Value Consistency
        property_value = property_data.get('PropertyHeader', {}).get('Valuation', {}).get('PropertyValue', 0)
        
        # Rough Council Tax band thresholds for London (higher than national average)
        if property_value < 300000:
            council_tax_band = random.choice(['A', 'B', 'C'])
        elif property_value < 500000:
            council_tax_band = random.choice(['C', 'D'])
        elif property_value < 750000:
            council_tax_band = random.choice(['D', 'E', 'F'])
        elif property_value < 1200000:
            council_tax_band = random.choice(['F', 'G'])
        else:
            council_tax_band = 'H'
        
        property_data['PropertyHeader']['PropertyAttributes']['CouncilTaxBand'] = council_tax_band
        
        # 7. Fix Flood Risk vs Protection Measures Consistency
        flood_risk = property_data.get('PropertyHeader', {}).get('RiskAssessment', {}).get('OverallFloodRisk')
        resilience_measures = property_data.get('ProtectionMeasures', {}).get('ResilienceMeasures', {})
        
        if flood_risk in ['High', 'Very High']:
            # High flood risk properties more likely to have protection measures
            resilience_measures['FloodGates'] = random.choice([True] * 7 + [False] * 3)  # 70% chance
            resilience_measures['FloodBarriers'] = random.choice([True] * 6 + [False] * 4)  # 60% chance
            resilience_measures['SumpPump'] = random.choice([True] * 5 + [False] * 5)  # 50% chance
            resilience_measures['FloodWarningSystem'] = random.choice([True] * 8 + [False] * 2)  # 80% chance
            
        elif flood_risk in ['Very Low', 'Low']:
            # Low flood risk properties less likely to have extensive protection
            resilience_measures['FloodGates'] = random.choice([True] * 1 + [False] * 9)  # 10% chance
            resilience_measures['FloodBarriers'] = random.choice([True] * 2 + [False] * 8)  # 20% chance
            resilience_measures['SumpPump'] = random.choice([True] * 1 + [False] * 9)  # 10% chance
        
        # 8. Fix Insurance Premium vs Risk Consistency
        risk_rating = property_data.get('ProtectionMeasures', {}).get('RiskAssessment', {}).get('RiskRating')
        insurance_premium = property_data.get('ProtectionMeasures', {}).get('RiskAssessment', {}).get('InsurancePremium', 0)
        
        # Recalculate insurance premium based on risk and value
        base_premium = (property_value / 1000) * random.uniform(1.5, 4.0)
        
        risk_multipliers = {
            'Very Low': random.uniform(0.8, 1.0),
            'Low': random.uniform(1.0, 1.2),
            'Medium': random.uniform(1.2, 1.5),
            'High': random.uniform(1.5, 2.2),
            'Very High': random.uniform(2.2, 3.5)
        }
        
        if flood_risk in risk_multipliers:
            adjusted_premium = base_premium * risk_multipliers[flood_risk]
            property_data['ProtectionMeasures']['RiskAssessment']['InsurancePremium'] = round(adjusted_premium, 2)
        
        # 9. Fix Property Period vs Construction Year
        construction_year = property_data.get('PropertyHeader', {}).get('PropertyAttributes', {}).get('ConstructionYear')
        if construction_year:
            correct_period = self._get_property_period(construction_year)
            property_data['PropertyHeader']['PropertyAttributes']['PropertyPeriod'] = correct_period
        
        # 10. Fix Rental Yield Reasonableness
        monthly_rent = property_data.get('TransactionHistory', {}).get('Rental', {}).get('MonthlyRentGbp', 0)
        if monthly_rent > 0 and property_value > 0:
            annual_rent = monthly_rent * 12
            rental_yield = (annual_rent / property_value) * 100
            
            # If yield is unrealistic (outside 2-12% for London), adjust rent
            if rental_yield < 2 or rental_yield > 12:
                # Target yield between 4-8% for London
                target_yield = random.uniform(0.04, 0.08)
                adjusted_monthly_rent = (property_value * target_yield) / 12
                property_data['TransactionHistory']['Rental']['MonthlyRentGbp'] = round(adjusted_monthly_rent, 2)
        
        # 11. Fix Storeys vs Property Type
        property_type = property_data.get('PropertyHeader', {}).get('PropertyAttributes', {}).get('PropertyResi')
        number_of_storeys = property_data.get('PropertyHeader', {}).get('PropertyAttributes', {}).get('NumberOfStoreys')
        
        if property_type == 'Bungalow' and number_of_storeys != 1:
            property_data['PropertyHeader']['PropertyAttributes']['NumberOfStoreys'] = 1
        elif property_type == 'Flat':
            # Flats are typically 1 storey (the flat itself)
            property_data['PropertyHeader']['PropertyAttributes']['NumberOfStoreys'] = 1
        
        # 12. Fix Basement vs Floor Level
        basement_present = property_data.get('PropertyHeader', {}).get('Construction', {}).get('BasementPresent')
        floor_level = property_data.get('PropertyHeader', {}).get('Construction', {}).get('FloorLevelMeters', 0)
        
        if basement_present and floor_level < 0.5:
            # If basement present, ground floor should be higher
            property_data['PropertyHeader']['Construction']['FloorLevelMeters'] = random.uniform(0.5, 1.5)
        
        return property_data

    # Main generation function
    def generate(self, count=100):
        """Generate synthetic property data."""
        print(f"Generating {count} properties based on CDM schema...")
        
        if not init_elevation_data():
            print("Warning: Could not initialize elevation data, using fallback calculations")
        
        # Generate locations
        locations = self.generate_location_data(count)
        
        properties = []
        property_ids = []
        
        # Get schema from PropertyCDM
        schema = self.property_cdm.schema
        
        # Generate properties
        for i in range(count):
            # Get location info
            location_info = self.get_location_info(locations[i])
            
            # Generate property ID
            prop_id = f"PROP-{str(uuid.uuid4())[:8]}"
            location_info["prop_id"] = prop_id
            property_ids.append(prop_id)
            
            # Populate schema with random data
            property_data = self.populate_schema(schema, location_info)
            
            # Ensure required fields are set correctly
            self.ensure_required_fields(property_data, location_info)
            
            # Quality Consistency Validate property
            property_data = self.quality_consistency_check(property_data, location_info)
            self.validate_property(property_data)
            
            properties.append(property_data)
        
        # Save to JSON file
        output_path = self.output_dir / "property_portfolio.json"
        with open(output_path, 'w') as f:
            json.dump({"properties": properties}, f, indent=2)
            
        print(f"Property data saved to: {output_path}")
        
        return {
            "data": {
                "properties": properties,
                "property_ids": property_ids,
                "locations": locations
            },
            "file_path": output_path
        }

if __name__ == "__main__":
    """Run the property portfolio generator."""
    # Output directory for generated files
    output_dir = paths.input_dir
    
    # Create generator
    generator = PropertyPortfolioGenerator(output_dir)
    
    # Generate properties
    result = generator.generate(count=200)
    
    print(f"Generated {len(result['data']['properties'])} properties.")
    print(f"Output saved to: {result['file_path']}")