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
Mortgage Portfolio Generator - Modified to link one mortgage per property.

This module generates synthetic mortgage data based on the MortgageCDM schema,
with realistic financial attributes linked to property data from property_portfolio.json.
"""

import os
import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
import random
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

from cdm.mortgage_cdm import MortgageCDM
from cdm.property_cdm import PropertyCDM

# Initialize project paths
paths = ProjectPaths(__file__)

class MortgagePortfolioGenerator:
    """Generates synthetic mortgage data based on the MortgageCDM schema, linked to properties."""
    
    def __init__(self, output_dir: Union[str, Path]):
        """
        Initialize the Mortgage Portfolio Generator.
        
        Args:
            output_dir: Directory to save generated files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.mortgage_cdm = MortgageCDM()
        self.property_cdm = PropertyCDM()
        
        print(f"📁 Output directory: {self.output_dir}")
        print(f"📋 CDM sections available: {list(self.mortgage_cdm.schema['Mortgage'].keys())}")
        
        # UK mortgage lenders
        self.uk_lenders = [
            "HSBC", "Barclays", "NatWest", "Lloyds", "Santander", 
            "Nationwide", "Halifax", "Royal Bank of Scotland", 
            "Yorkshire Building Society", "Coventry Building Society"
        ]
        
        # UK mortgage product types
        self.mortgage_types = [
            "Residential", "Buy-to-Let", "Second Home", 
            "Holiday Home", "Shared Ownership"
        ]
        
        # Product type weights (residential most common)
        self.type_weights = [0.7, 0.15, 0.05, 0.05, 0.05]
        
        # Rate types
        self.rate_types = [
            "Fixed", "Variable", "Tracker", "Discount", 
            "Capped", "Standard Variable Rate"
        ]
        
        # Rate type weights (fixed rates most common in UK)
        self.rate_weights = [0.6, 0.1, 0.15, 0.05, 0.03, 0.07]
        
        print("✅ Mortgage Portfolio Generator initialized with complete CDM coverage")
    
    def load_property_portfolio(self, file_path: Optional[Union[str, Path]] = None) -> Dict:
        """
        Load property portfolio data from JSON file.
        
        Args:
            file_path: Path to property portfolio JSON file. If None, uses default location.
            
        Returns:
            Dictionary containing property data
        """
        if file_path is None:
            # Use the same output directory as this generator instance
            file_path = self.output_dir / "property_portfolio.json"
        
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Property portfolio file not found: {file_path}")
        
        print(f"📂 Loading property portfolio from: {file_path}")
        
        with open(file_path, 'r') as f:
            property_data = json.load(f)
        
        properties = property_data.get("properties", [])
        print(f"✅ Loaded {len(properties)} properties from portfolio")
        
        return property_data
    
    def generate_from_properties(self, property_file_path: Optional[Union[str, Path]] = None) -> Dict:
        """
        Generate mortgages linked to properties from property portfolio.
        
        Args:
            property_file_path: Path to property portfolio JSON file
            
        Returns:
            Dictionary containing generated data and file path
        """
        # Load property portfolio
        property_data = self.load_property_portfolio(property_file_path)
        properties = property_data.get("properties", [])
        
        if not properties:
            raise ValueError("No properties found in the property portfolio")
        
        print(f"\n🚀 Generating mortgages for {len(properties)} properties...")
        print("=" * 60)
        
        # Reset mortgage list
        mortgages = []
        mortgage_ids = []
        validation_errors = []
        
        # Access the schema from the MortgageCDM instance
        schema = self.mortgage_cdm.schema
        
        print(f"📊 Generation Progress:")
        
        # Generate one mortgage per property
        for i, property_data in enumerate(properties):
            try:
                # Progress indicator
                if (i + 1) % 10 == 0 or i < 5:
                    progress = (i + 1) / len(properties) * 100
                    print(f"   {i+1:3d}/{len(properties)} ({progress:5.1f}%) - Generating mortgage for property {i+1}")
                
                # Extract property information
                property_info = self._extract_property_info(property_data)
                
                # Generate mortgage using helper methods
                mortgage_data, mortgage_id = self._generate_single_mortgage_for_property(
                    i, schema, property_info)
                
                # Quality Consistency Check - ensure mortgage internal consistency and property alignment
                mortgage_data = self.quality_consistency_check(mortgage_data, property_data)
                
                # Validate the mortgage structure and consistency
                structure_valid = self._validate_mortgage_structure(mortgage_data)
                consistency_errors = self.validate_mortgage_data_consistency(mortgage_data, property_data)
                
                if structure_valid and len(consistency_errors) == 0:
                    mortgages.append(mortgage_data)
                    mortgage_ids.append(mortgage_id)
                else:
                    error_msg = f"Mortgage {i+1}: "
                    if not structure_valid:
                        error_msg += "Structure validation failed. "
                    if consistency_errors:
                        error_msg += f"Consistency issues: {'; '.join(consistency_errors[:3])}"  # Limit to first 3 errors
                    validation_errors.append(error_msg)
                    
            except Exception as e:
                error_msg = f"Mortgage {i+1}: Generation error - {str(e)}"
                validation_errors.append(error_msg)
                print(f"   ❌ {error_msg}")
        
        # Report results
        print(f"\n📈 Generation Complete:")
        print(f"   ✅ Successfully generated: {len(mortgages)} mortgages")
        print(f"   ❌ Validation errors: {len(validation_errors)}")
        
        if validation_errors and len(validation_errors) <= 5:
            print(f"\n⚠️  Validation Issues:")
            for error in validation_errors:
                print(f"      • {error}")
        
        # Verify section coverage
        if mortgages:
            generated_sections = set(mortgages[0]["Mortgage"].keys())
            cdm_sections = set(schema["Mortgage"].keys())
            coverage = len(generated_sections) / len(cdm_sections) * 100
            
            print(f"\n📋 Section Coverage Analysis:")
            print(f"   📊 CDM sections: {len(cdm_sections)}")
            print(f"   ✅ Generated: {len(generated_sections)}")
            print(f"   📈 Coverage: {coverage:.1f}%")
            
            missing = cdm_sections - generated_sections
            if missing:
                print(f"   ❌ Missing: {', '.join(missing)}")
            else:
                print(f"   🎉 ALL SECTIONS GENERATED!")
        
        # Save to JSON file
        output_path = self.output_dir / "mortgage_portfolio.json"
        with open(output_path, 'w') as f:
            json.dump({"mortgages": mortgages}, f, indent=2)
            
        print(f"Mortgage data saved to: {output_path}")
        
        # Generate summary
        summary = self._generate_summary_statistics(mortgages)
        print(f"\n📊 Portfolio Summary:")
        for key, value in summary.items():
            print(f"   {key}: {value}")
        
        return {
            "data": {
                "mortgages": mortgages,
                "mortgage_ids": mortgage_ids,
                "summary": summary,
                "property_count": len(properties)
            },
            "file_path": output_path,
            "validation_errors": validation_errors
        }
    
    def _extract_property_info(self, property_data: Dict) -> Dict:
        """
        Extract relevant information from property data structure.
        
        Args:
            property_data: Property data from portfolio
            
        Returns:
            Dictionary containing extracted property information
        """
        property_info = {}
        
        # Extract header information
        if "PropertyHeader" in property_data and "Header" in property_data["PropertyHeader"]:
            header = property_data["PropertyHeader"]["Header"]
            property_info["property_id"] = header.get("PropertyID")
            property_info["uprn"] = header.get("UPRN")
            property_info["property_type"] = header.get("propertyType", "Residential")
        
        # Extract location information
        if "PropertyHeader" in property_data and "Location" in property_data["PropertyHeader"]:
            location = property_data["PropertyHeader"]["Location"]
            property_info["postcode"] = location.get("Postcode")
            property_info["town_city"] = location.get("TownCity")
            property_info["county"] = location.get("County")
            property_info["latitude"] = location.get("LatitudeDegrees")
            property_info["longitude"] = location.get("LongitudeDegrees")
            property_info["urban_rural"] = location.get("UrbanRuralClassification")
        
        # Extract property attributes
        if "PropertyHeader" in property_data and "PropertyAttributes" in property_data["PropertyHeader"]:
            attributes = property_data["PropertyHeader"]["PropertyAttributes"]
            property_info["property_area_sqm"] = attributes.get("PropertyAreaSqm")
            property_info["number_bedrooms"] = attributes.get("NumberBedrooms")
            property_info["number_bathrooms"] = attributes.get("NumberBathrooms")
            property_info["construction_year"] = attributes.get("ConstructionYear")
            property_info["council_tax_band"] = attributes.get("CouncilTaxBand")
            property_info["property_condition"] = attributes.get("PropertyCondition")
            property_info["occupancy_type"] = attributes.get("OccupancyType")
            property_info["building_residency"] = attributes.get("BuildingResidency")
        
        # Extract valuation - primary property value
        property_value = None
        
        # Try to get from Valuation section first
        if "PropertyHeader" in property_data and "Valuation" in property_data["PropertyHeader"]:
            property_value = property_data["PropertyHeader"]["Valuation"].get("PropertyValue")
        
        # Fallback to transaction history
        if not property_value and "TransactionHistory" in property_data:
            if "Sales" in property_data["TransactionHistory"]:
                property_value = property_data["TransactionHistory"]["Sales"].get("SalePriceGbp")
        
        # If still no value, estimate based on location and attributes
        if not property_value:
            property_value = self._estimate_property_value(property_info)
        
        property_info["property_value"] = property_value
        
        # Extract risk assessment
        if "PropertyHeader" in property_data and "RiskAssessment" in property_data["PropertyHeader"]:
            risk = property_data["PropertyHeader"]["RiskAssessment"]
            property_info["flood_risk"] = risk.get("OverallFloodRisk")
            property_info["river_distance"] = risk.get("RiverDistanceMeters")
            property_info["soil_type"] = risk.get("SoilType")
        
        # Extract energy performance
        if "EnergyPerformance" in property_data and "Ratings" in property_data["EnergyPerformance"]:
            ratings = property_data["EnergyPerformance"]["Ratings"]
            property_info["epc_rating"] = ratings.get("EPCRating")
        
        # Extract rental information for Buy-to-Let mortgages
        if "TransactionHistory" in property_data and "Rental" in property_data["TransactionHistory"]:
            rental = property_data["TransactionHistory"]["Rental"]
            property_info["monthly_rent"] = rental.get("MonthlyRentGbp")
            property_info["rental_history"] = rental.get("RentalHistory")
        
        return property_info
    
    def _estimate_property_value(self, property_info: Dict) -> float:
        """
        Estimate property value based on available information.
        
        Args:
            property_info: Dictionary containing property information
            
        Returns:
            Estimated property value in GBP
        """
        # Base value for UK property
        base_value = 300000
        
        # Adjust for location
        county = property_info.get("county", "").lower()
        if "london" in county or "greater london" in county:
            base_value *= 2.5
        elif county in ["surrey", "hertfordshire", "buckinghamshire"]:
            base_value *= 1.8
        elif county in ["kent", "essex", "berkshire"]:
            base_value *= 1.5
        
        # Adjust for property size
        bedrooms = property_info.get("number_bedrooms", 3)
        if bedrooms:
            base_value *= (0.7 + bedrooms * 0.15)
        
        # Adjust for property area
        area_sqm = property_info.get("property_area_sqm")
        if area_sqm:
            base_value *= (0.8 + area_sqm / 200)
        
        # Adjust for age
        construction_year = property_info.get("construction_year")
        if construction_year:
            age = 2025 - construction_year
            if age < 10:
                base_value *= 1.1
            elif age > 50:
                base_value *= 0.9
        
        # Add some randomness
        base_value *= random.uniform(0.9, 1.1)
        
        return round(base_value, 2)
    
    def _generate_single_mortgage_for_property(self, index: int, schema: Dict, property_info: Dict) -> tuple:
        """Generate a single mortgage data structure for a specific property."""
        # Generate unique ID
        mortgage_id = f"{str(uuid.uuid4())}"
        
        # Get property details
        property_id = property_info.get("property_id")
        property_value = property_info.get("property_value")
        
        if not property_value:
            property_value = self._estimate_property_value(property_info)
        
        # Determine mortgage type based on property characteristics
        mortgage_type = self._determine_mortgage_type(property_info)
        
        # Calculate financial values based on property and mortgage type
        financial_data = self._calculate_mortgage_financials(property_value, mortgage_type, property_info, index)
        
        # Store all property and financial data for use in field generation
        combined_data = {**financial_data, **property_info}
        combined_data["mortgage_type"] = mortgage_type
        combined_data["property_id"] = property_id
        
        # Build mortgage data structure for ALL sections
        mortgage_data = {"Mortgage": {}}
        
        # Generate ALL sections from the CDM schema
        for section_name, section_schema in schema["Mortgage"].items():
            mortgage_data["Mortgage"][section_name] = self._build_section(
                section_schema, index, combined_data, section_name
            )
        
        # Override specific important fields for consistency
        self._set_specific_mortgage_values(
            mortgage_data, mortgage_id, property_id, index, combined_data)
        
        return mortgage_data, mortgage_id
    
    def _determine_mortgage_type(self, property_info: Dict) -> str:
        """
        Determine appropriate mortgage type based on property characteristics.
        
        Args:
            property_info: Property information dictionary
            
        Returns:
            Mortgage type string
        """
        # Check if property has rental income - suggests Buy-to-Let
        if property_info.get("monthly_rent") or property_info.get("rental_history") == "Previously rented":
            return random.choices(["Buy-to-Let", "Residential"], weights=[0.7, 0.3])[0]
        
        # Check building residency type
        building_residency = property_info.get("building_residency", "").lower()
        if "multi family" in building_residency:
            return random.choices(["Buy-to-Let", "Residential"], weights=[0.5, 0.5])[0]
        
        # Check occupancy type
        occupancy = property_info.get("occupancy_type", "").lower()
        if occupancy == "vacant":
            return random.choices(["Buy-to-Let", "Second Home", "Residential"], weights=[0.4, 0.3, 0.3])[0]
        
        # Default distribution
        return random.choices(self.mortgage_types, weights=self.type_weights)[0]
    
    def _calculate_mortgage_financials(self, property_value: float, mortgage_type: str, property_info: Dict, index: int) -> Dict:
        """
        Calculate mortgage financial parameters based on property value and type.
        
        Args:
            property_value: Property value in GBP
            mortgage_type: Type of mortgage
            property_info: Property information
            index: Property index
            
        Returns:
            Dictionary containing financial calculations
        """
        # Adjust LTV based on mortgage type and property characteristics
        if mortgage_type == "Buy-to-Let":
            # BTL mortgages typically have lower LTV
            ltv_ratio = random.triangular(0.6, 0.7, 0.75)
        elif mortgage_type in ["Second Home", "Holiday Home"]:
            # Second homes often require larger deposits
            ltv_ratio = random.triangular(0.6, 0.7, 0.8)
        else:
            # Residential mortgages
            ltv_ratio = random.triangular(0.7, 0.8, 0.95)
        
        # Adjust LTV based on property risk factors
        flood_risk = property_info.get("flood_risk", "").lower()
        if "high" in flood_risk:
            ltv_ratio *= 0.95  # Slightly lower LTV for high flood risk
        
        # Calculate loan amount
        loan_amount = property_value * ltv_ratio
        
        # Term in months - varies by mortgage type
        if mortgage_type == "Buy-to-Let":
            term_years = random.randint(20, 25)  # BTL often shorter terms
        else:
            term_years = random.randint(25, 35)  # Standard residential
        
        term_months = term_years * 12
        
        # Current age of mortgage - between 0-7 years
        months_elapsed = random.randint(0, min(84, term_months - 12))
        
        # Calculate outstanding balance with proper amortization
        elapsed_ratio = months_elapsed / term_months
        repayment_ratio = elapsed_ratio * (1.1 - 0.2 * elapsed_ratio)
        outstanding_balance = loan_amount * (1 - repayment_ratio)
        
        # Current LTV based on outstanding balance and current property value
        # Property values may have changed since origination
        current_property_value = property_value * random.uniform(0.95, 1.15)  # Market movement
        current_ltv = outstanding_balance / current_property_value
        
        # Interest rate based on mortgage type and risk factors
        base_rate = 0.025  # Current typical base rate
        
        if mortgage_type == "Buy-to-Let":
            interest_rate = base_rate + random.uniform(0.015, 0.025)  # BTL premium
        elif mortgage_type in ["Second Home", "Holiday Home"]:
            interest_rate = base_rate + random.uniform(0.01, 0.02)  # Second home premium
        else:
            interest_rate = base_rate + random.uniform(0.005, 0.015)  # Residential rates
        
        # Risk adjustments
        if flood_risk and "high" in flood_risk:
            interest_rate += 0.002  # Flood risk premium
        
        # Location adjustments (London properties often get better rates due to security)
        county = property_info.get("county", "").lower()
        if "london" in county:
            interest_rate -= 0.001
        
        # Calculate monthly payment
        r = interest_rate / 12  # Monthly interest rate
        if r > 0:
            monthly_payment = loan_amount * r * (1 + r) ** term_months / ((1 + r) ** term_months - 1)
        else:
            monthly_payment = loan_amount / term_months
        
        # Borrower income calculation
        if mortgage_type == "Buy-to-Let":
            # BTL lending often based on rental yield rather than personal income
            monthly_rent = property_info.get("monthly_rent", property_value * 0.005)  # 0.5% yield
            if not monthly_rent:
                monthly_rent = property_value * random.uniform(0.003, 0.006)  # 3.6-7.2% annual yield
            
            # BTL stress test - rent must cover mortgage at stressed rate
            stress_coverage = random.uniform(1.25, 1.45)  # 125-145% coverage
            required_income = monthly_payment * 12 * stress_coverage
            borrower_income = max(required_income, monthly_rent * 12 * 2)  # Minimum 2x rental income
        else:
            # Residential lending based on income multiples
            annual_payment = monthly_payment * 12
            income_multiple = random.uniform(3.5, 4.5)  # Current affordability rules
            borrower_income = annual_payment * income_multiple
        
        # Status flags
        is_defaulted = random.random() < 0.02  # Lower default rate for property-backed lending
        is_in_arrears = random.random() < 0.04
        
        return {
            "property_value": property_value,
            "current_property_value": current_property_value,
            "loan_amount": loan_amount,
            "ltv_ratio": ltv_ratio,
            "term_months": term_months,
            "months_elapsed": months_elapsed,
            "outstanding_balance": outstanding_balance,
            "current_ltv": current_ltv,
            "interest_rate": interest_rate,
            "monthly_payment": monthly_payment,
            "borrower_income": borrower_income,
            "is_defaulted": is_defaulted,
            "is_in_arrears": is_in_arrears,
            "annual_payment": monthly_payment * 12
        }
    
    def _build_section(self, section_schema: Dict, index: int, financial_data: Dict, section_name: str = "") -> Dict:
        """Recursively build a section of mortgage data."""
        section_data = {}
        for field_name, field_def in section_schema.items():
            if isinstance(field_def, dict) and not field_def.get("type"):
                # This is a nested section
                section_data[field_name] = self._build_section(field_def, index, financial_data, field_name)
            else:
                # This is a field
                value = self._generate_value(field_def, index, field_name, financial_data, section_name)
                if value is not None:
                    section_data[field_name] = value
        return section_data
    
    def _generate_value(self, field_def, index, field_name=None, financial_data=None, section_name=""):
        """Generate a value for a field based on its definition."""
        if isinstance(field_def, dict):
            if "type" in field_def:
                field_type = field_def["type"]
                
                if field_type == "menu" or field_type == "enum":
                    options = field_def.get("options", field_def.get("values", []))
                    if options:
                        if field_name == "MortgageType":
                            return financial_data.get("mortgage_type", "Residential")
                        elif field_name == "OriginalRateType":
                            return random.choices(self.rate_types, weights=self.rate_weights)[0]
                        elif field_name == "PaymentFrequency":
                            return "Monthly"
                        elif field_name == "OccupancyType":
                            # Use property occupancy if available
                            property_occupancy = financial_data.get("occupancy_type")
                            if property_occupancy:
                                return property_occupancy
                            return "PrimaryResidence"
                        elif field_name == "LoanPurpose":
                            mortgage_type = financial_data.get("mortgage_type", "Residential")
                            if mortgage_type == "Buy-to-Let":
                                return random.choices(["Purchase", "Refinancing"], weights=[0.6, 0.4])[0]
                            else:
                                return random.choices(["Purchase", "Refinancing", "Home Improvement"], weights=[0.7, 0.25, 0.05])[0]
                        return random.choice(options)
                        
                elif field_type == "boolean":
                    # Property-specific boolean logic
                    if field_name == "DefaultFlag":
                        return financial_data.get("is_defaulted", False)
                    elif field_name == "InArrearsFlag":
                        return financial_data.get("is_in_arrears", False)
                    elif field_name == "BusinessOrCommercialPurpose":
                        return financial_data.get("mortgage_type") == "Buy-to-Let"
                    elif field_name == "FirstTimeBuyerFlag":
                        # Less likely for BTL or high-value properties
                        if financial_data.get("mortgage_type") == "Buy-to-Let":
                            return False
                        property_value = financial_data.get("property_value", 0)
                        if property_value > 600000:
                            return random.random() < 0.1
                        return random.random() < 0.3
                    return random.random() < 0.3
                    
                elif field_type == "decimal":
                    # Use calculated financial values
                    if field_name == "PurchaseValue" and financial_data:
                        return financial_data["property_value"]
                    elif field_name == "ApplicationPropertyValuation" and financial_data:
                        return financial_data["property_value"]
                    elif field_name == "OriginalLoan" and financial_data:
                        return financial_data["loan_amount"]
                    elif field_name == "OutstandingBalance" and financial_data:
                        return round(financial_data["outstanding_balance"], 2)
                    elif field_name == "OriginalLTV" and financial_data:
                        return round(financial_data["ltv_ratio"], 4)
                    elif field_name == "CurrentLTV" and financial_data:
                        return round(financial_data["current_ltv"], 4)
                    elif field_name == "OriginalLendingRate" and financial_data:
                        return round(financial_data["interest_rate"] * 100, 2)
                    elif field_name == "CurrentPayment" and financial_data:
                        return round(financial_data["monthly_payment"], 2)
                    elif field_name == "BorrowerIncome" and financial_data:
                        return financial_data["borrower_income"]
                    # Continue with existing decimal logic...
                    base_amount = financial_data.get("loan_amount", 500000) if financial_data else 500000
                    return round(base_amount * random.uniform(0.005, 0.03) + random.uniform(0, 1000), 2)
                    
                elif field_type == "integer":
                    if field_name == "OriginalTerm" and financial_data:
                        return financial_data["term_months"]
                    elif field_name == "TotalPayments" and financial_data:
                        return min(financial_data["months_elapsed"], financial_data["term_months"])
                    # Continue with existing integer logic...
                    return random.randint(1, 10)
                    
                elif field_type == "date":
                    # Property-specific date logic
                    if field_name == "ApplicationDate" and financial_data:
                        months_ago = financial_data["months_elapsed"] + random.randint(1, 3)
                        return (datetime.now() - timedelta(days=30*months_ago)).strftime("%Y-%m-%d")
                    elif field_name == "DisburalDate" and financial_data:
                        months_ago = financial_data["months_elapsed"]
                        return (datetime.now() - timedelta(days=30*months_ago)).strftime("%Y-%m-%d")
                    # Continue with existing date logic...
                    return (datetime.now() - timedelta(days=random.randint(1, 365))).strftime("%Y-%m-%d")
                    
                elif field_type == "text":
                    if field_name == "MortgageProvider":
                        return random.choice(self.uk_lenders)
                    elif field_name == "UPRN" and financial_data:
                        # Use actual property UPRN if available
                        return financial_data.get("uprn", f"UPRN-{random.randint(100000, 999999)}")
                    # Continue with existing text logic...
                    return f"Text-{index}-{random.randint(1000, 9999)}"
                    
        return f"Value-{index}"
    
    def _set_specific_mortgage_values(self, mortgage_data, mortgage_id, property_id, index, financial_data):
        """Set specific values in the mortgage data structure."""
        if "Mortgage" in mortgage_data:
            # Header section
            if "Header" in mortgage_data["Mortgage"]:
                mortgage_data["Mortgage"]["Header"]["MortgageID"] = mortgage_id
                mortgage_data["Mortgage"]["Header"]["PropertyID"] = property_id
                
                # Use actual UPRN from property if available
                uprn = financial_data.get("uprn")
                if uprn:
                    mortgage_data["Mortgage"]["Header"]["UPRN"] = uprn
                else:
                    property_numeric = hash(property_id) % 1000000
                    mortgage_data["Mortgage"]["Header"]["UPRN"] = f"UPRN-{property_numeric:06d}"
            
            # Continue with existing logic but use property-based financial data...
            # [Rest of the method remains largely the same, using the calculated financial_data]
    
    def _set_specific_mortgage_values(self, mortgage_data, mortgage_id, property_id, index, financial_data):
        """Set specific values in the mortgage data structure."""
        if "Mortgage" in mortgage_data:
            # Header section
            if "Header" in mortgage_data["Mortgage"]:
                mortgage_data["Mortgage"]["Header"]["MortgageID"] = mortgage_id
                mortgage_data["Mortgage"]["Header"]["PropertyID"] = property_id
                
                # Use actual UPRN from property if available
                uprn = financial_data.get("uprn")
                if uprn:
                    mortgage_data["Mortgage"]["Header"]["UPRN"] = uprn
                else:
                    property_numeric = hash(property_id) % 1000000
                    mortgage_data["Mortgage"]["Header"]["UPRN"] = f"UPRN-{property_numeric:06d}"
            
            # Set financial values consistently using property-based calculations
            if "FinancialTerms" in mortgage_data["Mortgage"]:
                terms = mortgage_data["Mortgage"]["FinancialTerms"]
                terms["PurchaseValue"] = financial_data["property_value"]
                terms["OriginalLoan"] = financial_data["loan_amount"]
                terms["OriginalLTV"] = round(financial_data["ltv_ratio"], 4)
                terms["LoanToValueRatio"] = round(financial_data["ltv_ratio"], 4)
                terms["OriginalTerm"] = financial_data["term_months"]
                terms["OriginalLendingRate"] = round(financial_data["interest_rate"] * 100, 2)
                terms["currency"] = "GBP"
                
                # Calculate maturity date
                remaining_months = financial_data["term_months"] - financial_data["months_elapsed"]
                terms["MaturityDate"] = (datetime.now() + timedelta(days=30*remaining_months)).strftime("%Y-%m-%d")
            
            # Set current status consistently
            if "CurrentStatus" in mortgage_data["Mortgage"]:
                status = mortgage_data["Mortgage"]["CurrentStatus"]
                status["OutstandingBalance"] = round(financial_data["outstanding_balance"], 2)
                status["CurrentLTV"] = round(financial_data["current_ltv"], 4)
                status["CurrentPayment"] = round(financial_data["monthly_payment"], 2)
                status["TotalPayments"] = min(financial_data["months_elapsed"], financial_data["term_months"])
                
                # Set status based on property and mortgage characteristics
                if financial_data["is_defaulted"]:
                    status["LatestStatus"] = "Defaulted"
                else:
                    # Status distribution based on mortgage type
                    mortgage_type = financial_data.get("mortgage_type", "Residential")
                    if mortgage_type == "Buy-to-Let":
                        status_options = ["Current", "Completed", "Redeemed"]
                        status_weights = [0.92, 0.05, 0.03]
                    else:
                        status_options = ["Current", "Completed", "Redeemed"]
                        status_weights = [0.94, 0.04, 0.02]
                    status["LatestStatus"] = random.choices(status_options, status_weights)[0]
            
            # Set default information consistently
            if "Default" in mortgage_data["Mortgage"]:
                mortgage_data["Mortgage"]["Default"]["DefaultFlag"] = financial_data["is_defaulted"]
                if financial_data["is_defaulted"]:
                    default_months_ago = random.randint(1, min(12, financial_data["months_elapsed"]))
                    mortgage_data["Mortgage"]["Default"]["DefaultDate"] = (datetime.now() - timedelta(days=30*default_months_ago)).strftime("%Y-%m-%d")
                    mortgage_data["Mortgage"]["Default"]["DaysInArrears"] = random.randint(30, 180)
            
            # Set borrower details based on mortgage type and property
            if "BorrowerDetails" in mortgage_data["Mortgage"]:
                borrower = mortgage_data["Mortgage"]["BorrowerDetails"]
                borrower["BorrowerIncome"] = financial_data["borrower_income"]
                
                # Employment status varies by mortgage type
                mortgage_type = financial_data.get("mortgage_type", "Residential")
                if mortgage_type == "Buy-to-Let":
                    # BTL borrowers often self-employed or high earners
                    employment_options = ["Self-employed", "Employed", "Director", "Retired"]
                    employment_weights = [0.4, 0.4, 0.15, 0.05]
                else:
                    employment_options = ["Employed", "Self-employed", "Retired", "Unemployed"]
                    employment_weights = [0.75, 0.15, 0.08, 0.02]
                
                borrower["BorrowerEmployment"] = random.choices(employment_options, employment_weights)[0]
                
                # Age distribution based on mortgage type and property value
                property_value = financial_data.get("property_value", 0)
                if mortgage_type == "Buy-to-Let" or property_value > 800000:
                    borrower_age = random.randint(35, 65)  # Older, more established borrowers
                else:
                    borrower_age = random.randint(25, 60)  # Standard range
                
                borrower["BorrowerAge"] = borrower_age
                
                # Marital status influences family size
                if borrower_age < 30:
                    marital_options = ["Single", "Married", "Civil Partnership"]
                    marital_weights = [0.6, 0.35, 0.05]
                else:
                    marital_options = ["Married", "Single", "Divorced", "Civil Partnership", "Widowed"]
                    marital_weights = [0.5, 0.25, 0.15, 0.05, 0.05]
                
                marital_status = random.choices(marital_options, marital_weights)[0]
                borrower["MaritalStatus"] = marital_status
                
                # Family members based on property size and marital status
                bedrooms = financial_data.get("number_bedrooms", 3)
                if marital_status in ["Married", "Civil Partnership"]:
                    if bedrooms >= 4:
                        borrower["FamilyMembers"] = random.choices([2, 3, 4, 5], weights=[0.2, 0.3, 0.3, 0.2])[0]
                    else:
                        borrower["FamilyMembers"] = random.choices([2, 3, 4], weights=[0.4, 0.4, 0.2])[0]
                else:
                    borrower["FamilyMembers"] = random.choices([1, 2, 3], weights=[0.7, 0.2, 0.1])[0]
                
                # Credit score based on mortgage rate and property value
                if financial_data["interest_rate"] < 0.035:  # Good rate suggests good credit
                    borrower["BorrowerCreditScore"] = random.randint(750, 850)
                elif property_value > 600000:  # High value suggests financial stability
                    borrower["BorrowerCreditScore"] = random.randint(700, 800)
                else:
                    borrower["BorrowerCreditScore"] = random.randint(650, 750)
            
            # Set mortgage features based on property and type
            if "Features" in mortgage_data["Mortgage"]:
                features = mortgage_data["Mortgage"]["Features"]
                features["MortgageType"] = financial_data.get("mortgage_type", "Residential")
                
                # Interest-only more common for BTL
                if financial_data.get("mortgage_type") == "Buy-to-Let":
                    repayment_options = ["Interest Only", "Repayment", "Part and Part"]
                    repayment_weights = [0.6, 0.3, 0.1]
                else:
                    repayment_options = ["Repayment", "Interest Only", "Part and Part"]
                    repayment_weights = [0.85, 0.1, 0.05]
                
                features["RepaymentType"] = random.choices(repayment_options, repayment_weights)[0]
            
            # Set regulatory compliance based on mortgage type and timing
            if "Regulatory" in mortgage_data["Mortgage"]:
                if "Common" in mortgage_data["Mortgage"]["Regulatory"]:
                    common = mortgage_data["Mortgage"]["Regulatory"]["Common"]
                    
                    # Business purpose for BTL
                    common["BusinessOrCommercialPurpose"] = financial_data.get("mortgage_type") == "Buy-to-Let"
                    
                    # Advice patterns
                    is_advised = random.random() < 0.85
                    common["AdvisedFlag"] = is_advised
                    common["ExecutionOnlyFlag"] = not is_advised
                
                if "MCOB" in mortgage_data["Mortgage"]["Regulatory"]:
                    mcob = mortgage_data["Mortgage"]["Regulatory"]["MCOB"]
                    mcob["MMRCompliantFlag"] = True
                    mcob["StressTestCompliantFlag"] = True
                    
                    # APRC calculations
                    base_rate = financial_data["interest_rate"] * 100
                    mcob["APRCInitialRate"] = round(base_rate + random.uniform(0.3, 1.0), 2)
                    mcob["APRCSecondaryRate"] = round(mcob["APRCInitialRate"] + random.uniform(0.5, 1.5), 2)
    
    def _validate_mortgage_structure(self, mortgage_data: Dict) -> bool:
        """Validate that mortgage has the expected structure."""
        try:
            if "Mortgage" not in mortgage_data:
                return False
            
            mortgage = mortgage_data["Mortgage"]
            required_sections = ["Header", "Application", "FinancialTerms"]
            
            for section in required_sections:
                if section not in mortgage:
                    return False
                if not isinstance(mortgage[section], dict):
                    return False
            
            # Check required fields
            if not mortgage["Header"].get("MortgageID"):
                return False
            if not mortgage["Application"].get("MortgageProvider"):
                return False
            if not mortgage["FinancialTerms"].get("PurchaseValue"):
                return False
            
            return True
            
        except Exception:
            return False
    
    def _generate_summary_statistics(self, mortgages: List[Dict]) -> Dict:
        """Generate summary statistics for the portfolio."""
        if not mortgages:
            return {}
        
        try:
            # Extract key metrics
            loan_amounts = []
            property_values = []
            ltv_ratios = []
            interest_rates = []
            providers = []
            mortgage_types = []
            
            for mortgage in mortgages:
                m = mortgage.get("Mortgage", {})
                
                # Financial metrics
                terms = m.get("FinancialTerms", {})
                loan_amounts.append(terms.get("OriginalLoan", 0))
                property_values.append(terms.get("PurchaseValue", 0))
                ltv_ratios.append(terms.get("OriginalLTV", 0))
                interest_rates.append(terms.get("OriginalLendingRate", 0))
                
                # Categorical data
                app = m.get("Application", {})
                providers.append(app.get("MortgageProvider", "Unknown"))
                
                features = m.get("Features", {})
                mortgage_types.append(features.get("MortgageType", "Unknown"))
            
            # Calculate statistics
            summary = {
                "Total Mortgages": len(mortgages),
                "Average Loan Amount": f"£{sum(loan_amounts)/len(loan_amounts):,.0f}" if loan_amounts else "N/A",
                "Average Property Value": f"£{sum(property_values)/len(property_values):,.0f}" if property_values else "N/A",
                "Average LTV": f"{sum(ltv_ratios)/len(ltv_ratios)*100:.1f}%" if ltv_ratios else "N/A",
                "Average Interest Rate": f"{sum(interest_rates)/len(interest_rates):.2f}%" if interest_rates else "N/A",
                "Top Provider": max(set(providers), key=providers.count) if providers else "N/A",
                "Most Common Type": max(set(mortgage_types), key=mortgage_types.count) if mortgage_types else "N/A"
            }
            
            # Add mortgage type breakdown
            type_counts = {}
            for mt in mortgage_types:
                type_counts[mt] = type_counts.get(mt, 0) + 1
            
            summary["Mortgage Type Breakdown"] = {k: f"{v} ({v/len(mortgage_types)*100:.1f}%)" 
                                                for k, v in type_counts.items()}
            
            return summary
            
        except Exception as e:
            return {"Error": f"Could not generate summary: {str(e)}"}

    def validate_mortgage_data(self, mortgage_data: Dict) -> bool:
        """
        Validate mortgage data against the CDM schema.
        
        Args:
            mortgage_data: Mortgage data to validate
            
        Returns:
            True if valid, False if invalid
        """
        validation_errors = self.mortgage_cdm.validate_mortgage(mortgage_data)
        if validation_errors:
            print(f"Validation errors: {validation_errors}")
            return False
        return True

    def quality_consistency_check(self, mortgage_data: Dict, property_data: Dict) -> Dict:
        """
        Perform comprehensive quality and consistency checks on mortgage data.
        Fixes logical inconsistencies within the mortgage and ensures alignment with property data.
        
        Args:
            mortgage_data: The mortgage data dictionary to validate and fix
            property_data: The linked property data for cross-validation
            
        Returns:
            dict: The corrected mortgage data
        """
        
        mortgage = mortgage_data.get("Mortgage", {})
        
        # Extract key mortgage sections for easier access
        header = mortgage.get("Header", {})
        financial_terms = mortgage.get("FinancialTerms", {})
        current_status = mortgage.get("CurrentStatus", {})
        borrower_details = mortgage.get("BorrowerDetails", {})
        features = mortgage.get("Features", {})
        application = mortgage.get("Application", {})
        default_info = mortgage.get("Default", {})
        risk_assessment = mortgage.get("RiskAssessment", {})
        regulatory = mortgage.get("Regulatory", {})
        
        # Extract property information for cross-validation
        property_header = property_data.get("PropertyHeader", {})
        property_value = property_header.get("Valuation", {}).get("PropertyValue", 0)
        property_attributes = property_header.get("PropertyAttributes", {})
        property_location = property_header.get("Location", {})
        property_risk = property_header.get("RiskAssessment", {})
        rental_info = property_data.get("TransactionHistory", {}).get("Rental", {})
        
        # ============================================================================
        # 1. PROPERTY-MORTGAGE ALIGNMENT CHECKS
        # ============================================================================
        
        # 1.1 Ensure Property Value Consistency
        purchase_value = financial_terms.get("PurchaseValue", 0)
        if abs(purchase_value - property_value) > property_value * 0.15:  # Allow 15% variance
            # Align mortgage purchase value with property value
            financial_terms["PurchaseValue"] = property_value
            financial_terms["ApplicationPropertyValuation"] = property_value
            
            # Recalculate loan amount based on existing LTV
            original_ltv = financial_terms.get("OriginalLTV", 0.8)
            financial_terms["OriginalLoan"] = round(property_value * original_ltv, 2)
            
            # Update outstanding balance proportionally
            loan_amount = financial_terms["OriginalLoan"]
            total_payments = current_status.get("TotalPayments", 0)
            original_term = financial_terms.get("OriginalTerm", 300)
            
            if original_term > 0:
                elapsed_ratio = total_payments / original_term
                repayment_ratio = elapsed_ratio * (1.1 - 0.2 * elapsed_ratio)
                current_status["OutstandingBalance"] = round(loan_amount * (1 - repayment_ratio), 2)
        
        # 1.2 Mortgage Type vs Property Characteristics
        mortgage_type = features.get("MortgageType", "Residential")
        monthly_rent = rental_info.get("MonthlyRentGbp", 0)
        occupancy_type = property_attributes.get("OccupancyType", "")
        
        # Fix Buy-to-Let alignment
        if mortgage_type == "Buy-to-Let":
            # Ensure regulatory flags are correct
            if "Common" in regulatory:
                regulatory["Common"]["BusinessOrCommercialPurpose"] = True
            
            # Ensure property has rental characteristics
            if monthly_rent == 0:
                # Estimate rental income based on property value (4-7% yield)
                estimated_yield = random.uniform(0.04, 0.07)
                estimated_monthly_rent = (property_value * estimated_yield) / 12
                rental_info["MonthlyRentGbp"] = round(estimated_monthly_rent, 2)
            
            # BTL properties often interest-only
            if features.get("RepaymentType") == "Repayment":
                features["RepaymentType"] = random.choice(["Interest Only", "Part and Part"])
        
        elif mortgage_type == "Residential":
            # Residential mortgages shouldn't be for business purposes
            if "Common" in regulatory:
                regulatory["Common"]["BusinessOrCommercialPurpose"] = False
            
            # Usually repayment mortgages
            if features.get("RepaymentType") == "Interest Only":
                features["RepaymentType"] = "Repayment"
        
        # 1.3 UPRN Consistency
        property_uprn = property_header.get("Header", {}).get("UPRN")
        mortgage_uprn = header.get("UPRN")
        if property_uprn and mortgage_uprn != property_uprn:
            header["UPRN"] = property_uprn
        
        # 1.4 Flood Risk vs Lending Terms
        flood_risk = property_risk.get("OverallFloodRisk", "").lower()
        current_ltv = current_status.get("CurrentLTV", 0)
        
        if "high" in flood_risk and current_ltv > 0.85:
            # High flood risk properties typically have lower LTV limits
            adjusted_ltv = min(current_ltv, 0.85)
            current_status["CurrentLTV"] = adjusted_ltv
            
            # Adjust outstanding balance accordingly
            outstanding_balance = property_value * adjusted_ltv
            current_status["OutstandingBalance"] = round(outstanding_balance, 2)
        
        # ============================================================================
        # 2. INTERNAL MORTGAGE CONSISTENCY CHECKS
        # ============================================================================
        
        # 2.1 LTV Ratio Consistency
        original_loan = financial_terms.get("OriginalLoan", 0)
        purchase_value = financial_terms.get("PurchaseValue", 1)
        
        if purchase_value > 0:
            calculated_ltv = original_loan / purchase_value
            stated_ltv = financial_terms.get("OriginalLTV", calculated_ltv)
            
            if abs(calculated_ltv - stated_ltv) > 0.01:  # 1% tolerance
                financial_terms["OriginalLTV"] = round(calculated_ltv, 4)
                financial_terms["LoanToValueRatio"] = round(calculated_ltv, 4)
        
        # 2.2 Outstanding Balance vs Payment History
        total_payments = current_status.get("TotalPayments", 0)
        original_term = financial_terms.get("OriginalTerm", 300)
        outstanding_balance = current_status.get("OutstandingBalance", 0)
        
        if original_term > 0 and total_payments <= original_term:
            # Recalculate based on amortization schedule
            elapsed_ratio = total_payments / original_term
            repayment_type = features.get("RepaymentType", "Repayment")
            
            if repayment_type == "Interest Only":
                # Interest-only: principal remains the same
                expected_balance = original_loan
            elif repayment_type == "Repayment":
                # Repayment: balance reduces over time
                repayment_ratio = elapsed_ratio * (1.1 - 0.2 * elapsed_ratio)
                expected_balance = original_loan * (1 - repayment_ratio)
            else:  # Part and Part
                # Mixed repayment
                repayment_ratio = elapsed_ratio * (1.05 - 0.1 * elapsed_ratio)
                expected_balance = original_loan * (1 - repayment_ratio)
            
            # Update if significantly different
            if abs(outstanding_balance - expected_balance) > original_loan * 0.1:
                current_status["OutstandingBalance"] = round(expected_balance, 2)
                outstanding_balance = expected_balance
        
        # 2.3 Current LTV Recalculation
        if outstanding_balance > 0 and property_value > 0:
            current_ltv_calculated = outstanding_balance / property_value
            current_status["CurrentLTV"] = round(current_ltv_calculated, 4)
        
        # 2.4 Interest Rate vs Market Conditions and Risk
        original_rate = financial_terms.get("OriginalLendingRate", 3.0)
        current_rate = current_status.get("CurrentLendingRate", original_rate)
        
        # Rate bounds based on mortgage type and risk
        if mortgage_type == "Buy-to-Let":
            min_rate, max_rate = 2.5, 8.0
        elif mortgage_type in ["Second Home", "Holiday Home"]:
            min_rate, max_rate = 2.0, 7.0
        else:  # Residential
            min_rate, max_rate = 1.5, 6.0
        
        # Adjust rates if outside reasonable bounds
        if original_rate < min_rate or original_rate > max_rate:
            financial_terms["OriginalLendingRate"] = random.uniform(min_rate, max_rate)
        
        if current_rate < min_rate or current_rate > max_rate:
            current_status["CurrentLendingRate"] = random.uniform(min_rate, max_rate)
        
        # 2.5 Payment Amount Consistency
        monthly_payment = current_status.get("CurrentPayment", 0)
        interest_rate = current_status.get("CurrentLendingRate", 3.0) / 100 / 12
        remaining_term = original_term - total_payments
        
        if remaining_term > 0 and interest_rate > 0:
            if repayment_type == "Interest Only":
                expected_payment = outstanding_balance * interest_rate
            elif repayment_type == "Repayment":
                # Standard repayment calculation
                if interest_rate > 0:
                    expected_payment = outstanding_balance * interest_rate * (1 + interest_rate) ** remaining_term / ((1 + interest_rate) ** remaining_term - 1)
                else:
                    expected_payment = outstanding_balance / remaining_term
            else:  # Part and Part
                # Mixed calculation
                interest_payment = outstanding_balance * interest_rate
                principal_payment = (outstanding_balance * 0.6) / remaining_term  # 60% repayment
                expected_payment = interest_payment + principal_payment
            
            # Update if significantly different (allow 10% variance)
            if abs(monthly_payment - expected_payment) > expected_payment * 0.1:
                current_status["CurrentPayment"] = round(expected_payment, 2)
        
        # 2.6 Default Status Consistency
        default_flag = default_info.get("DefaultFlag", False)
        days_in_arrears = default_info.get("DaysInArrears", 0)
        latest_status = current_status.get("LatestStatus", "Current")
        
        if default_flag:
            # Defaulted mortgages should have arrears and appropriate status
            if days_in_arrears < 90:
                default_info["DaysInArrears"] = random.randint(90, 365)
            
            if latest_status == "Current":
                current_status["LatestStatus"] = "Defaulted"
        else:
            # Non-defaulted mortgages shouldn't have excessive arrears
            if days_in_arrears > 30:
                default_info["DaysInArrears"] = random.randint(0, 30)
            
            if latest_status == "Defaulted":
                current_status["LatestStatus"] = random.choice(["Current", "Completed"])
        
        # 2.7 Borrower Income vs Affordability
        borrower_income = borrower_details.get("BorrowerIncome", 0)
        annual_payment = monthly_payment * 12
        
        if borrower_income > 0:
            affordability_ratio = annual_payment / borrower_income
            
            # Check affordability limits
            if mortgage_type == "Buy-to-Let":
                # BTL based on rental coverage, not personal income
                if monthly_rent > 0:
                    rental_coverage = (monthly_rent * 12) / annual_payment
                    if rental_coverage < 1.25:  # Minimum 125% coverage
                        # Adjust income or payment
                        required_payment = (monthly_rent * 12) / 1.35  # 135% coverage
                        current_status["CurrentPayment"] = round(required_payment / 12, 2)
            else:
                # Residential affordability rules (max ~45% of income)
                if affordability_ratio > 0.45:
                    # Increase income to meet affordability
                    required_income = annual_payment / 0.4  # 40% ratio
                    borrower_details["BorrowerIncome"] = round(required_income, 2)
                elif affordability_ratio < 0.15:
                    # Income too high - realistic range 15-40%
                    target_ratio = random.uniform(0.20, 0.35)
                    borrower_details["BorrowerIncome"] = round(annual_payment / target_ratio, 2)
        
        # 2.8 Age vs Term Consistency
        borrower_age = borrower_details.get("BorrowerAge", 35)
        remaining_term_years = remaining_term / 12 if remaining_term > 0 else 0
        retirement_age = 65
        
        if borrower_age + remaining_term_years > retirement_age + 5:
            # Mortgage extends too far past retirement
            max_term_years = retirement_age - borrower_age + 5
            if max_term_years > 5:  # Minimum viable term
                new_term_months = int(max_term_years * 12)
                financial_terms["OriginalTerm"] = new_term_months
            else:
                # Adjust borrower age to be younger
                borrower_details["BorrowerAge"] = retirement_age - int(original_term / 12) + 5
        
        # 2.9 Credit Score vs Interest Rate Consistency
        credit_score = borrower_details.get("BorrowerCreditScore", 700)
        
        # High credit scores should get better rates
        if credit_score >= 800 and original_rate > 4.0:
            financial_terms["OriginalLendingRate"] = random.uniform(2.0, 4.0)
        elif credit_score < 650 and original_rate < 4.0:
            financial_terms["OriginalLendingRate"] = random.uniform(4.0, 6.5)
        
        # 2.10 Regulatory Compliance Consistency
        if "MCOB" in regulatory:
            mcob = regulatory["MCOB"]
            
            # MMR compliance should be true for recent mortgages
            mcob["MMRCompliantFlag"] = True
            mcob["StressTestCompliantFlag"] = True
            
            # APRC rates should be higher than lending rates
            aprc_initial = mcob.get("APRCInitialRate", 0)
            aprc_secondary = mcob.get("APRCSecondaryRate", 0)
            lending_rate = financial_terms.get("OriginalLendingRate", 3.0)
            
            if aprc_initial <= lending_rate:
                mcob["APRCInitialRate"] = round(lending_rate + random.uniform(0.3, 1.0), 2)
            
            if aprc_secondary <= aprc_initial:
                mcob["APRCSecondaryRate"] = round(aprc_initial + random.uniform(0.5, 1.5), 2)
        
        # 2.11 Application vs Disbursement Date Logic
        app_date_str = application.get("ApplicationDate", "")
        disbursement_date_str = financial_terms.get("DisburalDate", "")
        
        if app_date_str and disbursement_date_str:
            try:
                app_date = datetime.strptime(app_date_str, "%Y-%m-%d")
                disbursement_date = datetime.strptime(disbursement_date_str, "%Y-%m-%d")
                
                # Disbursement should be after application (typical 1-3 months)
                if disbursement_date <= app_date:
                    new_disbursement = app_date + timedelta(days=random.randint(30, 90))
                    financial_terms["DisburalDate"] = new_disbursement.strftime("%Y-%m-%d")
            except ValueError:
                pass  # Skip if date parsing fails
        
        # 2.12 Maturity Date Consistency
        if disbursement_date_str and original_term > 0:
            try:
                disbursement_date = datetime.strptime(disbursement_date_str, "%Y-%m-%d")
                maturity_date = disbursement_date + timedelta(days=original_term * 30)
                financial_terms["MaturityDate"] = maturity_date.strftime("%Y-%m-%d")
            except ValueError:
                pass
        
        # ============================================================================
        # 3. RISK ASSESSMENT ALIGNMENT
        # ============================================================================
        
        # 3.1 Risk Scores vs Actual Risk Factors
        if "RiskAssessment" in mortgage:
            risk = mortgage["RiskAssessment"]
            
            # Calculate risk score based on factors
            base_risk_score = 50
            
            # LTV impact
            if current_ltv > 0.9:
                base_risk_score += 20
            elif current_ltv > 0.8:
                base_risk_score += 10
            elif current_ltv < 0.6:
                base_risk_score -= 10
            
            # Income impact
            if affordability_ratio > 0.4:
                base_risk_score += 15
            elif affordability_ratio < 0.2:
                base_risk_score -= 5
            
            # Credit score impact
            if credit_score >= 800:
                base_risk_score -= 15
            elif credit_score < 650:
                base_risk_score += 20
            
            # Default history impact
            if default_flag:
                base_risk_score += 30
            
            # Property risk impact
            if "high" in flood_risk:
                base_risk_score += 10
            
            # Update risk scores
            risk["BehavioralScore"] = max(10, min(100, base_risk_score + random.randint(-10, 10)))
            
            # Prepayment risk higher for high rates
            if current_rate > 5.0:
                risk["PrepaymentRisk"] = random.randint(7, 10)
            else:
                risk["PrepaymentRisk"] = random.randint(1, 5)
        
        return mortgage_data

    def validate_mortgage_data_consistency(self, mortgage_data: Dict, property_data: Dict) -> List[str]:
        """
        Validate mortgage data for consistency issues.
        
        Args:
            mortgage_data: Mortgage data to validate
            property_data: Associated property data
            
        Returns:
            List of validation error messages
        """
        errors = []
        mortgage = mortgage_data.get("Mortgage", {})
        
        # Check critical financial ratios
        financial_terms = mortgage.get("FinancialTerms", {})
        current_status = mortgage.get("CurrentStatus", {})
        
        original_loan = financial_terms.get("OriginalLoan", 0)
        purchase_value = financial_terms.get("PurchaseValue", 1)
        outstanding_balance = current_status.get("OutstandingBalance", 0)
        
        # LTV checks
        if purchase_value > 0:
            original_ltv = original_loan / purchase_value
            stated_ltv = financial_terms.get("OriginalLTV", 0)
            
            if abs(original_ltv - stated_ltv) > 0.02:
                errors.append(f"LTV mismatch: calculated {original_ltv:.3f} vs stated {stated_ltv:.3f}")
        
        # Outstanding balance reasonableness
        if outstanding_balance > original_loan * 1.1:
            errors.append(f"Outstanding balance ({outstanding_balance}) exceeds original loan ({original_loan}) by >10%")
        
        # Property value alignment
        property_value = property_data.get("PropertyHeader", {}).get("Valuation", {}).get("PropertyValue", 0)
        if property_value > 0 and purchase_value > 0:
            value_variance = abs(property_value - purchase_value) / property_value
            if value_variance > 0.2:
                errors.append(f"Property value variance too high: {value_variance:.1%}")
        
        return errors


    # Legacy method for backward compatibility
    def generate(self, count: int = 100, property_data: Optional[Dict] = None) -> Dict:
        """
        Legacy generate method - now redirects to property-based generation.
        
        Args:
            count: Number of mortgages to generate (ignored - uses property count)
            property_data: Optional dictionary containing property data (ignored - loads from file)
            
        Returns:
            Dictionary containing generated data and file path
        """
        print("⚠️  Legacy generate() method called - redirecting to property-based generation")
        return self.generate_from_properties()


if __name__ == "__main__":
    """Run the mortgage portfolio generator with property linking."""
    # Output directory for generated files
    output_dir = paths.input_dir
    
    # Create generator
    generator = MortgagePortfolioGenerator(output_dir)
    
    # Generate mortgages linked to properties
    try:
        result = generator.generate_from_properties()
        
        print(f"\n🎉 Successfully generated {len(result['data']['mortgages'])} mortgages")
        print(f"📊 Linked to {result['data']['property_count']} properties")
        print(f"💾 Output saved to: {result['file_path']}")
        
        if result['validation_errors']:
            print(f"⚠️  {len(result['validation_errors'])} validation errors occurred")
        
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        print("Please ensure property_portfolio.json exists in the input directory")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")