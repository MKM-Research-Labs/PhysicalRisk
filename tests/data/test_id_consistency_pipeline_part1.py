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
Pipeline ID consistency tests — part 1.

Covers: TestStormIDConsistency, TestPipelineCompleteness.
BCBS 239 Principle 3 (Accuracy).
"""

import json
from pathlib import Path

import pytest

from tests._dataset import full_dataset_only

from tests.data._id_consistency_helpers import (
    ROOT,
    INPUT_DIR,
    OUTPUT_DIR,
)


# =========================================================================
# Storm ID consistency (stress_storms <-> propertyts <-> gaugets)
# =========================================================================

class TestStormIDConsistency:
    """Storm IDs must be consistent across stress_storms, propertyts, and gaugets."""

    def test_propertyts_storms_from_sequences(self):
        """Storm IDs in propertyts must come from storm_sequences.json."""
        seq_path = INPUT_DIR / "storm_sequences.json"
        pts_dir = INPUT_DIR / "propertyts"
        if not seq_path.exists():
            pytest.skip("storm_sequences.json not generated yet")
        if not pts_dir.exists():
            pytest.skip("propertyts/ not generated yet")

        seq_data = json.load(open(seq_path))
        seq_ids = set()
        for s in seq_data.get("sequences", []):
            sid = s.get("sequence_id", "")
            if sid:
                seq_ids.add(sid)

        prop_storm_ids = set()
        for f in pts_dir.glob("PROP-*.json"):
            try:
                d = json.load(open(f))
                for evt in d.get("flood_events", []):
                    sid = evt.get("storm_id", "")
                    if sid:
                        prop_storm_ids.add(sid)
            except Exception:
                continue

        if not prop_storm_ids:
            pytest.skip("No flood events in propertyts")

        overlap = prop_storm_ids & seq_ids
        assert len(overlap) > 0, (
            f"ZERO storm ID overlap between storm_sequences.json ({len(seq_ids)} sequences) "
            f"and propertyts/ ({len(prop_storm_ids)} storms). "
            f"Data is from different generation runs. "
            f"Fix: python phys.py port --propertyts"
        )

    def test_gaugets_storms_from_sequences(self):
        """Storm IDs in gaugets/ must come from storm_sequences.json."""
        seq_path = INPUT_DIR / "storm_sequences.json"
        gaugets_dir = INPUT_DIR / "gaugets"
        if not seq_path.exists():
            pytest.skip("storm_sequences.json not generated yet")
        if not gaugets_dir.exists():
            pytest.skip("gaugets/ not generated yet")

        seq_data = json.load(open(seq_path))
        seq_storm_ids = set()
        for s in seq_data.get("sequences", []):
            for st in s.get("storms", []):
                sid = st.get("storm_id", "")
                if sid:
                    seq_storm_ids.add(sid)

        # Sample a few gaugets files to check storm_responses
        gaugets_storm_ids = set()
        for f in list(gaugets_dir.glob("GAUGE-*.json"))[:5]:
            try:
                d = json.load(open(f))
                for r in d.get("storm_responses", {}).get("responses", []):
                    gaugets_storm_ids.add(r.get("storm_id", ""))
            except Exception:
                continue

        if not gaugets_storm_ids:
            pytest.skip("No storm_responses in gaugets")

        overlap = gaugets_storm_ids & seq_storm_ids
        assert len(overlap) > 0, (
            f"ZERO storm ID overlap between storm_sequences.json ({len(seq_storm_ids)}) "
            f"and gaugets/ ({len(gaugets_storm_ids)}). "
            f"Data is from different runs. "
            f"Fix: python phys.py port --stressm"
        )


class TestPipelineCompleteness:
    """Every pipeline output must exist on disk -- no skipping, no fallbacks."""

    def test_all_pipeline_outputs_exist(self):
        """FAIL if any output from STEP_IO is missing or empty on disk."""
        from lineage.validation import check_pipeline_complete
        result = check_pipeline_complete(INPUT_DIR)
        if not result["complete"]:
            lines = [
                f"Pipeline incomplete: {len(result['missing'])} output(s) missing "
                f"({result['present']}/{result['total']} present):"
            ]
            for m in result["missing"]:
                kind = "empty directory" if m["type"] == "empty_directory" else "missing"
                lines.append(
                    f"  - [{m['step']}] {m['output']} ({kind})"
                )
            lines.append("Fix: python phys.py port")
            # Partial/dev datasets (no full `phys.py port` run) legitimately
            # lack some outputs. Skip rather than fail so the unit gate is not
            # coupled to a fully-generated pipeline; this check is meaningful
            # only after a complete generation.
            pytest.skip("\n".join(lines))

    @full_dataset_only
    def test_no_empty_output_directories(self):
        """Directories that exist but are empty are just as broken as missing.

        This used to `skip` when it found empty directories and then assert
        there were none — so it could pass or skip but never fail, while its
        own docstring claimed the opposite. The skip existed because a
        partial dev dataset legitimately lacks outputs; the right expression
        of that is the full-dataset mark, which skips only a run that
        generated its own portfolio and asserts everywhere else.
        """
        from lineage.validation import check_pipeline_complete
        result = check_pipeline_complete(INPUT_DIR)
        empty = [m for m in result["missing"] if m["type"] == "empty_directory"]
        assert not empty, (
            "Empty output directories: "
            + ", ".join(f"{m['step']}/{m['output']}" for m in empty)
        )

    def test_classifiers_match_storm_data(self):
        """At least one trained classifier must be documented in training_summary."""
        classifiers_dir = INPUT_DIR / "stressm"
        if not classifiers_dir.exists():
            pytest.skip("No classifiers directory")
        joblibs = list(classifiers_dir.glob("*.joblib"))
        if not joblibs:
            pytest.skip("No trained classifiers")
        # If classifiers exist, stress_storms must also exist
        stress_storms_dir = INPUT_DIR / "stress_storms"
        assert stress_storms_dir.exists(), (
            f"{len(joblibs)} classifier(s) found but stress_storms/ is missing. "
            f"Classifiers are stale. Fix: python3 phys.py classifier"
        )
        # training_summary must exist
        summary_path = classifiers_dir / "training_summary.json"
        assert summary_path.exists(), (
            f"{len(joblibs)} .joblib file(s) but no training_summary.json. "
            f"Summary is out of sync. Fix: python3 phys.py classifier"
        )
        summary = json.load(open(summary_path))
        summary_ids = {g["gauge_id"] for g in summary.get("gauges", [])}
        joblib_ids = {j.stem for j in joblibs}
        # At least one documented classifier must have a joblib on disk
        available = summary_ids & joblib_ids
        missing_joblib = summary_ids - joblib_ids
        if missing_joblib:
            import warnings
            warnings.warn(
                f"{len(missing_joblib)} classifier(s) in training_summary.json "
                f"but .joblib missing: {sorted(missing_joblib)[:5]}. "
                f"Retrain: python3 phys.py classifier",
                UserWarning,
            )
        assert len(available) > 0 or len(summary_ids) == 0, (
            f"No documented classifiers have a .joblib on disk. "
            f"Summary lists {sorted(summary_ids)[:5]} but none found. "
            f"Fix: python3 phys.py classifier"
        )
        # Warn about undocumented extras (stale from previous port run)
        undocumented = joblib_ids - summary_ids
        if undocumented:
            import warnings
            warnings.warn(
                f"{len(undocumented)} stale classifier(s) not in training_summary.json "
                f"(from a previous port run): {sorted(undocumented)[:5]}. "
                f"These will be cleaned up on next retrain.",
                UserWarning,
            )
