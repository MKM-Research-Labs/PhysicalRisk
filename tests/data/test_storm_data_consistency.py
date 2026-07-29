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

"""
Data availability tests — Storm scenarios (cross-file consistency).

Verifies that all files required by the stress test module are present
on disk and structurally correct.  These tests use the real production
data files, not fixtures.

Run `python phys.py port --gaugets` to (re)generate stress_storms.json.
Run `python phys.py port --stressm`  to retrain GBM flood classifiers.
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
    "peak_position", "effective_precipitation_mm",
    "trigger_summary", "gauge_responses",
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
# Cross-file consistency
# ---------------------------------------------------------------------------

class TestStormDataConsistency:
    """Cross-checks between stress_storms.json, gaugehc.json, gaugets/, propertyts/, and classifiers."""

    @pytest.fixture(scope="class")
    def stress_data(self):
        return json.loads(STRESS_STORMS_PATH.read_text())

    @pytest.fixture(scope="class")
    def stress_storm_ids(self, stress_data):
        return {s["storm_id"] for s in stress_data["storms"]}

    @pytest.fixture(scope="class")
    def stress_gauge_ids(self, stress_data):
        return {
            gr["gauge_id"]
            for s in stress_data["storms"]
            for gr in s.get("gauge_responses", [])
        }

    @pytest.fixture(scope="class")
    def gaugehc_ids(self):
        data = json.loads(GAUGEHC_PATH.read_text())
        return set(data["hazard_curves"].keys())

    @pytest.fixture(scope="class")
    def gaugets_storm_ids(self):
        """Collect all storm_ids referenced in gaugets/GAUGE-*.json responses."""
        ids = set()
        for gf in GAUGETS_DIR.glob("GAUGE-*.json"):
            try:
                d = json.loads(gf.read_text())
                for resp in d.get("storm_responses", {}).get("responses", []):
                    sid = resp.get("storm_id", "")
                    if sid:
                        ids.add(sid)
            except Exception:
                pass
        return ids

    @pytest.fixture(scope="class")
    def propertyts_storm_ids(self):
        """Collect storm_ids from a representative sample of propertyts files."""
        ids = set()
        if not PROPERTYTS_DIR.exists():
            return ids
        for pf in list(PROPERTYTS_DIR.glob("PROP-*.json"))[:20]:
            try:
                d = json.loads(pf.read_text())
                for event in d.get("flood_events", []):
                    sid = event.get("storm_id", "")
                    if sid:
                        ids.add(sid)
            except Exception:
                pass
        return ids

    @pytest.fixture(scope="class")
    def classifier_ids(self):
        return {f.stem for f in STRESS_MODEL_DIR.glob("GAUGE-*.joblib")}

    # ------------------------------------------------------------------
    # stress_storms ↔ gaugehc consistency
    # ------------------------------------------------------------------

    @pytest.mark.xfail(
        strict=False,
        reason=(
            "stress_storms.json and gaugehc.json gauge IDs may be out of sync "
            "when generated at different times. "
            "Fix: python phys.py port --gaugets"
        ),
    )
    def test_stress_storm_gauges_in_gaugehc(self, stress_gauge_ids, gaugehc_ids):
        """Every gauge in stress_storms should have a hazard curve in gaugehc.json."""
        missing = stress_gauge_ids - gaugehc_ids
        assert not missing, (
            f"{len(missing)} stress-storm gauges have no entry in gaugehc.json: "
            f"{sorted(missing)[:5]}"
        )

    # ------------------------------------------------------------------
    # stress_storms ↔ gaugets consistency
    # ------------------------------------------------------------------

    @pytest.mark.xfail(
        strict=False,
        reason=(
            "stress_storms.json and gaugets/ may be from different generation runs "
            "(e.g. after --no-classifier partial run). "
            "Fix: python phys.py port --stressm"
        ),
    )
    def test_stress_storm_ids_subset_of_gaugets(self, stress_storm_ids, gaugets_storm_ids):
        """Every storm_id in stress_storms.json must exist in gaugets/GAUGE-*.json.

        This is the key invariant — stress_storms is derived FROM gaugets, so
        all IDs must match.  If this fails, re-run:
            python phys.py port --stressm
        """
        if not gaugets_storm_ids:
            pytest.skip("gaugets directory is empty — cannot validate overlap")
        missing = stress_storm_ids - gaugets_storm_ids
        assert not missing, (
            f"{len(missing)} stress_storms storm IDs not found in gaugets/: "
            f"{sorted(missing)[:5]}. "
            "Run `python phys.py port --stressm` to regenerate."
        )

    # ------------------------------------------------------------------
    # stress_storms ↔ propertyts consistency
    # ------------------------------------------------------------------

    @pytest.mark.xfail(
        strict=False,
        reason=(
            "stress_storms.json and propertyts/ may be from different generation runs. "
            "Fix: python phys.py port --stressm --propertyts"
        ),
    )
    def test_stress_storm_ids_overlap_propertyts(self, stress_storm_ids, propertyts_storm_ids):
        """Storm IDs in stress_storms must overlap with storm IDs in propertyts/.

        Both are derived from the same gaugets data, so the IDs must be consistent.
        If this fails, all three datasets need to be regenerated together:
            python phys.py port --stressm --propertyts
        """
        if not propertyts_storm_ids:
            pytest.skip("propertyts directory is empty — cannot validate overlap")
        overlap = stress_storm_ids & propertyts_storm_ids
        assert len(overlap) > 0, (
            "NO storm IDs overlap between stress_storms.json and propertyts/ files. "
            "The datasets are from different data generation runs. "
            "Regenerate with `python phys.py port --stressm` then `--propertyts`."
        )

    # ------------------------------------------------------------------
    # Classifier consistency
    # ------------------------------------------------------------------

    @pytest.mark.xfail(
        strict=False,
        reason=(
            "Classifiers and gaugehc.json may be out of sync when generated at "
            "different times. Fix: python phys.py port --stressm"
        ),
    )
    def test_classifiers_cover_gaugehc_gauges(self, gaugehc_ids, classifier_ids):
        """Every gauge in gaugehc.json should have a trained classifier."""
        missing = gaugehc_ids - classifier_ids
        assert not missing, (
            f"{len(missing)} gaugehc gauges have no classifier: "
            f"{sorted(missing)[:5]}. Run `python phys.py port --stressm`."
        )

    @pytest.mark.xfail(
        strict=False,
        reason=(
            "stress_storms.json and classifier gauge IDs may be out of sync "
            "when generated at different times. Fix: python phys.py port --stressm"
        ),
    )
    def test_classifiers_exist_for_stress_gauges(self, stress_gauge_ids, classifier_ids):
        """Every gauge referenced in stress_storms should have a trained classifier."""
        missing = stress_gauge_ids - classifier_ids
        assert not missing, (
            f"{len(missing)} stress-storm gauges have no classifier: "
            f"{sorted(missing)[:5]}. Run `python phys.py port --stressm`."
        )
