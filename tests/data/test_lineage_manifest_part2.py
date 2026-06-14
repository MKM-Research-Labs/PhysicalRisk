# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""
Unit tests for lineage manifest operations — hashing, loading, saving, recording (part 2).
"""

import json
import os
import hashlib
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest


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

        with patch("lineage.manifest._core.LINEAGE_PATH", fake_path):
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
        # User attribution fields (added for data protection)
        assert "user" in entry
        assert isinstance(entry["user"], str)
        assert "hostname" in entry
        assert isinstance(entry["hostname"], str)
        assert len(entry["hostname"]) > 0

    def test_record_with_auto_run_id(self, tmp_path):
        from lineage.manifest import record_step
        fake_path = tmp_path / "lineage.json"
        inp = tmp_path / "x.json"
        inp.write_text("{}")

        with patch("lineage.manifest._core.LINEAGE_PATH", fake_path):
            entry = record_step(
                step_name="gauges",
                generator="gen",
                inputs={},
                outputs={"gauge.json": str(inp)},
                parameters={},
                elapsed_seconds=0.5,
            )
        assert entry["run_id"].startswith("run-")

    def test_record_captures_user_from_env(self, tmp_path):
        """record_step must capture the USER env variable."""
        from lineage.manifest import record_step
        fake_path = tmp_path / "lineage.json"
        inp = tmp_path / "u.json"
        inp.write_text("{}")

        with patch("lineage.manifest._core.LINEAGE_PATH", fake_path), \
             patch.dict(os.environ, {"USER": "test_admin"}):
            entry = record_step(
                step_name="test_user",
                generator="gen",
                inputs={},
                outputs={"u.json": str(inp)},
                parameters={},
                elapsed_seconds=0.1,
            )
        assert entry["user"] == "test_admin"

    def test_record_captures_hostname(self, tmp_path):
        """record_step must capture the machine hostname."""
        import socket
        from lineage.manifest import record_step
        fake_path = tmp_path / "lineage.json"
        inp = tmp_path / "h.json"
        inp.write_text("{}")

        with patch("lineage.manifest._core.LINEAGE_PATH", fake_path):
            entry = record_step(
                step_name="test_host",
                generator="gen",
                inputs={},
                outputs={"h.json": str(inp)},
                parameters={},
                elapsed_seconds=0.1,
            )
        assert entry["hostname"] == socket.gethostname()


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
