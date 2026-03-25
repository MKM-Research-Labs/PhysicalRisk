# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""
Data availability tests — Storm scenarios (classifiers + gaugets).

Verifies that all files required by the stress test module are present
on disk and structurally correct.  These tests use the real production
data files, not fixtures.

Run `python app.py port --gaugets` to (re)generate stress_storms.json.
Run `python app.py port --stressm`  to retrain GBM flood classifiers.
"""

import json
import pathlib
import pytest

import sys
sys.path.insert(0, str(pathlib.Path(__file__).parents[2]))
from config import PortfolioConfig

config = PortfolioConfig()

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

STRESS_STORMS_DIR   = pathlib.Path(config.get_input_dir()) / "stress_storms"
STRESS_STORMS_INDEX = STRESS_STORMS_DIR / "_index.json"
# Legacy single-file fallback
STRESS_STORMS_PATH  = pathlib.Path(config.get_input_dir()) / "stress_storms.json"
GAUGETS_DIR         = pathlib.Path(config.get_gaugets_dir())
STRESS_MODEL_DIR    = pathlib.Path(config.get_classifiers_dir())
TRAINING_SUMMARY    = STRESS_MODEL_DIR / "training_summary.json"
GAUGEHC_PATH        = pathlib.Path(config.get_input_dir()) / "gaugehc.json"

PROPERTYTS_DIR       = pathlib.Path(config.get_input_dir()) / "propertyts"

STORM_REQUIRED_FIELDS = {
    "storm_id", "name", "intensity_category", "duration_hours",
    "peak_position", "trigger_summary", "gauge_responses",
}
TRIGGER_SUMMARY_FIELDS = {
    "gauges_alert", "gauges_warning", "gauges_severe", "gauges_impacted", "max_trigger",
}
GAUGE_RESPONSE_FIELDS = {
    "gauge_id", "peak_level_m",
    "exceeded_alert", "exceeded_warning", "exceeded_severe",
}
MIN_STORM_COUNT = 100
MIN_AUC = 0.90
MIN_CLASSIFIERS = 40


# ---------------------------------------------------------------------------
# Flood classifier models
# ---------------------------------------------------------------------------

class TestStressClassifiers:
    """Trained GBM classifier .joblib files must be present and summary valid."""

    @pytest.fixture(scope="class")
    def classifier_files(self):
        assert STRESS_MODEL_DIR.exists(), f"Stress model dir not found: {STRESS_MODEL_DIR}"
        return list(STRESS_MODEL_DIR.glob("GAUGE-*.joblib"))

    @pytest.fixture(scope="class")
    def summary(self):
        assert TRAINING_SUMMARY.exists(), f"training_summary.json not found: {TRAINING_SUMMARY}"
        return json.loads(TRAINING_SUMMARY.read_text())

    def test_stress_model_dir_exists(self):
        assert STRESS_MODEL_DIR.exists(), f"Missing: {STRESS_MODEL_DIR}"

    def test_classifier_count(self, classifier_files):
        assert len(classifier_files) >= MIN_CLASSIFIERS, (
            f"Expected >= {MIN_CLASSIFIERS} classifier files, got {len(classifier_files)}. "
            "Run `python app.py port --stress` to retrain."
        )

    def test_classifier_filenames_well_formed(self, classifier_files):
        bad = [f.name for f in classifier_files if not f.stem.startswith(("GAUGE-", "SYNTH-"))]
        assert not bad, f"Classifier files with unexpected names: {bad}"

    def test_classifiers_not_empty(self, classifier_files):
        empty = [f.name for f in classifier_files if f.stat().st_size == 0]
        assert not empty, f"Zero-byte classifier files: {empty}"

    def test_training_summary_exists(self):
        assert TRAINING_SUMMARY.exists(), f"Missing: {TRAINING_SUMMARY}"

    def test_training_summary_has_required_keys(self, summary):
        required = {"num_gauges", "num_trained", "avg_auc_roc"}
        missing = required - set(summary.keys())
        assert not missing, f"training_summary.json missing keys: {missing}"

    def test_all_gauges_trained(self, summary):
        n_gauges = summary.get("num_gauges", 0)
        n_trained = summary.get("num_trained", 0)
        n_skipped = summary.get("num_skipped", 0)
        assert n_skipped == 0, f"{n_skipped} gauges were skipped during training"
        assert n_trained == n_gauges, f"Only {n_trained}/{n_gauges} gauges trained"

    def test_avg_auc_above_threshold(self, summary):
        auc = summary.get("avg_auc_roc", 0)
        assert auc >= MIN_AUC, (
            f"Average AUC-ROC {auc:.4f} is below minimum threshold {MIN_AUC}. "
            "Model quality may be degraded."
        )

    def test_classifier_count_matches_summary(self, classifier_files, summary):
        n_files = len(classifier_files)
        n_summary = summary.get("num_trained", 0)
        # After --no-classifier runs, stale .joblib files may remain from a
        # previous training run while training_summary reflects only the latest.
        # Accept either exact match or n_files >= n_summary (stale files OK).
        assert n_files >= n_summary, (
            f"Classifier file count ({n_files}) is less than "
            f"training_summary num_trained ({n_summary})"
        )


# ---------------------------------------------------------------------------
# gaugets/ directory (hydrograph source)
# ---------------------------------------------------------------------------

class TestGaugetsData:
    """gaugets/ directory must contain per-gauge timeseries files with valid structure."""

    @pytest.fixture(scope="class")
    def gaugets_files(self):
        assert GAUGETS_DIR.exists(), f"gaugets directory not found: {GAUGETS_DIR}"
        return list(GAUGETS_DIR.glob("*.json"))

    def test_gaugets_dir_exists(self):
        assert GAUGETS_DIR.exists(), f"Missing: {GAUGETS_DIR}"

    def test_gaugets_not_empty(self, gaugets_files):
        assert gaugets_files, f"No .json files found in {GAUGETS_DIR}"

    def test_gaugets_gauge_id_format(self, gaugets_files):
        bad = [f.name for f in gaugets_files if not f.stem.startswith(("GAUGE-", "SYNTH-"))]
        assert not bad, f"gaugets files with unexpected names: {bad}"

    def test_each_file_has_required_keys(self, gaugets_files):
        required = {"gauge_id", "flood_simulation"}
        bad = {}
        for f in gaugets_files:
            d = json.loads(f.read_text())
            absent = required - set(d.keys())
            if absent:
                bad[f.name] = absent
        assert not bad, f"gaugets files missing required keys: {bad}"

    def test_flood_simulation_has_readings(self, gaugets_files):
        bad = []
        for f in gaugets_files:
            d = json.loads(f.read_text())
            fs = d.get("flood_simulation", {})
            if not fs.get("readings"):
                bad.append(f.name)
        assert not bad, f"gaugets files with empty flood_simulation.readings: {bad[:5]}"

    def test_readings_count_matches_simulation_hours(self, gaugets_files):
        """simulation_hours should match number of reading entries."""
        from config.models import STORM_SIMULATION_HOURS
        mismatches = []
        for f in gaugets_files:
            d = json.loads(f.read_text())
            fs = d.get("flood_simulation", {})
            sim_hours = fs.get("simulation_hours")
            readings = fs.get("readings", [])
            if sim_hours is not None and len(readings) != sim_hours:
                mismatches.append((f.name, sim_hours, len(readings)))
        assert not mismatches, f"Reading count/simulation_hours mismatch: {mismatches[:3]}"

    def test_gauge_id_field_matches_filename(self, gaugets_files):
        bad = []
        for f in gaugets_files:
            d = json.loads(f.read_text())
            gid = d.get("gauge_id", "")
            if gid != f.stem:
                bad.append((f.name, gid))
        assert not bad, f"gauge_id field doesn't match filename: {bad[:5]}"
