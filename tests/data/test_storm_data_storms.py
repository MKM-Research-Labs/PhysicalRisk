# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""
Data availability tests — Storm scenarios.

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


class TestStressStormsFile:
    """stress_storms/ directory (or legacy .json) must exist and have correct structure."""

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

    def test_storms_cover_multiple_gauges(self, storms):
        gauges = {gr["gauge_id"] for s in storms for gr in s.get("gauge_responses", [])}
        assert len(gauges) >= 10, f"Expected storms to cover >= 10 gauges, got {len(gauges)}"

    def test_intensity_categories_present(self, storms):
        cats = {s.get("intensity_category") for s in storms}
        cats.discard(None)
        assert cats, "No intensity_category values found in stress_storms"

    def test_intensity_categories_populated_for_all_storms(self, storms):
        """Every storm must have a non-empty intensity_category from storm_sequences.json."""
        missing = [
            s["storm_id"] for s in storms
            if not s.get("intensity_category")
        ]
        assert len(missing) == 0, (
            f"{len(missing)} storms have empty intensity_category: {missing[:5]}. "
            "Check storm_sequences.json enrichment in stress_storms generator."
        )

    def test_effective_precipitation_populated(self, storms):
        """Every storm must have effective_precipitation_mm > 0 from storm_sequences.json."""
        zero_precip = [
            s["storm_id"] for s in storms
            if not s.get("effective_precipitation_mm")
        ]
        # Allow up to 5% missing (e.g. orphaned storms without sequence metadata)
        tolerance = max(1, len(storms) * 5 // 100)
        assert len(zero_precip) <= tolerance, (
            f"{len(zero_precip)} storms have zero/missing effective_precipitation_mm "
            f"(>{tolerance} tolerance): {zero_precip[:5]}. "
            "Check storm_sequences.json enrichment in stress_storms generator."
        )

    def test_total_storms_key_matches_list_length(self):
        if STRESS_STORMS_INDEX.exists():
            data = json.loads(STRESS_STORMS_INDEX.read_text())
        elif STRESS_STORMS_PATH.exists():
            data = json.loads(STRESS_STORMS_PATH.read_text())
        else:
            pytest.skip("No stress_storms data")
        assert data["total_storms"] == len(data["storms"]), (
            f"total_storms={data['total_storms']} but len(storms)={len(data['storms'])}"
        )

    def test_trigger_summary_populated_for_all_storms(self, storms):
        """Every storm must have a fully-populated trigger_summary dict."""
        missing = {}
        for s in storms:
            ts = s.get("trigger_summary", {})
            absent = TRIGGER_SUMMARY_FIELDS - set(ts.keys())
            if absent:
                missing[s.get("storm_id", "?")] = absent
        assert not missing, (
            f"Storms with incomplete trigger_summary: {dict(list(missing.items())[:3])}"
        )

    def test_trigger_summary_max_trigger_valid(self, storms):
        valid = {"alert", "warning", "severe"}
        bad = [
            s["storm_id"]
            for s in storms
            if s.get("trigger_summary", {}).get("max_trigger") not in valid
        ]
        assert not bad, f"Storms with invalid max_trigger: {bad[:5]}"

    def test_storms_sorted_by_severity_descending(self, storms):
        """Storms must be sorted: gauges_severe DESC, gauges_warning DESC."""
        severe_counts = [s["trigger_summary"]["gauges_severe"] for s in storms]
        assert severe_counts == sorted(severe_counts, reverse=True), (
            "stress_storms.json is NOT sorted by gauges_severe DESC. "
            "Re-run `python app.py port --gaugets`."
        )

    def test_all_gauge_ids_use_gauge_prefix(self, storms):
        """All gauge_id values in gauge_responses must match GAUGE-/SYNTH-xxxx format."""
        valid_prefixes = ("GAUGE-", "SYNTH-")
        bad = set()
        for s in storms:
            for gr in s.get("gauge_responses", []):
                gid = gr.get("gauge_id", "")
                if not gid.startswith(valid_prefixes):
                    bad.add(gid)
        assert not bad, (
            f"gauge_response entries with wrong gauge_id prefix "
            f"(expected GAUGE-/SYNTH-): {list(bad)[:5]}"
        )

    def test_all_storm_ids_use_valid_prefix(self, storms):
        """All storm_id values must use STORM- prefix."""
        from config.port import STORM_ID_PREFIX
        bad = [
            s["storm_id"] for s in storms
            if not s["storm_id"].startswith(f"{STORM_ID_PREFIX}-")
        ]
        assert not bad, (
            f"storm_id values not matching '{STORM_ID_PREFIX}-' prefix: {bad[:5]}"
        )

    def test_52_unique_gauge_ids_in_responses(self, storms):
        """Thames catchment has 52 gauges; all must be represented."""
        gauge_ids = {
            gr["gauge_id"]
            for s in storms
            for gr in s.get("gauge_responses", [])
        }
        assert len(gauge_ids) == 52, (
            f"Expected 52 unique gauge IDs in stress_storms responses, "
            f"got {len(gauge_ids)}. "
            "Run `python app.py port --gaugets` to regenerate."
        )
