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

"""Shared fixtures for risk report generation tests."""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import numpy as np
import pytest


def _generate_sample_gauges(count: int = 20, high_levels: bool = False) -> Dict[str, Any]:
    base_lat, base_lon = 51.5074, -0.3000
    gauges = {}
    for i in range(count):
        lat = base_lat + (i * 0.01) - 0.05
        lon = base_lon + (i * 0.02) - 0.1
        if high_levels:
            max_level = 6.5 + np.random.uniform(0, 2.0)
            severe_level = 6.0 + np.random.uniform(0, 1.0)
        else:
            max_level = 5.0 + np.random.uniform(0, 1.5)
            severe_level = 5.5 + np.random.uniform(0, 1.0)
        gid = f"THAMES_GAUGE_{i:03d}"
        gauges[gid] = {
            "gauge_id": gid,
            "gauge_name": f"Thames Station {i + 1}",
            "latitude": round(lat, 6),
            "longitude": round(lon, 6),
            "elevation": round(2.0 + np.random.uniform(-0.5, 1.0), 2),
            "max_level": round(max_level, 2),
            "severe_level": round(severe_level, 2),
            "current_level": round(max_level * 0.9, 2),
        }
    return gauges


def _generate_sample_property_risk(count: int, high_risk_bias: bool = False) -> Dict[str, Any]:
    risk_levels = ["High", "Medium", "Low", "Minimal"]
    properties = {}
    for i in range(count):
        pid = f"PROP_{i:04d}"
        probs = [0.5, 0.3, 0.15, 0.05] if high_risk_bias else [0.15, 0.25, 0.35, 0.25]
        risk_level = np.random.choice(risk_levels, p=probs)
        if risk_level == "High":
            flood_depth, risk_value = np.random.uniform(1.5, 3.0), np.random.uniform(0.6, 0.9)
        elif risk_level == "Medium":
            flood_depth, risk_value = np.random.uniform(0.5, 1.5), np.random.uniform(0.3, 0.6)
        elif risk_level == "Low":
            flood_depth, risk_value = np.random.uniform(0.1, 0.5), np.random.uniform(0.1, 0.3)
        else:
            flood_depth, risk_value = 0.0, 0.0
        prop_value = np.random.uniform(300_000, 2_000_000)
        properties[pid] = {
            "property_id": pid,
            "latitude": round(51.5074 + np.random.uniform(-0.1, 0.1), 6),
            "longitude": round(-0.3000 + np.random.uniform(-0.1, 0.1), 6),
            "elevation": round(5.0 + np.random.uniform(-2.0, 15.0), 2),
            "property_value": round(prop_value, 2),
            "flood_depth": round(flood_depth, 2),
            "risk_value": round(risk_value, 3),
            "value_at_risk": round(prop_value * risk_value, 2),
            "risk_level": risk_level,
        }
    return properties


@pytest.fixture
def sample_portfolio_data() -> Dict[str, Any]:
    return {
        "timestamp": datetime.now().isoformat(),
        "catchment": "Thames",
        "summary": {
            "total_properties": 100,
            "properties_at_risk": 25,
            "percentage_at_risk": 25.0,
            "total_value": 100_000_000,
            "value_at_risk": 15_000_000,
            "percentage_value_at_risk": 15.0,
            "mortgage_summary": {
                "total_mortgages": 75,
                "total_mortgage_value": 60_000_000,
                "mortgages_at_risk_count": 18,
                "percentage_mortgages_at_risk": 24.0,
                "mortgage_value_at_risk": 9_000_000,
                "percentage_mortgage_value_at_risk": 15.0,
            },
        },
        "gauge_data": _generate_sample_gauges(),
        "property_risk": _generate_sample_property_risk(100),
    }


@pytest.fixture
def minimal_portfolio_data() -> Dict[str, Any]:
    return {
        "timestamp": datetime.now().isoformat(),
        "catchment": "Thames",
        "summary": {
            "total_properties": 10,
            "properties_at_risk": 2,
            "percentage_at_risk": 20.0,
            "total_value": 5_000_000,
            "value_at_risk": 500_000,
            "percentage_value_at_risk": 10.0,
        },
        "gauge_data": _generate_sample_gauges(count=3),
        "property_risk": _generate_sample_property_risk(10),
    }


@pytest.fixture
def high_risk_portfolio_data() -> Dict[str, Any]:
    return {
        "timestamp": datetime.now().isoformat(),
        "catchment": "Thames",
        "summary": {
            "total_properties": 50,
            "properties_at_risk": 40,
            "percentage_at_risk": 80.0,
            "total_value": 50_000_000,
            "value_at_risk": 30_000_000,
            "percentage_value_at_risk": 60.0,
            "mortgage_summary": {
                "total_mortgages": 40,
                "total_mortgage_value": 30_000_000,
                "mortgages_at_risk_count": 35,
                "percentage_mortgages_at_risk": 87.5,
                "mortgage_value_at_risk": 20_000_000,
                "percentage_mortgage_value_at_risk": 66.7,
            },
        },
        "gauge_data": _generate_sample_gauges(count=10, high_levels=True),
        "property_risk": _generate_sample_property_risk(50, high_risk_bias=True),
    }


@pytest.fixture
def output_dir(tmp_path) -> Path:
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir(parents=True)
    return reports_dir
