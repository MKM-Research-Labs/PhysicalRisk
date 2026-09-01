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
Synthetic timeseries generation for flood gauges.

Creates realistic daily water level timeseries that respect:
- Gauge-specific flood thresholds (FloodAlert, FloodWarning, SevereFloodWarning)
- Historical high levels and dates from the gauge portfolio
- Seasonal patterns (higher levels in winter)
- Appropriate flood frequency based on historical records
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

import database
from config import config
from models.statistics.synthetic import generate_synthetic_timeseries  # noqa: F401
from models.statistics.timeseries import calculate_level_statistics

logger = logging.getLogger(__name__)


def generate_from_gauge_portfolio(
    gauge_data: Dict[str, Any],
    catchment: Optional[str] = None,
    years: int = 50
) -> Dict[str, Any]:
    """
    Generate historical daily JSON from gauge portfolio data.

    Args:
        gauge_data: Single gauge entry from the gauge portfolio
        catchment: Catchment to store under (defaults to ``database.active_catchment()``)
        years: Years of history to generate

    Returns:
        The generated data dictionary
    """
    # Extract gauge info
    flood_gauge = gauge_data.get("FloodGauge", gauge_data)
    header = flood_gauge.get("Header", {})
    flood_stages = flood_gauge.get("FloodStages", {})
    location = flood_gauge.get("Location", {})

    gauge_id = header.get("GaugeID", "UNKNOWN")
    gauge_name = header.get("GaugeName", "")
    catchment_id = header.get("CatchmentID", config.CATCHMENT)

    # Generate synthetic timeseries with reproducible seed
    seed = hash(gauge_id) % (2**32)
    daily_observations = generate_synthetic_timeseries(gauge_data, years=years, seed=seed)


    # Calculate statistics
    stats = calculate_level_statistics(daily_observations, flood_stages)


    # Build output structure
    output_data = {
        "schema_version": "1.0",
        "data_type": "GaugeHistoricalDaily",
        "generated_at": datetime.now().isoformat(),
        "generator": "gaugehd.py",
        "generation_mode": "synthetic",
        "years_included": years,
        "gauge_metadata": {
            "gauge_id": gauge_id,
            "gauge_name": gauge_name,
            "catchment_id": catchment_id,
            "latitude": location.get("GaugeLatitude"),
            "longitude": location.get("GaugeLongitude"),
            "elevation": location.get("GaugeElevation"),
            "flood_stages": flood_stages,
        },
        "statistics": stats,
        "daily_observations": daily_observations,
    }

    # Persist through the database seam (keyed gauge_history artifact).
    if catchment is None:
        catchment = database.active_catchment()
    database.save_gauge_history(catchment, gauge_id, output_data)

    logger.info("Generated gauge history for %s (%s)", gauge_name, gauge_id)
    logger.info("Records: %d days (%s years)", len(daily_observations), stats.get('total_years', 0))
    logger.info("Period: %s to %s", stats.get('record_start', 'N/A'), stats.get('record_end', 'N/A'))
    logger.info("Mean Level: %s m", stats.get('mean_level', 'N/A'))
    logger.info("Max Level: %s m on %s", stats.get('max_level', 'N/A'), stats.get('max_level_date', 'N/A'))

    return output_data
