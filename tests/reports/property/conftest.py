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

"""Shared fixtures for single property flood risk analysis tests."""

import json
from pathlib import Path
from typing import Any, Dict

import pandas as pd
import pytest


@pytest.fixture
def sample_property() -> Dict[str, Any]:
    """Single Thames property for testing."""
    return {
        "property_id": "THAMES_TEST_001",
        "address": "123 River Street, Teddington, London",
        "latitude": 51.4310,
        "longitude": -0.3215,
        "elevation": 8.5,
        "property_type": "residential",
        "value": 750000,
        "floor_level_metres": 0.15,
        "construction_year": 1985,
        "floors": 2,
        "has_basement": False,
    }


@pytest.fixture
def sample_properties_df(sample_property) -> pd.DataFrame:
    """DataFrame with multiple test properties."""
    properties = [
        sample_property,
        {
            "property_id": "THAMES_TEST_002",
            "address": "45 Flood Lane, Richmond",
            "latitude": 51.4613,
            "longitude": -0.3037,
            "elevation": 5.2,
            "property_type": "residential",
            "value": 950000,
            "floor_level_metres": 0.0,
            "construction_year": 1920,
            "floors": 3,
            "has_basement": True,
        },
        {
            "property_id": "THAMES_TEST_003",
            "address": "78 High Ground Ave, Hampstead",
            "latitude": 51.5565,
            "longitude": -0.1780,
            "elevation": 25.0,
            "property_type": "residential",
            "value": 1500000,
            "floor_level_metres": 0.3,
            "construction_year": 2010,
            "floors": 2,
            "has_basement": False,
        },
    ]
    return pd.DataFrame(properties)


@pytest.fixture
def sample_gauges() -> pd.DataFrame:
    """Sample Thames flood gauges."""
    gauges = [
        {
            "gauge_id": "THAMES_TEDDINGTON",
            "station_name": "Teddington Lock",
            "latitude": 51.4310,
            "longitude": -0.3215,
            "flood_warning_level": 5.5,
            "datum_elevation": 2.5,
        },
        {
            "gauge_id": "THAMES_RICHMOND",
            "station_name": "Richmond Lock",
            "latitude": 51.4613,
            "longitude": -0.3098,
            "flood_warning_level": 5.2,
            "datum_elevation": 2.2,
        },
        {
            "gauge_id": "THAMES_KEW",
            "station_name": "Kew Bridge",
            "latitude": 51.4875,
            "longitude": -0.2889,
            "flood_warning_level": 4.8,
            "datum_elevation": 1.8,
        },
    ]
    return pd.DataFrame(gauges)


@pytest.fixture
def sample_gauge_readings() -> Dict[str, list]:
    """Sample gauge readings with flood event."""
    return {
        "THAMES_TEDDINGTON": [
            {"timestamp": "2024-01-15T00:00:00", "level": 4.2},
            {"timestamp": "2024-01-15T02:00:00", "level": 4.8},
            {"timestamp": "2024-01-15T04:00:00", "level": 5.5},
            {"timestamp": "2024-01-15T06:00:00", "level": 6.2},
            {"timestamp": "2024-01-15T08:00:00", "level": 5.8},
            {"timestamp": "2024-01-15T10:00:00", "level": 5.1},
            {"timestamp": "2024-01-15T12:00:00", "level": 4.5},
        ],
        "THAMES_RICHMOND": [
            {"timestamp": "2024-01-15T00:00:00", "level": 3.8},
            {"timestamp": "2024-01-15T02:00:00", "level": 4.3},
            {"timestamp": "2024-01-15T04:00:00", "level": 5.0},
            {"timestamp": "2024-01-15T06:00:00", "level": 5.6},
            {"timestamp": "2024-01-15T08:00:00", "level": 5.2},
            {"timestamp": "2024-01-15T10:00:00", "level": 4.6},
            {"timestamp": "2024-01-15T12:00:00", "level": 4.0},
        ],
    }


@pytest.fixture
def thames_input_dir(tmp_path, sample_properties_df, sample_gauges, sample_gauge_readings) -> Path:
    """Create temporary input directory with test data files."""
    input_dir = tmp_path / "input" / "thames"
    input_dir.mkdir(parents=True)

    (input_dir / "property.json").write_text(json.dumps(
        {"properties": sample_properties_df.to_dict(orient="records")}, indent=2
    ))

    (input_dir / "gauge.json").write_text(json.dumps(
        {"flood_gauges": sample_gauges.to_dict(orient="records")}, indent=2
    ))

    time_series = [
        {"gauge_id": gid, "readings": readings}
        for gid, readings in sample_gauge_readings.items()
    ]
    (input_dir / "gauge_floodts.json").write_text(json.dumps(
        {"time_series": time_series}, indent=2
    ))

    return input_dir
