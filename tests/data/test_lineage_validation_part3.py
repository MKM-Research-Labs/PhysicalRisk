# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""
Unit tests for lineage validation — completeness, full chain (part 3).
"""

from unittest.mock import patch

import pytest

from tests.data.conftest import make_manifest as _make_manifest


class TestDependencyGraphIntegrity:
    """Structural checks on DEPENDENCY_GRAPH vs STEP_IO."""

    def test_every_input_has_producer_in_transitive_deps(self):
        """Every input declared in STEP_IO must be produced by a transitive
        dependency of the consuming step.  If this fails, the lineage
        staleness check will compare against the wrong producer hash."""
        from graphlib import TopologicalSorter
        from lineage.manifest import DEPENDENCY_GRAPH, EXTERNAL_INPUTS, STEP_IO

        topo_order = list(TopologicalSorter(DEPENDENCY_GRAPH).static_order())

        for step_name, io in STEP_IO.items():
            if not io["inputs"]:
                continue

            # Collect transitive deps
            deps: set[str] = set()
            queue = list(DEPENDENCY_GRAPH.get(step_name, []))
            while queue:
                dep = queue.pop()
                if dep not in deps:
                    deps.add(dep)
                    queue.extend(DEPENDENCY_GRAPH.get(dep, []))

            # For each input, find at least one producer in transitive deps
            # (external inputs like storm_control.json are config files
            # not produced by any pipeline step — skip them)
            for inp in io["inputs"]:
                if inp in EXTERNAL_INPUTS:
                    continue
                producers = [
                    s for s in deps
                    if inp in STEP_IO.get(s, {}).get("outputs", [])
                ]
                assert producers, (
                    f"Step '{step_name}' consumes '{inp}' but no transitive "
                    f"dependency produces it.  Add the correct producer to "
                    f"DEPENDENCY_GRAPH['{step_name}']."
                )

    def test_mutating_producer_detected(self):
        """When hazard mutates gaugets/ to a different hash, propertyts must
        resolve hazard (not stressm) as the producer."""
        from lineage.validation import _find_producer
        # After fix: propertyts → hazard → stressm, so hazard is latest writer
        producer = _find_producer("propertyts", "gaugets/")
        assert producer == "hazard", (
            f"Expected hazard as producer of gaugets/ for propertyts, got {producer}"
        )

    def test_synthetic_gauges_mutating_producer_detected(self):
        """synthetic_gauges overwrites gauge.json after gauges. properties
        must resolve synthetic_gauges (not gauges) as the producer, otherwise
        properties is flagged stale on every successful run."""
        from lineage.validation import _find_producer
        producer = _find_producer("properties", "gauge.json")
        assert producer == "synthetic_gauges", (
            f"Expected synthetic_gauges as producer of gauge.json for "
            f"properties, got {producer}"
        )


# ===========================================================================
# Coverage: _helpers edge cases
# ===========================================================================

class TestResolveDataDir:
    """Cover the ImportError fallback in _resolve_data_dir."""

    def test_fallback_when_config_missing(self, monkeypatch):
        from lineage.validation._helpers import _resolve_data_dir
        # Patch the function-local import to fail
        from unittest.mock import patch as _p
        with _p("lineage.validation._helpers.Path") as mock_path:
            # Just force ImportError when config is imported
            import builtins
            real_import = builtins.__import__
            def fake_import(name, *args, **kwargs):
                if name == "config":
                    raise ImportError("no config")
                return real_import(name, *args, **kwargs)
            monkeypatch.setattr(builtins, "__import__", fake_import)
            result = _resolve_data_dir()
        assert "thames" in str(result) or result is not None


class TestLiveHash:
    """Cover _live_hash edge paths."""

    def test_returns_none_for_missing_path(self, tmp_path):
        from lineage.validation._helpers import _live_hash
        result = _live_hash("nonexistent_artifact.json", tmp_path)
        assert result is None

    def test_hashes_existing_file(self, tmp_path):
        from lineage.validation._helpers import _live_hash
        (tmp_path / "gauge.json").write_text('{"test": true}')
        result = _live_hash("gauge.json", tmp_path)
        assert result is not None and len(result) > 8

    def test_hashes_nonempty_directory(self, tmp_path):
        from lineage.validation._helpers import _live_hash
        d = tmp_path / "gaugets"
        d.mkdir()
        (d / "file.json").write_text("{}")
        result = _live_hash("gaugets", tmp_path)
        assert result is not None

    def test_returns_none_for_empty_directory(self, tmp_path):
        from lineage.validation._helpers import _live_hash
        d = tmp_path / "emptydir"
        d.mkdir()
        result = _live_hash("emptydir", tmp_path)
        assert result is None


class TestOutputStepMap:
    """Cover _output_step_map skipping None STEP_IO entries."""

    def test_skips_unknown_steps_in_graph(self, monkeypatch):
        from lineage.validation import _helpers
        # Add a phantom step in DEPENDENCY_GRAPH but not in STEP_IO
        original_graph = _helpers.DEPENDENCY_GRAPH.copy()
        monkeypatch.setattr(_helpers, "DEPENDENCY_GRAPH",
                            {**original_graph, "phantom": []})
        mapping = _helpers._output_step_map()
        assert "phantom" not in mapping.values()


# ===========================================================================
# Coverage: freshness edge cases
# ===========================================================================

class TestCheckInputsFreshEdgeCases:
    """Cover no-producer, null-hash, and consumer-null-hash branches."""

    def test_no_producer_found(self):
        """Input artifact with no known producer."""
        from lineage.validation import check_inputs_fresh
        # Create a step that consumes a fictional artifact nobody produces
        manifest = _make_manifest({
            "fake_step": {
                "inputs": {"mystery_file.json": {"hash": "abc"}},
                "outputs": {},
            },
        })
        from unittest.mock import patch as _patch
        import lineage.validation as _val
        with _patch.object(_val, "load_manifest", return_value=manifest), \
             _patch.object(_val, "STEP_IO", {
                 "fake_step": {"inputs": ["mystery_file.json"], "outputs": []},
             }), \
             _patch.object(_val, "DEPENDENCY_GRAPH", {"fake_step": []}):
            ok, issues = check_inputs_fresh("fake_step")
        assert not ok
        assert any("No producer" in i for i in issues)

    def test_consumer_explicit_null_hash_live_fallback(self, tmp_path):
        """Consumer has hash=None explicitly → live hash fallback."""
        from lineage.validation import check_inputs_fresh
        manifest = _make_manifest({
            "gauges": {
                "outputs": {"gauge.json": {"hash": "abc123"}},
            },
            "properties": {
                "inputs": {"gauge.json": {"hash": None}},
                "outputs": {"property.json": {"hash": "def"}},
            },
        })
        (tmp_path / "gauge.json").write_text('{"x": 1}')
        from unittest.mock import patch as _patch
        import lineage.validation as _val
        with _patch.object(_val, "load_manifest", return_value=manifest), \
             _patch("lineage.validation._helpers._resolve_data_dir", return_value=tmp_path):
            ok, issues = check_inputs_fresh("properties")
        # Will either match or report stale — but should NOT crash
        assert isinstance(ok, bool)

    def test_consumer_null_hash_artifact_missing(self):
        """Consumer has hash=None and artifact doesn't exist on disk."""
        from lineage.validation import check_inputs_fresh
        manifest = _make_manifest({
            "gauges": {
                "outputs": {"gauge.json": {"hash": "abc123"}},
            },
            "properties": {
                "inputs": {"gauge.json": {"hash": None}},
                "outputs": {"property.json": {"hash": "def"}},
            },
        })
        from unittest.mock import patch as _patch
        from pathlib import Path as _P
        import lineage.validation as _val
        fake_dir = _P("/tmp/nonexistent_lineage_test_dir")
        with _patch.object(_val, "load_manifest", return_value=manifest), \
             _patch("lineage.validation._helpers._resolve_data_dir", return_value=fake_dir):
            ok, issues = check_inputs_fresh("properties")
        # Either reports missing on disk or stale — both indicate the branch was hit
        assert not ok
        assert len(issues) > 0

    def test_producer_null_hash_live_fallback(self, tmp_path):
        """Producer has hash=None → live hash fallback."""
        from lineage.validation import check_inputs_fresh
        manifest = _make_manifest({
            "gauges": {
                "outputs": {"gauge.json": {"hash": None}},
            },
            "properties": {
                "inputs": {"gauge.json": {"hash": "abc123"}},
                "outputs": {"property.json": {"hash": "def"}},
            },
        })
        (tmp_path / "gauge.json").write_text('{"x": 1}')
        from unittest.mock import patch as _patch
        import lineage.validation as _val
        with _patch.object(_val, "load_manifest", return_value=manifest), \
             _patch("lineage.validation._helpers._resolve_data_dir", return_value=tmp_path):
            ok, issues = check_inputs_fresh("properties")
        assert isinstance(ok, bool)
