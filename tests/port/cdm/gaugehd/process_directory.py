# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.
#
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Tests for process_directory."""

from pathlib import Path
from unittest.mock import patch

from port.cdm.gaugehd import process_directory

from .conftest import write_nrfa_csv


class TestProcessDirectory:

    def test_processes_matching_files(self, tmp_path):
        write_nrfa_csv(tmp_path, station_id="39001")
        write_nrfa_csv(tmp_path, station_id="40007")
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        with patch("port.cdm.gaugehd.directory.config") as mock_config:
            mock_config.input_dir = output_dir
            result = process_directory(tmp_path, output_dir=output_dir, years=2)
        assert len(result) == 2

    def test_output_files_created(self, tmp_path):
        write_nrfa_csv(tmp_path, station_id="39001")
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        with patch("port.cdm.gaugehd.directory.config") as mock_config:
            mock_config.input_dir = output_dir
            result = process_directory(tmp_path, output_dir=output_dir, years=2)
        assert all(Path(p).exists() for p in result)

    def test_empty_directory_returns_empty_list(self, tmp_path):
        output_dir = tmp_path / "empty_out"
        output_dir.mkdir()
        with patch("port.cdm.gaugehd.directory.config") as mock_config:
            mock_config.input_dir = output_dir
            result = process_directory(tmp_path, output_dir=output_dir)
        assert result == []

    def test_non_matching_files_skipped(self, tmp_path):
        (tmp_path / "station.csv").write_text("2020-01-01,50.0\n")
        output_dir = tmp_path / "out"
        output_dir.mkdir()
        with patch("port.cdm.gaugehd.directory.config") as mock_config:
            mock_config.input_dir = output_dir
            result = process_directory(tmp_path, output_dir=output_dir)
        assert result == []

    def test_output_dir_none_uses_input_dir(self, tmp_path):
        write_nrfa_csv(tmp_path, station_id="39999")
        with patch("port.cdm.gaugehd.directory.config") as mock_config:
            mock_config.input_dir = tmp_path
            result = process_directory(tmp_path, output_dir=None, years=2)
        assert isinstance(result, list)
        assert any("gaugehd_39999" in r for r in result)

    def test_process_directory_error_continues(self, tmp_path):
        write_nrfa_csv(tmp_path, station_id="39001")
        (tmp_path / "bad_gdf.csv").write_text("")
        output_dir = tmp_path / "out"
        output_dir.mkdir()
        with patch("port.cdm.gaugehd.directory.config") as mock_config:
            mock_config.input_dir = output_dir
            result = process_directory(tmp_path, output_dir=output_dir, years=2)
        assert isinstance(result, list)
