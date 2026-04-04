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

"""Shared fixture for PropertyHazardCurve tests."""

import json
import pytest


@pytest.fixture
def output_dir(tmp_path):
    """Create output directory with propertyts data and hazard curves."""
    input_dir = tmp_path / "input" / "thames"
    input_dir.mkdir(parents=True)

    pts_dir = input_dir / "propertyts"
    pts_dir.mkdir()

    # Property with 5 flood events (enough for GEV)
    prop1 = {
        "property_id": "PROP-001",
        "location": {"lat": 51.45, "lon": -0.30},
        "elevation_m": 4.0,
        "floor_level_m": 0.3,
        "flood_zone": "Zone 2",
        "property_type": "Semi-detached",
        "construction_year": 1995,
        "nearest_gauges": [
            {"gauge_id": "GAUGE-001", "distance_m": 1000, "gauge_elevation_m": 3.5},
            {"gauge_id": "GAUGE-002", "distance_m": 2000, "gauge_elevation_m": 4.0},
            {"gauge_id": "GAUGE-003", "distance_m": 3000, "gauge_elevation_m": 4.5},
        ],
        "flood_events": [
            {"storm_id": "S1", "flood_depth_m": 0.5, "flooded": True, "damage_ratio": 0.25, "exceeded_severe": True},
            {"storm_id": "S2", "flood_depth_m": 1.2, "flooded": True, "damage_ratio": 0.42, "exceeded_severe": True},
            {"storm_id": "S3", "flood_depth_m": 0.3, "flooded": True, "damage_ratio": 0.15, "exceeded_severe": True},
            {"storm_id": "S4", "flood_depth_m": 2.1, "flooded": True, "damage_ratio": 0.60, "exceeded_severe": True},
            {"storm_id": "S5", "flood_depth_m": 0.8, "flooded": True, "damage_ratio": 0.35, "exceeded_severe": True},
        ],
        "summary": {
            "property_id": "PROP-001",
            "floods_at_nearest_gauge": 20,
            "severe_at_nearest_gauge": 8,
            "floods_at_property": 5,
        },
    }

    # Property with only 2 flood events (below GEV threshold)
    prop2 = {
        "property_id": "PROP-002",
        "location": {"lat": 51.46, "lon": -0.31},
        "elevation_m": 6.0,
        "floor_level_m": 0.5,
        "flood_zone": "Zone 1",
        "property_type": "Detached",
        "construction_year": 2005,
        "nearest_gauges": [
            {"gauge_id": "GAUGE-001", "distance_m": 1500, "gauge_elevation_m": 3.5},
        ],
        "flood_events": [
            {"storm_id": "S1", "flood_depth_m": 0.1, "flooded": True, "damage_ratio": 0.05, "exceeded_severe": True},
            {"storm_id": "S4", "flood_depth_m": 0.4, "flooded": True, "damage_ratio": 0.20, "exceeded_severe": True},
        ],
        "summary": {
            "property_id": "PROP-002",
            "floods_at_nearest_gauge": 20,
            "severe_at_nearest_gauge": 8,
            "floods_at_property": 2,
        },
    }

    # Property with many floods
    prop3 = {
        "property_id": "PROP-003",
        "location": {"lat": 51.44, "lon": -0.29},
        "elevation_m": 3.0,
        "floor_level_m": 0.1,
        "flood_zone": "Zone 3a",
        "property_type": "Flat",
        "construction_year": 1980,
        "nearest_gauges": [
            {"gauge_id": "GAUGE-001", "distance_m": 200, "gauge_elevation_m": 3.5},
            {"gauge_id": "GAUGE-002", "distance_m": 800, "gauge_elevation_m": 4.0},
        ],
        "flood_events": [
            {"storm_id": f"S{i}", "flood_depth_m": 0.2 + i * 0.1, "flooded": True,
             "damage_ratio": 0.1 + i * 0.05, "exceeded_severe": True}
            for i in range(10)
        ],
        "summary": {
            "property_id": "PROP-003",
            "floods_at_nearest_gauge": 10,
            "severe_at_nearest_gauge": 10,
            "floods_at_property": 10,
        },
    }

    for prop in [prop1, prop2, prop3]:
        with open(pts_dir / f"{prop['property_id']}.json", "w") as f:
            json.dump(prop, f)

    gauge_hc = {
        "metadata": {"catchment_id": "thames", "num_gauges": 3, "num_storms": 100},
        "hazard_curves": {
            "GAUGE-001": {
                "gauge_id": "GAUGE-001",
                "gauge_name": "Test Gauge 1",
                "annual_hazard_rate_alert": 0.05,
                "annual_hazard_rate_warning": 0.02,
                "annual_hazard_rate_severe": 0.005,
                "severe_event_count": 8,
            },
            "GAUGE-002": {
                "gauge_id": "GAUGE-002",
                "gauge_name": "Test Gauge 2",
                "annual_hazard_rate_alert": 0.04,
                "annual_hazard_rate_warning": 0.015,
                "annual_hazard_rate_severe": 0.003,
                "severe_event_count": 6,
            },
            "GAUGE-003": {
                "gauge_id": "GAUGE-003",
                "gauge_name": "Test Gauge 3",
                "annual_hazard_rate_alert": 0.03,
                "annual_hazard_rate_warning": 0.01,
                "annual_hazard_rate_severe": 0.002,
                "severe_event_count": 4,
            },
        },
    }

    with open(input_dir / "gaugehc.json", "w") as f:
        json.dump(gauge_hc, f)

    return input_dir
