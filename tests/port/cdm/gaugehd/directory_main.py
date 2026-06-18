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

"""Tests for the main() CLI entry point in directory.py."""

from unittest.mock import patch

from port.cdm.gaugehd import main

from .conftest import write_nrfa_csv


class TestMain:

    def test_main_with_csv_files_runs_without_error(self, tmp_path):
        """main() processes any *_gdf.csv files found in config.input_dir."""
        write_nrfa_csv(tmp_path, station_id="39001")
        with patch("port.cdm.gaugehd.directory.config") as mock_config:
            mock_config.input_dir = tmp_path
            main()   # should not raise

    def test_main_with_no_csv_files_runs_without_error(self, tmp_path):
        """main() handles an empty directory gracefully."""
        with patch("port.cdm.gaugehd.directory.config") as mock_config:
            mock_config.input_dir = tmp_path
            main()   # should not raise

    def test_main_skips_bad_file_without_raising(self, tmp_path):
        """main() logs errors for unreadable files and continues."""
        (tmp_path / "bad_gdf.csv").write_text("not,valid,csv\n")
        with patch("port.cdm.gaugehd.directory.config") as mock_config:
            mock_config.input_dir = tmp_path
            main()   # should not raise
