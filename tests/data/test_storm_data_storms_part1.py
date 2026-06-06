# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""
Data availability tests — Storm scenarios (part 1).

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
# stress_storms.json
# ---------------------------------------------------------------------------

def _load_storms_from_dir_or_file():
    """Load full storm records — directory format (preferred) or legacy single file."""
    if STRESS_STORMS_INDEX.exists():
        index = json.loads(STRESS_STORMS_INDEX.read_text())
        storms = []
        for entry in index.get("storms", []):
            storm_file = STRESS_STORMS_DIR / f"{entry['storm_id']}.json"
            if storm_file.exists():
                storms.append(json.loads(storm_file.read_text()))
        return storms
    if STRESS_STORMS_PATH.exists():
        data = json.loads(STRESS_STORMS_PATH.read_text())
        return data.get("storms", [])
    return None


class TestStressStormsFilePart1:
    """stress_storms/ directory (or legacy .json) must exist and have correct structure (part 1)."""

    @pytest.fixture(scope="class")
    def storms(self):
        result = _load_storms_from_dir_or_file()
        if result is None:
            pytest.skip(
                f"stress_storms data not generated — skipping. "
                f"Run `python app.py port --stressm` to create."
            )
        return result

    def test_file_exists(self):
        if not (STRESS_STORMS_INDEX.exists() or STRESS_STORMS_PATH.exists()):
            pytest.skip(
                f"stress_storms data not generated — skipping. "
                f"Run `python app.py port --stressm` to create."
            )

    def test_has_storms(self):
        storms = _load_storms_from_dir_or_file()
        if storms is None:
            pytest.skip("stress_storms data not generated")
        assert len(storms) > 0

    def test_minimum_storm_count(self, storms):
        assert len(storms) >= MIN_STORM_COUNT, (
            f"Expected >= {MIN_STORM_COUNT} stress storms, got {len(storms)}. "
            "Run `python app.py port --stressm` to regenerate."
        )

    def test_storm_ids_unique(self, storms):
        ids = [s["storm_id"] for s in storms]
        dupes = [sid for sid in set(ids) if ids.count(sid) > 1]
        assert not dupes, f"Duplicate storm IDs: {dupes[:5]}"

    def test_storm_ids_well_formed(self, storms):
        # All storm IDs use STORM- prefix
        bad = [s["storm_id"] for s in storms
               if not s["storm_id"].startswith("STORM-")]
        assert not bad, f"Storm IDs not in STORM-xxxx format: {bad[:5]}"

    def test_each_storm_has_required_fields(self, storms):
        missing = {}
        for s in storms:
            absent = STORM_REQUIRED_FIELDS - set(s.keys())
            if absent:
                missing[s.get("storm_id", "?")] = absent
        assert not missing, f"Storms missing required fields: {dict(list(missing.items())[:3])}"

    def test_each_storm_has_gauge_responses(self, storms):
        empty = [s["storm_id"] for s in storms if not s.get("gauge_responses")]
        assert not empty, f"Storms with no gauge_responses: {empty[:5]}"

    def test_gauge_responses_have_required_fields(self, storms):
        missing = {}
        for s in storms:
            for gr in s.get("gauge_responses", []):
                absent = GAUGE_RESPONSE_FIELDS - set(gr.keys())
                if absent:
                    key = f"{s['storm_id']}:{gr.get('gauge_id','?')}"
                    missing[key] = absent
                    break  # one error per storm is enough
        assert not missing, f"gauge_responses missing fields: {dict(list(missing.items())[:3])}"

    def test_gauge_ids_well_formed(self, storms):
        bad = set()
        for s in storms:
            for gr in s.get("gauge_responses", []):
                gid = gr.get("gauge_id", "")
                if not gid.startswith(("GAUGE-", "SYNTH-")):
                    bad.add(gid)
        assert not bad, f"gauge_response gauge_ids not in GAUGE-/SYNTH-xxxx format: {list(bad)[:5]}"

    def test_peak_levels_positive(self, storms):
        violations = []
        for s in storms:
            for gr in s.get("gauge_responses", []):
                if gr.get("peak_level_m", 0) <= 0:
                    violations.append((s["storm_id"], gr.get("gauge_id")))
                    break
        assert not violations, f"Storms with non-positive peak_level_m: {violations[:3]}"

    def test_peak_level_exceeds_base(self, storms):
        violations = []
        for s in storms:
            for gr in s.get("gauge_responses", []):
                base = gr.get("base_level_m", 0)
                peak = gr.get("peak_level_m", 0)
                if peak < base:
                    violations.append((s["storm_id"], gr.get("gauge_id"), base, peak))
                    break
        assert not violations, f"Storms where peak < base level: {violations[:3]}"

    def test_at_least_one_storm_exceeds_alert(self, storms):
        any_alert = any(
            gr.get("exceeded_alert")
            for s in storms
            for gr in s.get("gauge_responses", [])
        )
        assert any_alert, "No storm in stress_storms.json has exceeded_alert=True"
