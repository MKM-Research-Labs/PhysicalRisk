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

"""Tests for port.src.stressm.gaugets_writer.populate_gaugets — covers the
merge branch where each gauge's base-simulation timeseries is read back through
the database seam, storm_responses are attached, and it is saved again.
"""

from unittest.mock import MagicMock, patch

import pytest

import database
from db_helpers import tmp_catchment


@pytest.fixture
def populate_env(tmp_path):
    """Bind a tmp catchment and seed base-simulation gaugets through the seam so
    populate_gaugets' merge branch executes (file rows on the file backend, table
    rows under pg)."""
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    with tmp_catchment(input_dir, catchment="thames"):
        catchment = database.active_catchment()
        database.save_gauge_timeseries(catchment, "GAUGE-001", {
            "flood_simulation": {"readings": [{"hour": 0, "waterLevel": 2.0}]},
        })
        database.save_gauge_timeseries(catchment, "GAUGE-002", {
            "flood_simulation": {"readings": [{"hour": 0, "waterLevel": 2.5}]},
        })
        yield input_dir, catchment


class TestPopulateGaugetsMergeBranch:
    def test_merges_storm_responses_into_existing_files(self, populate_env):
        """Existing gauge timeseries → read, merge storm_responses, save back."""
        from port.src.stressm.gaugets_writer import populate_gaugets

        input_dir, catchment = populate_env

        gauge_ids = ["GAUGE-001", "GAUGE-002"]
        gauge_params_list = [
            {"gauge_id": "GAUGE-001", "base_level": 1.5},
            {"gauge_id": "GAUGE-002", "base_level": 2.0},
        ]
        sequence_records = [
            {
                "sequence_id": "STORM-001",
                "peaks_m": [4.0, 5.5],
                "alert": [True, True],
                "warning": [True, True],
                "severe": [False, True],
                "pulse_peaks": [
                    [{"storm_index": 0, "peak_m": 4.0}],
                    [{"storm_index": 0, "peak_m": 5.5}],
                ],
                "sequence_type": "isolated",
                "num_storms": 1,
            },
        ]

        # Mock the heavy GaugeTimeSeriesGenerator and generate_stress_storms
        mock_gen = MagicMock()
        mock_gen.generate.return_value = {"data": {"num_gauges": 2}}

        with patch(
            "port.src.gauge.gaugets.GaugeTimeSeriesGenerator",
            return_value=mock_gen,
        ):
            with patch(
                "port.src.gauge.stress_storms.generate_stress_storms",
                return_value={"total_storms": 1},
            ):
                populate_gaugets(
                    input_dir=input_dir,
                    gauge_params_list=gauge_params_list,
                    gauge_ids=gauge_ids,
                    sequence_records=sequence_records,
                    sequences=[],
                )

        # Both gauge timeseries now contain storm_responses (read via the seam)
        for gid in gauge_ids:
            data = database.get_gauge_timeseries(catchment, gid)
            assert "storm_responses" in data
            responses = data["storm_responses"]["responses"]
            assert len(responses) == 1
            assert responses[0]["storm_id"] == "STORM-001"
            assert "pulse_peaks" in responses[0]

    def test_skips_missing_gauge_files(self, tmp_path):
        """Gauge absent from the seam → continue (no merge, not created)."""
        from port.src.stressm.gaugets_writer import populate_gaugets

        input_dir = tmp_path / "input"
        input_dir.mkdir()
        with tmp_catchment(input_dir, catchment="thames"):
            catchment = database.active_catchment()
            # Only ONE gauge has a pre-existing timeseries
            database.save_gauge_timeseries(catchment, "GAUGE-001", {"x": 1})

            gauge_ids = ["GAUGE-001", "GAUGE-MISSING"]
            gauge_params_list = [
                {"gauge_id": "GAUGE-001", "base_level": 1.0},
                {"gauge_id": "GAUGE-MISSING", "base_level": 1.0},
            ]
            sequence_records = [{
                "sequence_id": "STORM-X",
                "peaks_m": [3.0, 3.0],
                "alert": [True, True],
                "warning": [False, False],
                "severe": [False, False],
            }]

            mock_gen = MagicMock()
            mock_gen.generate.return_value = {"data": {"num_gauges": 2}}

            with patch(
                "port.src.gauge.gaugets.GaugeTimeSeriesGenerator",
                return_value=mock_gen,
            ):
                with patch(
                    "port.src.gauge.stress_storms.generate_stress_storms",
                    return_value={"total_storms": 0},
                ):
                    populate_gaugets(
                        input_dir=input_dir,
                        gauge_params_list=gauge_params_list,
                        gauge_ids=gauge_ids,
                        sequence_records=sequence_records,
                        sequences=[],
                    )

            # Existing gauge got merged
            data = database.get_gauge_timeseries(catchment, "GAUGE-001")
            assert "storm_responses" in data
            # Missing gauge was not created
            assert "GAUGE-MISSING" not in set(
                database.iter_gauge_timeseries_ids(catchment))
