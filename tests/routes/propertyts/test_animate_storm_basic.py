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

"""Tests for GET /propertyts/animate/<storm_id> — error paths, top-level
response shape, and frame structure.

See also:
  test_animate_storm_state.py  — gauge/property state and stats
  test_animate_composite.py    — composite animation endpoint
"""

import pytest

from tests.routes.propertyts.conftest import (
    STORM_ID, STORM_HOURS,
    make_gauge_json, make_gaugets_json, make_prop_file, make_anim_client,
)


# ===========================================================================
# animate_storm: error paths
# ===========================================================================

class TestAnimateStormErrors:

    def test_no_pts_dir_returns_404(self, pts_client_no_data):
        r = pts_client_no_data.get(f"/api/v1/propertyts/animate/{STORM_ID}")
        assert r.status_code == 404

    def test_no_pts_dir_status_error(self, pts_client_no_data):
        assert pts_client_no_data.get(
            f"/api/v1/propertyts/animate/{STORM_ID}"
        ).get_json()["status"] == "error"

    def test_options_returns_ok(self, pts_client_no_data):
        r = pts_client_no_data.options(f"/api/v1/propertyts/animate/{STORM_ID}")
        assert r.status_code == 200

    def test_unknown_storm_returns_404(self, tmp_path, monkeypatch):
        client = make_anim_client(
            tmp_path, monkeypatch,
            gauge_json=make_gauge_json(),
            gaugets={"GAUGE-001.json": make_gaugets_json()},
            prop_files={"PROP-001.json": make_prop_file("PROP-001", STORM_ID)},
        )
        assert client.get("/api/v1/propertyts/animate/STORM-GHOST").status_code == 404

    def test_unknown_storm_status_error(self, tmp_path, monkeypatch):
        client = make_anim_client(
            tmp_path, monkeypatch,
            gauge_json=make_gauge_json(),
            gaugets={"GAUGE-001.json": make_gaugets_json()},
            prop_files={"PROP-001.json": make_prop_file("PROP-001", STORM_ID)},
        )
        assert client.get(
            "/api/v1/propertyts/animate/STORM-GHOST"
        ).get_json()["status"] == "error"

    def test_unknown_storm_message_mentions_storm_id(self, tmp_path, monkeypatch):
        client = make_anim_client(
            tmp_path, monkeypatch,
            gauge_json=make_gauge_json(),
            gaugets={"GAUGE-001.json": make_gaugets_json()},
            prop_files={"PROP-001.json": make_prop_file("PROP-001", STORM_ID)},
        )
        msg = client.get(
            "/api/v1/propertyts/animate/STORM-GHOST"
        ).get_json()["message"]
        assert "STORM-GHOST" in msg


# ===========================================================================
# animate_storm: happy path — top-level response
# ===========================================================================

class TestAnimateStormSuccess:

    @pytest.fixture
    def anim_client(self, tmp_path, monkeypatch):
        return make_anim_client(
            tmp_path, monkeypatch,
            gauge_json=make_gauge_json(),
            gaugets={"GAUGE-001.json": make_gaugets_json()},
            prop_files={"PROP-001.json": make_prop_file("PROP-001", STORM_ID)},
        )

    def test_returns_200(self, anim_client):
        assert anim_client.get(f"/api/v1/propertyts/animate/{STORM_ID}").status_code == 200

    def test_status_success(self, anim_client):
        data = anim_client.get(f"/api/v1/propertyts/animate/{STORM_ID}").get_json()
        assert data["status"] == "success"

    def test_storm_id_in_response(self, anim_client):
        data = anim_client.get(f"/api/v1/propertyts/animate/{STORM_ID}").get_json()
        assert data["storm_id"] == STORM_ID

    def test_n_frames_equals_storm_hours(self, anim_client):
        data = anim_client.get(f"/api/v1/propertyts/animate/{STORM_ID}").get_json()
        assert data["n_frames"] == STORM_HOURS

    def test_frames_list_length_equals_storm_hours(self, anim_client):
        data = anim_client.get(f"/api/v1/propertyts/animate/{STORM_ID}").get_json()
        assert len(data["frames"]) == STORM_HOURS

    def test_n_properties_affected_is_one(self, anim_client):
        data = anim_client.get(f"/api/v1/propertyts/animate/{STORM_ID}").get_json()
        assert data["n_properties_affected"] == 1

    def test_stray_non_gauge_file_is_skipped(self, tmp_path, monkeypatch):
        """A non-``GAUGE-`` document in the gaugets collection is ignored when
        building the gauge readings (the storm still animates)."""
        client = make_anim_client(
            tmp_path, monkeypatch,
            gauge_json=make_gauge_json(),
            gaugets={"GAUGE-001.json": make_gaugets_json(),
                     "metadata.json": {"not": "a gauge"}},
            prop_files={"PROP-001.json": make_prop_file("PROP-001", STORM_ID)},
        )
        r = client.get(f"/api/v1/propertyts/animate/{STORM_ID}")
        assert r.status_code == 200
        assert r.get_json()["status"] == "success"


# ===========================================================================
# animate_storm: frame structure
# ===========================================================================

class TestAnimateStormFrameStructure:

    @pytest.fixture
    def frame0(self, tmp_path, monkeypatch):
        client = make_anim_client(
            tmp_path, monkeypatch,
            gauge_json=make_gauge_json(),
            gaugets={"GAUGE-001.json": make_gaugets_json()},
            prop_files={"PROP-001.json": make_prop_file("PROP-001", STORM_ID)},
        )
        return client.get(f"/api/v1/propertyts/animate/{STORM_ID}").get_json()["frames"][0]

    def test_frame_has_hour_field(self, frame0):
        assert "hour" in frame0

    def test_frame_hour_zero_is_first(self, frame0):
        assert frame0["hour"] == 0

    def test_frame_has_gauges(self, frame0):
        assert "gauges" in frame0
        assert len(frame0["gauges"]) == 1

    def test_frame_has_properties(self, frame0):
        assert "properties" in frame0
        assert len(frame0["properties"]) == 1

    def test_frame_has_stats(self, frame0):
        stats = frame0["stats"]
        assert "gauges_flooded" in stats
        assert "properties_flooded" in stats
        assert "total_depth_m" in stats

    def test_hour_values_sequential(self, tmp_path, monkeypatch):
        client = make_anim_client(
            tmp_path, monkeypatch,
            gauge_json=make_gauge_json(),
            gaugets={"GAUGE-001.json": make_gaugets_json()},
            prop_files={"PROP-001.json": make_prop_file("PROP-001", STORM_ID)},
        )
        frames = client.get(
            f"/api/v1/propertyts/animate/{STORM_ID}"
        ).get_json()["frames"]
        assert [f["hour"] for f in frames] == list(range(STORM_HOURS))
