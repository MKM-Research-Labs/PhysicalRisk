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

"""Tests for _print_gauge_progression and _print_classifier_result."""

from port.src.stressm import (
    _print_classifier_result,
    _print_gauge_progression,
)


# ---------------------------------------------------------------------------
# Line 480 / 493: _print_gauge_progression branches
# ---------------------------------------------------------------------------

class TestPrintGaugeProgression:

    # Gauge with alert=3.5, warning=4.6, severe=5.5
    _GAUGE = {
        "gauge_id":      "GAUGE-test-pgp",
        "base_level":    1.225,
        "flood_alert":   3.5,
        "flood_warning": 4.6,
        "severe_warning": 5.5,
    }

    def _make_record(self, peak, cat, alert=False, warning=False, severe=False):
        return {
            "peaks_m":            [peak],
            "peak_hours":         [50],
            "intensity_category": cat,
            "sequence_type":      "isolated",
            "alert":              [alert],
            "warning":            [warning],
            "severe":             [severe],
        }

    def test_alert_marker_in_output(self, capsys):
        """Percentile between alert and warning -> '← ALERT' marker (line 480)."""
        # 20 records below alert + 80 just above alert but below warning
        # P50 ~ 3.8 -> in [alert, warning) -> triggers ALERT marker
        records = (
            [self._make_record(2.0, "moderate")] * 20 +
            [self._make_record(3.8, "moderate", alert=True)] * 80
        )
        _print_gauge_progression(self._GAUGE, records, total=100)
        out = capsys.readouterr().out
        assert "ALERT" in out

    def test_warning_marker_in_output(self, capsys):
        """Percentile between warning and severe -> '← WARNING' marker."""
        records = (
            [self._make_record(2.0, "moderate")] * 20 +
            [self._make_record(5.0, "severe", alert=True, warning=True)] * 80
        )
        _print_gauge_progression(self._GAUGE, records, total=100)
        out = capsys.readouterr().out
        assert "WARNING" in out

    def test_severe_marker_in_output(self, capsys):
        """Percentile >= severe -> '← SEVERE' marker."""
        records = [
            self._make_record(6.0, "catastrophic", alert=True, warning=True, severe=True)
        ] * 100
        _print_gauge_progression(self._GAUGE, records, total=100)
        out = capsys.readouterr().out
        assert "SEVERE" in out

    def test_empty_category_skipped(self, capsys):
        """Categories with zero peaks are skipped via `continue` (line 493)."""
        # All records have category="moderate"; severe/extreme/catastrophic are empty
        records = [self._make_record(2.5, "moderate")] * 20
        _print_gauge_progression(self._GAUGE, records, total=20)
        out = capsys.readouterr().out
        # moderate should appear; catastrophic should not
        assert "moderate" in out
        assert "catastrophic" not in out

    def test_output_contains_gauge_id(self, capsys):
        records = [self._make_record(2.5, "moderate")] * 10
        _print_gauge_progression(self._GAUGE, records, total=10)
        out = capsys.readouterr().out
        assert "GAUGE-test-pgp" in out

    def test_all_sequence_types_reported(self, capsys):
        records = [
            {**self._make_record(2.5, "moderate"), "sequence_type": "isolated"},
            {**self._make_record(3.0, "moderate"), "sequence_type": "doublet"},
            {**self._make_record(3.5, "moderate"), "sequence_type": "cluster"},
        ]
        _print_gauge_progression(self._GAUGE, records, total=3)
        out = capsys.readouterr().out
        assert "isolated" in out
        assert "doublet" in out
        assert "cluster" in out


# ---------------------------------------------------------------------------
# Lines 676-710: _print_classifier_result
# ---------------------------------------------------------------------------

class TestPrintClassifierResult:

    def _trained_result(self, gauge_id="GAUGE-clf-test"):
        return {
            "status":      "trained",
            "gauge_id":    gauge_id,
            "n_samples":   1000,
            "test_size":   200,
            "flood_rate":  0.15,
            "label_threshold": "severe_warning",
            "label_level_m": 5.5,
            "metrics": {
                "auc_roc":    0.92,
                "accuracy":   0.88,
                "brier_score": 0.08,
                "log_loss":   0.35,
            },
            "feature_importance": {
                "log_h_s":    0.45,
                "log_t_end":  0.30,
                "delta_log_h": 0.15,
                "delta2_log_h": 0.10,
            },
            "model_path": "/tmp/GAUGE-clf-test.joblib",
        }

    def test_trained_status_prints_metrics(self, capsys):
        _print_classifier_result(self._trained_result())
        out = capsys.readouterr().out
        assert "trained" in out
        assert "0.9200" in out   # AUC-ROC
        assert "GAUGE-clf-test" in out

    def test_trained_shows_feature_importance(self, capsys):
        _print_classifier_result(self._trained_result())
        out = capsys.readouterr().out
        assert "log_h_s" in out
        assert "log_t_end" in out

    def test_trained_shows_label_info(self, capsys):
        _print_classifier_result(self._trained_result())
        out = capsys.readouterr().out
        assert "severe_warning" in out
        assert "5.50" in out

    def test_not_trained_status(self, capsys):
        result = {
            "status":     "insufficient_data",
            "gauge_id":   "GAUGE-bad",
            "reason":     "only 2 positive samples",
            "n_positive": 2,
        }
        _print_classifier_result(result)
        out = capsys.readouterr().out
        assert "insufficient_data" in out
        assert "GAUGE-bad" in out
        assert "only 2 positive" in out

    def test_not_trained_no_metrics_printed(self, capsys):
        result = {
            "status":   "failed",
            "gauge_id": "GAUGE-fail",
            "reason":   "no data",
            "n_positive": 0,
        }
        _print_classifier_result(result)
        out = capsys.readouterr().out
        assert "AUC" not in out
