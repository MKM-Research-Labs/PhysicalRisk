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

"""Tests for GET /propertyts/animate/<storm_id> — gauge state, property state,
and per-frame statistics.

See also:
  test_animate_storm_basic.py  — error paths, response shape, frame structure
  test_animate_composite.py    — composite animation endpoint
"""

import pytest

from tests.routes.propertyts.conftest import (
    STORM_ID, STORM_HOURS,
    make_gauge_json, make_gaugets_json, make_prop_file, make_anim_client,
)


# ===========================================================================
# animate_storm: gauge state fields
# ===========================================================================

class TestAnimateStormGaugeState:

    @pytest.fixture
    def gauge0(self, tmp_path, monkeypatch):
        client = make_anim_client(
            tmp_path, monkeypatch,
            gauge_json=make_gauge_json(),
            gaugets={"GAUGE-001.json": make_gaugets_json(level=4.2)},
            prop_files={"PROP-001.json": make_prop_file("PROP-001", STORM_ID)},
        )
        return client.get(
            f"/api/v1/propertyts/animate/{STORM_ID}"
        ).get_json()["frames"][0]["gauges"][0]

    def test_gauge_has_required_fields(self, gauge0):
        for f in ["gauge_id", "name", "lat", "lon", "water_level_m", "alert_level", "status"]:
            assert f in gauge0, f"Missing: {f}"

    def test_gauge_id_correct(self, gauge0):
        assert gauge0["gauge_id"] == "GAUGE-001"

    def test_water_level_from_readings(self, gauge0):
        assert gauge0["water_level_m"] == 4.2

    def test_gauge_status_alert_when_above_alert(self, gauge0):
        # level=4.2 >= alert=4.0, < warning=4.5
        assert gauge0["status"] == "alert"

    def test_gauge_status_normal_when_below_alert(self, tmp_path, monkeypatch):
        client = make_anim_client(
            tmp_path, monkeypatch,
            gauge_json=make_gauge_json(alert=5.0, warning=6.0, severe=7.0),
            gaugets={"GAUGE-001.json": make_gaugets_json(level=3.0)},
            prop_files={"PROP-001.json": make_prop_file("PROP-001", STORM_ID)},
        )
        g = client.get(
            f"/api/v1/propertyts/animate/{STORM_ID}"
        ).get_json()["frames"][0]["gauges"][0]
        assert g["status"] == "normal"

    def test_gauge_status_warning(self, tmp_path, monkeypatch):
        client = make_anim_client(
            tmp_path, monkeypatch,
            gauge_json=make_gauge_json(alert=4.0, warning=4.5, severe=5.0),
            gaugets={"GAUGE-001.json": make_gaugets_json(level=4.7)},
            prop_files={"PROP-001.json": make_prop_file("PROP-001", STORM_ID)},
        )
        g = client.get(
            f"/api/v1/propertyts/animate/{STORM_ID}"
        ).get_json()["frames"][0]["gauges"][0]
        assert g["status"] == "warning"

    def test_gauge_status_severe(self, tmp_path, monkeypatch):
        client = make_anim_client(
            tmp_path, monkeypatch,
            gauge_json=make_gauge_json(alert=4.0, warning=4.5, severe=5.0),
            gaugets={"GAUGE-001.json": make_gaugets_json(level=5.5)},
            prop_files={"PROP-001.json": make_prop_file("PROP-001", STORM_ID)},
        )
        g = client.get(
            f"/api/v1/propertyts/animate/{STORM_ID}"
        ).get_json()["frames"][0]["gauges"][0]
        assert g["status"] == "severe"

    def test_gauge_water_level_key_fallback(self, tmp_path, monkeypatch):
        """Gauge readings using water_level_m key (not waterLevel) still work."""
        client = make_anim_client(
            tmp_path, monkeypatch,
            gauge_json=make_gauge_json(),
            gaugets={"GAUGE-001.json": make_gaugets_json(level=4.3, key="water_level_m")},
            prop_files={"PROP-001.json": make_prop_file("PROP-001", STORM_ID)},
        )
        g = client.get(
            f"/api/v1/propertyts/animate/{STORM_ID}"
        ).get_json()["frames"][0]["gauges"][0]
        assert g["water_level_m"] == 4.3

    def test_gauge_with_no_readings_defaults_to_zero(self, tmp_path, monkeypatch):
        client = make_anim_client(
            tmp_path, monkeypatch,
            gauge_json=make_gauge_json(),
            gaugets={"GAUGE-001.json": {
                "gauge_id": "GAUGE-001",
                "flood_simulation": {"readings": [{"waterLevel": 4.2}] * 5},
            }},
            prop_files={"PROP-001.json": make_prop_file("PROP-001", STORM_ID)},
        )
        frames = client.get(
            f"/api/v1/propertyts/animate/{STORM_ID}"
        ).get_json()["frames"]
        assert frames[10]["gauges"][0]["water_level_m"] == 0


# ===========================================================================
# animate_storm: property state fields
# ===========================================================================

