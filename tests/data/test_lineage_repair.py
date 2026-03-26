# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""
Unit tests for lineage manifest repair — rebuilding from on-disk hashes.
"""

import json
import os
import hashlib
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest


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
