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

"""Batch processor and CLI entry point for gaugehd CDM."""

import logging
from pathlib import Path
from typing import List, Optional

from config import config

from .generator import GaugeHistoricalDaily

logger = logging.getLogger(__name__)


def process_directory(input_dir: Path, output_dir: Optional[Path] = None,
                      years: int = 50, pattern: str = "*_gdf.csv") -> List[str]:
    """
    Process all NRFA gauge files in a directory.

    Args:
        input_dir: Directory containing NRFA CSV files
        output_dir: Directory for output JSON files (defaults to input_dir)
        years: Number of years of history to include
        pattern: Glob pattern for input files

    Returns:
        List of generated file paths
    """
    generator = GaugeHistoricalDaily(years_of_history=years)
    generated_files = []

    if output_dir is None:
        output_dir = input_dir

    for csv_file in input_dir.glob(pattern):
        station_id = csv_file.stem.replace('_gdf', '')
        output_file = output_dir / f"gaugehd_{station_id}.json"

        try:
            generator.generate(csv_file, output_file, years)
            generated_files.append(str(output_file))
        except Exception as e:
            logger.error("Error processing %s: %s", csv_file, e)

    logger.info("Processed %d gauge files", len(generated_files))
    return generated_files


def main():
    """Example usage of the gauge historical daily generator."""
    logger.info("=" * 70)
    logger.info("Gauge Historical Daily (gaugehd) Generator")
    logger.info("=" * 70)

    input_dir = config.input_dir
    csv_files = list(input_dir.glob("*_gdf.csv"))

    if csv_files:
        logger.info("Found %d GDF files in %s", len(csv_files), input_dir)
        generator = GaugeHistoricalDaily(years_of_history=50)

        for csv_file in csv_files:
            logger.info("Processing: %s", csv_file.name)
            try:
                generator.generate(csv_file, years=50)
            except Exception as e:
                logger.error("Error: %s", e)
    else:
        logger.info("No GDF files found in %s", input_dir)
        logger.info("Place NRFA *_gdf.csv files in the input directory and run again.")
        logger.info("Example usage:")
        logger.info("  generator = GaugeHistoricalDaily()")
        logger.info("  generator.generate(Path('39001_gdf.csv'))")


if __name__ == "__main__":
    main()
