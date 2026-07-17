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

"""Fixtures for advanced data directories: propertyts, propertyhc."""

import json

import pytest


@pytest.fixture
def sample_propertyts_dir(temp_data_dir):
    """Create sample per-property flood timeseries files in propertyts/ directory."""
    pts_dir = temp_data_dir / "propertyts"
    pts_dir.mkdir(parents=True, exist_ok=True)

    # Property with 4 flood events (enough for GEV fitting)
    prop1_data = {
        "property_id": "PROP-001",
        "location": {"lat": 25.7617, "lon": -80.1918},
        "elevation_m": 3.5,
        "floor_level_m": 0.15,
        "nearest_gauges": [
            {"gauge_id": "GAUGE-001", "distance_km": 2.1, "name": "Thames at Teddington"}
        ],
        "flood_events": [
            {
                "storm_id": "STORM-001", "flood_depth_m": 0.8, "damage_ratio": 0.25,
                "flooded": True, "arrival_time_hrs": 5, "peak_time_hrs": 12,
                "travel_time_hrs": 3, "retention_factor": 0.85,
                "readings": [{"hour": h, "wse_m": 3.5 + (0.8 if 5 <= h <= 20 else 0),
                              "depth_m": 0.8 if 5 <= h <= 20 else 0,
                              "flooded": 5 <= h <= 20} for h in range(24)]
            },
            {
                "storm_id": "STORM-002", "flood_depth_m": 1.2, "damage_ratio": 0.4,
                "flooded": True, "arrival_time_hrs": 3, "peak_time_hrs": 10,
                "travel_time_hrs": 2, "retention_factor": 0.9,
                "readings": [{"hour": h, "wse_m": 3.5 + (1.2 if 3 <= h <= 18 else 0),
                              "depth_m": 1.2 if 3 <= h <= 18 else 0,
                              "flooded": 3 <= h <= 18} for h in range(24)]
            },
            {
                "storm_id": "STORM-003", "flood_depth_m": 0.3, "damage_ratio": 0.08,
                "flooded": True, "arrival_time_hrs": 8, "peak_time_hrs": 15,
                "travel_time_hrs": 4, "retention_factor": 0.7,
                "readings": []
            },
            {
                "storm_id": "STORM-004", "flood_depth_m": 0.5, "damage_ratio": 0.15,
                "flooded": True, "arrival_time_hrs": 6, "peak_time_hrs": 14,
                "travel_time_hrs": 3.5, "retention_factor": 0.8,
                "readings": []
            },
        ],
        "summary": {"total_floods": 4, "max_depth_m": 1.2, "mean_depth_m": 0.7}
    }
    with open(pts_dir / "PROP-001.json", 'w') as f:
        json.dump(prop1_data, f)

    # Property with 1 flood event (not enough for GEV)
    prop2_data = {
        "property_id": "PROP-002",
        "location": {"lat": 25.7825, "lon": -80.1340},
        "elevation_m": 5.0,
        "floor_level_m": 0.15,
        "nearest_gauges": [
            {"gauge_id": "GAUGE-002", "distance_km": 3.5}
        ],
        "flood_events": [
            {
                "storm_id": "STORM-002", "flood_depth_m": 0.2, "damage_ratio": 0.05,
                "flooded": True, "arrival_time_hrs": 10, "peak_time_hrs": 18,
                "travel_time_hrs": 5, "retention_factor": 0.6,
                "readings": []
            }
        ],
        "summary": {"total_floods": 1, "max_depth_m": 0.2, "mean_depth_m": 0.2}
    }
    with open(pts_dir / "PROP-002.json", 'w') as f:
        json.dump(prop2_data, f)

    # Property with 0 flood events (high elevation, no flooding)
    prop3_data = {
        "property_id": "PROP-003",
        "location": {"lat": 25.7900, "lon": -80.1500},
        "elevation_m": 15.0,
        "floor_level_m": 0.15,
        "nearest_gauges": [
            {"gauge_id": "GAUGE-001", "distance_km": 5.0}
        ],
        "flood_events": [],
        "summary": {"total_floods": 0, "max_depth_m": 0, "mean_depth_m": 0,
                     "floods_at_nearest_gauge": 10}
    }
    with open(pts_dir / "PROP-003.json", 'w') as f:
        json.dump(prop3_data, f)

    summary_data = {
        "total_properties": 3,
        "properties_flooded": 2,
        "total_flood_events": 5,
        "max_depth_m": 1.2
    }
    with open(pts_dir / "portfolio_flood_summary.json", 'w') as f:
        json.dump(summary_data, f)

    return pts_dir


@pytest.fixture
def sample_propertyhc_file(temp_data_dir):
    """Create sample property hazard curves file."""
    data = {
        "metadata": {"generated": "2025-01-01", "catchment": "test", "num_properties": 1},
        "summary": {"properties_with_curves": 1, "properties_skipped": 2},
        "property_hazard_curves": {
            "PROP-001": {
                "property_id": "PROP-001",
                "flood_count": 4,
                "gev_location": 0.5,
                "gev_scale": 0.3,
                "gev_shape": 0.1,
                "base_rate": 0.4,
                "curve_points": [
                    {"depth_m": 0, "exceedance_prob": 0.4},
                    {"depth_m": 0.5, "exceedance_prob": 0.2},
                    {"depth_m": 1.0, "exceedance_prob": 0.08}
                ],
                "nearest_gauges": [
                    {
                        "gauge_id": "GAUGE-001",
                        "distance_km": 2.1,
                        "event_basis": 15.5,
                        "flood_transmission_rate": 0.85
                    }
                ],
                "summary": {
                    "max_depth_m": 1.2,
                    "avg_basis_bps": 15.5,
                    "flood_transmission_rate": 0.85,
                    "prs_spread_any_bps": 400,
                    "prs_spread_moderate_bps": 200,
                    "prs_spread_severe_bps": 80
                }
            }
        }
    }
    filepath = temp_data_dir / "propertyhc.json"
    with open(filepath, 'w') as f:
        json.dump(data, f)
    return filepath
