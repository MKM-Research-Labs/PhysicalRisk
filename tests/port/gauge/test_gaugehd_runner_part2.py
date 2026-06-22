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

"""Tests for port.src.gauge.gaugehd.runner — part 2: NRFA processing and CLI."""

import json
import logging
from pathlib import Path

import pytest

from db_helpers import tmp_catchment
from tests.port.gauge.conftest import SAMPLE_GAUGE_ENTRY, setup_gauge_env, write_nrfa_csv


@pytest.fixture(autouse=True)
def _iso_catchment(tmp_path):
    """Bind a tmp-rooted backend so the migrated gaugehd writers/readers (and the NRFA
    importer) persist per-gauge history through database under tmp_path/gaugehd."""
    with tmp_catchment(tmp_path):
        yield


# ===========================================================================
# process_nrfa_directory — additional coverage
# ===========================================================================

class TestProcessNrfaDirectoryRunner:

    def test_custom_pattern(self, tmp_path):
        """Line 61/80: custom glob pattern selects different files."""
        from port.src.gauge.gaugehd.runner import process_nrfa_directory
        # Write a file with non-default pattern
        csv_file = tmp_path / "station1_daily.csv"
        lines = [
            "file,timestamp,2024-01-01T00:00",
            "station,id,S001",
            "station,name,Test Station",
            "2020-01-01,10.0",
            "2020-01-02,11.0",
        ]
        csv_file.write_text("\n".join(lines))
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        result = process_nrfa_directory(
            tmp_path, years=5, pattern="*_daily.csv"
        )
        assert len(result) == 1

    def test_multiple_csv_files(self, tmp_path):
        """Multiple CSV files in directory are all processed."""
        from port.src.gauge.gaugehd.runner import process_nrfa_directory
        write_nrfa_csv(tmp_path, station_id="39001", n_rows=10)
        write_nrfa_csv(tmp_path, station_id="39002", n_rows=10)
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        result = process_nrfa_directory(tmp_path, years=5)
        assert len(result) == 2

    def test_station_id_from_filename(self, tmp_path):
        """Line 81: station_id extracted by stripping _gdf from stem."""
        from port.src.gauge.gaugehd.runner import process_nrfa_directory
        write_nrfa_csv(tmp_path, station_id="99999", n_rows=5)
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        result = process_nrfa_directory(tmp_path, years=5)
        assert len(result) == 1
        assert "99999" in result[0]

    def test_error_in_one_csv_continues(self, tmp_path, caplog):
        """Line 87-88: error on one file doesn't stop processing others."""
        from port.src.gauge.gaugehd.runner import process_nrfa_directory
        # One good, one bad
        write_nrfa_csv(tmp_path, station_id="GOOD1", n_rows=10)
        bad = tmp_path / "BAD1_gdf.csv"
        bad.write_text("not valid csv content at all")
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        with caplog.at_level(logging.ERROR):
            result = process_nrfa_directory(tmp_path, years=5)
        # Good file should succeed
        assert len(result) >= 1

    def test_generate_from_nrfa_exception_is_logged(self, tmp_path, caplog,
                                                     monkeypatch):
        """Lines 89-90: when generate_from_nrfa raises, the error is logged
        and processing continues to the next file.
        """
        import logging as _logging
        from port.src.gauge.gaugehd import runner

        write_nrfa_csv(tmp_path, station_id="EXC1", n_rows=10)
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        monkeypatch.setattr(
            runner, "generate_from_nrfa",
            lambda *a, **kw: (_ for _ in ()).throw(RuntimeError("boom"))
        )
        with caplog.at_level(_logging.ERROR):
            result = runner.process_nrfa_directory(
                tmp_path, years=5
            )

        assert result == []
        assert "EXC1" in caplog.text
        assert "boom" in caplog.text


# ===========================================================================
# main() — CLI entry point
# ===========================================================================

class TestMain:

    def test_main_default_synthetic(self, tmp_path, monkeypatch):
        """Lines 120-122: default (no --nrfa-dir) calls generate_all_gauge_histories."""
        from port.src.gauge.gaugehd.runner import main
        setup_gauge_env(tmp_path)
        monkeypatch.setattr("sys.argv", ["gaugehd"])
        main()

    def test_main_with_years(self, tmp_path, monkeypatch):
        """Line 101: --years flag is passed through."""
        from port.src.gauge.gaugehd.runner import main
        setup_gauge_env(tmp_path)
        monkeypatch.setattr("sys.argv", ["gaugehd", "--years", "10"])
        main()

    def test_main_with_catchment(self, tmp_path, monkeypatch):
        """Lines 113-115: --catchment activates that catchment for the run (scoped).

        ``main`` now switches catchment via ``config.use_catchment`` — active *during*
        the run and restored on exit — rather than permanently mutating the global."""
        from config import config
        from port.src.gauge.gaugehd import runner
        setup_gauge_env(tmp_path)
        original = config.catchment_id
        seen = {}

        def _spy(years=50):
            seen["catchment"] = config.CATCHMENT
            return []

        monkeypatch.setattr(runner, "generate_all_gauge_histories", _spy)
        monkeypatch.setattr("sys.argv", ["gaugehd", "--catchment", "rhine"])

        runner.main()

        assert seen["catchment"] == "rhine"       # active during the run
        assert config.catchment_id == original    # restored after (scoped, not pinned)

    def test_main_with_nrfa_dir(self, tmp_path, monkeypatch):
        """Lines 117-119: --nrfa-dir calls process_nrfa_directory."""
        from port.src.gauge.gaugehd.runner import main
        nrfa_dir = tmp_path / "nrfa"
        nrfa_dir.mkdir()
        write_nrfa_csv(nrfa_dir, station_id="39001", n_rows=10)
        gaugehd_dir = tmp_path / "gaugehd"
        gaugehd_dir.mkdir()
        from config import config
        monkeypatch.setattr(config, "get_gaugehd_dir", lambda: gaugehd_dir)
        monkeypatch.setattr("sys.argv", [
            "gaugehd", "--nrfa-dir", str(nrfa_dir), "--years", "5"
        ])
        main()
        # Should have created output file
        assert list(gaugehd_dir.glob("gauge_*_hd.json"))

    def test_main_short_years_flag(self, tmp_path, monkeypatch):
        """Line 101: -y short flag for years."""
        from port.src.gauge.gaugehd.runner import main
        setup_gauge_env(tmp_path)
        monkeypatch.setattr("sys.argv", ["gaugehd", "-y", "3"])
        main()

    def test_main_short_catchment_flag(self, tmp_path, monkeypatch):
        """Line 108: -c short flag for catchment (scoped + self-restoring)."""
        from port.src.gauge.gaugehd.runner import main
        setup_gauge_env(tmp_path)
        monkeypatch.setattr("sys.argv", ["gaugehd", "-c", "thames"])
        main()  # use_catchment("thames") activates + restores on its own

    def test_main_no_catchment_leaves_config_unchanged(self, tmp_path, monkeypatch):
        """Lines 107-108: without --catchment, config.catchment_id is untouched."""
        from config import config
        from port.src.gauge.gaugehd.runner import main
        setup_gauge_env(tmp_path)
        original = config.catchment_id
        monkeypatch.setattr("sys.argv", ["gaugehd"])
        main()
        assert config.catchment_id == original
