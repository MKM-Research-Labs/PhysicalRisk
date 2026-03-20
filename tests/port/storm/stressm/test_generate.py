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

"""Tests for generate_stressm: summary dict, output files, edge cases, progress."""

import json

import pytest

from port.src.stressm import (
    GAUGE_SUMMARY_FILENAME,
    SCHEMA_VERSION_SPATIAL,
    generate_stressm,
)
from port.src.storm_multi.utils.serialization import (
    SEQUENCES_FILENAME,
    SUMMARY_FILENAME,
    load_sequences,
)


# ---------------------------------------------------------------------------
# generate_stressm — summary dict
# ---------------------------------------------------------------------------

class TestGenerateStressmSummary:

    def test_returns_dict(self, full_run):
        assert isinstance(full_run, dict)

    def test_num_sequences(self, full_run):
        assert full_run["num_sequences"] == 40

    def test_num_gauges(self, full_run):
        assert full_run["num_gauges"] == 3

    def test_type_counts_present(self, full_run):
        assert "type_counts" in full_run
        assert sum(full_run["type_counts"].values()) == 40

    def test_alert_count_non_negative(self, full_run):
        assert full_run["alert_sequences"] >= 0

    def test_warning_lte_alert(self, full_run):
        assert full_run["warning_sequences"] <= full_run["alert_sequences"]

    def test_severe_lte_warning(self, full_run):
        assert full_run["severe_sequences"] <= full_run["warning_sequences"]

    def test_elapsed_positive(self, full_run):
        assert full_run["elapsed_seconds"] > 0


# ---------------------------------------------------------------------------
# generate_stressm — output files
# ---------------------------------------------------------------------------

class TestGenerateStressmFiles:

    def test_sequences_json_written(self, gauge_dir, full_run):
        assert (gauge_dir / SEQUENCES_FILENAME).exists()

    def test_summary_json_written(self, gauge_dir, full_run):
        assert (gauge_dir / SUMMARY_FILENAME).exists()

    def test_gauge_summary_json_written(self, gauge_dir, full_run):
        assert (gauge_dir / GAUGE_SUMMARY_FILENAME).exists()

    def test_sequences_file_loadable(self, gauge_dir, full_run):
        seqs = load_sequences(gauge_dir / SEQUENCES_FILENAME)
        assert len(seqs) == 40

    def test_gauge_summary_schema_version(self, gauge_dir, full_run):
        with open(gauge_dir / GAUGE_SUMMARY_FILENAME) as f:
            d = json.load(f)
        assert d["schema_version"] == SCHEMA_VERSION_SPATIAL

    def test_gauge_summary_num_gauges(self, gauge_dir, full_run):
        with open(gauge_dir / GAUGE_SUMMARY_FILENAME) as f:
            d = json.load(f)
        assert d["num_gauges"] == 3

    def test_gauge_summary_gauge_ids(self, gauge_dir, full_run):
        with open(gauge_dir / GAUGE_SUMMARY_FILENAME) as f:
            d = json.load(f)
        assert len(d["gauge_ids"]) == 3

    def test_gauge_summary_sequence_count(self, gauge_dir, full_run):
        with open(gauge_dir / GAUGE_SUMMARY_FILENAME) as f:
            d = json.load(f)
        assert len(d["sequences"]) == 40


# ---------------------------------------------------------------------------
# Missing gauge.json — graceful degradation
# ---------------------------------------------------------------------------

class TestMissingGaugeJson:

    def test_no_crash_when_gauge_json_absent(self, tmp_path):
        result = generate_stressm(
            input_dir=tmp_path,
            output_dir=tmp_path,
            count=10,
            catchment_id="thames",
            seed=0,
        )
        assert isinstance(result, dict)

    def test_sequences_still_written_without_gauge_json(self, tmp_path):
        generate_stressm(
            input_dir=tmp_path,
            output_dir=tmp_path,
            count=10,
            catchment_id="thames",
            seed=0,
        )
        assert (tmp_path / SEQUENCES_FILENAME).exists()

    def test_num_gauges_zero_without_gauge_json(self, tmp_path):
        result = generate_stressm(
            input_dir=tmp_path,
            output_dir=tmp_path,
            count=10,
            catchment_id="thames",
            seed=0,
        )
        assert result["num_gauges"] == 0


# ---------------------------------------------------------------------------
# Lines 198-199: gauge.json exists but all records are invalid (n_all == 0)
# ---------------------------------------------------------------------------

class TestNoValidGauges:

    def test_returns_gracefully_when_all_gauges_invalid(self, tmp_path):
        """gauge.json present but every record missing gauge_id → n_all == 0."""
        bad_gauge_json = {
            "flood_gauges": [
                {"FloodGauge": {"Header": {}, "Location": {}, "FloodStages": {}}},
                {"FloodGauge": {"Header": {}, "Location": {}, "FloodStages": {}}},
            ]
        }
        (tmp_path / "gauge.json").write_text(json.dumps(bad_gauge_json))
        result = generate_stressm(
            input_dir=tmp_path,
            output_dir=tmp_path,
            count=5,
            catchment_id="thames",
            seed=0,
        )
        assert isinstance(result, dict)
        assert result["num_gauges"] == 0
        assert result["num_sequences"] == 5

    def test_sequences_still_written_when_all_gauges_invalid(self, tmp_path):
        bad_gauge_json = {"flood_gauges": [
            {"FloodGauge": {"Header": {}, "Location": {}, "FloodStages": {}}}
        ]}
        (tmp_path / "gauge.json").write_text(json.dumps(bad_gauge_json))
        generate_stressm(input_dir=tmp_path, output_dir=tmp_path, count=5, seed=0)
        assert (tmp_path / SEQUENCES_FILENAME).exists()


# ---------------------------------------------------------------------------
# Lines 268-271: verbose progress logging (triggers at i == 500)
# ---------------------------------------------------------------------------

class TestVerboseProgressLogging:

    def test_verbose_run_completes(self, gauge_dir, tmp_path, capsys):
        """count=501 with verbose=True triggers the progress line at i=500."""
        result = generate_stressm(
            input_dir=gauge_dir,
            output_dir=tmp_path,
            count=501,
            catchment_id="thames",
            seed=0,
            verbose=True,
        )
        out = capsys.readouterr().out
        assert result["num_sequences"] == 501
        # Progress line format: "[500/501]"
        assert "[500" in out or "500/" in out

    def test_verbose_false_no_mid_loop_output_at_small_count(self, gauge_dir,
                                                               tmp_path, capsys):
        """With count < 2000 and verbose=False, no mid-loop progress line."""
        generate_stressm(
            input_dir=gauge_dir,
            output_dir=tmp_path,
            count=40,
            seed=0,
            verbose=False,
        )
        out = capsys.readouterr().out
        # The ETA format only appears at i==2000+; should not appear here
        assert "ETA" not in out or "[" not in out
