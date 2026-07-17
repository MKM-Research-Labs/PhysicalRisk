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
Tests for models.hazard.io — save_hazard_curves, save_gauge_storm_responses.
"""

import json

import pytest

import database
from db_helpers import tmp_catchment
from models.hazard.data_structures import GaugeResponse
from tests.port.hazard.conftest import _make_hazard_curve


@pytest.fixture(autouse=True)
def _iso_catchment(tmp_path):
    """Bind a tmp-rooted backend so the migrated hazard savers persist the hazard
    curve + per-gauge storm-response merge through database (catchment "thames")."""
    with tmp_catchment(tmp_path, catchment="thames"):
        yield


# ===========================================================================
# save_hazard_curves
# ===========================================================================

class TestSaveHazardCurves:

    def test_persists(self, tmp_path):
        from models.hazard.io import save_hazard_curves
        curve = _make_hazard_curve()
        result = save_hazard_curves({"GAUGE-001": curve}, "thames")
        assert result == "thames"
        assert database.get_gauge_hazard_curves("thames") is not None

    def test_has_metadata(self, tmp_path):
        from models.hazard.io import save_hazard_curves
        curve = _make_hazard_curve()
        save_hazard_curves({"GAUGE-001": curve}, "thames")
        data = database.get_gauge_hazard_curves("thames")
        assert "metadata" in data
        assert data["metadata"]["catchment_id"] == "thames"

    def test_has_hazard_curves(self, tmp_path):
        from models.hazard.io import save_hazard_curves
        curve = _make_hazard_curve()
        save_hazard_curves({"GAUGE-001": curve}, "thames")
        data = database.get_gauge_hazard_curves("thames")
        assert "GAUGE-001" in data["hazard_curves"]

    def test_metadata_merged(self, tmp_path):
        from models.hazard.io import save_hazard_curves
        curve = _make_hazard_curve()
        save_hazard_curves(
            {"GAUGE-001": curve}, "thames",
            metadata={"num_storms": 100, "distribution": "gev"}
        )
        data = database.get_gauge_hazard_curves("thames")
        assert data["metadata"]["num_storms"] == 100


# ===========================================================================
# save_gauge_storm_responses
# ===========================================================================

class TestSaveGaugeStormResponses:

    def _make_responses(self, gauge_id="GAUGE-001", n=2):
        return [
            GaugeResponse(
                gauge_id=gauge_id,
                storm_id=f"STORM-{i:04d}",
                base_level_m=3.0,
                level_change_m=1.0 + i * 0.5,
                peak_level_m=4.0 + i * 0.5,
                exceeded_alert=True,
                exceeded_warning=i > 0,
                exceeded_severe=False,
            )
            for i in range(n)
        ]

    def test_persists_gauge_responses(self, tmp_path):
        from models.hazard.io import save_gauge_storm_responses
        responses = {"GAUGE-001": self._make_responses()}
        save_gauge_storm_responses(responses, "thames")
        assert database.get_gauge_timeseries("thames", "GAUGE-001") is not None

    def test_saved_record_has_responses(self, tmp_path):
        from models.hazard.io import save_gauge_storm_responses
        responses = {"GAUGE-001": self._make_responses(n=3)}
        save_gauge_storm_responses(responses, "thames")
        data = database.get_gauge_timeseries("thames", "GAUGE-001")
        assert "storm_responses" in data
        assert len(data["storm_responses"]["responses"]) == 3

    def test_merges_with_existing_record(self, tmp_path):
        """If a gauge timeseries record already exists, merge storm_responses into it."""
        from models.hazard.io import save_gauge_storm_responses
        database.save_gauge_timeseries("thames", "GAUGE-001", {
            "gauge_id": "GAUGE-001",
            "flood_simulation": {"readings": []},
        })
        responses = {"GAUGE-001": self._make_responses(n=1)}
        save_gauge_storm_responses(responses, "thames")
        data = database.get_gauge_timeseries("thames", "GAUGE-001")
        assert "flood_simulation" in data
        assert "storm_responses" in data

    def test_multiple_gauges(self, tmp_path):
        from models.hazard.io import save_gauge_storm_responses
        responses = {
            "GAUGE-001": self._make_responses("GAUGE-001", 2),
            "GAUGE-002": self._make_responses("GAUGE-002", 2),
        }
        save_gauge_storm_responses(responses, "thames")
        assert database.get_gauge_timeseries("thames", "GAUGE-001") is not None
        assert database.get_gauge_timeseries("thames", "GAUGE-002") is not None
