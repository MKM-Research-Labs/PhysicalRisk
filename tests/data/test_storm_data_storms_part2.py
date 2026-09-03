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
Data availability tests — Storm scenarios (part 2).

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


class TestStressStormsFilePart2:
    """stress_storms/ directory (or legacy .json) must exist and have correct structure (part 2)."""

    @pytest.fixture(scope="class")
    def storms(self):
        result = _load_storms_from_dir_or_file()
        if result is None:
            pytest.skip(
                f"stress_storms data not generated — skipping. "
                f"Run `python phys.py port --stressm` to create."
            )
        return result

    def test_storms_cover_every_gauge(self, storms):
        """Stress storms must produce a response for every generated gauge.

        Was ``>= 10`` guarded by a skip when fewer than 10 were covered, so the
        assertion was unreachable when false. The threshold also assumed the
        full portfolio; a 10-gauge set is a legitimate dataset.

        Comparing against the gauges actually generated is scale-free and
        catches the real defect — a gauge the storm pipeline silently skipped.
        """
        covered = {gr["gauge_id"] for s in storms
                   for gr in s.get("gauge_responses", [])}

        gauge_path = pathlib.Path(config.get_input_dir()) / "gauge.json"
        if not gauge_path.exists():
            pytest.skip(f"gauge.json not generated at {gauge_path}")
        gauges = json.loads(gauge_path.read_text()).get("gauges", [])
        expected = {
            (g.get("GaugeHeader", {}).get("Header", {}).get("GaugeID")
             or g.get("gauge_id"))
            for g in gauges
        }
        expected.discard(None)
        if not expected:
            pytest.skip("gauge.json has no gauges")

        # Synthetic gauges are not storm-driven, so they are not expected here.
        expected = {g for g in expected if not str(g).startswith("SYNTH-")}

        missing = expected - covered
        assert not missing, (
            f"storms cover {len(covered)} gauges but {len(missing)} of "
            f"{len(expected)} have no response: {sorted(missing)[:5]}"
        )

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
            "Re-run `python phys.py port --gaugets`."
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
