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

"""Tests for NRFA CSV parsing, year filtering, and generate_from_nrfa."""

import pytest

import database
from db_helpers import tmp_catchment
from tests.port.gauge.conftest import write_nrfa_csv


@pytest.fixture(autouse=True)
def _iso_catchment(tmp_path):
    """Bind a tmp-rooted backend so the migrated NRFA importer persists gauge history
    through database (physically under tmp_path/gaugehd)."""
    with tmp_catchment(tmp_path):
        yield


# ===========================================================================
# parse_nrfa_csv
# ===========================================================================

class TestParseNrfaCsv:

    def test_returns_tuple(self, tmp_path):
        from port.src.gauge.gaugehd.nrfa import parse_nrfa_csv
        csv_file = write_nrfa_csv(tmp_path)
        metadata, flows = parse_nrfa_csv(csv_file)
        assert isinstance(metadata, dict)
        assert isinstance(flows, list)

    def test_metadata_contains_station_id(self, tmp_path):
        from port.src.gauge.gaugehd.nrfa import parse_nrfa_csv
        csv_file = write_nrfa_csv(tmp_path, station_id="39001")
        metadata, _ = parse_nrfa_csv(csv_file)
        assert "station_id" in metadata
        assert metadata["station_id"] == "39001"

    def test_metadata_contains_station_name(self, tmp_path):
        from port.src.gauge.gaugehd.nrfa import parse_nrfa_csv
        csv_file = write_nrfa_csv(tmp_path, station_name="Test River")
        metadata, _ = parse_nrfa_csv(csv_file)
        assert metadata.get("station_name") == "Test River"

    def test_flows_have_date_and_flow(self, tmp_path):
        from port.src.gauge.gaugehd.nrfa import parse_nrfa_csv
        csv_file = write_nrfa_csv(tmp_path, n_rows=5)
        _, flows = parse_nrfa_csv(csv_file)
        assert len(flows) == 5
        for f in flows:
            assert "date" in f
            assert "flow_cumecs" in f

    def test_skips_short_rows(self, tmp_path):
        """Lines with fewer than 2 columns are skipped."""
        from port.src.gauge.gaugehd.nrfa import parse_nrfa_csv
        p = tmp_path / "short.csv"
        p.write_text("single_col\n2020-01-01,10.0\nbad_date,not_a_float\n")
        _, flows = parse_nrfa_csv(p)
        assert len(flows) == 1

    def test_empty_file(self, tmp_path):
        from port.src.gauge.gaugehd.nrfa import parse_nrfa_csv
        p = tmp_path / "empty.csv"
        p.write_text("")
        metadata, flows = parse_nrfa_csv(p)
        assert metadata == {}
        assert flows == []


# ===========================================================================
# filter_by_years
# ===========================================================================

class TestFilterByYears:

    def _flows(self, years_back=60):
        """Generate daily_flows spanning years_back years."""
        from datetime import date, timedelta
        flows = []
        start = date(2024 - years_back, 1, 1)
        for i in range(0, years_back * 365, 30):
            d = start + timedelta(days=i)
            flows.append({"date": d.isoformat(), "flow_cumecs": float(i)})
        return flows

    def test_none_years_returns_all(self):
        from port.src.gauge.gaugehd.nrfa import filter_by_years
        flows = self._flows(10)
        result = filter_by_years(flows, years=None)
        assert len(result) == len(flows)

    def test_empty_list_returns_empty(self):
        from port.src.gauge.gaugehd.nrfa import filter_by_years
        result = filter_by_years([], years=5)
        assert result == []

    def test_5_year_filter(self):
        from port.src.gauge.gaugehd.nrfa import filter_by_years
        flows = self._flows(20)
        result = filter_by_years(flows, years=5)
        assert len(result) < len(flows)
        assert len(result) > 0

    def test_large_years_returns_all(self):
        from port.src.gauge.gaugehd.nrfa import filter_by_years
        flows = self._flows(10)
        result = filter_by_years(flows, years=100)
        assert len(result) == len(flows)


# ===========================================================================
# generate_from_nrfa
# ===========================================================================

class TestGenerateFromNrfa:

    def test_persists_history(self, tmp_path):
        from port.src.gauge.gaugehd.nrfa import generate_from_nrfa
        csv_file = write_nrfa_csv(tmp_path, n_rows=30)
        generate_from_nrfa(csv_file, years=50)
        # Persisted as a keyed gauge_history record through database.
        assert list(database.iter_gauge_history_ids(database.active_catchment()))

    def test_returns_dict(self, tmp_path):
        from port.src.gauge.gaugehd.nrfa import generate_from_nrfa
        csv_file = write_nrfa_csv(tmp_path, n_rows=30)
        output = tmp_path / "output.json"
        result = generate_from_nrfa(csv_file, years=50)
        assert isinstance(result, dict)

    def test_schema_version_in_output(self, tmp_path):
        from port.src.gauge.gaugehd.nrfa import generate_from_nrfa
        csv_file = write_nrfa_csv(tmp_path, n_rows=30)
        output = tmp_path / "output.json"
        result = generate_from_nrfa(csv_file, years=50)
        assert result["schema_version"] == "1.0"
        assert result["data_type"] == "GaugeHistoricalDaily"

    def test_station_metadata_extracted(self, tmp_path):
        from port.src.gauge.gaugehd.nrfa import generate_from_nrfa
        csv_file = write_nrfa_csv(tmp_path, station_id="39001",
                                   station_name="Thames at Kingston")
        output = tmp_path / "output.json"
        result = generate_from_nrfa(csv_file)
        assert result["station_metadata"]["station_name"] == "Thames at Kingston"

    def test_gauge_id_override(self, tmp_path):
        from port.src.gauge.gaugehd.nrfa import generate_from_nrfa
        csv_file = write_nrfa_csv(tmp_path)
        output = tmp_path / "output.json"
        result = generate_from_nrfa(csv_file, gauge_id="GAUGE-CUSTOM")
        assert result["station_metadata"]["station_id"] == "GAUGE-CUSTOM"

    def test_auto_output_path(self, tmp_path, monkeypatch):
        """When output_path=None, uses config.get_gaugehd_dir()."""
        from port.src.gauge.gaugehd.nrfa import generate_from_nrfa
        from config import config
        monkeypatch.setattr(config, "get_gaugehd_dir", lambda: tmp_path / "gaugehd")
        (tmp_path / "gaugehd").mkdir()
        csv_file = write_nrfa_csv(tmp_path, station_id="AUTO-01")
        result = generate_from_nrfa(csv_file, years=10)
        assert isinstance(result, dict)
        assert (tmp_path / "gaugehd" / "gauge_AUTO-01_hd.json").exists()
