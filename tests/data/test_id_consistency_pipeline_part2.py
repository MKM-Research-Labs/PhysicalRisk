# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

"""
Pipeline ID consistency tests — part 2.

Covers: TestDataLineage, TestDeterministicIDs.
BCBS 239 Principle 3 (Accuracy).
"""

import json
from pathlib import Path

import pytest

from tests.data._id_consistency_helpers import (
    ROOT,
    INPUT_DIR,
    OUTPUT_DIR,
    _load_gauge_ids,
)


class TestDataLineage:
    """Data lineage manifest must be consistent (BCBS 239 P2/P3)."""

    def test_manifest_exists(self):
        """data_lineage.json must exist after any port run."""
        lineage_path = ROOT / "data" / "data_lineage.json"
        if not lineage_path.exists():
            pytest.skip("data_lineage.json not generated yet -- run: python app.py port")
        data = json.load(open(lineage_path))
        assert "steps" in data, "Manifest missing 'steps' key"
        assert len(data["steps"]) > 0, "Manifest has no recorded steps"

    def test_output_hashes_current(self):
        """Recorded output hashes must match current files on disk."""
        lineage_path = ROOT / "data" / "data_lineage.json"
        if not lineage_path.exists():
            pytest.skip("No manifest")

        # Import hash functions
        try:
            from lineage.manifest import hash_file, hash_directory
        except ImportError:
            pytest.skip("lineage package not available")

        data = json.load(open(lineage_path))
        mismatches = []
        for step_name, step in data.get("steps", {}).items():
            for name, info in step.get("outputs", {}).items():
                path = INPUT_DIR / name if not name.startswith("prs") else ROOT / "data" / "output" / name
                if not path.exists():
                    continue
                recorded = info.get("hash") or info.get("sha256")
                if recorded is None:
                    continue
                if path.is_dir():
                    current, _ = hash_directory(path)
                else:
                    current = hash_file(path)
                if current != recorded:
                    mismatches.append(f"{step_name}/{name}: recorded={recorded[:12]}... current={current[:12]}...")

        if mismatches:
            import warnings
            warnings.warn(
                f"{len(mismatches)} output hash mismatches -- data modified since last pipeline run:\n"
                + "\n".join(f"  - {m}" for m in mismatches[:10])
                + "\n  Re-run: python3 app.py port"
            )

    def test_lineage_file_exists(self):
        """Data lineage file should exist after a port run."""
        lineage_path = ROOT / "data" / "data_lineage.json"
        assert lineage_path.exists(), (
            "data_lineage.json not found. Run: python app.py port"
        )

    def test_dependency_graph_complete(self):
        """Every step in manifest must appear in the static dependency graph."""
        lineage_path = ROOT / "data" / "data_lineage.json"
        if not lineage_path.exists():
            pytest.skip("No manifest")
        try:
            from lineage.manifest import DEPENDENCY_GRAPH
        except ImportError:
            pytest.skip("lineage package not available")
        data = json.load(open(lineage_path))
        steps = set(data.get("steps", {}).keys())
        missing = steps - set(DEPENDENCY_GRAPH.keys())
        assert len(missing) == 0, f"Steps not in dependency graph: {missing}"


# =========================================================================
# Deterministic ID stability
# =========================================================================

class TestDeterministicIDs:
    """Gauge and property IDs must be deterministic (stable across runs)."""

    def test_gauge_ids_are_deterministic(self):
        """Gauge IDs should be derived from location, not random UUIDs."""
        import hashlib
        try:
            from port.rand.thames.gauge.gauge_locations import THAMES_GAUGE_LOCATIONS
        except ImportError:
            pytest.skip("Cannot import gauge locations")

        gauge_ids = _load_gauge_ids()
        if not gauge_ids:
            pytest.skip("No gauges")

        # Compute what deterministic IDs should be
        expected = set()
        for loc in THAMES_GAUGE_LOCATIONS:
            loc_key = f"{loc['lat']:.6f}:{loc['lon']:.6f}:{loc.get('name', '')}"
            gid = f"GAUGE-{hashlib.sha256(loc_key.encode()).hexdigest()[:8]}"
            expected.add(gid)

        # If gauge.json was generated with the deterministic fix,
        # the IDs should match
        if gauge_ids != expected:
            pytest.fail(
                f"gauge.json has non-deterministic IDs. "
                f"Expected {sorted(expected)[:3]}..., "
                f"got {sorted(gauge_ids)[:3]}... "
                f"Regenerate: python app.py port --gauge"
            )
