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
Unified statistics calculations for timeseries data.

Works with both synthetic water level data (level_meters) and
NRFA flow data (flow_cumecs) via a configurable value_key.

Computes: basic stats, percentiles, flood exceedance counts,
monthly means, annual maxima, and extreme event detection.
"""

import statistics as stats_lib
from typing import Any, Dict, List, Optional


def calculate_timeseries_statistics(
    observations: List[Dict[str, Any]],
    value_key: str,
    flood_stages: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    Calculate comprehensive statistics from daily timeseries data.

    Handles both synthetic water levels and NRFA flow data by using
    a configurable value_key to extract numeric values.

    Args:
        observations: List of dicts with 'date' and a numeric value field
        value_key: Key for the numeric value (e.g. 'level_meters' or 'flow_cumecs')
        flood_stages: Optional flood thresholds for exceedance analysis
            (keys: FloodAlert, FloodWarning, SevereFloodWarning)

    Returns:
        Dictionary of statistics
    """
    if not observations:
        return {}

    values = [obs[value_key] for obs in observations]
    dates = [obs["date"] for obs in observations]

    # Basic statistics
    result = {
        "record_start": min(dates),
        "record_end": max(dates),
        "total_days": len(values),
        "total_years": round(len(values) / 365.25, 1),
        f"mean_{value_key}": round(stats_lib.mean(values), 3),
        f"median_{value_key}": round(stats_lib.median(values), 3),
        "std_dev": round(stats_lib.stdev(values), 3) if len(values) > 1 else 0,
        f"min_{value_key}": round(min(values), 3),
        f"max_{value_key}": round(max(values), 3),
    }

    # Find max value date
    max_idx = values.index(max(values))
    result[f"max_{value_key}_date"] = dates[max_idx]

    # Percentiles
    sorted_values = sorted(values)
    n = len(sorted_values)

    def percentile(p):
        idx = int(n * p / 100)
        return round(sorted_values[min(idx, n - 1)], 3)

    result["percentiles"] = {
        "p5": percentile(5),
        "p10": percentile(10),
        "p25": percentile(25),
        "p50": percentile(50),
        "p75": percentile(75),
        "p90": percentile(90),
        "p95": percentile(95),
        "p99": percentile(99),
    }

    # Flood exceedance counts (only for level data with thresholds)
    if flood_stages:
        flood_alert = flood_stages.get("FloodAlert", float("inf"))
        flood_warning = flood_stages.get("FloodWarning", float("inf"))
        severe_warning = flood_stages.get("SevereFloodWarning", float("inf"))

        alert_count = sum(1 for obs in observations if obs[value_key] >= flood_alert)
        warning_count = sum(1 for obs in observations if obs[value_key] >= flood_warning)
        severe_count = sum(1 for obs in observations if obs[value_key] >= severe_warning)

        result["flood_exceedances"] = {
            "flood_alert": {
                "threshold": flood_alert,
                "count": alert_count,
                "frequency_per_year": round(alert_count / result["total_years"], 2),
            },
            "flood_warning": {
                "threshold": flood_warning,
                "count": warning_count,
                "frequency_per_year": round(warning_count / result["total_years"], 2),
            },
            "severe_warning": {
                "threshold": severe_warning,
                "count": severe_count,
                "frequency_per_year": round(severe_count / result["total_years"], 2),
            },
        }

    # Q5/Q95 for NRFA flow data
    if value_key == "flow_cumecs":
        result["q95_flow"] = result["percentiles"]["p5"]
        result["q5_flow"] = result["percentiles"]["p95"]

    # Monthly means
    monthly_values = {}
    for obs in observations:
        month = obs["date"][5:7]
        if month not in monthly_values:
            monthly_values[month] = []
        monthly_values[month].append(obs[value_key])

    result["monthly_means"] = {
        month: round(stats_lib.mean(vals), 3)
        for month, vals in sorted(monthly_values.items())
    }

    # Annual maxima
    annual_data = {}
    for obs in observations:
        year = obs["date"][:4]
        if year not in annual_data:
            annual_data[year] = {"max": 0, "max_date": ""}
        if obs[value_key] > annual_data[year]["max"]:
            annual_data[year]["max"] = obs[value_key]
            annual_data[year]["max_date"] = obs["date"]

    annual_maxima = [v["max"] for v in annual_data.values()]
    top_events = sorted(annual_data.items(), key=lambda x: x[1]["max"], reverse=True)[:10]

    result["annual_maxima"] = {
        "mean": round(stats_lib.mean(annual_maxima), 3) if annual_maxima else 0,
        "std_dev": round(stats_lib.stdev(annual_maxima), 3) if len(annual_maxima) > 1 else 0,
        "years_count": len(annual_maxima),
        "events": [
            {"year": y, f"max_{value_key}": round(v["max"], 3), "date": v["max_date"]}
            for y, v in top_events
        ],
    }

    # Extreme events (above P99)
    extreme_threshold = result["percentiles"]["p99"]
    extreme_events = [
        {"date": obs["date"], value_key: obs[value_key]}
        for obs in observations
        if obs[value_key] >= extreme_threshold
    ]

    result["extreme_events"] = {
        "threshold_p99": extreme_threshold,
        "count": len(extreme_events),
        "top_10": sorted(extreme_events, key=lambda x: x[value_key], reverse=True)[:10],
    }

    return result


def calculate_level_statistics(
    daily_observations: List[Dict[str, Any]],
    flood_stages: Dict[str, float]
) -> Dict[str, Any]:
    """
    Calculate statistics from daily water level data.

    Convenience wrapper for synthetic gauge data.

    Args:
        daily_observations: List with 'date' and 'level_meters'
        flood_stages: Flood threshold levels

    Returns:
        Statistics dict with level-specific keys
    """
    raw = calculate_timeseries_statistics(daily_observations, "level_meters", flood_stages)

    # Remap keys for backward compatibility with existing JSON schema
    compat = {}
    for k, v in raw.items():
        new_key = k.replace("level_meters", "level")
        compat[new_key] = v

    return compat


def calculate_flow_statistics(
    daily_flows: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Calculate statistics from daily flow data (NRFA).

    Convenience wrapper for NRFA flow data.

    Args:
        daily_flows: List with 'date' and 'flow_cumecs'

    Returns:
        Statistics dict with flow-specific keys
    """
    raw = calculate_timeseries_statistics(daily_flows, "flow_cumecs")

    # Remap keys for backward compatibility with existing JSON schema
    compat = {}
    for k, v in raw.items():
        new_key = k.replace("flow_cumecs", "flow")
        compat[new_key] = v

    return compat
