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

"""Tests for port.src.gauge.gaugehd.runner — part 1: stale file cleanup and error handling."""

import json
import logging
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from tests.port.gauge.conftest import SAMPLE_GAUGE_ENTRY, setup_gauge_env, write_nrfa_csv


# ===========================================================================
# generate_all_gauge_histories — stale file cleanup
# ===========================================================================

class TestStaleFileCleanup:

    def test_removes_stale_gauge_files(self, tmp_path, monkeypatch):
        """Lines 37-39: old gauge_GAUGE-*_hd.json files are removed."""
        from port.src.gauge.gaugehd.runner import generate_all_gauge_histories
        _, gaugehd_dir = setup_gauge_env(tmp_path, monkeypatch)
        # Create a stale file that should be cleaned up
        stale = gaugehd_dir / "gauge_GAUGE-OLD_hd.json"
        stale.write_text("{}")
        assert stale.exists()
        generate_all_gauge_histories(years=5)
        assert not stale.exists()

    def test_does_not_remove_non_matching_files(self, tmp_path, monkeypatch):
        """Only gauge_GAUGE-*_hd.json files are removed, not other files."""
        from port.src.gauge.gaugehd.runner import generate_all_gauge_histories
        _, gaugehd_dir = setup_gauge_env(tmp_path, monkeypatch)
        other = gaugehd_dir / "other_data.json"
        other.write_text("{}")
        generate_all_gauge_histories(years=5)
        assert other.exists()

    def test_removes_multiple_stale_files(self, tmp_path, monkeypatch):
        """Multiple stale files are all removed."""
        from port.src.gauge.gaugehd.runner import generate_all_gauge_histories
        _, gaugehd_dir = setup_gauge_env(tmp_path, monkeypatch)
        stales = []
        for i in range(3):
            s = gaugehd_dir / f"gauge_GAUGE-STALE{i}_hd.json"
            s.write_text("{}")
            stales.append(s)
        generate_all_gauge_histories(years=5)
        for s in stales:
            assert not s.exists()

    def test_removes_stale_synth_files(self, tmp_path, monkeypatch):
        """Line 41: stale gauge_SYNTH-*_hd.json files are also removed."""
        from port.src.gauge.gaugehd.runner import generate_all_gauge_histories
        _, gaugehd_dir = setup_gauge_env(tmp_path, monkeypatch)
        synth_stale = gaugehd_dir / "gauge_SYNTH-OLD_hd.json"
        synth_stale.write_text("{}")
        assert synth_stale.exists()
        generate_all_gauge_histories(years=5)
        assert not synth_stale.exists()


# ===========================================================================
# generate_all_gauge_histories — error handling
# ===========================================================================

class TestGenerateAllErrorPaths:

    def test_error_extracts_gauge_id_from_nested_header(self, tmp_path, monkeypatch, caplog):
        """Line 50: error path extracts GaugeID from FloodGauge.Header."""
        from port.src.gauge.gaugehd.runner import generate_all_gauge_histories
        bad_entry = {
            "FloodGauge": {
                "Header": {"GaugeID": "GAUGE-BADONE"},
                "FloodStages": {"FloodAlert": 3.0, "FloodWarning": 4.5, "SevereFloodWarning": 5.5},
            }
        }
        setup_gauge_env(tmp_path, monkeypatch, gauge_entries=[bad_entry])
        # Mock generate_from_gauge_portfolio to raise an error
        with patch("port.src.gauge.gaugehd.runner.generate_from_gauge_portfolio",
                   side_effect=ValueError("test error")):
            with caplog.at_level(logging.ERROR):
                result = generate_all_gauge_histories(years=5)
        assert len(result) == 0
        assert "GAUGE-BADONE" in caplog.text

    def test_error_with_no_header_uses_unknown(self, tmp_path, monkeypatch, caplog):
        """Line 50: completely empty entry uses UNKNOWN as gauge_id."""
        from port.src.gauge.gaugehd.runner import generate_all_gauge_histories
        setup_gauge_env(tmp_path, monkeypatch, gauge_entries=[{}])
        with patch("port.src.gauge.gaugehd.runner.generate_from_gauge_portfolio",
                   side_effect=RuntimeError("boom")):
            with caplog.at_level(logging.ERROR):
                result = generate_all_gauge_histories(years=5)
        assert len(result) == 0
        assert "UNKNOWN" in caplog.text

    def test_mixed_good_and_bad_gauges(self, tmp_path, monkeypatch):
        """Good gauges succeed even when bad ones fail."""
        from port.src.gauge.gaugehd.runner import generate_all_gauge_histories
        setup_gauge_env(tmp_path, monkeypatch, gauge_entries=[SAMPLE_GAUGE_ENTRY, SAMPLE_GAUGE_ENTRY])
        call_count = [0]

        def _side_effect(entry, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise ValueError("first gauge fails")
            # Import and call real function for second gauge
            from port.src.gauge.gaugehd.synthetic import generate_from_gauge_portfolio as real
            return real(entry, **kwargs)

        with patch("port.src.gauge.gaugehd.runner.generate_from_gauge_portfolio",
                   side_effect=_side_effect):
            result = generate_all_gauge_histories(years=5)
        assert len(result) == 1  # only the second one

    def test_empty_portfolio_returns_empty(self, tmp_path, monkeypatch):
        """No gauges in portfolio returns empty list."""
        from port.src.gauge.gaugehd.runner import generate_all_gauge_histories
        setup_gauge_env(tmp_path, monkeypatch, gauge_entries=[])
        result = generate_all_gauge_histories(years=5)
        assert result == []
