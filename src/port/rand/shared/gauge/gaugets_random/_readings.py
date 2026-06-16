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

"""Per-gauge reading generation and full flood-simulation time series."""

import logging
import random
from datetime import datetime, timedelta
from typing import Any, Dict, List

from ._levels import DEFAULT_PARAMS, calculate_water_level, determine_alert_status


def generate_gauge_reading(
    hour: int,
    gauge_index: int,
    gauge_data: Dict[str, Any],
    timestamp: datetime,
    params: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Generate a single gauge reading for a specific hour.

    Args:
        hour: Current simulation hour
        gauge_index: Index of the gauge
        gauge_data: Gauge data dictionary from portfolio
        timestamp: Timestamp for this reading
        params: Simulation parameters (uses defaults if None)

    Returns:
        Reading dictionary with water level and alert status
    """
    # Extract gauge info
    flood_gauge = gauge_data.get("FloodGauge", {})
    header = flood_gauge.get("Header", {})
    flood_stages = flood_gauge.get("FloodStages", {})

    gauge_id = header.get("GaugeID", f"GAUGE-{gauge_index}")

    # Get flood levels
    alert_level = flood_stages.get("FloodAlert", 5.0)
    warning_level = flood_stages.get("FloodWarning", 6.0)
    severe_level = flood_stages.get("SevereFloodWarning", 7.0)

    # Calculate base level (below alert)
    base_level = alert_level - 1.0

    # Calculate water level
    water_level = calculate_water_level(hour, gauge_index, base_level, params)

    # Determine alert status
    alert_status = determine_alert_status(water_level, alert_level, warning_level, severe_level)

    return {
        "gaugeId": gauge_id,
        "timestamp": timestamp.isoformat() if isinstance(timestamp, datetime) else timestamp,
        "waterLevel": water_level,
        "alertLevel": alert_level,
        "warningLevel": warning_level,
        "severeLevel": severe_level,
        "alertStatus": alert_status
    }


def generate_timestep_readings(
    hour: int,
    gauges: List[Dict[str, Any]],
    start_time: datetime,
    params: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Generate readings for all gauges at a single timestep.

    Args:
        hour: Current simulation hour
        gauges: List of gauge data dictionaries
        start_time: Simulation start time
        params: Simulation parameters (uses defaults if None)

    Returns:
        Dictionary with 'readings' array for this timestep
    """
    timestamp = start_time + timedelta(hours=hour)

    readings = []
    for i, gauge in enumerate(gauges):
        try:
            reading = generate_gauge_reading(hour, i, gauge, timestamp, params)
            readings.append(reading)
        except Exception as e:
            # Log error but continue with other gauges
            logging.getLogger(__name__).error(f"Error generating reading for gauge {i}: {e}")
            continue

    return {"readings": readings}


def generate_flood_simulation(
    gauges: List[Dict[str, Any]],
    params: Dict[str, Any] = None
) -> List[Dict[str, Any]]:
    """
    Generate complete flood simulation time series.

    Args:
        gauges: List of gauge data dictionaries from portfolio
        params: Simulation parameters (uses defaults if None)

    Returns:
        List of timestep dictionaries, each containing 'readings' array
    """
    if params is None:
        params = DEFAULT_PARAMS

    # Randomise peak hour within configured range
    params = dict(params)
    peak_min = params.get('peak_hour_min', 36)
    peak_max = params.get('peak_hour_max', 60)
    if 'peak_hour_base' not in params:
        params['peak_hour_base'] = random.randint(peak_min, peak_max)

    # Ensure simulation is long enough for recession after late peaks
    simulation_hours = params.get('simulation_hours', 168)
    min_hours = params['peak_hour_base'] + 18
    simulation_hours = max(simulation_hours, min_hours)
    params['simulation_hours'] = simulation_hours

    start_time = params.get('simulation_start_date', datetime.now())

    if isinstance(start_time, str):
        start_time = datetime.fromisoformat(start_time)

    time_series_data = []

    for hour in range(simulation_hours):
        timestep_data = generate_timestep_readings(hour, gauges, start_time, params)
        time_series_data.append(timestep_data)

    return time_series_data


# Alias for backward compatibility
def generate_time_series(
    gauges: List[Dict[str, Any]],
    params: Dict[str, Any] = None
) -> List[Dict[str, Any]]:
    """
    Alias for generate_flood_simulation for backward compatibility.

    Args:
        gauges: List of gauge data dictionaries from portfolio
        params: Simulation parameters (uses defaults if None)

    Returns:
        List of timestep dictionaries, each containing 'readings' array
    """
    return generate_flood_simulation(gauges, params)
