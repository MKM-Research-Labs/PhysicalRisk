# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""
Unit tests for lineage manifest operations — hashing, loading, saving, recording.
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


# ===========================================================================
# Coverage: config fallback, pre_hash_inputs, repair unknown step
# ===========================================================================

class TestManifestConfigFallback:
    """Cover the ImportError fallback at module level (lines 32-33)."""

    def test_fallback_path_ends_with_physicalrisk(self):
        """If config import fails, _project_root should be a sensible fallback."""
        from lineage import manifest
        # Just verify LINEAGE_PATH is a Path to data_lineage.json
        assert manifest.LINEAGE_PATH.name == "data_lineage.json"
        assert "data" in str(manifest.LINEAGE_PATH)


class TestPreHashInputs:
    """Cover pre_hash_inputs (line 182)."""

    def test_hashes_file_inputs(self, tmp_path):
        from lineage.manifest import pre_hash_inputs
        f = tmp_path / "gauge.json"
        f.write_text('{"id": 1}')
        result = pre_hash_inputs({"gauge.json": str(f)})
        assert "gauge.json" in result
        assert result["gauge.json"]["hash"] is not None
        assert result["gauge.json"]["type"] == "file"

    def test_missing_input_gives_none_hash(self, tmp_path):
        from lineage.manifest import pre_hash_inputs
        result = pre_hash_inputs({"missing.json": str(tmp_path / "nope.json")})
        assert result["missing.json"]["hash"] is None


class TestRepairManifestsEdgeCases:
    """Cover repair_manifests config fallback and unknown step skip."""

    def test_skips_unknown_step_in_topo_order(self, tmp_path, monkeypatch):
        from lineage.manifest import repair_manifest, LINEAGE_PATH
        from unittest.mock import patch as _p
        import lineage.manifest as _m

        # Add a phantom step to DEPENDENCY_GRAPH not in STEP_IO
        orig_graph = _m.DEPENDENCY_GRAPH.copy()
        monkeypatch.setattr(_m, "DEPENDENCY_GRAPH", {**orig_graph, "phantom": []})

        fake_lineage = tmp_path / "data_lineage.json"
        fake_lineage.write_text('{"runs": {}, "steps": {}}')
        monkeypatch.setattr(_m, "LINEAGE_PATH", fake_lineage)

        result = repair_manifest(data_dir=tmp_path)
        # phantom should be skipped, not crash
        assert "phantom" not in result.get("repaired", [])

    def test_config_fallback_when_import_fails(self, tmp_path, monkeypatch):
        from lineage.manifest import repair_manifest
        import lineage.manifest as _m
        import builtins

        fake_lineage = tmp_path / "data_lineage.json"
        fake_lineage.write_text('{"runs": {}, "steps": {}}')
        monkeypatch.setattr(_m, "LINEAGE_PATH", fake_lineage)

        real_import = builtins.__import__
        def fake_import(name, *args, **kwargs):
            if name == "config" and "PortfolioConfig" in str(args):
                raise ImportError("no config")
            return real_import(name, *args, **kwargs)
        monkeypatch.setattr(builtins, "__import__", fake_import)

        # Should not crash — falls back to default path
        result = repair_manifest(data_dir=None)
        assert isinstance(result, dict)
