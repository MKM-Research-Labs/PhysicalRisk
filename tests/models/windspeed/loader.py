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

"""Tests for models.windspeed.loader — read EVT-*.json files."""

import json
from datetime import datetime

import pytest

from config.typhoon import RegimeClass, ScenarioFamily
from models.typhoon.data_structures import TyphoonState, TyphoonTrajectory
from models.typhoon.pipeline import write_event_trajectory
from models.windspeed.loader import load_event


def _trajectory():
    s = TyphoonState(
        longitude=5.0, latitude=5.0,
        translation_speed_kmh=15.0, heading_deg=270.0,
        v_max_ms=40.0, r_max_km=30.0, r_outer_km=120.0,
        regime=RegimeClass.STRAIGHT_WESTWARD, land_flag=False, time_hours=0.0,
    )
    return TyphoonTrajectory(
        event_id="EVT-TEST",
        particle_id=0,
        scenario_family=ScenarioFamily.BASELINE,
        genesis_time=datetime(2026, 1, 1),
        states=[s],
    )


class TestLoadEvent:

    def test_round_trip_via_pipeline_writer(self, tmp_path):
        traj = _trajectory()
        path = tmp_path / "EVT-TEST.json"
        write_event_trajectory(traj, path, event_idx=0)

        restored = load_event(path)
        assert restored.event_id == traj.event_id
        assert restored.scenario_family is ScenarioFamily.BASELINE
        assert len(restored.states) == 1

    def test_accepts_string_path(self, tmp_path):
        traj = _trajectory()
        path = tmp_path / "EVT-TEST.json"
        write_event_trajectory(traj, path, event_idx=0)

        restored = load_event(str(path))
        assert restored.event_id == traj.event_id

    def test_passes_trajectory_through(self):
        traj = _trajectory()
        assert load_event(traj) is traj

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_event(tmp_path / "missing.json")

    def test_strips_summary_header(self, tmp_path):
        # write_event_trajectory adds a summary block; load_event must ignore it.
        traj = _trajectory()
        path = tmp_path / "EVT-with-summary.json"
        write_event_trajectory(traj, path, event_idx=0)
        with path.open() as f:
            payload = json.load(f)
        assert "summary" in payload   # writer produced it
        restored = load_event(path)
        assert restored.event_id == traj.event_id   # loader stripped it cleanly
