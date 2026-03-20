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

"""Helper functions for property flood risk analysis tests."""

import json
from math import atan2, cos, radians, sin, sqrt
from pathlib import Path
from typing import Any, Dict, Tuple

import numpy as np
import pandas as pd


def calculate_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate Haversine distance between two points in km."""
    R = 6371
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return R * 2 * atan2(sqrt(a), sqrt(1 - a))


def calculate_flood_depth(
    property_elevation: float,
    gauge_level: float,
    distance_km: float,
    trigger_level: float = 5.5,
) -> float:
    """Calculate estimated flood depth at property."""
    if gauge_level < trigger_level:
        return 0.0
    excess_level = gauge_level - trigger_level
    attenuation = np.exp(-0.1 * distance_km)
    flood_level_at_property = trigger_level + (excess_level * attenuation)
    return max(0.0, flood_level_at_property - property_elevation)


def calculate_damage_ratio(flood_depth: float, property_type: str = "residential") -> float:
    """Calculate damage ratio using depth-damage curves."""
    if flood_depth <= 0:
        return 0.0
    depth_points = [0.0, 0.1, 0.3, 0.5, 1.0, 1.5, 2.0, 3.0, 5.0]
    if property_type.lower() == "commercial":
        damage_points = [0.0, 0.10, 0.20, 0.30, 0.45, 0.55, 0.65, 0.75, 0.85]
    else:
        damage_points = [0.0, 0.08, 0.15, 0.25, 0.40, 0.50, 0.60, 0.70, 0.80]
    return float(np.interp(flood_depth, depth_points, damage_points))


def classify_risk_level(flood_depth: float) -> str:
    """Classify risk level based on flood depth."""
    if flood_depth > 2.0:
        return "HIGH"
    elif flood_depth > 0.5:
        return "MEDIUM"
    elif flood_depth > 0:
        return "LOW"
    return "MINIMAL"


def load_property_data(input_dir: Path) -> pd.DataFrame:
    """Load property portfolio from JSON file."""
    with open(input_dir / "property.json") as f:
        data = json.load(f)
    properties = data.get("properties", data.get("data", [data] if isinstance(data, dict) else data))
    return pd.DataFrame(properties)


def load_gauge_data(input_dir: Path) -> Tuple[pd.DataFrame, Dict[str, list]]:
    """Load flood gauge metadata and readings."""
    with open(input_dir / "gauge.json") as f:
        data = json.load(f)
    gauge_metadata = pd.DataFrame(data.get("flood_gauges", data))

    with open(input_dir / "gauge_floodts.json") as f:
        data = json.load(f)
    gauge_readings = {
        ts["gauge_id"]: ts.get("readings", [])
        for ts in data.get("time_series", [])
    }
    return gauge_metadata, gauge_readings


def find_nearest_gauge(
    property_lat: float, property_lon: float, gauge_metadata: pd.DataFrame
) -> Tuple[str, float]:
    """Find the nearest gauge to a property."""
    min_distance = float("inf")
    nearest_gauge = None
    for _, gauge in gauge_metadata.iterrows():
        distance = calculate_distance_km(
            property_lat, property_lon, gauge["latitude"], gauge["longitude"]
        )
        if distance < min_distance:
            min_distance = distance
            nearest_gauge = gauge["gauge_id"]
    return nearest_gauge, min_distance


def run_single_property_test(input_dir: Path, property_index: int = 0) -> Dict[str, Any]:
    """Run flood risk analysis on a single property."""
    results: Dict[str, Any] = {"success": False, "property": None, "flood_analysis": None, "errors": []}

    properties = load_property_data(input_dir)
    if properties is None or len(properties) == 0:
        results["errors"].append("No property data")
        return results

    prop = properties.iloc[property_index].to_dict()
    property_lat = float(prop["latitude"])
    property_lon = float(prop["longitude"])
    property_elevation = float(prop.get("elevation", 15.0))
    property_type = prop.get("property_type", "residential")
    property_value = float(prop.get("value", 500000))

    results["property"] = {
        "property_id": prop.get("property_id"),
        "latitude": property_lat,
        "longitude": property_lon,
        "elevation": property_elevation,
        "value": property_value,
        "property_type": property_type,
    }

    gauge_metadata, gauge_readings = load_gauge_data(input_dir)
    nearest_gauge, distance_km = find_nearest_gauge(property_lat, property_lon, gauge_metadata)

    if nearest_gauge in gauge_readings:
        gauge_level = max(r.get("level", 0) for r in gauge_readings[nearest_gauge])
    else:
        gauge_level = 6.0

    flood_depth = calculate_flood_depth(property_elevation, gauge_level, distance_km)
    damage_ratio = calculate_damage_ratio(flood_depth, property_type)

    results["flood_analysis"] = {
        "nearest_gauge": nearest_gauge,
        "distance_to_gauge_km": distance_km,
        "gauge_level": gauge_level,
        "flood_depth_m": flood_depth,
        "damage_ratio": damage_ratio,
        "estimated_loss_gbp": property_value * damage_ratio,
        "risk_level": classify_risk_level(flood_depth),
    }

    results["success"] = True
    return results
