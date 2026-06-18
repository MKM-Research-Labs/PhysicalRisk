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

"""Tests for GET /propertyts/animate/composite — worst-case composite animation.

See also:
  test_animate_storm_basic.py  — per-storm error paths, response shape, frames
  test_animate_storm_state.py  — per-storm gauge/property state and stats
"""

import pytest

from tests.routes.propertyts.conftest import (
    STORM_ID, STORM_HOURS,
    make_gauge_json, make_gaugets_json, make_anim_client,
)

_COMPOSITE_URL = "/api/v1/propertyts/animate/composite"


# ===========================================================================
# animate_composite: error paths
# ===========================================================================

class TestAnimateCompositeErrors:

    def test_no_pts_dir_returns_404(self, pts_client_no_data):
        assert pts_client_no_data.get(_COMPOSITE_URL).status_code == 404

    def test_no_pts_dir_status_error(self, pts_client_no_data):
        assert pts_client_no_data.get(_COMPOSITE_URL).get_json()["status"] == "error"

    def test_options_returns_ok(self, pts_client_no_data):
        assert pts_client_no_data.options(_COMPOSITE_URL).status_code == 200

    def test_no_flooding_returns_404(self, tmp_path, monkeypatch):
        """pts dir exists but all flood_depths are zero → 404."""
        prop_data = {
            "property_id": "PROP-001",
            "location": {"lat": 51.5, "lon": -0.12},
            "elevation_m": 3.0, "floor_level_m": 3.2,
            "flood_events": [{"storm_id": STORM_ID, "flood_depth_m": 0.0, "damage_ratio": 0}],
        }
        client = make_anim_client(
            tmp_path, monkeypatch,
            gauge_json=make_gauge_json(),
            gaugets={"GAUGE-001.json": make_gaugets_json()},
            prop_files={"PROP-001.json": prop_data},
        )
        assert client.get(_COMPOSITE_URL).status_code == 404

    def test_no_flood_events_at_all_returns_404(self, tmp_path, monkeypatch):
        """pts dir exists but property has no flood_events → 404."""
        prop_data = {
            "property_id": "PROP-001",
            "location": {"lat": 51.5, "lon": -0.12},
            "elevation_m": 3.0, "floor_level_m": 3.2,
            "flood_events": [],
        }
        client = make_anim_client(
            tmp_path, monkeypatch,
            gauge_json=make_gauge_json(),
            gaugets={"GAUGE-001.json": make_gaugets_json()},
            prop_files={"PROP-001.json": prop_data},
        )
        assert client.get(_COMPOSITE_URL).status_code == 404


# ===========================================================================
# animate_composite: happy path — top-level response
# ===========================================================================

class TestAnimateCompositeSuccess:

    def test_returns_200(self, pts_env):
        assert pts_env["client"].get(_COMPOSITE_URL).status_code == 200

    def test_status_success(self, pts_env):
        assert pts_env["client"].get(_COMPOSITE_URL).get_json()["status"] == "success"

    def test_storm_id_is_composite(self, pts_env):
        assert pts_env["client"].get(_COMPOSITE_URL).get_json()["storm_id"] == "COMPOSITE"

    def test_n_frames_equals_storm_hours(self, pts_env):
        assert pts_env["client"].get(_COMPOSITE_URL).get_json()["n_frames"] == STORM_HOURS

    def test_frames_list_length(self, pts_env):
        assert len(pts_env["client"].get(_COMPOSITE_URL).get_json()["frames"]) == STORM_HOURS

    def test_n_properties_affected_is_one(self, pts_env):
        assert pts_env["client"].get(_COMPOSITE_URL).get_json()["n_properties_affected"] == 1


# ===========================================================================
# animate_composite: frame structure
# ===========================================================================

class TestAnimateCompositeFrameStructure:

    @pytest.fixture
    def frame0(self, pts_env):
        return pts_env["client"].get(_COMPOSITE_URL).get_json()["frames"][0]

    def test_frame_has_hour(self, frame0):
        assert frame0["hour"] == 0

    def test_frame_has_gauges(self, frame0):
        assert "gauges" in frame0

    def test_frame_has_properties(self, frame0):
        assert "properties" in frame0

    def test_frame_has_stats(self, frame0):
        stats = frame0["stats"]
        assert "gauges_flooded" in stats
        assert "properties_flooded" in stats
        assert "total_depth_m" in stats


