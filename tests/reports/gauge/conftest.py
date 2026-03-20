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

"""Shared fixtures for single gauge analysis tests."""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def sample_gauge() -> Dict[str, Any]:
    """Single Thames gauge for testing - Teddington Lock."""
    return {
        "gauge_id": "THAMES_TEDDINGTON",
        "station_name": "Teddington Lock",
        "river_name": "Thames",
        "catchment": "Thames",
        "latitude": 51.4310,
        "longitude": -0.3215,
        "datum_elevation": 2.5,
        "typical_range_min": 0.5,
        "typical_range_max": 4.5,
        "flood_alert_level": 5.0,
        "flood_warning_level": 5.5,
        "severe_flood_level": 6.5,
        "status": "active",
        "data_provider": "Environment Agency"
    }


@pytest.fixture
def sample_gauges_df() -> pd.DataFrame:
    """DataFrame with multiple Thames gauges."""
    gauges = [
        {
            "gauge_id": "THAMES_TEDDINGTON",
            "station_name": "Teddington Lock",
            "river_name": "Thames",
            "latitude": 51.4310,
            "longitude": -0.3215,
            "datum_elevation": 2.5,
            "flood_alert_level": 5.0,
            "flood_warning_level": 5.5,
            "severe_flood_level": 6.5,
        },
        {
            "gauge_id": "THAMES_RICHMOND",
            "station_name": "Richmond Lock",
            "river_name": "Thames",
            "latitude": 51.4613,
            "longitude": -0.3098,
            "datum_elevation": 2.2,
            "flood_alert_level": 4.7,
            "flood_warning_level": 5.2,
            "severe_flood_level": 6.2,
        },
        {
            "gauge_id": "THAMES_KEW",
            "station_name": "Kew Bridge",
            "river_name": "Thames",
            "latitude": 51.4875,
            "longitude": -0.2889,
            "datum_elevation": 1.8,
            "flood_alert_level": 4.3,
            "flood_warning_level": 4.8,
            "severe_flood_level": 5.8,
        },
        {
            "gauge_id": "THAMES_KINGSTON",
            "station_name": "Kingston",
            "river_name": "Thames",
            "latitude": 51.4109,
            "longitude": -0.3065,
            "datum_elevation": 3.0,
            "flood_alert_level": 5.2,
            "flood_warning_level": 5.7,
            "severe_flood_level": 6.7,
        },
    ]
    return pd.DataFrame(gauges)


@pytest.fixture
def normal_readings() -> List[Dict[str, Any]]:
    """Normal gauge readings - no flood."""
    base_time = datetime(2024, 1, 15, 0, 0, 0)
    readings = []
    for i in range(24):
        readings.append({
            "timestamp": (base_time + timedelta(hours=i)).isoformat(),
            "level": 3.0 + 0.3 * np.sin(i * np.pi / 12),
            "flow_rate": 150 + 20 * np.sin(i * np.pi / 12),
            "quality": "good"
        })
    return readings


@pytest.fixture
def flood_event_readings() -> List[Dict[str, Any]]:
    """Flood event readings - exceeds warning level."""
    base_time = datetime(2024, 1, 15, 0, 0, 0)
    readings = []
    for i in range(48):
        hour = i
        flood_component = 3.0 * np.exp(-((hour - 24) ** 2) / 100)
        level = 3.5 + flood_component
        readings.append({
            "timestamp": (base_time + timedelta(hours=i)).isoformat(),
            "level": round(level, 3),
            "flow_rate": round(100 + flood_component * 150, 1),
            "quality": "good"
        })
    return readings


@pytest.fixture
def severe_flood_readings() -> List[Dict[str, Any]]:
    """Severe flood readings - exceeds severe level."""
    base_time = datetime(2024, 1, 15, 0, 0, 0)
    readings = []
    for i in range(48):
        hour = i
        flood_component = 5.0 * np.exp(-((hour - 24) ** 2) / 80)
        level = 3.5 + flood_component
        readings.append({
            "timestamp": (base_time + timedelta(hours=i)).isoformat(),
            "level": round(level, 3),
            "flow_rate": round(100 + flood_component * 200, 1),
            "quality": "good"
        })
    return readings


@pytest.fixture
def thames_input_dir(tmp_path, sample_gauges_df, flood_event_readings) -> Path:
    """Create temporary input directory with gauge test data."""
    input_dir = tmp_path / "input" / "thames"
    input_dir.mkdir(parents=True)

    gauge_file = input_dir / "gauge.json"
    gauge_file.write_text(json.dumps({
        "flood_gauges": sample_gauges_df.to_dict(orient='records')
    }, indent=2))

    time_series = []
    for gauge_id in sample_gauges_df['gauge_id']:
        time_series.append({
            "gauge_id": gauge_id,
            "station_name": sample_gauges_df[sample_gauges_df['gauge_id'] == gauge_id]['station_name'].iloc[0],
            "readings": flood_event_readings
        })

    ts_file = input_dir / "gauge_floodts.json"
    ts_file.write_text(json.dumps({
        "generated_at": datetime.now().isoformat(),
        "time_series": time_series
    }, indent=2))

    return input_dir
