# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""
Unit tests for lineage validation — staleness, prerequisites, completeness.
"""

import json
import os
import hashlib
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest


# ---------------------------------------------------------------------------
# validation.py tests
# ---------------------------------------------------------------------------

def _make_manifest(steps: dict) -> dict:
    """Helper to build a manifest dict for testing."""
    return {"runs": {}, "steps": steps}


class TestCheckInputsFresh:
    """check_inputs_fresh: detect stale inputs."""

    def test_unknown_step(self):
        from lineage.validation import check_inputs_fresh
        with patch("lineage.validation.load_manifest", return_value=_make_manifest({})):
            ok, issues = check_inputs_fresh("nonexistent_step")
        assert not ok
        assert "Unknown step" in issues[0]

    def test_root_step_always_fresh(self):
        """Root steps (gauges, counterparties) have no inputs → always fresh."""
        from lineage.validation import check_inputs_fresh
        manifest = _make_manifest({"gauges": {"outputs": {"gauge.json": {"hash": "abc"}}}})
        with patch("lineage.validation.load_manifest", return_value=manifest):
            ok, issues = check_inputs_fresh("gauges")
        assert ok
        assert issues == []

    def test_fresh_when_hashes_match(self):
        from lineage.validation import check_inputs_fresh
        manifest = _make_manifest({
            "gauges": {
                "outputs": {"gauge.json": {"hash": "abc123"}},
            },
            "properties": {
                "inputs": {"gauge.json": {"hash": "abc123"}},
                "outputs": {"property.json": {"hash": "def456"}},
            },
        })
        with patch("lineage.validation.load_manifest", return_value=manifest):
            ok, issues = check_inputs_fresh("properties")
        assert ok
        assert issues == []

    def test_stale_when_hashes_differ(self):
        from lineage.validation import check_inputs_fresh
        manifest = _make_manifest({
            "gauges": {
                "outputs": {"gauge.json": {"hash": "new_hash_12345"}},
            },
            "properties": {
                "inputs": {"gauge.json": {"hash": "old_hash_12345"}},
                "outputs": {"property.json": {"hash": "xxx"}},
            },
        })
        with patch("lineage.validation.load_manifest", return_value=manifest):
            ok, issues = check_inputs_fresh("properties")
        assert not ok
        assert "stale" in issues[0].lower()

    def test_producer_never_run(self):
        from lineage.validation import check_inputs_fresh
        manifest = _make_manifest({
            "properties": {
                "inputs": {"gauge.json": {"hash": "abc"}},
                "outputs": {},
            },
        })
        with patch("lineage.validation.load_manifest", return_value=manifest):
            ok, issues = check_inputs_fresh("properties")
        assert not ok
        assert "never run" in issues[0].lower()

    def test_consumer_never_run(self):
        from lineage.validation import check_inputs_fresh
        manifest = _make_manifest({
            "gauges": {
                "outputs": {"gauge.json": {"hash": "abc123"}},
            },
        })
        with patch("lineage.validation.load_manifest", return_value=manifest):
            ok, issues = check_inputs_fresh("properties")
        assert not ok
        assert "never run" in issues[0].lower()

    def test_no_hash_recorded_for_producer_output(self):
        from lineage.validation import check_inputs_fresh
        manifest = _make_manifest({
            "gauges": {
                "outputs": {"gauge.json": {"type": "file"}},  # no hash key
            },
            "properties": {
                "inputs": {"gauge.json": {"hash": "abc"}},
                "outputs": {},
            },
        })
        with patch("lineage.validation.load_manifest", return_value=manifest):
            ok, issues = check_inputs_fresh("properties")
        assert not ok
        assert "No hash recorded" in issues[0]

    def test_consumer_has_no_hash_for_input(self):
        from lineage.validation import check_inputs_fresh
        manifest = _make_manifest({
            "gauges": {
                "outputs": {"gauge.json": {"hash": "abc123"}},
            },
            "properties": {
                "inputs": {"gauge.json": {}},  # empty — no hash
                "outputs": {},
            },
        })
        with patch("lineage.validation.load_manifest", return_value=manifest):
            ok, issues = check_inputs_fresh("properties")
        assert not ok
        assert "no recorded hash" in issues[0].lower()


class TestCheckStepPrerequisites:
    """check_step_prerequisites: all upstream steps must exist."""

    def test_all_present(self):
        from lineage.validation import check_step_prerequisites
        manifest = _make_manifest({"gauges": {}, "properties": {}})
        with patch("lineage.validation.load_manifest", return_value=manifest):
            ok, missing = check_step_prerequisites("properties")
        assert ok
        assert missing == []

    def test_missing_upstream(self):
        from lineage.validation import check_step_prerequisites
        manifest = _make_manifest({})
        with patch("lineage.validation.load_manifest", return_value=manifest):
            ok, missing = check_step_prerequisites("properties")
        assert not ok
        assert "gauges" in missing


class TestGetStaleDownstream:
    """get_stale_downstream: BFS over dependency graph."""

    def test_gauges_affects_many(self):
        from lineage.validation import get_stale_downstream
        downstream = get_stale_downstream("gauges")
        # gauges is upstream of properties, gaugehd, stressm, hazard, etc.
        assert "properties" in downstream
        assert "gaugehd" in downstream
        assert "stressm" in downstream

    def test_leaf_has_no_downstream(self):
        from lineage.validation import get_stale_downstream
        downstream = get_stale_downstream("blotter")
        assert downstream == []

    def test_mid_chain(self):
        from lineage.validation import get_stale_downstream
        downstream = get_stale_downstream("stressm")
        assert "hazard" in downstream
        assert "propertyts" in downstream


class TestCheckPipelineComplete:
    """check_pipeline_complete: verify all pipeline outputs exist on disk."""

    def test_complete_pipeline(self, tmp_path):
        """All outputs present → complete."""
        from lineage.validation import check_pipeline_complete
        from lineage.manifest import STEP_IO
        # Create every output
        for step, io in STEP_IO.items():
            for output in io["outputs"]:
                if output.endswith("/"):
                    d = tmp_path / output
                    d.mkdir(parents=True, exist_ok=True)
                    (d / "dummy.json").write_text("{}")
                else:
                    (tmp_path / output).write_text("{}")
        result = check_pipeline_complete(tmp_path)
        assert result["complete"]
        assert result["missing"] == []
        assert result["present"] == result["total"]

    def test_missing_file(self, tmp_path):
        """Missing gauge.json → incomplete."""
        from lineage.validation import check_pipeline_complete
        # Create nothing
        result = check_pipeline_complete(tmp_path)
        assert not result["complete"]
        missing_outputs = [m["output"] for m in result["missing"]]
        assert "gauge.json" in missing_outputs
        assert "propertyts/" in missing_outputs
        assert "stress_storms/" in missing_outputs

    def test_empty_directory_detected(self, tmp_path):
        """Empty directory is as broken as missing."""
        from lineage.validation import check_pipeline_complete
        from lineage.manifest import STEP_IO
        # Create all outputs but leave propertyts/ empty
        for step, io in STEP_IO.items():
            for output in io["outputs"]:
                if output.endswith("/"):
                    d = tmp_path / output
                    d.mkdir(parents=True, exist_ok=True)
                    if output != "propertyts/":
                        (d / "dummy.json").write_text("{}")
                else:
                    (tmp_path / output).write_text("{}")
        result = check_pipeline_complete(tmp_path)
        assert not result["complete"]
        empty = [m for m in result["missing"] if m["type"] == "empty_directory"]
        assert len(empty) == 1
        assert empty[0]["output"] == "propertyts/"
        assert empty[0]["step"] == "propertyts"

    def test_partial_pipeline(self, tmp_path):
        """Only root steps present → reports downstream as missing."""
        from lineage.validation import check_pipeline_complete
        (tmp_path / "gauge.json").write_text("{}")
        (tmp_path / "counterparty.json").write_text("{}")
        result = check_pipeline_complete(tmp_path)
        assert not result["complete"]
        assert result["present"] == 2
        missing_outputs = [m["output"] for m in result["missing"]]
        assert "property.json" in missing_outputs
        assert "stress_storms/" in missing_outputs
        assert "propertyts/" in missing_outputs


class TestValidateFullChain:
    """validate_full_chain: end-to-end consistency check."""

    def test_empty_manifest(self):
        from lineage.validation import validate_full_chain
        with patch("lineage.validation.load_manifest", return_value=_make_manifest({})):
            result = validate_full_chain()
        assert not result["is_consistent"]
        assert len(result["missing_steps"]) == 15  # all steps missing (incl synthetic_gauges + synthetic HC variants)

    def test_consistent_chain(self):
        from lineage.validation import validate_full_chain
        # Build a minimal consistent manifest: root steps only
        manifest = _make_manifest({
            "gauges": {"inputs": {}, "outputs": {"gauge.json": {"hash": "a"}}},
            "counterparties": {"inputs": {}, "outputs": {"counterparty.json": {"hash": "b"}}},
            "properties": {
                "inputs": {"gauge.json": {"hash": "a"}},
                "outputs": {"property.json": {"hash": "c"}},
            },
            "synthetic_gauges": {
                "inputs": {"gauge.json": {"hash": "a"}, "property.json": {"hash": "c"}},
                "outputs": {},
            },
            "mortgages": {
                "inputs": {"property.json": {"hash": "c"}},
                "outputs": {"mortgage.json": {"hash": "d"}},
            },
            "gaugehd": {
                "inputs": {"gauge.json": {"hash": "a"}},
                "outputs": {"gaugehd/": {"hash": "e"}},
            },
            "stressm": {
                "inputs": {"gauge.json": {"hash": "a"}, "gaugehd/": {"hash": "e"}},
                "outputs": {
                    "gaugets/": {"hash": "f"},
                    "stress_storms/": {"hash": "g"},
                    "storm_sequences.json": {"hash": "h"},
                    "sequence_gauge/": {"hash": "i"},
                },
            },
            "hazard": {
                "inputs": {"gauge.json": {"hash": "a"}, "gaugets/": {"hash": "f"}},
                "outputs": {"gaugehc.json": {"hash": "j"}, "gaugets/": {"hash": "f"}},
            },
            "propertyts": {
                "inputs": {
                    "property.json": {"hash": "c"},
                    "gauge.json": {"hash": "a"},
                    "gaugets/": {"hash": "f"},
                },
                "outputs": {"propertyts/": {"hash": "k"}},
            },
            "propertytsd": {
                "inputs": {
                    "property.json": {"hash": "c"},
                    "gauge.json": {"hash": "a"},
                    "gaugets/": {"hash": "f"},
                },
                "outputs": {"propertytsd/": {"hash": "k1"}},
            },
            "propertytse": {
                "inputs": {
                    "property.json": {"hash": "c"},
                    "gauge.json": {"hash": "a"},
                    "gaugets/": {"hash": "f"},
                },
                "outputs": {"propertytse/": {"hash": "k2"}},
            },
            "propertyhc": {
                "inputs": {
                    "propertyts/": {"hash": "k"},
                    "gaugehc.json": {"hash": "j"},
                    "gauge.json": {"hash": "a"},
                },
                "outputs": {"propertyhc.json": {"hash": "l"}},
            },
            "propertyshd": {
                "inputs": {
                    "propertytsd/": {"hash": "k1"},
                    "gaugehc.json": {"hash": "j"},
                    "gauge.json": {"hash": "a"},
                },
                "outputs": {"propertyshd.json": {"hash": "l1"}},
            },
            "propertyshe": {
                "inputs": {
                    "propertytse/": {"hash": "k2"},
                    "gaugehc.json": {"hash": "j"},
                    "gauge.json": {"hash": "a"},
                },
                "outputs": {"propertyshe.json": {"hash": "l2"}},
            },
            "blotter": {
                "inputs": {"gaugehc.json": {"hash": "j"}, "counterparty.json": {"hash": "b"}},
                "outputs": {"prs/": {"hash": "m"}},
            },
        })
        with patch("lineage.validation.load_manifest", return_value=manifest):
            result = validate_full_chain()
        assert result["is_consistent"]
        assert result["stale_steps"] == []
        assert result["missing_steps"] == []

    def test_stale_step_detected(self):
        from lineage.validation import validate_full_chain
        manifest = _make_manifest({
            "gauges": {"inputs": {}, "outputs": {"gauge.json": {"hash": "new"}}},
            "properties": {
                "inputs": {"gauge.json": {"hash": "old"}},
                "outputs": {"property.json": {"hash": "x"}},
            },
        })
        with patch("lineage.validation.load_manifest", return_value=manifest):
            result = validate_full_chain()
        assert not result["is_consistent"]
        assert "properties" in result["stale_steps"]
