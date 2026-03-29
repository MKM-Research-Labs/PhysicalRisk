# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""
Property Portfolio Generator.

This module generates synthetic property data based on the PropertyCDM schema.
Random value generation is delegated to catchment-specific modules in port.random.

Usage:
    from port.src.property import PropertyPortfolioGenerator, generate_properties

    # Option 1: Use convenience function (uses config.CATCHMENT)
    result = generate_properties(count=200)

    # Option 2: Use generator class with config defaults
    generator = PropertyPortfolioGenerator()
    result = generator.generate(count=200)

    # Option 3: Explicit module injection
    from port.random.thames import property_random
    from catchments.thames import ThamesCatchment
    generator = PropertyPortfolioGenerator(
        random_module=property_random,
        catchment_params=ThamesCatchment()
    )
    result = generator.generate(count=200)
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union

from config import config
from port.cdm import PropertyCDM

from .builder import BuilderMixin
from .encoder import DateTimeEncoder
from .locations import LocationsMixin

logger = logging.getLogger(__name__)


class PropertyPortfolioGenerator(LocationsMixin, BuilderMixin):
    """
    Property Portfolio Generator.

    Generates synthetic property data based on CDM schema.
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
        Initialize the Property Portfolio Generator.

        Args:
            output_dir: Directory to save generated files (defaults to config.get_input_dir())
            random_module: Catchment-specific random value generator module
                          (defaults to port.random.{CATCHMENT}.property_random)
            catchment_params: Catchment parameters instance
                             (defaults to catchments.{CATCHMENT}.{Catchment}Catchment())
            verbose: Enable detailed processing information
        """
        self.output_dir = Path(output_dir) if output_dir else config.get_input_dir()
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.property_cdm = PropertyCDM()
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
        self.log(f"Output directory: {self.output_dir}", "INFO")

        # Load actual gauge IDs from gauge.json for ReferenceGauges mapping
        self._gauge_id_map = {}  # index -> actual UUID
        gauge_file = self.output_dir / 'gauge.json'
        if gauge_file.exists():
            try:
                with open(gauge_file) as f:
                    gauge_portfolio = json.load(f)
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

        # Access the schema from the PropertyCDM instance
        schema = self.property_cdm.schema
        self.log("Schema loaded from PropertyCDM", "DEBUG")

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

        # Save to JSON file
        self.log("Saving property data to JSON file...", "INFO")
        output_path = self.output_dir / "property.json"

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

            with open(output_path, 'w') as f:
                json.dump(output_data, f, indent=2, cls=DateTimeEncoder)

            self.log(f"Property data saved successfully to: {output_path}", "INFO")

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
        self.log(f"Output file: {output_path}", "INFO")

        return {
            "data": {
                "properties": properties,
                "property_ids": property_ids,
                "locations": locations
            },
            "file_path": output_path,
            "processing_stats": self.processing_stats
        }


def generate_properties(
    count: int = 200,
    output_dir: Optional[Path] = None,
    catchment_id: Optional[str] = None
) -> Dict:
    """
    Convenience function to generate property portfolio.

    If catchment_id is provided, set config.CATCHMENT accordingly before loading
    random/params modules, otherwise use existing config.CATCHMENT.
    """
    if catchment_id is not None:
        config.CATCHMENT = catchment_id.lower()

    generator = PropertyPortfolioGenerator(output_dir=output_dir)
    return generator.generate(count=count)
