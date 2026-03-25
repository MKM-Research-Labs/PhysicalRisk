# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""
Unit tests for the lineage package — manifest, validation, and query modules.

Exercises all public functions and error paths to ensure BCBS 239
compliance infrastructure is robust against corrupt/missing data.
"""

import json
import os
import hashlib
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest


# ---------------------------------------------------------------------------
# manifest.py tests
# ---------------------------------------------------------------------------

class TestHashFile:
    """hash_file: SHA-256 of a file, streamed."""

    def test_hash_known_content(self, tmp_path):
        from lineage.manifest import hash_file
        p = tmp_path / "test.json"
        p.write_text('{"key": "value"}')
        result = hash_file(p)
        expected = hashlib.sha256(b'{"key": "value"}').hexdigest()
        assert result == expected

    def test_hash_empty_file(self, tmp_path):
        from lineage.manifest import hash_file
        p = tmp_path / "empty.json"
        p.write_bytes(b"")
        result = hash_file(p)
        expected = hashlib.sha256(b"").hexdigest()
        assert result == expected

    def test_hash_binary_file(self, tmp_path):
        from lineage.manifest import hash_file
        p = tmp_path / "bin.dat"
        content = bytes(range(256))
        p.write_bytes(content)
        result = hash_file(p)
        expected = hashlib.sha256(content).hexdigest()
        assert result == expected


class TestHashDirectory:
    """hash_directory: aggregate hash over sorted files."""

    def test_hash_single_file(self, tmp_path):
        from lineage.manifest import hash_file, hash_directory
        p = tmp_path / "a.json"
        p.write_text('{"a": 1}')
        digest, count = hash_directory(tmp_path)
        assert count == 1
        assert len(digest) == 64  # SHA-256 hex

    def test_hash_multiple_files_deterministic(self, tmp_path):
        from lineage.manifest import hash_directory
        (tmp_path / "b.json").write_text('{"b": 2}')
        (tmp_path / "a.json").write_text('{"a": 1}')
        d1, c1 = hash_directory(tmp_path)
        d2, c2 = hash_directory(tmp_path)
        assert d1 == d2
        assert c1 == c2 == 2

    def test_hash_empty_directory(self, tmp_path):
        from lineage.manifest import hash_directory
        digest, count = hash_directory(tmp_path)
        assert count == 0
        assert len(digest) == 64

    def test_hash_respects_pattern(self, tmp_path):
        from lineage.manifest import hash_directory
        (tmp_path / "a.json").write_text("{}")
        (tmp_path / "b.csv").write_text("x,y")
        _, count_json = hash_directory(tmp_path, "*.json")
        _, count_csv = hash_directory(tmp_path, "*.csv")
        assert count_json == 1
        assert count_csv == 1


class TestLoadManifest:
    """load_manifest: JSON loading with corrupt-file recovery."""

    def test_load_missing_returns_skeleton(self, tmp_path):
        from lineage.manifest import load_manifest
        fake_path = tmp_path / "nonexistent.json"
        with patch("lineage.manifest.LINEAGE_PATH", fake_path):
            result = load_manifest()
        assert result == {"runs": {}, "steps": {}}

    def test_load_valid_manifest(self, tmp_path):
        from lineage.manifest import load_manifest
        fake_path = tmp_path / "lineage.json"
        data = {"runs": {"r1": ["gauges"]}, "steps": {"gauges": {}}}
        fake_path.write_text(json.dumps(data))
        with patch("lineage.manifest.LINEAGE_PATH", fake_path):
            result = load_manifest()
        assert result == data

    def test_load_corrupt_json_returns_skeleton(self, tmp_path):
        from lineage.manifest import load_manifest
        fake_path = tmp_path / "lineage.json"
        fake_path.write_text("{{{not valid json")
        with patch("lineage.manifest.LINEAGE_PATH", fake_path):
            result = load_manifest()
        assert result == {"runs": {}, "steps": {}}


class TestSaveManifest:
    """save_manifest: atomic write with temp + rename."""

    def test_save_creates_file(self, tmp_path):
        from lineage.manifest import save_manifest, load_manifest
        fake_path = tmp_path / "lineage.json"
        data = {"runs": {}, "steps": {"gauges": {"status": "ok"}}}
        with patch("lineage.manifest.LINEAGE_PATH", fake_path):
            save_manifest(data)
            result = load_manifest()
        assert result == data

    def test_save_overwrites_existing(self, tmp_path):
        from lineage.manifest import save_manifest, load_manifest
        fake_path = tmp_path / "lineage.json"
        fake_path.write_text('{"old": true}')
        new_data = {"runs": {}, "steps": {}}
        with patch("lineage.manifest.LINEAGE_PATH", fake_path):
            save_manifest(new_data)
            result = load_manifest()
        assert result == new_data

    def test_save_cleans_up_on_failure(self, tmp_path):
        from lineage.manifest import save_manifest
        fake_path = tmp_path / "lineage.json"
        # Make json.dump fail by passing un-serialisable data
        with patch("lineage.manifest.LINEAGE_PATH", fake_path):
            with pytest.raises(TypeError):
                save_manifest({"bad": {1, 2, 3}})  # sets aren't JSON-serialisable
        # Temp file should be cleaned up
        assert len(list(tmp_path.glob("*.tmp"))) == 0


class TestHashArtifact:
    """_hash_artifact: dispatch to file/dir/missing."""

    def test_hash_file(self, tmp_path):
        from lineage.manifest import _hash_artifact
        p = tmp_path / "test.json"
        p.write_text("{}")
        result = _hash_artifact(p)
        assert result["type"] == "file"
        assert result["hash"] is not None

    def test_hash_directory(self, tmp_path):
        from lineage.manifest import _hash_artifact
        d = tmp_path / "subdir"
        d.mkdir()
        (d / "a.json").write_text("{}")
        result = _hash_artifact(d)
        assert result["type"] == "directory"
        assert result["hash"] is not None
        assert result["file_count"] == 1

    def test_hash_missing(self, tmp_path):
        from lineage.manifest import _hash_artifact
        p = tmp_path / "nope"
        result = _hash_artifact(p)
        assert result == {"hash": None, "type": "missing"}


class TestGetCurrentRunId:
    """get_current_run_id: timestamp-based."""

    def test_format(self):
        from lineage.manifest import get_current_run_id
        rid = get_current_run_id()
        assert rid.startswith("run-")
        assert len(rid) == 19  # run-YYYYMMDD-HHMMSS


class TestRecordStep:
    """record_step: full integration of hashing + manifest update."""

    def test_record_and_reload(self, tmp_path):
        from lineage.manifest import record_step, load_manifest
        fake_path = tmp_path / "lineage.json"
        # Create input/output files
        inp = tmp_path / "gauge.json"
        inp.write_text('{"gauges": []}')
        out_dir = tmp_path / "gaugehd"
        out_dir.mkdir()
        (out_dir / "a.json").write_text("{}")

        with patch("lineage.manifest.LINEAGE_PATH", fake_path):
            entry = record_step(
                step_name="gaugehd",
                generator="test_gen",
                inputs={"gauge.json": str(inp)},
                outputs={"gaugehd/": str(out_dir)},
                parameters={"seed": 42},
                elapsed_seconds=1.234,
                run_id="run-test-001",
            )
            manifest = load_manifest()

        assert "gaugehd" in manifest["steps"]
        assert manifest["steps"]["gaugehd"]["run_id"] == "run-test-001"
        assert manifest["steps"]["gaugehd"]["generator"] == "test_gen"
        assert manifest["steps"]["gaugehd"]["status"] == "success"
        assert manifest["runs"]["run-test-001"] == ["gaugehd"]
        assert entry["elapsed_seconds"] == 1.234

    def test_record_with_auto_run_id(self, tmp_path):
        from lineage.manifest import record_step
        fake_path = tmp_path / "lineage.json"
        inp = tmp_path / "x.json"
        inp.write_text("{}")

        with patch("lineage.manifest.LINEAGE_PATH", fake_path):
            entry = record_step(
                step_name="gauges",
                generator="gen",
                inputs={},
                outputs={"gauge.json": str(inp)},
                parameters={},
                elapsed_seconds=0.5,
            )
        assert entry["run_id"].startswith("run-")


class TestRepairManifest:
    """repair_manifest: rebuild manifest from on-disk hashes."""

    def _create_pipeline_files(self, data_dir):
        """Create minimal files for all pipeline steps."""
        from lineage.manifest import STEP_IO
        for step, io in STEP_IO.items():
            for output in io["outputs"]:
                if output.endswith("/"):
                    d = data_dir / output
                    d.mkdir(parents=True, exist_ok=True)
                    (d / "dummy.json").write_text("{}")
                else:
                    (data_dir / output).write_text("{}")

    def test_repair_from_scratch(self, tmp_path):
        """Repair with no existing manifest creates entries for all steps."""
        from lineage.manifest import repair_manifest, STEP_IO
        fake_path = tmp_path / "lineage.json"
        self._create_pipeline_files(tmp_path)
        with patch("lineage.manifest.LINEAGE_PATH", fake_path):
            result = repair_manifest(data_dir=tmp_path)
        assert len(result["repaired"]) == len(STEP_IO)
        assert result["skipped"] == []
        # Manifest should have been written
        assert fake_path.exists()
        data = json.loads(fake_path.read_text())
        assert len(data["steps"]) == len(STEP_IO)

    def test_repair_preserves_existing_metadata(self, tmp_path):
        """Repair keeps run_id, timestamp, generator from existing entries."""
        from lineage.manifest import repair_manifest
        fake_path = tmp_path / "lineage.json"
        self._create_pipeline_files(tmp_path)
        # Write an existing manifest with metadata for gauges
        existing = {
            "runs": {"run-original": ["gauges"]},
            "steps": {
                "gauges": {
                    "run_id": "run-original",
                    "timestamp": "2025-01-01T00:00:00",
                    "generator": "port.gauge_gen",
                    "parameters": {"seed": 42},
                    "elapsed_seconds": 5.5,
                },
            },
        }
        fake_path.write_text(json.dumps(existing))
        with patch("lineage.manifest.LINEAGE_PATH", fake_path):
            result = repair_manifest(data_dir=tmp_path)
        assert "gauges" in result["repaired"]
        data = json.loads(fake_path.read_text())
        gauges_entry = data["steps"]["gauges"]
        assert gauges_entry["run_id"] == "run-original"
        assert gauges_entry["timestamp"] == "2025-01-01T00:00:00"
        assert gauges_entry["generator"] == "port.gauge_gen"
        assert gauges_entry["parameters"] == {"seed": 42}

    def test_repair_skips_missing_outputs(self, tmp_path):
        """Steps whose outputs don't exist on disk are skipped."""
        from lineage.manifest import repair_manifest
        fake_path = tmp_path / "lineage.json"
        # Only create gauge.json — everything else missing
        (tmp_path / "gauge.json").write_text("{}")
        with patch("lineage.manifest.LINEAGE_PATH", fake_path):
            result = repair_manifest(data_dir=tmp_path)
        assert "gauges" in result["repaired"]
        assert "properties" in result["skipped"]
        assert "blotter" in result["skipped"]

    def test_repair_hashes_are_current(self, tmp_path):
        """Repaired hashes must match current file content."""
        from lineage.manifest import repair_manifest, hash_file
        fake_path = tmp_path / "lineage.json"
        gauge_file = tmp_path / "gauge.json"
        gauge_file.write_text('{"flood_gauges": []}')
        with patch("lineage.manifest.LINEAGE_PATH", fake_path):
            repair_manifest(data_dir=tmp_path)
        data = json.loads(fake_path.read_text())
        recorded_hash = data["steps"]["gauges"]["outputs"]["gauge.json"]["hash"]
        assert recorded_hash == hash_file(gauge_file)

    def test_repair_run_id_format(self, tmp_path):
        """Repair uses repair-YYYYMMDD-HHMMSS as run_id for new entries."""
        from lineage.manifest import repair_manifest
        fake_path = tmp_path / "lineage.json"
        (tmp_path / "gauge.json").write_text("{}")
        with patch("lineage.manifest.LINEAGE_PATH", fake_path):
            repair_manifest(data_dir=tmp_path)
        data = json.loads(fake_path.read_text())
        gauges_entry = data["steps"]["gauges"]
        assert gauges_entry["run_id"].startswith("repair-")

    def test_repair_empty_dir_skipped(self, tmp_path):
        """Steps with empty output directories are skipped."""
        from lineage.manifest import repair_manifest
        fake_path = tmp_path / "lineage.json"
        self._create_pipeline_files(tmp_path)
        # Empty out propertyts/
        for f in (tmp_path / "propertyts").iterdir():
            f.unlink()
        with patch("lineage.manifest.LINEAGE_PATH", fake_path):
            result = repair_manifest(data_dir=tmp_path)
        assert "propertyts" in result["skipped"]

    def test_repair_updates_runs_index(self, tmp_path):
        """Repair adds a runs entry listing all repaired steps."""
        from lineage.manifest import repair_manifest
        fake_path = tmp_path / "lineage.json"
        self._create_pipeline_files(tmp_path)
        with patch("lineage.manifest.LINEAGE_PATH", fake_path):
            result = repair_manifest(data_dir=tmp_path)
        data = json.loads(fake_path.read_text())
        repair_runs = [k for k in data["runs"] if k.startswith("repair-")]
        assert len(repair_runs) == 1
        assert set(data["runs"][repair_runs[0]]) == set(result["repaired"])

    def test_repair_inputs_hashed_correctly(self, tmp_path):
        """Input hashes recorded by repair should match the producer's output hash."""
        from lineage.manifest import repair_manifest
        fake_path = tmp_path / "lineage.json"
        self._create_pipeline_files(tmp_path)
        with patch("lineage.manifest.LINEAGE_PATH", fake_path):
            repair_manifest(data_dir=tmp_path)
        data = json.loads(fake_path.read_text())
        # properties takes gauge.json as input — its recorded input hash
        # must match gauges' output hash for gauge.json
        gauges_out = data["steps"]["gauges"]["outputs"]["gauge.json"]["hash"]
        props_in = data["steps"]["properties"]["inputs"]["gauge.json"]["hash"]
        assert gauges_out == props_in

    def test_repair_idempotent(self, tmp_path):
        """Running repair twice produces identical hashes."""
        from lineage.manifest import repair_manifest
        fake_path = tmp_path / "lineage.json"
        self._create_pipeline_files(tmp_path)
        with patch("lineage.manifest.LINEAGE_PATH", fake_path):
            repair_manifest(data_dir=tmp_path)
            data1 = json.loads(fake_path.read_text())
            repair_manifest(data_dir=tmp_path)
            data2 = json.loads(fake_path.read_text())
        # All output hashes should be identical
        for step in data1["steps"]:
            for out_name, out_info in data1["steps"][step].get("outputs", {}).items():
                assert out_info["hash"] == data2["steps"][step]["outputs"][out_name]["hash"]


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
        assert len(result["missing_steps"]) == 11  # all steps missing (incl synthetic_gauges)

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
            "propertyhc": {
                "inputs": {
                    "propertyts/": {"hash": "k"},
                    "gaugehc.json": {"hash": "j"},
                    "gauge.json": {"hash": "a"},
                },
                "outputs": {"propertyhc.json": {"hash": "l"}},
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


# ---------------------------------------------------------------------------
# query.py tests
# ---------------------------------------------------------------------------

class TestOutputToStep:
    """_output_to_step: reverse mapping."""

    def test_known_outputs(self):
        from lineage.query import _output_to_step
        m = _output_to_step()
        assert m["gauge.json"] == "gauges"
        assert m["property.json"] == "properties"
        assert m["gaugehd/"] == "gaugehd"


class TestInputToStep:
    """_input_to_step: reverse mapping of consumers."""

    def test_known_inputs(self):
        from lineage.query import _input_to_step
        m = _input_to_step()
        assert "properties" in m["gauge.json"]
        assert "gaugehd" in m["gauge.json"]


class TestWalkUpstream:
    """_walk_upstream: DFS dependency resolution."""

    def test_root_has_no_upstream(self):
        from lineage.query import _walk_upstream
        result = _walk_upstream("gauges")
        assert result == ["gauges"]

    def test_mid_chain(self):
        from lineage.query import _walk_upstream
        result = _walk_upstream("properties")
        assert "gauges" in result
        assert result.index("gauges") < result.index("properties")

    def test_deep_chain(self):
        from lineage.query import _walk_upstream
        result = _walk_upstream("propertyhc")
        # propertyhc depends on propertyts, hazard, which depend on gauges, stressm, etc.
        assert "gauges" in result
        assert "propertyhc" in result

    def test_cycle_safety(self):
        """_walk_upstream should not infinite loop on revisited nodes."""
        from lineage.query import _walk_upstream
        # stressm depends on gauges,gaugehd; hazard depends on gauges,stressm
        result = _walk_upstream("hazard")
        # gauges should appear only once
        assert result.count("gauges") == 1


class TestTraceDataPoint:
    """trace_data_point: provenance chain for data IDs."""

    def test_gauge_id_chain(self):
        from lineage.query import trace_data_point
        manifest = _make_manifest({
            "gauges": {"run_id": "r1", "timestamp": "t1", "status": "success"},
            "stressm": {"run_id": "r1", "timestamp": "t1", "status": "success"},
        })
        with patch("lineage.query.load_manifest", return_value=manifest):
            chain = trace_data_point("gauge_id", "GAUGE-abc123")
        assert len(chain) == 4  # gauges, gaugehd, stressm, hazard
        assert chain[0]["step"] == "gauges"
        assert chain[0]["recorded"] is True
        assert chain[0]["data_id"] == "GAUGE-abc123"
        # gaugehd not in manifest → recorded=False
        assert chain[1]["step"] == "gaugehd"
        assert chain[1]["recorded"] is False

    def test_property_id_chain(self):
        from lineage.query import trace_data_point
        with patch("lineage.query.load_manifest", return_value=_make_manifest({})):
            chain = trace_data_point("property_id", "PROP-001")
        assert len(chain) == 3  # properties, propertyts, propertyhc
        assert all(c["recorded"] is False for c in chain)

    def test_unknown_data_type(self):
        from lineage.query import trace_data_point
        with patch("lineage.query.load_manifest", return_value=_make_manifest({})):
            chain = trace_data_point("unknown_type", "X-001")
        assert chain == []


class TestGetFileLineage:
    """get_file_lineage: producer/consumer lookup."""

    def test_known_file(self):
        from lineage.query import get_file_lineage
        manifest = _make_manifest({
            "gauges": {"run_id": "r1", "timestamp": "t1"},
        })
        with patch("lineage.query.load_manifest", return_value=manifest):
            result = get_file_lineage("gauge.json")
        assert result["produced_by"] == "gauges"
        assert result["producer_run_id"] == "r1"
        assert "properties" in result["consumed_by"]

    def test_unknown_file(self):
        from lineage.query import get_file_lineage
        with patch("lineage.query.load_manifest", return_value=_make_manifest({})):
            result = get_file_lineage("nonexistent.json")
        assert result["produced_by"] is None
        assert result["producer_run_id"] is None
        assert result["consumed_by"] == []

    def test_file_with_no_producer_entry(self):
        """Producer step exists in STEP_IO but not in manifest."""
        from lineage.query import get_file_lineage
        with patch("lineage.query.load_manifest", return_value=_make_manifest({})):
            result = get_file_lineage("gauge.json")
        assert result["produced_by"] == "gauges"
        assert result["producer_run_id"] is None  # not in manifest


class TestGetStepLineage:
    """get_step_lineage: upstream/downstream tree."""

    def test_root_step(self):
        from lineage.query import get_step_lineage
        manifest = _make_manifest({
            "gauges": {"run_id": "r1", "timestamp": "t1"},
        })
        with patch("lineage.query.load_manifest", return_value=manifest):
            result = get_step_lineage("gauges")
        assert result["upstream"] == []
        assert "properties" in result["downstream"]
        assert result["last_run"] == "r1"
        assert result["inputs"] == []
        assert "gauge.json" in result["outputs"]

    def test_mid_step(self):
        from lineage.query import get_step_lineage
        with patch("lineage.query.load_manifest", return_value=_make_manifest({})):
            result = get_step_lineage("properties")
        assert "gauges" in result["upstream"]
        assert "mortgages" in result["downstream"]
        assert result["last_run"] is None

    def test_step_not_in_manifest(self):
        from lineage.query import get_step_lineage
        with patch("lineage.query.load_manifest", return_value=_make_manifest({})):
            result = get_step_lineage("gauges")
        assert result["last_run"] is None
        assert result["last_timestamp"] is None
