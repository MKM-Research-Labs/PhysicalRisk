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
Shared helpers and fixtures for propertyts tests.
"""

import json
from pathlib import Path

import pytest
from db_helpers import tmp_catchment


@pytest.fixture(autouse=True)
def _seam_backend(tmp_path):
    """Bind a scratch backend rooted at tmp_path so the property hazard-curve
    generator/loader's seam I/O (gauge hazard curves, storm sequences,
    sequence_gauge) resolves there — the same path the file-writing test helpers
    (write_gauge_hc, etc.) stage their inputs under."""
    with tmp_catchment(tmp_path, "thames"):
        yield


def make_prop(prop_id="PROP-001", lat=51.5, lon=-0.1, elevation=5.0,
              floor_level=0.3):
    """Minimal CDM property dict."""
    return {
        "PropertyHeader": {
            "Header": {"PropertyID": prop_id},
            "Location": {
                "LatitudeDegrees": lat,
                "LongitudeDegrees": lon,
                "RiskAssessment": {"GroundLevelMeters": elevation},
            },
            "Construction": {"FloorLevelMeters": floor_level},
            "PropertyAttributes": {
                "PropertyResi": "Detached",
                "ConstructionYear": 2000,
                "PropertyPeriod": "2000-2008",
            },
            "RiskAssessment": {"EAFloodZone": "Zone 2"},
        }
    }


def make_gauge_lookup(gauge_id="GAUGE-001", lat=51.50, lon=-0.10,
                      elevation=3.0, alert=3.5, warning=4.5, severe=5.0):
    return {
        gauge_id: {
            "gauge_id": gauge_id,
            "lat": lat,
            "lon": lon,
            "elevation": elevation,
            "alert_level": alert,
            "warning_level": warning,
            "severe_level": severe,
        }
    }


def make_gaugets(gauge_id="GAUGE-001", peak_level=5.8,
                 exceeded_alert=True, storm_id="STORM-001",
                 with_readings=True):
    """Gaugets dict with storm_responses and optional flood_simulation."""
    readings = []
    if with_readings:
        readings = [
            {"hour": h, "waterLevel": peak_level * (1 - abs(h - 12) / 20)}
            for h in range(25)
        ]
    return {
        gauge_id: {
            "gauge_id": gauge_id,
            "storm_responses": {
                "responses": [
                    {
                        "storm_id": storm_id,
                        "peak_level_m": peak_level,
                        "exceeded_alert": exceeded_alert,
                        "exceeded_warning": peak_level > 4.5,
                        "exceeded_severe": peak_level > 5.5,
                    }
                ]
            },
            "flood_simulation": {"readings": readings},
        }
    }


def make_generator(tmp_path):
    from port.src.property.propertyts import PropertyTimeSeriesGenerator
    return PropertyTimeSeriesGenerator(output_dir=tmp_path, verbose=False)


# ---------------------------------------------------------------------------
# PropertyHazardCurve helpers and fixtures
# ---------------------------------------------------------------------------

def write_gauge_hc(output_dir: Path, num_storms: int = 100):
    """Write a minimal gaugehc.json into output_dir."""
    data = {
        "metadata": {"catchment_id": "thames", "num_storms": num_storms},
        "hazard_curves": {
            "GAUGE-001": {
                "annual_hazard_rate_alert": 0.05,
                "annual_hazard_rate_warning": 0.02,
                "annual_hazard_rate_severe": 0.005,
            },
            "GAUGE-002": {
                "annual_hazard_rate_alert": 0.03,
                "annual_hazard_rate_warning": 0.01,
                "annual_hazard_rate_severe": 0.002,
            },
        },
    }
    (output_dir / "gaugehc.json").write_text(json.dumps(data))
    return data


def write_property_ts(pts_dir: Path, prop_id: str, n_floods: int,
                      include_non_flooded: bool = False,
                      nearest_gauges=None):
    """Write a PROP-*.json time-series file into pts_dir."""
    flood_events = []
    for i in range(n_floods):
        flood_events.append({
            "storm_id": f"S{i}",
            "flood_depth_m": 0.3 + i * 0.2,
            "flooded": True,
            "damage_ratio": 0.1,
            "exceeded_severe": True,
        })
    if include_non_flooded:
        flood_events.append({
            "storm_id": "SNON",
            "flood_depth_m": 0.0,
            "flooded": False,
            "damage_ratio": 0.0,
            "exceeded_severe": False,
        })
    pdata = {
        "property_id": prop_id,
        "location": {"lat": 51.45, "lon": -0.30},
        "elevation_m": 5.0,
        "floor_level_m": 0.3,
        "flood_zone": "Zone 2",
        "property_type": "Detached",
        "construction_year": 2000,
        "nearest_gauges": nearest_gauges or [
            {"gauge_id": "GAUGE-001", "distance_m": 1200, "gauge_elevation_m": 3.5},
        ],
        "flood_events": flood_events,
        "summary": {
            "property_id": prop_id,
            "floods_at_nearest_gauge": 20,
            "floods_at_property": n_floods,
        },
    }
    # Seed the per-asset timeseries through the seam (the hazard-curve generator
    # reads it back the same way). The seam mode is derived from the ts dir name
    # (propertyts→flood, propertytsd→shd, propertytse→she, …) so existing call
    # sites that vary only `pts_dir` seed the right collection unchanged.
    import database
    from port.utils.asset_config import RESIDENTIAL_CONFIG
    _dir = Path(pts_dir).name
    _mode = "flood"
    for _local, _dname in RESIDENTIAL_CONFIG.ts_dirs.items():
        if _dname == _dir:
            _mode = "flood" if _local == "normal" else _local
            break
    database.save_property_timeseries(
        database.active_catchment(), prop_id, pdata, mode=_mode)
    return pdata


def make_readings(peak_level, n_hours=25):
    """Synthetic gauge flood readings -- rise-and-fall shape."""
    return [
        {"hour": h, "waterLevel": peak_level * max(0, 1 - abs(h - 12) / 20)}
        for h in range(n_hours)
    ]


def make_gaugets_multi_storm(gauge_id="GAUGE-001", storm_defs=None):
    """
    Build a gaugets dict with multiple storm responses (simulates MKM-SS-001).

    storm_defs: list of (storm_id, peak_level, exceeded_alert) tuples.
    """
    if storm_defs is None:
        storm_defs = [
            ("STORM-seq001a", 5.5, True),
            ("STORM-seq001b", 5.8, True),
        ]
    responses = [
        {
            "storm_id": sid,
            "peak_level_m": peak,
            "exceeded_alert": exceeded,
            "exceeded_warning": peak > 4.5,
            "exceeded_severe": peak > 5.5,
        }
        for sid, peak, exceeded in storm_defs
    ]
    return {
        gauge_id: {
            "gauge_id": gauge_id,
            "storm_responses": {"responses": responses},
            "flood_simulation": {"readings": make_readings(6.0)},
        }
    }


@pytest.fixture
def basic_output_dir(tmp_path):
    """Output dir with propertyts + gaugehc."""
    pts_dir = tmp_path / "propertyts"
    pts_dir.mkdir(parents=True)
    write_gauge_hc(tmp_path)
    return tmp_path, pts_dir


# ---------------------------------------------------------------------------
# PropertyPortfolioGenerator helpers (shared by test_geometry / test_locations
# / test_property_values)
# ---------------------------------------------------------------------------

from unittest.mock import MagicMock

from port.src.property.main import PropertyPortfolioGenerator

# Three minimally-spaced gauge points along a notional line
GAUGE_POINTS = [
    (51.45, -0.50, 3.0),
    (51.46, -0.30, 4.0),
    (51.47, -0.10, 5.0),
    (51.48,  0.10, 6.0),
    (51.49,  0.30, 7.0),
]


def make_portfolio_params(gauge_points=None, areas=None):
    """Build a minimal params MagicMock for PropertyPortfolioGenerator."""
    params = MagicMock()
    params.AREAS = areas or ["Area1", "Area2", "Area3"]
    params.AREA_VALUE_FACTORS = {"Area1": 1.0, "Area2": 1.2, "Area3": 0.9}
    params.STREETS = {}
    params.CENTER_LAT = 51.5
    params.CENTER_LON = -0.1
    params.GAUGE_POINTS = gauge_points if gauge_points is not None else GAUGE_POINTS
    del params.GAUGEPOINTS  # avoid attribute clash
    params.get_elevation = MagicMock(return_value=8.0)
    return params


def make_portfolio_gen(tmp_path, gauge_points=None, areas=None):
    """Create a PropertyPortfolioGenerator with minimal mock params.

    The WP2.4 generator no longer takes ``output_dir``; storage is resolved through
    the ``database`` package against the active catchment. Tests that call
    ``.generate()`` must run inside ``tmp_catchment(tmp_path)`` (their module's autouse
    fixture); construction alone needs no backend. ``tmp_path`` is kept in the signature
    for call-site compatibility."""
    params = make_portfolio_params(gauge_points=gauge_points, areas=areas)
    return PropertyPortfolioGenerator(
        verbose=False,
        catchment_params=params,
    )
