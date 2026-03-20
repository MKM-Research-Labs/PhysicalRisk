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

"""Tests for single-gauge mode and single-gauge + classifier training."""

import json

import pytest

from port.src.stressm import SCHEMA_VERSION_SPATIAL, generate_stressm


# ---------------------------------------------------------------------------
# Single-gauge mode
# ---------------------------------------------------------------------------

class TestSingleGaugeMode:

    def test_summary_num_gauges_is_one(self, single_run):
        assert single_run["num_gauges"] == 1

    def test_named_output_file_written(self, gauge_dir, single_run):
        assert (gauge_dir / "sequence_gauge_GAUGE-test002.json").exists()

    def test_named_file_schema_version(self, gauge_dir, single_run):
        with open(gauge_dir / "sequence_gauge_GAUGE-test002.json") as f:
            d = json.load(f)
        assert d["schema_version"] == SCHEMA_VERSION_SPATIAL

    def test_named_file_gauge_ids(self, gauge_dir, single_run):
        with open(gauge_dir / "sequence_gauge_GAUGE-test002.json") as f:
            d = json.load(f)
        assert d["gauge_ids"] == ["GAUGE-test002"]

    def test_named_file_peaks_length_one(self, gauge_dir, single_run):
        with open(gauge_dir / "sequence_gauge_GAUGE-test002.json") as f:
            d = json.load(f)
        assert all(len(r["peaks_m"]) == 1 for r in d["sequences"])

    def test_named_file_sequence_count(self, gauge_dir, single_run):
        with open(gauge_dir / "sequence_gauge_GAUGE-test002.json") as f:
            d = json.load(f)
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
