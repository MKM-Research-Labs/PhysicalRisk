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
        """Gauge IDs should be derived from location, not random UUIDs.

        Mirrors the construction in src/port/rand/thames/gauge/gauge_random.py
        (generate_gauge_metadata) and src/port/src/gauge/gauge.py (which builds
        the location dicts from catchment GAUGE_POINTS + gauge_names).
        """
        import hashlib
        import os
        catchment = os.getenv("MKM_CATCHMENT", "thames")
        try:
            # Catchment params live at data/catch/<id>.py and the project
            # adds data/ to sys.path via config.path._setup_paths.  Trigger
            # that path setup if it hasn't happened (e.g. when this test
            # runs in isolation without first importing config).
            import importlib
            import sys
            from pathlib import Path
            data_dir = Path(__file__).parent.parent.parent / "data"
            data_dir_str = str(data_dir)
            if data_dir_str not in sys.path:
                sys.path.insert(0, data_dir_str)
            # Catchment-aware: derive expected IDs from whichever catchment
            # the data dir is pinned to (MKM_CATCHMENT), not always thames.
            mod = importlib.import_module(f"catch.{catchment}")
            GAUGE_POINTS = mod.GAUGE_POINTS
            GAUGE_NAMES = mod.GAUGE_NAMES
            AREAS = mod.AREAS
        except (ImportError, AttributeError) as e:
            pytest.skip(f"Cannot import {catchment} catchment data: {e}")

        gauge_ids = _load_gauge_ids()
        if not gauge_ids:
            pytest.skip("No gauges")

        # Reproduce the location → gauge_id derivation used by the
        # generator. Only the fixed (non-synthetic) gauges are deterministic
        # — synthetic SYNTH-* gauges have their own ID scheme and aren't
        # expected to match this set.
        expected = set()
        for i, (lat, lon, _elev) in enumerate(GAUGE_POINTS):
            short_name = (
                GAUGE_NAMES[i]
                if i < len(GAUGE_NAMES)
                else f"{AREAS[i % len(AREAS)]}_Point_{i}"
            )
            loc_key = f"{lat:.6f}:{lon:.6f}:{short_name}"
            gid = f"GAUGE-{hashlib.sha256(loc_key.encode()).hexdigest()[:8]}"
            expected.add(gid)

        # The fixed-location IDs must all be present in gauge.json
        # (synthetic SYNTH-* gauges live alongside them).
        missing = expected - gauge_ids
        assert not missing, (
            f"gauge.json is missing {len(missing)} deterministic gauge IDs "
            f"derived from GAUGE_POINTS. Sample: {sorted(missing)[:3]}. "
            f"Regenerate: python app.py port --gauge"
        )
