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
Flood Gauge Portfolio Generator.

This module generates synthetic flood gauge data based on the FloodGaugeCDM schema.
Random value generation is delegated to catchment-specific modules in port.random.

Usage:
    from port.src.gauge import GaugePortfolioGenerator, generate_gauges

    # Option 1: Use convenience function (uses config.CATCHMENT)
    result = generate_gauges(count=40)

    # Option 2: Use generator class with config defaults
    generator = GaugePortfolioGenerator()
    result = generator.generate(count=40)

    # Option 3: Explicit module injection
    from port.random.thames import gauge_random, params
    generator = GaugePortfolioGenerator(
        random_module=gauge_random,
        catchment_params=params
    )
    result = generator.generate(count=40)
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union

import numpy as np

from config import config
from port.cdm import FloodGaugeCDM

logger = logging.getLogger(__name__)

class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle datetime objects."""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)


class GaugePortfolioGenerator:
    """
    Flood Gauge Portfolio Generator.

    Generates synthetic flood gauge data based on CDM schema.
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
        Initialize the Flood Gauge Portfolio Generator.

        Args:
            output_dir: Directory to save generated files (defaults to config.get_input_dir())
            random_module: Catchment-specific random value generator module
                          (defaults to port.random.{CATCHMENT}.gauge_random)
            catchment_params: Catchment parameters module
                             (defaults to port.random.{CATCHMENT}.params)
            verbose: Enable detailed processing information
        """
        # Use config defaults if not provided
        self.output_dir = Path(output_dir) if output_dir else config.get_input_dir()
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.flood_gauge_cdm = FloodGaugeCDM()
        self.verbose = verbose
        if not verbose:
            logging.getLogger(__name__).setLevel(logging.WARNING)

        # Load catchment-specific modules from config if not provided
        self.random = random_module or config.load_random_module('gauge.gauge_random')
        self.params = catchment_params or config.load_params_module()

        # Get catchment name for gauge naming
        self.catchment_name = getattr(self.params, 'DISPLAYNAME',
                                      getattr(self.params, 'NAME',
                                             config.CATCHMENT.capitalize()))

        # Processing statistics
        self.processing_stats = {
            'total_gauges': 0,
            'successful_gauges': 0,
            'failed_gauges': 0,
            'elevation_successes': 0,
            'elevation_failures': 0,
            'start_time': None,
            'end_time': None
        }

    def log(self, message: str, level: str = "INFO"):
        """Log processing information."""
        log_func = getattr(logger, level.lower(), logger.info)
        log_func(message)

    def generate(self, count: int = 40) -> Dict:
        """
        Generate synthetic flood gauge data.

        Args:
            count: Number of flood gauges to generate

        Returns:
            Dictionary containing generated data, file path, and processing information
        """
        self.processing_stats['start_time'] = datetime.now()
        self.processing_stats['total_gauges'] = count

        self.log("=" * 60, "INFO")
        self.log("FLOOD GAUGE PORTFOLIO GENERATOR", "INFO")
        self.log("=" * 60, "INFO")
        self.log(f"Catchment: {config.CATCHMENT}", "INFO")
        self.log(f"Target gauge count: {count}", "INFO")
        self.log(f"Output directory: {self.output_dir}", "INFO")

        # Get gauge points from catchment params
        gauge_points = self.params.GAUGE_POINTS
        areas = self.params.AREAS
        gauge_names = getattr(self.params, 'GAUGE_NAMES', None)

        # Validate gauge count against available points
        max_gauges = len(gauge_points)
        if count < 1:
            self.log(f"Invalid gauge count: {count}. Must be at least 1.", "ERROR")
            raise ValueError(f"Gauge count must be at least 1, got {count}")

        if count > max_gauges:
            self.log(f"Requested {count} gauges but only {max_gauges} points available", "WARNING")
            self.log(f"Reducing gauge count to {max_gauges}", "INFO")
            count = max_gauges
            self.processing_stats['total_gauges'] = count

        self.log(f"Generating {count} gauges from {max_gauges} available points", "INFO")

        # Create gauge locations from catchment points
        self.log("Creating gauge locations from catchment points...", "INFO")
        selected_locations = []

        for i in range(count):
            lat, lon, elevation = gauge_points[i]
            area_index = i % len(areas)
            area_name = areas[area_index]
            short_name = gauge_names[i] if gauge_names and i < len(gauge_names) else f"{area_name}_Point_{i}"

            location = {
                "lat": lat,
                "lon": lon,
                "name": short_name,
                "area": area_name,
                "distance_to_river": 0,
                "elevation": elevation
            }
            selected_locations.append(location)

            if i < 5:
                self.log(f"Point {i}: {short_name} ({area_name}) at ({lat:.5f}, {lon:.5f}), elevation: {elevation:.1f}m", "DEBUG")

        self.log(f"Selected {len(selected_locations)} gauge locations", "SUCCESS")

        # Access the schema from the FloodGaugeCDM instance
        schema = self.flood_gauge_cdm.schema
        self.log("Schema loaded from FloodGaugeCDM", "DEBUG")

        # Generate gauges
        self.log("Starting gauge generation process...", "INFO")
        gauges = []
        gauge_ids = []

        for i, location in enumerate(selected_locations):
            self.log(f"Generating gauge {i+1}/{count} at {location['name']}", "INFO")
            try:
                gauge_data, gauge_id = self._generate_single_gauge(i, schema, location)
                gauges.append(gauge_data)
                gauge_ids.append(gauge_id)
                self.processing_stats['successful_gauges'] += 1

                gauge_name = gauge_data.get('FloodGauge', {}).get('Header', {}).get('GaugeName', 'Unknown')
                elevation = location['elevation']
                self.log(f"Gauge {i+1} created: {gauge_name} (ID: {gauge_id[:12]}...) at {elevation:.1f}m", "SUCCESS")

            except Exception as e:
                self.log(f"Failed to generate gauge {i+1}: {str(e)}", "ERROR")
                self.processing_stats['failed_gauges'] += 1
                continue

        # Save to JSON file
        self.log("Saving gauge data to JSON file...", "INFO")
        output_path = self.output_dir / "gauge.json"

        try:
            serializable_stats = self.processing_stats.copy()
            if serializable_stats.get('start_time'):
                serializable_stats['start_time'] = serializable_stats['start_time'].isoformat()
            if serializable_stats.get('end_time'):
                serializable_stats['end_time'] = serializable_stats['end_time'].isoformat()

            output_data = {
                "flood_gauges": gauges,
                "generation_metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "generator_version": "Refactored v3.0",
                    "catchment": config.CATCHMENT,
                    "total_gauges_generated": len(gauges),
                    "points_used": len(selected_locations),
                    "processing_stats": serializable_stats
                }
            }

            with open(output_path, 'w') as f:
                json.dump(output_data, f, indent=2, cls=DateTimeEncoder)

            self.log(f"Gauge data saved successfully to: {output_path}", "SUCCESS")

        except Exception as e:
            self.log(f"Error saving gauge data: {str(e)}", "ERROR")
            raise

        # Update processing statistics
        self.processing_stats['end_time'] = datetime.now()
        processing_time = (self.processing_stats['end_time'] - self.processing_stats['start_time']).total_seconds()

        # Final summary
        self.log("=" * 60, "INFO")
        self.log("GENERATION COMPLETE", "SUCCESS")
        self.log("=" * 60, "INFO")
        self.log(f"Successfully generated: {self.processing_stats['successful_gauges']}/{self.processing_stats['total_gauges']} gauges", "SUCCESS")
        self.log(f"Failed generations: {self.processing_stats['failed_gauges']}", "INFO" if self.processing_stats['failed_gauges'] == 0 else "WARNING")
        self.log(f"Processing time: {processing_time:.2f} seconds", "INFO")
        self.log(f"Output file: {output_path}", "INFO")

        return {
            "data": {
                "flood_gauges": gauges,
                "gauge_ids": gauge_ids,
                "locations": selected_locations
            },
            "file_path": output_path,
            "processing_stats": self.processing_stats
        }

    def _generate_single_gauge(self, index: int, schema: Dict, location: Dict) -> tuple:
        """Generate a single flood gauge data structure."""
        metadata = self.random.generate_gauge_metadata(index, location, self.catchment_name)
        gauge_id = metadata['gauge_id']

        self.log(f"  Creating gauge {gauge_id} at location {location['name']}", "DEBUG")
        self.log(f"  Generated levels: Alert={metadata['flood_alert']:.1f}m, Warning={metadata['flood_warning']:.1f}m, Severe={metadata['severe_flood_warning']:.1f}m", "DEBUG")

        gauge_data = self._build_section(schema, index, metadata)
        self._set_specific_gauge_values(gauge_data, gauge_id, index, metadata)

        return gauge_data, gauge_id

    def _build_section(self, section_schema: Dict, index: int, metadata: Dict) -> Dict:
        """Recursively build a section of flood gauge data based on the schema."""
        result = {}

        if not isinstance(section_schema, dict):
            return {}

        for field_name, field_def in section_schema.items():
            if field_name in ['type', 'options', 'description', 'values']:
                continue

            if isinstance(field_def, dict) and not field_def.get("type"):
                result[field_name] = self._build_section(field_def, index, metadata)
            else:
                value = self.random.generate_field_value(field_name, field_def, index, metadata)
                if value is not None:
                    result[field_name] = value

        return result

    def _set_specific_gauge_values(self, gauge_data: Dict, gauge_id: str, index: int, metadata: Dict):
        """Set specific gauge values that need to be consistent across sections."""
        location = metadata['location']

        if 'FloodGauge' not in gauge_data:
            gauge_data['FloodGauge'] = {}
        if 'Header' not in gauge_data['FloodGauge']:
            gauge_data['FloodGauge']['Header'] = {}

        header = gauge_data['FloodGauge']['Header']
        header['GaugeID'] = gauge_id
        header['CatchmentID'] = config.CATCHMENT

        if 'Location' not in gauge_data['FloodGauge']:
            gauge_data['FloodGauge']['Location'] = {}

        loc = gauge_data['FloodGauge']['Location']
        loc['GaugeLatitude'] = location['lat']
        loc['GaugeLongitude'] = location['lon']
        loc['GaugeElevation'] = location['elevation']

        if 'FloodStages' not in gauge_data['FloodGauge']:
            gauge_data['FloodGauge']['FloodStages'] = {}

        stages = gauge_data['FloodGauge']['FloodStages']
        stages['FloodAlert'] = round(metadata['flood_alert'], 2)
        stages['FloodWarning'] = round(metadata['flood_warning'], 2)
        stages['SevereFloodWarning'] = round(metadata['severe_flood_warning'], 2)
        stages['HistoricalHighLevel'] = round(metadata['historical_high_level'], 2)
        stages['HistoricalHighDate'] = metadata['historical_high_date']


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================

def generate_gauges(count: int = 40, output_dir: Optional[Path] = None) -> Dict:
    """
    Convenience function to generate flood gauge portfolio for current catchment.

    Uses config.CATCHMENT to determine which random module and params to use.

    Args:
        count: Number of gauges to generate
        output_dir: Output directory (defaults to config.get_input_dir())

    Returns:
        Generation result dictionary
    """
    generator = GaugePortfolioGenerator(output_dir=output_dir)
    return generator.generate(count=count)


if __name__ == "__main__":
    logger.info(f"Generating gauges for catchment: {config.CATCHMENT}")
    result = generate_gauges(count=40)
    logger.info(f"Generated {len(result['data']['flood_gauges'])} gauges.")
    logger.info(f"Output saved to: {result['file_path']}")
