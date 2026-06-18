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

import json

import pytest

from tests.port.gauge.conftest import write_nrfa_csv, SAMPLE_GAUGE_ENTRY


# ===========================================================================
# load_gauge_portfolio
# ===========================================================================

class TestLoadGaugePortfolio:

    def test_load_gauge_portfolio_success(self, tmp_path, monkeypatch):
        """Lines 72-80: load_gauge_portfolio reads gauge.json."""
        from config import config
        gauge_data = {"flood_gauges": [{"FloodGauge": {"Header": {"GaugeID": "GAUGE-001"}}}]}
        gauge_file = tmp_path / "gauge.json"
        gauge_file.write_text(json.dumps(gauge_data))
        monkeypatch.setattr(config, "get_input_path", lambda f: gauge_file)
        from port.src.gauge.gaugehd import load_gauge_portfolio
        result = load_gauge_portfolio()
        assert isinstance(result, list)
        assert len(result) == 1

    def test_load_gauge_portfolio_file_not_found(self, tmp_path, monkeypatch):
        """Lines 74-75: missing file raises FileNotFoundError."""
        from config import config
        monkeypatch.setattr(config, "get_input_path", lambda f: tmp_path / "nonexistent.json")
        from port.src.gauge.gaugehd import load_gauge_portfolio
        with pytest.raises(FileNotFoundError):
            load_gauge_portfolio()


# ===========================================================================
# generate_all_gauge_histories
# ===========================================================================

class TestGenerateAllGaugeHistories:

    def test_generate_all_gauge_histories(self, tmp_path, monkeypatch):
        """Lines 83-110: generate_all_gauge_histories processes all gauges."""
        from config import config
        gauge_data = {"flood_gauges": [SAMPLE_GAUGE_ENTRY]}
        gauge_file = tmp_path / "gauge.json"
        gauge_file.write_text(json.dumps(gauge_data))
        gaugehd_dir = tmp_path / "gaugehd"
        gaugehd_dir.mkdir()
        monkeypatch.setattr(config, "get_input_path", lambda f: gauge_file)
        monkeypatch.setattr(config, "get_gaugehd_dir", lambda: gaugehd_dir)
        from port.src.gauge.gaugehd import generate_all_gauge_histories
        result = generate_all_gauge_histories(years=5)
        assert isinstance(result, list)
        assert len(result) == 1

    def test_generate_all_gauge_histories_error_continues(self, tmp_path, monkeypatch):
        """Lines 105-107: error on one gauge -> logged, continues."""
        from config import config
        gauge_data = {"flood_gauges": [
            SAMPLE_GAUGE_ENTRY,
            {"FloodGauge": {"Header": {}}},  # bad entry
        ]}
        gauge_file = tmp_path / "gauge.json"
        gauge_file.write_text(json.dumps(gauge_data))
        gaugehd_dir = tmp_path / "gaugehd"
        gaugehd_dir.mkdir()
        monkeypatch.setattr(config, "get_input_path", lambda f: gauge_file)
        monkeypatch.setattr(config, "get_gaugehd_dir", lambda: gaugehd_dir)
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
        result = process_nrfa_directory(tmp_path, output_dir=output_dir, years=5)
        assert isinstance(result, list)
        assert len(result) == 1

    def test_process_nrfa_directory_default_output(self, tmp_path, monkeypatch):
        """Line 134: output_dir=None uses config.get_gaugehd_dir()."""
        from config import config
        output_dir = tmp_path / "gaugehd"
        output_dir.mkdir()
        monkeypatch.setattr(config, "get_gaugehd_dir", lambda: output_dir)
        write_nrfa_csv(tmp_path, station_id="39002", n_rows=10)
        from port.src.gauge.gaugehd import process_nrfa_directory
        result = process_nrfa_directory(tmp_path, output_dir=None, years=5)
        assert isinstance(result, list)

    def test_process_nrfa_directory_empty_dir(self, tmp_path):
        """Lines 131-147: no matching files -> empty list."""
        from port.src.gauge.gaugehd import process_nrfa_directory
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        result = process_nrfa_directory(tmp_path, output_dir=output_dir, years=5)
        assert result == []

    def test_process_nrfa_directory_bad_csv_continues(self, tmp_path):
        """Lines 143-144: bad CSV -> error logged, continues."""
        from port.src.gauge.gaugehd import process_nrfa_directory
        bad = tmp_path / "badstation_gdf.csv"
        bad.write_text("this is not a valid csv for generate_from_nrfa")
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        result = process_nrfa_directory(tmp_path, output_dir=output_dir, years=5)
        assert isinstance(result, list)
