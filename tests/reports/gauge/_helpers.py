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

"""Helper functions for single gauge flood analysis tests."""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd


def classify_gauge_status(level: float, gauge: Dict[str, Any]) -> str:
    """Classify gauge flood status based on current level."""
    if level >= gauge.get('severe_flood_level', float('inf')):
        return "SEVERE"
    elif level >= gauge.get('flood_warning_level', float('inf')):
        return "WARNING"
    elif level >= gauge.get('flood_alert_level', float('inf')):
        return "ALERT"
    return "NORMAL"


def get_peak_level(readings: List[Dict]) -> Dict[str, Any]:
    """Get peak level from readings."""
    if not readings:
        return {"level": 0, "timestamp": None}

    peak = max(readings, key=lambda r: r.get('level', 0))
    return {"level": peak['level'], "timestamp": peak['timestamp']}


def get_current_level(readings: List[Dict]) -> float:
    """Get most recent level reading."""
    if not readings:
        return 0.0
    return readings[-1].get('level', 0.0)


def calculate_level_trend(readings: List[Dict], window: int = 4) -> str:
    """Calculate trend from recent readings."""
    if len(readings) < 2:
        return "STABLE"

    recent = readings[-window:] if len(readings) >= window else readings
    levels = [r.get('level', 0) for r in recent]

    diff = levels[-1] - levels[0]

    if diff > 0.1:
        return "RISING"
    elif diff < -0.1:
        return "FALLING"
    return "STABLE"


def calculate_duration_above_threshold(readings: List[Dict], threshold: float) -> float:
    """Calculate hours above threshold level."""
    if len(readings) < 2:
        return 0

    hours_above = 0
    for i in range(1, len(readings)):
        if readings[i].get('level', 0) > threshold:
            t1 = datetime.fromisoformat(readings[i-1]['timestamp'])
            t2 = datetime.fromisoformat(readings[i]['timestamp'])
            hours_above += (t2 - t1).total_seconds() / 3600

    return hours_above


def estimate_annual_exceedance_probability(level: float, gauge: Dict[str, Any]) -> float:
    """Estimate annual probability of exceeding given level."""
    typical_max = gauge.get('typical_range_max', 4.0)
    warning = gauge.get('flood_warning_level', 5.5)
    severe = gauge.get('severe_flood_level', 6.5)

    if level <= typical_max:
        return 0.9
    elif level <= warning:
        frac = (level - typical_max) / (warning - typical_max)
        return 0.9 - frac * 0.7
    elif level <= severe:
        frac = (level - warning) / (severe - warning)
        return 0.2 - frac * 0.15
    else:
        excess = level - severe
        return max(0.01, 0.05 * np.exp(-excess))


def calculate_mean_level(readings: List[Dict]) -> float:
    """Calculate mean water level."""
    levels = [r.get('level', 0) for r in readings]
    return np.mean(levels) if levels else 0.0


def calculate_max_level(readings: List[Dict]) -> float:
    """Calculate maximum level."""
    levels = [r.get('level', 0) for r in readings]
    return max(levels) if levels else 0.0


def calculate_min_level(readings: List[Dict]) -> float:
    """Calculate minimum level."""
    levels = [r.get('level', 0) for r in readings]
    return min(levels) if levels else 0.0


def calculate_level_range(readings: List[Dict]) -> float:
    """Calculate level range."""
    return calculate_max_level(readings) - calculate_min_level(readings)


def calculate_max_rate_of_rise(readings: List[Dict]) -> float:
    """Calculate maximum rate of rise (m/hr)."""
    if len(readings) < 2:
        return 0.0

    max_rate = 0.0
    for i in range(1, len(readings)):
        t1 = datetime.fromisoformat(readings[i-1]['timestamp'])
        t2 = datetime.fromisoformat(readings[i]['timestamp'])
        hours = (t2 - t1).total_seconds() / 3600

        if hours > 0:
            level_diff = readings[i]['level'] - readings[i-1]['level']
            rate = level_diff / hours
            max_rate = max(max_rate, rate)

    return max_rate


def load_gauge_metadata(input_dir: Path) -> pd.DataFrame:
    """Load gauge metadata from JSON."""
    import json
    gauge_file = input_dir / "gauge.json"
    with open(gauge_file, 'r') as f:
        data = json.load(f)
    return pd.DataFrame(data.get('flood_gauges', data))


def load_gauge_readings(input_dir: Path) -> Dict[str, List]:
    """Load gauge time series from JSON."""
    import json
    ts_file = input_dir / "gauge_floodts.json"
    with open(ts_file, 'r') as f:
        data = json.load(f)

    readings = {}
    for ts in data.get('time_series', []):
        readings[ts['gauge_id']] = ts.get('readings', [])
    return readings


def run_single_gauge_test(input_dir: Path, gauge_id: str) -> Dict[str, Any]:
    """Run flood analysis on a single gauge."""
    results = {'success': False, 'gauge': None, 'flood_analysis': None, 'errors': []}

    gauges_df = load_gauge_metadata(input_dir)
    gauge_row = gauges_df[gauges_df['gauge_id'] == gauge_id]

    if len(gauge_row) == 0:
        results['errors'].append(f"Gauge {gauge_id} not found")
        return results

    gauge = gauge_row.iloc[0].to_dict()
    results['gauge'] = gauge

    all_readings = load_gauge_readings(input_dir)
    if gauge_id not in all_readings:
        results['errors'].append(f"No readings for gauge {gauge_id}")
        return results

    readings = all_readings[gauge_id]

    peak = get_peak_level(readings)
    current = get_current_level(readings)
    trend = calculate_level_trend(readings)
    status = classify_gauge_status(current, gauge)
    duration = calculate_duration_above_threshold(
        readings, gauge.get('flood_warning_level', 5.5)
    )

    results['flood_analysis'] = {
        'peak_level': peak['level'],
        'peak_timestamp': peak['timestamp'],
        'current_level': current,
        'trend': trend,
        'status': status,
        'hours_above_warning': duration,
        'mean_level': calculate_mean_level(readings),
        'max_rate_of_rise': calculate_max_rate_of_rise(readings),
    }

    results['success'] = True
    return results


def find_highest_level_gauge(input_dir: Path) -> Dict[str, Any]:
    """Find gauge with highest current level."""
    gauges_df = load_gauge_metadata(input_dir)
    readings = load_gauge_readings(input_dir)

    highest = {'gauge_id': None, 'level': 0}

    for gauge_id in gauges_df['gauge_id']:
        if gauge_id in readings:
            current = get_current_level(readings[gauge_id])
            if current > highest['level']:
                highest = {'gauge_id': gauge_id, 'level': current}

    return highest


def count_gauges_above_warning(input_dir: Path) -> int:
    """Count gauges currently above warning level."""
    gauges_df = load_gauge_metadata(input_dir)
    readings = load_gauge_readings(input_dir)

    count = 0
    for _, gauge in gauges_df.iterrows():
        gauge_id = gauge['gauge_id']
        if gauge_id in readings:
            current = get_current_level(readings[gauge_id])
            if current >= gauge.get('flood_warning_level', float('inf')):
                count += 1

    return count
