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

"""Mortgage generation methods for MortgagePortfolioGenerator (mixin)."""

import logging
from datetime import datetime
from typing import Dict

import database
from config import config
from port.utils.schema import build_section

logger = logging.getLogger(__name__)


class _MortgageGenerateMixin:
    """Core mortgage generation, single-mortgage build, and value-setting methods."""

    def generate(self) -> Dict:
        """
        Generate synthetic mortgage data linked to properties.

        Reads the property portfolio for the active catchment through the
        ``database`` seam and persists the generated loans the same way.

        Returns:
            Dictionary containing generated data, catchment, and processing information
        """
        self.processing_stats['start_time'] = datetime.now()

        self.log("=" * 60, "INFO")
        self.log("MORTGAGE PORTFOLIO GENERATOR", "INFO")
        self.log("=" * 60, "INFO")
        self.log(f"Catchment: {config.CATCHMENT}", "INFO")
        self.log(f"Catchment (storage): {self.catchment}", "INFO")

        # Load the property portfolio through the database seam.
        property_data = database.get_property_portfolio(self.catchment)
        if property_data is None:
            self.log(f"Property portfolio not found for catchment: {self.catchment}", "ERROR")
            raise FileNotFoundError(
                f"Property portfolio not found for catchment {self.catchment}. "
                "Generate properties first using PropertyPortfolioGenerator."
            )
        properties = property_data.get('properties', [])
        self.log(f"Loaded {len(properties)} properties", "SUCCESS")

        self.processing_stats['total_mortgages'] = len(properties)

        # Access the schema from LoanCDM
        schema = self.mortgage_cdm.schema
        self.log("Schema loaded from LoanCDM", "DEBUG")

        # Generate mortgages
        self.log("Starting mortgage generation process...", "INFO")
        mortgages = []
        mortgage_ids = []

        for i, property_record in enumerate(properties):
            if i % 50 == 0:
                self.log(f"Generating mortgage {i+1}/{len(properties)}...", "INFO")

            try:
                property_info = self._extract_property_info(property_record)
                mortgage_data, mortgage_id = self._generate_single_mortgage(i, schema, property_info)

                mortgages.append(mortgage_data)
                mortgage_ids.append(mortgage_id)
                self.processing_stats['successful_mortgages'] += 1

            except Exception as e:
                self.log(f"Failed to generate mortgage {i+1}: {str(e)}", "ERROR")
                self.processing_stats['failed_mortgages'] += 1
                continue

        # Persist through the database seam (catchment-keyed, storage-agnostic).
        self.log("Saving mortgage data...", "INFO")

        try:
            output_data = {
                "loans": mortgages,
                "generation_metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "generator_version": "Refactored v3.0",
                    "catchment": config.CATCHMENT,
                    "total_mortgages_generated": len(mortgages),
                    "linked_properties": len(properties)
                }
            }

            database.save_loans(self.catchment, output_data)

            self.log(f"Mortgage data saved successfully for catchment: {self.catchment}", "SUCCESS")

        except Exception as e:
            self.log(f"Error saving mortgage data: {str(e)}", "ERROR")
            raise

        # Update processing statistics
        self.processing_stats['end_time'] = datetime.now()
        processing_time = (self.processing_stats['end_time'] - self.processing_stats['start_time']).total_seconds()

        # Final summary
        self.log("=" * 60, "INFO")
        self.log("GENERATION COMPLETE", "SUCCESS")
        self.log("=" * 60, "INFO")
        self.log(f"Successfully generated: {self.processing_stats['successful_mortgages']}/{self.processing_stats['total_mortgages']} mortgages", "SUCCESS")
        self.log(f"Failed generations: {self.processing_stats['failed_mortgages']}", "INFO" if self.processing_stats['failed_mortgages'] == 0 else "WARNING")
        self.log(f"Processing time: {processing_time:.2f} seconds", "INFO")
        self.log(f"Saved to catchment: {self.catchment}", "INFO")

        return {
            "data": {
                "mortgages": mortgages,
                "mortgage_ids": mortgage_ids
            },
            "catchment": self.catchment,
            "processing_stats": self.processing_stats
        }

    def _extract_property_info(self, property_record: Dict) -> Dict:
        """Extract relevant property information for mortgage generation."""
        header = property_record.get('PropertyHeader', {})
        # PropertyID is in Header, not PropertyAttributes
        header_info = header.get('Header', {})
        attrs = header.get('PropertyAttributes', {})
        valuation = header.get('Valuation', {})
        location = header.get('Location', {})

        from config.visual import get_map_center
        _center_lat, _center_lon = get_map_center()

        return {
            'property_id': header_info.get('PropertyID', ''),  # FIXED: Use Header.PropertyID
            'property_value': valuation.get('PropertyValue', 500000),
            'property_type': attrs.get('PropertyResi', 'Flat'),
            'construction_year': attrs.get('ConstructionYear', 1990),
            'property_condition': attrs.get('PropertyCondition', 'Good'),
            'flood_risk': header.get('RiskAssessment', {}).get('OverallFloodRisk', 'Low'),
            'postcode': location.get('PostCode', ''),
            'latitude': location.get('LatitudeDegrees', _center_lat),
            'longitude': location.get('LongitudeDegrees', _center_lon)
        }

    def _generate_single_mortgage(self, index: int, schema: Dict, property_info: Dict) -> tuple:
        """Generate a single mortgage data structure."""
        financial_data = self.random.generate_financial_data(property_info, index)
        mortgage_id = financial_data['mortgage_id']
        property_id = property_info.get('property_id', 'N/A')

        # Show linkage for first few and every 50th
        if index < 5 or index % 50 == 0:
            property_value = financial_data.get('property_value', 0)
            loan_amount = financial_data.get('loan_amount', 0)
            self.log(f"Mortgage {index+1}: {mortgage_id} -> Property: {property_id} (Value: GBP{property_value:,.0f}, Loan: GBP{loan_amount:,.0f})", "SUCCESS")
        else:
            self.log(f"  Creating mortgage {mortgage_id} for property {property_id}", "DEBUG")

        mortgage_data = self._build_section(schema, index, financial_data)
        self._set_specific_mortgage_values(mortgage_data, mortgage_id, index, financial_data, property_info)

        # Quality check
        mortgage_data = self._quality_consistency_check(mortgage_data, financial_data)

        return mortgage_data, mortgage_id

    def _build_section(self, section_schema: Dict, index: int, financial_data: Dict) -> Dict:
        """Recursively build a section of mortgage data based on the schema."""
        return build_section(section_schema, index, financial_data, self.random)

    def _set_specific_mortgage_values(self, mortgage_data: Dict, mortgage_id: str,
                                     index: int, financial_data: Dict, property_info: Dict):
        """Set specific loan values that need to be consistent across sections."""
        if 'RLoan' not in mortgage_data:
            mortgage_data['RLoan'] = {}

        mortgage = mortgage_data['RLoan']

        if 'Header' not in mortgage:
            mortgage['Header'] = {}

        header = mortgage['Header']
        header['RLoanID'] = mortgage_id
        header['PropertyID'] = property_info.get('property_id', '')
        header['CatchmentID'] = config.CATCHMENT

    def _quality_consistency_check(self, mortgage_data: Dict, financial_data: Dict) -> Dict:
        """Perform quality and consistency checks on mortgage data."""
        if hasattr(self.random, 'quality_consistency_check'):
            return self.random.quality_consistency_check(mortgage_data, financial_data)

        from port.rand.thames.mortgage.quality import quality_consistency_check
        return quality_consistency_check(mortgage_data, financial_data)
