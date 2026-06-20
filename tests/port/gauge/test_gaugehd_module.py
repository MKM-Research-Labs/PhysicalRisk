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

"""Tests for module-level functions: load_gauge_portfolio, generate_all, process_nrfa_directory."""

import pytest

import database
from db_helpers import tmp_catchment
from tests.port.gauge.conftest import write_nrfa_csv, SAMPLE_GAUGE_ENTRY


@pytest.fixture(autouse=True)
def _iso_catchment(tmp_path):
    """Bind a tmp-rooted backend so the migrated gaugehd module functions read the
    gauge portfolio and write per-gauge history through database."""
    with tmp_catchment(tmp_path):
        yield


def _seed_gauges(entries):
    """Persist a gauge portfolio for the active (tmp) catchment."""
    database.save_gauges(database.active_catchment(), {"flood_gauges": entries})


# ===========================================================================
# load_gauge_portfolio
# ===========================================================================

class TestLoadGaugePortfolio:

    def test_load_gauge_portfolio_success(self, tmp_path):
        """load_gauge_portfolio reads the gauge portfolio via database."""
        _seed_gauges([{"FloodGauge": {"Header": {"GaugeID": "GAUGE-001"}}}])
        from port.src.gauge.gaugehd import load_gauge_portfolio
        result = load_gauge_portfolio()
        assert isinstance(result, list)
        assert len(result) == 1

    def test_load_gauge_portfolio_file_not_found(self, tmp_path):
        """Missing gauge portfolio raises FileNotFoundError."""
        from port.src.gauge.gaugehd import load_gauge_portfolio
        # No gauge portfolio seeded in the empty tmp backend.
        with pytest.raises(FileNotFoundError):
            load_gauge_portfolio()


# ===========================================================================
# generate_all_gauge_histories
# ===========================================================================

class TestGenerateAllGaugeHistories:

    def test_generate_all_gauge_histories(self, tmp_path):
        """generate_all_gauge_histories processes all gauges in the portfolio."""
        _seed_gauges([SAMPLE_GAUGE_ENTRY])
        from port.src.gauge.gaugehd import generate_all_gauge_histories
        result = generate_all_gauge_histories(years=5)
        assert isinstance(result, list)
        assert len(result) == 1

    def test_generate_all_gauge_histories_error_continues(self, tmp_path):
        """Error on one gauge -> logged, continues."""
        _seed_gauges([
            SAMPLE_GAUGE_ENTRY,
            {"FloodGauge": {"Header": {}}},  # bad entry
        ])
        from port.src.gauge.gaugehd import generate_all_gauge_histories
        result = generate_all_gauge_histories(years=5)
        assert isinstance(result, list)


# ===========================================================================
# process_nrfa_directory
# ===========================================================================

class TestProcessNrfaDirectory:

    def test_process_nrfa_directory_basic(self, tmp_path):
        """Lines 113-147: process_nrfa_directory scans CSV files."""
        from port.src.gauge.gaugehd import process_nrfa_directory
        write_nrfa_csv(tmp_path, station_id="39001", n_rows=10)
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        result = process_nrfa_directory(tmp_path, years=5)
        assert isinstance(result, list)
        assert len(result) == 1

    def test_process_nrfa_directory_persists_history(self, tmp_path):
        """Generated histories persist through database under the active catchment."""
        write_nrfa_csv(tmp_path, station_id="39002", n_rows=10)
        from port.src.gauge.gaugehd import process_nrfa_directory
        result = process_nrfa_directory(tmp_path, years=5)
        assert isinstance(result, list)
        assert list(database.iter_gauge_history_ids(database.active_catchment()))

    def test_process_nrfa_directory_empty_dir(self, tmp_path):
        """Lines 131-147: no matching files -> empty list."""
        from port.src.gauge.gaugehd import process_nrfa_directory
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        result = process_nrfa_directory(tmp_path, years=5)
        assert result == []

    def test_process_nrfa_directory_bad_csv_continues(self, tmp_path):
        """Lines 143-144: bad CSV -> error logged, continues."""
        from port.src.gauge.gaugehd import process_nrfa_directory
        bad = tmp_path / "badstation_gdf.csv"
        bad.write_text("this is not a valid csv for generate_from_nrfa")
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        result = process_nrfa_directory(tmp_path, years=5)
        assert isinstance(result, list)
