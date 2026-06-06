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
Mortgage Portfolio Generator.

This module generates synthetic mortgage data based on the LoanCDM schema.
Mortgages are linked to properties from the property portfolio.
Random value generation is delegated to catchment-specific modules in port.random.

Usage:
    from port.src.mortgage import MortgagePortfolioGenerator, generate_mortgages

    # Option 1: Use convenience function (uses config.CATCHMENT)
    result = generate_mortgages()  # Uses existing property portfolio

    # Option 2: Use generator class with config defaults
    generator = MortgagePortfolioGenerator()
    result = generator.generate()

    # Option 3: Explicit module injection
    from port.random.thames import mortgage_random, params
    generator = MortgagePortfolioGenerator(
        random_module=mortgage_random,
        catchment_params=params
    )
    result = generator.generate()
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union

import numpy as np

from config import config
from port.cdm import LoanCDM
from port.utils.schema import build_section

logger = logging.getLogger(__name__)


from port.utils.encoders import DateTimeEncoder  # noqa: F401


class MortgagePortfolioGenerator:
    """
    Mortgage Portfolio Generator.

    Generates synthetic mortgage data based on CDM schema.
    Mortgages are linked to properties from the property portfolio.
    Delegates random value generation to catchment-specific modules.
    """

    def __init__(
        self,
        output_dir: Optional[Union[str, Path]] = None,
        random_module: Optional[Any] = None,
        catchment_params: Optional[Any] = None,
        verbose: bool = True
    ):
        """
        Initialize the Mortgage Portfolio Generator.

        Args:
            output_dir: Directory to save generated files (defaults to config.get_input_dir())
            random_module: Catchment-specific random value generator module
                          (defaults to port.random.{CATCHMENT}.mortgage_random)
            catchment_params: Catchment parameters module
                             (defaults to port.params.{CATCHMENT})
            verbose: Enable detailed processing information
        """
        # Use config defaults if not provided
        self.output_dir = Path(output_dir) if output_dir else config.get_input_dir()
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.mortgage_cdm = LoanCDM()
        self.verbose = verbose
        if not verbose:
            logging.getLogger(__name__).setLevel(logging.WARNING)

        # Load catchment-specific modules from config if not provided
        self.random = random_module or config.load_random_module('mortgage.mortgage_random')
        self.params = catchment_params or config.load_params_module()

        # Processing statistics
        self.processing_stats = {
            'total_mortgages': 0,
            'successful_mortgages': 0,
            'failed_mortgages': 0,
            'start_time': None,
            'end_time': None
        }

    def log(self, message: str, level: str = "INFO"):
        """Log processing information."""
        log_func = getattr(logger, level.lower(), logger.info)
        log_func(message)

    def generate(self, property_portfolio_path: Optional[Path] = None) -> Dict:
        """
        Generate synthetic mortgage data linked to properties.

        Args:
            property_portfolio_path: Path to property portfolio JSON
                                    (defaults to config.get_input_path('property.json'))

        Returns:
            Dictionary containing generated data, file path, and processing information
        """
        self.processing_stats['start_time'] = datetime.now()

        self.log("=" * 60, "INFO")
        self.log("MORTGAGE PORTFOLIO GENERATOR", "INFO")
        self.log("=" * 60, "INFO")
        self.log(f"Catchment: {config.CATCHMENT}", "INFO")
        self.log(f"Output directory: {self.output_dir}", "INFO")

        # Load property portfolio using config path helper
        if property_portfolio_path is None:
            property_portfolio_path = config.get_input_path("property.json")

        self.log(f"Loading properties from: {property_portfolio_path}", "INFO")

        try:
            with open(property_portfolio_path, 'r') as f:
                property_data = json.load(f)
            properties = property_data.get('properties', [])
            self.log(f"Loaded {len(properties)} properties", "SUCCESS")
        except FileNotFoundError:
            self.log(f"Property portfolio not found: {property_portfolio_path}", "ERROR")
            raise FileNotFoundError(
                f"Property portfolio not found at {property_portfolio_path}. "
                "Generate properties first using PropertyPortfolioGenerator."
            )

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

        # Save to JSON file
        self.log("Saving mortgage data to JSON file...", "INFO")
        output_path = self.output_dir / "loan.json"

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

            with open(output_path, 'w') as f:
                json.dump(output_data, f, indent=2, cls=DateTimeEncoder)

            self.log(f"Mortgage data saved successfully to: {output_path}", "SUCCESS")

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
        self.log(f"Output file: {output_path}", "INFO")

        return {
            "data": {
                "mortgages": mortgages,
                "mortgage_ids": mortgage_ids
            },
            "file_path": output_path,
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


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================

def generate_mortgages(output_dir: Optional[Path] = None) -> Dict:
    """
    Convenience function to generate mortgage portfolio for current catchment.

    Uses config.CATCHMENT to determine which random module and params to use.

    Args:
        output_dir: Output directory (defaults to config.get_input_dir())
                   Must contain property.json

    Returns:
        Generation result dictionary
    """
    generator = MortgagePortfolioGenerator(output_dir=output_dir)
    return generator.generate()


if __name__ == "__main__":
    logger.info(f"Generating mortgages for catchment: {config.CATCHMENT}")
    result = generate_mortgages()
    logger.info(f"Generated {len(result['data']['mortgages'])} mortgages.")
    logger.info(f"Output saved to: {result['file_path']}")
