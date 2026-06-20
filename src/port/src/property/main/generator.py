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
Property Portfolio Generator.

This module generates synthetic property data based on the ResidentialAssetCDM schema.
Random value generation is delegated to catchment-specific modules in port.random.

Usage:
    from port.src.property import PropertyPortfolioGenerator, generate_properties

    # Option 1: Use convenience function (uses config.CATCHMENT)
    result = generate_properties(count=200)

    # Option 2: Use generator class with config defaults
    generator = PropertyPortfolioGenerator()
    result = generator.generate(count=200)

    # Option 3: Explicit module injection (any catchment)
    from port.rand.<catchment_id> import property_random
    from catch.<catchment_id> import <Catchment>Catchment
    generator = PropertyPortfolioGenerator(
        random_module=property_random,
        catchment_params=<Catchment>Catchment()
    )
    result = generator.generate(count=200)
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

import database
from config import config
from port.cdm import ResidentialAssetCDM

from .locations import LocationsMixin
from .builder import BuilderMixin

logger = logging.getLogger(__name__)


class PropertyPortfolioGenerator(LocationsMixin, BuilderMixin):
    """
    Property Portfolio Generator.

    Generates synthetic property data based on CDM schema.
    Delegates random value generation to catchment-specific modules.
    """

    def __init__(
        self,
        catchment: Optional[str] = None,
        random_module: Optional[Any] = None,
        catchment_params: Optional[Any] = None,
        verbose: bool = True
    ):
        """
        Initialize the Property Portfolio Generator.

        Args:
            catchment: Catchment to generate for; storage is resolved inside the
                       ``database`` package (defaults to ``database.active_catchment()``)
            random_module: Catchment-specific random value generator module
                          (defaults to port.random.{CATCHMENT}.property_random)
            catchment_params: Catchment parameters instance
                             (defaults to catchments.{CATCHMENT}.{Catchment}Catchment())
            verbose: Enable detailed processing information
        """
        # Run-scoped catchment identity; storage location lives in ``database``.
        self.catchment = catchment or database.active_catchment()

        self.property_cdm = ResidentialAssetCDM()
        self.verbose = verbose
        if not verbose:
            logging.getLogger(__name__).setLevel(logging.WARNING)

        self.random = random_module or config.load_random_module('property.property_random')
        self.params = catchment_params or config.load_params_module()

        self.processing_stats = {
            'total_properties': 0,
            'successful_properties': 0,
            'failed_properties': 0,
            'start_time': None,
            'end_time': None
        }

    def log(self, message: str, level: str = "INFO"):
        """Log processing information."""
        log_func = getattr(logger, level.lower(), logger.info)
        log_func(message)

    def generate(self, count: int = 200) -> Dict:
        """
        Generate synthetic property data.

        Args:
            count: Number of properties to generate

        Returns:
            Dictionary containing generated data, file path, and processing information
        """
        self.processing_stats['start_time'] = datetime.now()
        self.processing_stats['total_properties'] = count

        self.log("=" * 60, "INFO")
        self.log("PROPERTY PORTFOLIO GENERATOR", "INFO")
        self.log("=" * 60, "INFO")
        self.log(f"Catchment: {config.CATCHMENT}", "INFO")
        self.log(f"Target property count: {count}", "INFO")
        self.log(f"Catchment (storage): {self.catchment}", "INFO")

        # Load actual gauge IDs from the gauge portfolio for ReferenceGauges mapping.
        # Best-effort: a missing/corrupt portfolio just yields an empty map.
        self._gauge_id_map = {}  # index -> actual UUID
        try:
            gauge_portfolio = database.get_gauge_portfolio(self.catchment) or {}
            for idx, g in enumerate(gauge_portfolio.get('flood_gauges', gauge_portfolio.get('gauges', []))):
                gid = g.get('FloodGauge', {}).get('Header', {}).get('GaugeID', '')
                if gid:
                    self._gauge_id_map[idx] = gid
            self.log(f"Loaded {len(self._gauge_id_map)} gauge IDs for reference mapping", "DEBUG")
        except Exception as e:
            self.log(f"Could not load gauge IDs: {e}", "DEBUG")

        # Generate locations using catchment params
        self.log("Generating property locations...", "INFO")
        locations = self._generate_locations(count)
        self.log(f"Generated {len(locations)} locations", "INFO")

        # Access the schema from the ResidentialAssetCDM instance
        schema = self.property_cdm.schema
        self.log("Schema loaded from ResidentialAssetCDM", "DEBUG")

        # Generate properties
        self.log("Starting property generation process...", "INFO")
        properties = []
        property_ids = []

        for i, location in enumerate(locations):
            if i % 50 == 0:
                self.log(f"Generating property {i+1}/{count}...", "INFO")

            try:
                property_data, property_id = self._generate_single_property(i, schema, location)

                properties.append(property_data)
                property_ids.append(property_id)
                self.processing_stats['successful_properties'] += 1

                if i < 5:  # Show first few for verification
                    property_type = location.get('property_type', 'Unknown')
                    postcode = property_data.get('PropertyHeader', {}).get('Location', {}).get('PostCode', 'N/A')
                    self.log(f"Property {i+1}: {property_id} ({property_type}) at {postcode}", "INFO")

            except Exception as e:
                self.log(f"Failed to generate property {i+1}: {str(e)}", "ERROR")
                self.processing_stats['failed_properties'] += 1
                continue

        # Persist through the database seam (catchment-keyed, storage-agnostic).
        self.log("Saving property data...", "INFO")

        try:
            output_data = {
                "properties": properties,
                "generation_metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "generator_version": "Refactored v3.0",
                    "catchment": config.CATCHMENT,
                    "total_properties_generated": len(properties),
                    "locations_used": len(locations)
                }
            }

            database.save_properties(self.catchment, output_data)

            self.log(f"Property data saved successfully for catchment: {self.catchment}", "INFO")

        except Exception as e:
            self.log(f"Error saving property data: {str(e)}", "ERROR")
            raise

        # Update processing statistics
        self.processing_stats['end_time'] = datetime.now()
        processing_time = (self.processing_stats['end_time'] - self.processing_stats['start_time']).total_seconds()

        # Final summary
        self.log("=" * 60, "INFO")
        self.log("GENERATION COMPLETE", "INFO")
        self.log("=" * 60, "INFO")
        self.log(f"Successfully generated: {self.processing_stats['successful_properties']}/{self.processing_stats['total_properties']} properties", "INFO")
        self.log(f"Failed generations: {self.processing_stats['failed_properties']}", "INFO" if self.processing_stats['failed_properties'] == 0 else "WARNING")
        self.log(f"Processing time: {processing_time:.2f} seconds", "INFO")
        self.log(f"Saved to catchment: {self.catchment}", "INFO")

        return {
            "data": {
                "properties": properties,
                "property_ids": property_ids,
                "locations": locations
            },
            "catchment": self.catchment,
            "processing_stats": self.processing_stats
        }


def generate_properties(
    count: int = 200,
    catchment: Optional[str] = None,
) -> Dict:
    """Convenience function to generate property portfolio.

    The active catchment defaults to ``database.active_catchment()`` (set by the
    CLI / server entry point via ``config.catchment_id``). This function no longer
    mutates global catchment state.
    """
    generator = PropertyPortfolioGenerator(catchment=catchment)
    return generator.generate(count=count)