class TestAnimateStormPropertyState:

    @pytest.fixture
    def frames(self, tmp_path, monkeypatch):
        client = make_anim_client(
            tmp_path, monkeypatch,
            gauge_json=make_gauge_json(),
            gaugets={"GAUGE-001.json": make_gaugets_json()},
            prop_files={"PROP-001.json": make_prop_file("PROP-001", STORM_ID, arrival=5)},
        )
        return client.get(
            f"/api/v1/propertyts/animate/{STORM_ID}"
        ).get_json()["frames"]

    def test_property_has_required_fields(self, frames):
        p = frames[0]["properties"][0]
        for f in ["property_id", "lat", "lon", "wse_m", "depth_m", "flooded", "arrived"]:
            assert f in p, f"Missing: {f}"

    def test_property_id_correct(self, frames):
        assert frames[0]["properties"][0]["property_id"] == "PROP-001"

    def test_arrived_false_before_arrival_time(self, frames):
        assert frames[0]["properties"][0]["arrived"] is False
        assert frames[4]["properties"][0]["arrived"] is False

    def test_arrived_true_at_and_after_arrival_time(self, frames):
        assert frames[5]["properties"][0]["arrived"] is True
        assert frames[10]["properties"][0]["arrived"] is True

    def test_property_beyond_readings_defaults_to_zero(self, tmp_path, monkeypatch):
        """When hour >= len(readings), flooded=False, depth_m=0, wse_m=0."""
        prop_data = {
            "property_id": "PROP-001",
            "location": {"lat": 51.5, "lon": -0.12},
            "elevation_m": 3.0, "floor_level_m": 3.2,
            "flood_events": [{
                "storm_id": STORM_ID, "flood_depth_m": 0.5, "damage_ratio": 0.1,
                "arrival_time_hrs": 5, "peak_time_hrs": 12,
                "travel_time_hrs": 5, "retention_factor": 0.9,
                "readings": [{"wse_m": 3.5, "depth_m": 0.3, "flooded": True}] * 10,
            }],
        }
        client = make_anim_client(
            tmp_path, monkeypatch,
            gauge_json=make_gauge_json(),
            gaugets={"GAUGE-001.json": make_gaugets_json()},
            prop_files={"PROP-001.json": prop_data},
        )
        p = client.get(
            f"/api/v1/propertyts/animate/{STORM_ID}"
        ).get_json()["frames"][50]["properties"][0]
        assert p["flooded"] is False
        assert p["depth_m"] == 0
        assert p["wse_m"] == 0


# ===========================================================================
# animate_storm: per-frame stats
# ===========================================================================

class TestAnimateStormStats:

    def test_gauges_flooded_counts_non_normal(self, tmp_path, monkeypatch):
        # level=4.2 >= alert=4.0 → counted as flooded
        client = make_anim_client(
            tmp_path, monkeypatch,
            gauge_json=make_gauge_json(alert=4.0, warning=4.5, severe=5.0),
            gaugets={"GAUGE-001.json": make_gaugets_json(level=4.2)},
            prop_files={"PROP-001.json": make_prop_file("PROP-001", STORM_ID)},
        )
        stats = client.get(
            f"/api/v1/propertyts/animate/{STORM_ID}"
        ).get_json()["frames"][0]["stats"]
        assert stats["gauges_flooded"] == 1

    def test_gauges_flooded_zero_when_normal(self, tmp_path, monkeypatch):
        client = make_anim_client(
            tmp_path, monkeypatch,
            gauge_json=make_gauge_json(alert=10.0, warning=11.0, severe=12.0),
            gaugets={"GAUGE-001.json": make_gaugets_json(level=3.0)},
            prop_files={"PROP-001.json": make_prop_file("PROP-001", STORM_ID)},
        )
        stats = client.get(
            f"/api/v1/propertyts/animate/{STORM_ID}"
        ).get_json()["frames"][0]["stats"]
        assert stats["gauges_flooded"] == 0

    def test_properties_flooded_is_positive_early_on(self, tmp_path, monkeypatch):
        # readings h<20 have flooded=True
        client = make_anim_client(
            tmp_path, monkeypatch,
            gauge_json=make_gauge_json(),
            gaugets={"GAUGE-001.json": make_gaugets_json()},
            prop_files={"PROP-001.json": make_prop_file("PROP-001", STORM_ID)},
        )
        stats = client.get(
            f"/api/v1/propertyts/animate/{STORM_ID}"
        ).get_json()["frames"][0]["stats"]
        assert stats["properties_flooded"] >= 1

    def test_total_depth_m_non_negative(self, tmp_path, monkeypatch):
        client = make_anim_client(
            tmp_path, monkeypatch,
            gauge_json=make_gauge_json(),
            gaugets={"GAUGE-001.json": make_gaugets_json()},
            prop_files={"PROP-001.json": make_prop_file("PROP-001", STORM_ID)},
        )
        frames = client.get(
            f"/api/v1/propertyts/animate/{STORM_ID}"
        ).get_json()["frames"]
        assert all(f["stats"]["total_depth_m"] >= 0 for f in frames[:5])
