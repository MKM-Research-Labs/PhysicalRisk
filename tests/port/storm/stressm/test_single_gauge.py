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

"""Tests for single-gauge mode and single-gauge + classifier training."""

import pytest

import database
from port.src.stressm import SCHEMA_VERSION_SPATIAL, generate_stressm

# ---------------------------------------------------------------------------
# Single-gauge mode
# ---------------------------------------------------------------------------

class TestSingleGaugeMode:

    def test_summary_num_gauges_is_one(self, single_run):
        assert single_run["num_gauges"] == 1

    def test_named_output_file_written(self, gauge_dir, single_run):
        # Single-gauge output is persisted under the gauge's sequence_gauge key.
        assert database.get_sequence_gauge("thames", "GAUGE-test002") is not None

    def test_named_file_schema_version(self, gauge_dir, single_run):
        d = database.get_sequence_gauge("thames", "GAUGE-test002")
        assert d["schema_version"] == SCHEMA_VERSION_SPATIAL

    def test_named_file_gauge_ids(self, gauge_dir, single_run):
        d = database.get_sequence_gauge("thames", "GAUGE-test002")
        assert d["gauge_ids"] == ["GAUGE-test002"]

    def test_named_file_peaks_length_one(self, gauge_dir, single_run):
        d = database.get_sequence_gauge("thames", "GAUGE-test002")
        assert all(len(r["peaks_m"]) == 1 for r in d["sequences"])

    def test_named_file_sequence_count(self, gauge_dir, single_run):
        d = database.get_sequence_gauge("thames", "GAUGE-test002")
        assert len(d["sequences"]) == 40

    def test_invalid_gauge_id_raises(self, gauge_dir, tmp_path):
        with pytest.raises(ValueError, match="not found"):
            generate_stressm(
                input_dir=gauge_dir,
                output_dir=tmp_path,
                count=5,
                catchment_id="thames",
                seed=0,
                gauge_id="GAUGE-doesnotexist",
            )

    def test_error_message_lists_available_ids(self, gauge_dir, tmp_path):
        with pytest.raises(ValueError) as exc_info:
            generate_stressm(
                input_dir=gauge_dir,
                output_dir=tmp_path,
                count=5,
                catchment_id="thames",
                seed=0,
                gauge_id="GAUGE-bad",
            )
        assert "GAUGE-test001" in str(exc_info.value)


# ---------------------------------------------------------------------------
# Lines 353-361: single-gauge + train_classifier=True
# ---------------------------------------------------------------------------

class TestSingleGaugeWithClassifier:

    def test_single_gauge_train_classifier(self, gauge_dir, tmp_path):
        """Single gauge + train_classifier=True covers lines 353-361."""
        result = generate_stressm(
            input_dir=gauge_dir,
            output_dir=tmp_path,
            count=20,
            catchment_id="thames",
            seed=42,
            gauge_id="GAUGE-test001",
            train_classifier=True,
        )
        assert result["num_gauges"] == 1
        # Classifier model should be written to stressm/
        stressm_dir = tmp_path / "stressm"
        assert stressm_dir.exists()

    def test_single_gauge_classifier_result_dict(self, gauge_dir, tmp_path):
        result = generate_stressm(
            input_dir=gauge_dir,
            output_dir=tmp_path,
            count=20,
            catchment_id="thames",
            seed=0,
            gauge_id="GAUGE-test002",
            train_classifier=True,
        )
        assert isinstance(result, dict)