# ===========================================================================
# animate_composite: property state fields (differs from per-storm)
# ===========================================================================

class TestAnimateCompositePropertyState:

    @pytest.fixture
    def frames(self, pts_env):
        return pts_env["client"].get(_COMPOSITE_URL).get_json()["frames"]

    def test_property_has_peak_field(self, frames):
        assert "peak" in frames[0]["properties"][0]

    def test_property_does_not_have_wse_m(self, frames):
        # composite omits wse_m (unlike per-storm endpoint)
        assert "wse_m" not in frames[0]["properties"][0]

    def test_property_has_required_fields(self, frames):
        p = frames[0]["properties"][0]
        for f in ["property_id", "lat", "lon", "depth_m", "flooded", "arrived", "peak"]:
            assert f in p, f"Missing: {f}"

    def test_peak_true_at_and_after_peak_time(self, pts_env):
        # pts_env: peak_time_hrs=12
        frames = pts_env["client"].get(_COMPOSITE_URL).get_json()["frames"]
        assert frames[11]["properties"][0]["peak"] is False
        assert frames[12]["properties"][0]["peak"] is True

    def test_arrived_true_at_arrival_time(self, pts_env):
        # pts_env: arrival_time_hrs=5
        frames = pts_env["client"].get(_COMPOSITE_URL).get_json()["frames"]
        assert frames[4]["properties"][0]["arrived"] is False
        assert frames[5]["properties"][0]["arrived"] is True

    def test_property_beyond_readings_defaults(self, tmp_path, monkeypatch):
        """hour >= len(readings) → flooded=False, depth_m=0, arrived=False, peak=False."""
        prop_data = {
            "property_id": "PROP-001",
            "location": {"lat": 51.5, "lon": -0.12},
            "elevation_m": 3.0, "floor_level_m": 3.2,
            "flood_events": [{
                "storm_id": STORM_ID, "flood_depth_m": 0.5, "damage_ratio": 0.1,
                "arrival_time_hrs": 2, "peak_time_hrs": 5,
                "travel_time_hrs": 2, "retention_factor": 0.9,
                "readings": [{"depth_m": 0.3, "flooded": True}] * 8,
            }],
        }
        client = make_anim_client(
            tmp_path, monkeypatch,
            gauge_json=make_gauge_json(),
            gaugets={"GAUGE-001.json": make_gaugets_json()},
            prop_files={"PROP-001.json": prop_data},
        )
        p = client.get(_COMPOSITE_URL).get_json()["frames"][50]["properties"][0]
        assert p["flooded"] is False
        assert p["depth_m"] == 0
        assert p["arrived"] is False
        assert p["peak"] is False


# ===========================================================================
# animate_composite: picks worst storm per property
# ===========================================================================

class TestAnimateCompositeWorstStorm:

    def test_composite_picks_higher_depth_storm(self, tmp_path, monkeypatch):
        """Property with two storms: composite uses the one with higher flood_depth."""
        prop_data = {
            "property_id": "PROP-001",
            "location": {"lat": 51.5, "lon": -0.12},
            "elevation_m": 3.0, "floor_level_m": 3.2,
            "flood_events": [
                {
                    "storm_id": "STORM-0001", "flood_depth_m": 0.3, "damage_ratio": 0.05,
                    "arrival_time_hrs": 10, "peak_time_hrs": 20,
                    "readings": [{"depth_m": 0.3, "flooded": True}] * STORM_HOURS,
                },
                {
                    "storm_id": "STORM-0002", "flood_depth_m": 1.5, "damage_ratio": 0.4,
                    "arrival_time_hrs": 3, "peak_time_hrs": 8,
                    "readings": [{"depth_m": 1.5, "flooded": True}] * STORM_HOURS,
                },
            ],
        }
        client = make_anim_client(
            tmp_path, monkeypatch,
            gauge_json=make_gauge_json(),
            gaugets={"GAUGE-001.json": make_gaugets_json()},
            prop_files={"PROP-001.json": prop_data},
        )
        data = client.get(_COMPOSITE_URL).get_json()
        assert data["status"] == "success"
        assert data["frames"][0]["properties"][0]["depth_m"] == pytest.approx(1.5)
