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

"""Batch runners: generate_all_gauge_histories, process_nrfa_directory, main."""

import logging
from pathlib import Path
from typing import List

import database
from config import config

from .loader import load_gauge_portfolio
from .nrfa import generate_from_nrfa
from .synthetic import generate_from_gauge_portfolio

logger = logging.getLogger(__name__)


def generate_all_gauge_histories(years: int = 50) -> List[str]:
    """
    Generate historical daily timeseries for all gauges in the portfolio.

    Args:
        years: Number of years of history to generate

    Returns:
        List of generated gauge IDs
    """
    generated_ids = []

    catchment = database.active_catchment()
    gauges = load_gauge_portfolio(catchment)
    logger.info("Found %d gauges in portfolio", len(gauges))

    # Remove stale per-gauge histories from previous runs, then write fresh.
    for stale_id in list(database.iter_gauge_history_ids(catchment)):
        database.delete_gauge_history(catchment, stale_id)

    for gauge_entry in gauges:
        try:
            result = generate_from_gauge_portfolio(gauge_entry, catchment=catchment, years=years)
            generated_ids.append(result["gauge_metadata"]["gauge_id"])
        except Exception as e:
            gauge_id = gauge_entry.get("FloodGauge", {}).get("Header", {}).get("GaugeID", "UNKNOWN")
            logger.error("Error processing %s: %s", gauge_id, e)

    logger.info("Generated %d gauge history records for catchment %s", len(generated_ids), catchment)
    return generated_ids


def process_nrfa_directory(
    input_dir: Path,
    years: int = 50,
    pattern: str = "*_gdf.csv"
) -> List[str]:
    """
    Process all NRFA gauge files in a directory.

    Args:
        input_dir: Directory containing NRFA CSV files (external source data)
        years: Number of years of history to include
        pattern: Glob pattern for input files

    Returns:
        List of generated gauge IDs
    """
    generated_ids = []
    catchment = database.active_catchment()

    for csv_file in input_dir.glob(pattern):
        station_id = csv_file.stem.replace('_gdf', '')
        try:
            generate_from_nrfa(csv_file, catchment=catchment, years=years)
            generated_ids.append(station_id)
        except Exception as e:
            logger.error("Error processing %s: %s", csv_file, e)

    logger.info("Processed %d NRFA gauge files for catchment %s", len(generated_ids), catchment)
    return generated_ids


def main():
    """Main entry point for gauge historical data generation."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate historical daily timeseries for flood gauges"
    )
    parser.add_argument("--years", "-y", type=int, default=50)
    parser.add_argument("--catchment", "-c", type=str, default=None)
    parser.add_argument("--nrfa-dir", type=Path, default=None)

    args = parser.parse_args()

    if args.catchment:
        config.catchment_id = args.catchment

    logger.info("=" * 70)
    logger.info("Gauge Historical Daily (gaugehd) Generator")
    logger.info("=" * 70)
    logger.info(f"Catchment: {config.CATCHMENT}")
    logger.info(f"Years of history: {args.years}")
    logger.info(f"Output directory: {config.get_gaugehd_dir()}")

    if args.nrfa_dir:
        logger.info(f"Processing NRFA files from: {args.nrfa_dir}")
        process_nrfa_directory(args.nrfa_dir, years=args.years)
    else:
        logger.info("Generating synthetic histories from gauge portfolio...")
        generate_all_gauge_histories(years=args.years)
