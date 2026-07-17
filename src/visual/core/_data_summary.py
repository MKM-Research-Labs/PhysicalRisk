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

"""
DataLoader reporting helpers.

Pulled out of ``data_loader.py`` so the main DataLoader class stays
focused on load orchestration. These helpers consume a fully-loaded
``DataLoader`` instance and produce log output / summary dicts.
"""

import logging
from typing import Any, Dict

from loaders import analyze_id_relationships

logger = logging.getLogger(__name__)


def print_relationship_analysis(loader) -> None:
    """Log ID relationship analysis for property / mortgage / hazard data."""
    logger.info("Analyzing ID relationships...")

    analysis = analyze_id_relationships(
        property_data=loader.loaded_data.property_data,
        rloan_data=loader.loaded_data.rloan_data,
        flood_risk_data=loader.loaded_data.property_hazard_data
    )

    counts = analysis["counts"]
    overlaps = analysis["overlaps"]

    logger.info(f"Properties: {counts['properties']}")
    logger.info(f"Mortgages: {counts['loans']}")
    logger.info(
        f"Properties with mortgages: {overlaps['properties_with_loans']}/"
        f"{counts['properties']}"
    )
    logger.info(
        f"Properties with flood risk: {overlaps['properties_with_flood_risk']}/"
        f"{counts['properties']}"
    )
    logger.info(
        f"Mortgages with flood risk: {overlaps['loans_with_flood_risk']}/"
        f"{counts['loans']}"
    )


def print_loading_summary(loader) -> None:
    """Log a one-line-per-section summary of the loaded data."""
    d = loader.loaded_data

    gauge_count = d.gauge_data.get("count", 0) if d.gauge_data else 0
    prop_count = d.property_data.get("count", 0) if d.property_data else 0
    mort_count = d.rloan_data.get("count", 0) if d.rloan_data else 0
    hc_count = len(d.hazard_data.get("hazard_curves", {})) if d.hazard_data else 0
    phc_count = (
        len(d.property_hazard_data.get("property_hazard_curves", {}))
        if d.property_hazard_data else 0
    )

    logger.info("DATA LOADING SUMMARY")
    logger.info(
        f"Portfolio:   {gauge_count} gauges | {prop_count} properties | "
        f"{mort_count} mortgages"
    )
    logger.info(f"Hazard:      {hc_count} gauge curves | {phc_count} property curves")
    logger.info(f"Storms:      {'loaded' if d.storm_data else 'not loaded'}")
    logger.info(
        f"Timeseries:  {d.gaugets_count} gaugets | {d.gaugehd_count} gaugehd | "
        f"{d.propertyts_count} propertyts"
    )
    logger.info(
        f"Lookups:     {len(d.gauge_flood_info or {})} gauge flood | "
        f"{len(d.property_flood_info or {})} property flood | "
        f"{len(d.rloan_lookup or {})} mortgage"
    )


def build_data_summary(loader) -> Dict[str, Any]:
    """Build a per-data-type summary dict (loaded, warning count, error count)."""
    summary = {}
    for data_type, validation in loader._validation_results.items():
        summary[data_type] = {
            "loaded": validation.is_valid,
            "summary": validation.summary,
            "warnings": len(validation.warnings),
            "errors": len(validation.errors),
        }
    return summary
