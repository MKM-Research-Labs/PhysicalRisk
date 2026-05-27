# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Batch runners: generate_all_gauge_histories, process_nrfa_directory, main."""

import logging
from pathlib import Path
from typing import List, Optional

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
        List of generated file paths
    """
    generated_files = []

    gauges = load_gauge_portfolio()
    logger.info("Found %d gauges in portfolio", len(gauges))

    # Remove stale gauge history files from previous runs (GAUGE-* and SYNTH-*)
    gaugehd_dir = config.get_gaugehd_dir()
    for stale in gaugehd_dir.glob('gauge_GAUGE-*_hd.json'):
        stale.unlink()
    for stale in gaugehd_dir.glob('gauge_SYNTH-*_hd.json'):
        stale.unlink()

    logger.info("Output directory: %s", gaugehd_dir)

    for gauge_entry in gauges:
        try:
            result = generate_from_gauge_portfolio(gauge_entry, years=years)
            gauge_id = result["gauge_metadata"]["gauge_id"]
            output_path = config.get_gaugehd_dir() / f"gauge_{gauge_id}_hd.json"
            generated_files.append(str(output_path))
        except Exception as e:
            gauge_id = gauge_entry.get("FloodGauge", {}).get("Header", {}).get("GaugeID", "UNKNOWN")
            logger.error("Error processing %s: %s", gauge_id, e)

    logger.info("Generated %d gauge history files", len(generated_files))
    return generated_files


def process_nrfa_directory(
    input_dir: Path,
    output_dir: Optional[Path] = None,
    years: int = 50,
    pattern: str = "*_gdf.csv"
) -> List[str]:
    """
    Process all NRFA gauge files in a directory.

    Args:
        input_dir: Directory containing NRFA CSV files
        output_dir: Directory for output JSON files (defaults to gaugehd dir)
        years: Number of years of history to include
        pattern: Glob pattern for input files

    Returns:
        List of generated file paths
    """
    generated_files = []

    if output_dir is None:
        output_dir = config.get_gaugehd_dir()

    for csv_file in input_dir.glob(pattern):
        station_id = csv_file.stem.replace('_gdf', '')
        output_file = output_dir / f"gauge_{station_id}_hd.json"

        try:
            generate_from_nrfa(csv_file, output_file, years)
            generated_files.append(str(output_file))
        except Exception as e:
            logger.error("Error processing %s: %s", csv_file, e)

    logger.info("Processed %d NRFA gauge files", len(generated_files))
    return generated_files


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
