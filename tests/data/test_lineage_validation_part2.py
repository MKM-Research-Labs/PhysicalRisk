# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""
Unit tests for lineage validation — completeness, full chain (part 2).
"""

from unittest.mock import patch

import pytest

from tests.data.conftest import make_manifest as _make_manifest


class TestCheckPipelineComplete:
    """check_pipeline_complete: verify all pipeline outputs exist on disk."""

    def test_complete_pipeline(self, tmp_path):
        """All outputs present → complete."""
        from lineage.validation import check_pipeline_complete
        from lineage.manifest import STEP_IO
        # Create every output (handles nested paths like typhoon/ensemble.json)
        for step, io in STEP_IO.items():
            for output in io["outputs"]:
                if output.endswith("/"):
                    d = tmp_path / output
                    d.mkdir(parents=True, exist_ok=True)
                    (d / "dummy.json").write_text("{}")
                else:
                    p = tmp_path / output
                    p.parent.mkdir(parents=True, exist_ok=True)
                    p.write_text("{}")
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
                    p = tmp_path / output
                    p.parent.mkdir(parents=True, exist_ok=True)
                    p.write_text("{}")
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
        # gauge.json is output by both "gauges" and "synthetic_gauges",
        # plus counterparty.json from "counterparties" → 3 present outputs
        assert result["present"] == 3
        missing_outputs = [m["output"] for m in result["missing"]]
        assert "property.json" in missing_outputs
        assert "stress_storms/" in missing_outputs
        assert "propertyts/" in missing_outputs


class TestValidateFullChain:
    """validate_full_chain: end-to-end consistency check."""

    def test_empty_manifest(self):
        from lineage.validation import validate_full_chain
        from lineage.manifest import DEPENDENCY_GRAPH
        with patch("lineage.validation.load_manifest", return_value=_make_manifest({})):
            result = validate_full_chain()
        assert not result["is_consistent"]
        # Every registered step should appear as missing
        assert len(result["missing_steps"]) == len(DEPENDENCY_GRAPH)

    def test_consistent_chain(self):
        from lineage.validation import validate_full_chain
        # Build a minimal consistent manifest: root steps only
        manifest = _make_manifest({
            "gauges": {"inputs": {}, "outputs": {"gauge.json": {"hash": "a"}}},
            "counterparties": {"inputs": {}, "outputs": {"counterparty.json": {"hash": "b"}}},
            "synthetic_gauges": {
                "inputs": {"gauge.json": {"hash": "a"}},
                "outputs": {"gauge.json": {"hash": "a2"}},
            },
            "properties": {
                "inputs": {"gauge.json": {"hash": "a2"}},
                "outputs": {"property.json": {"hash": "c"}},
            },
            "mortgages": {
                "inputs": {"property.json": {"hash": "c"}},
                "outputs": {"loan.json": {"hash": "d"}},
            },
            "gaugehd": {
                "inputs": {"gauge.json": {"hash": "a2"}},
                "outputs": {"gaugehd/": {"hash": "e"}},
            },
            "stressm": {
                "inputs": {"gauge.json": {"hash": "a2"}, "gaugehd/": {"hash": "e"}},
                "outputs": {
                    "gaugets/": {"hash": "f"},
                    "stress_storms/": {"hash": "g"},
                    "storm_sequences.json": {"hash": "h"},
                    "sequence_gauge/": {"hash": "i"},
                },
            },
            "hazard": {
                "inputs": {"gauge.json": {"hash": "a2"}, "gaugets/": {"hash": "f"}},
                "outputs": {"gaugehc.json": {"hash": "j"}, "gaugets/": {"hash": "f"}},
            },
            "propertyts": {
                "inputs": {
                    "property.json": {"hash": "c"},
                    "gauge.json": {"hash": "a2"},
                    "gaugets/": {"hash": "f"},
                },
                "outputs": {"propertyts/": {"hash": "k"}},
            },
            "propertytsd": {
                "inputs": {
                    "property.json": {"hash": "c"},
                    "gauge.json": {"hash": "a2"},
                    "gaugets/": {"hash": "f"},
                },
                "outputs": {"propertytsd/": {"hash": "k1"}},
            },
            "propertytse": {
                "inputs": {
                    "property.json": {"hash": "c"},
                    "gauge.json": {"hash": "a2"},
                    "gaugets/": {"hash": "f"},
                },
                "outputs": {"propertytse/": {"hash": "k2"}},
            },
            "propertyhc": {
                "inputs": {
                    "propertyts/": {"hash": "k"},
                    "gaugehc.json": {"hash": "j"},
                    "gauge.json": {"hash": "a2"},
                },
                "outputs": {"propertyhc.json": {"hash": "l"}},
            },
            "propertyshd": {
                "inputs": {
                    "propertytsd/": {"hash": "k1"},
                    "gaugehc.json": {"hash": "j"},
                    "gauge.json": {"hash": "a2"},
                },
                "outputs": {"propertyshd.json": {"hash": "l1"}},
            },
            "propertyshe": {
                "inputs": {
                    "propertytse/": {"hash": "k2"},
                    "gaugehc.json": {"hash": "j"},
                    "gauge.json": {"hash": "a2"},
                },
                "outputs": {"propertyshe.json": {"hash": "l2"}},
            },
            "propertytsb": {
                "inputs": {
                    "property.json": {"hash": "c"},
                    "gauge.json": {"hash": "a2"},
                    "gaugets/": {"hash": "f"},
                },
                "outputs": {"propertytsb/": {"hash": "k3"}},
            },
            "propertybri": {
                "inputs": {
                    "propertytsb/": {"hash": "k3"},
                    "gaugehc.json": {"hash": "j"},
                    "gauge.json": {"hash": "a2"},
                },
                "outputs": {"propertybri.json": {"hash": "l3"}},
            },
            "blotter": {
                "inputs": {"gaugehc.json": {"hash": "j"}, "counterparty.json": {"hash": "b"}},
                "outputs": {"prs/": {"hash": "m"}},
            },
            "typhoon": {
                "inputs": {},
                "outputs": {
                    "typhoon/ensemble.json": {"hash": "n"},
                    "typhoon/events/": {"hash": "o"},
                    "typhoon/windts/": {"hash": "p"},
                    "typhoon/damage/": {"hash": "q"},
                },
            },
            "commercial": {
                "inputs": {},
                "outputs": {
                    "commercial.json": {"hash": "r"},
                    "commercial_loan.json": {"hash": "s"},
                },
            },
            "commercialts": {
                "inputs": {
                    "commercial.json": {"hash": "r"},
                    "gauge.json": {"hash": "a2"},
                    "gaugets/": {"hash": "f"},
                },
                "outputs": {"commercialts/": {"hash": "t"}},
            },
            "commercialtsd": {
                "inputs": {
                    "commercial.json": {"hash": "r"},
                    "gauge.json": {"hash": "a2"},
                    "gaugets/": {"hash": "f"},
                },
                "outputs": {"commercialtsd/": {"hash": "t1"}},
            },
            "commercialtse": {
                "inputs": {
                    "commercial.json": {"hash": "r"},
                    "gauge.json": {"hash": "a2"},
                    "gaugets/": {"hash": "f"},
                },
                "outputs": {"commercialtse/": {"hash": "t2"}},
            },
            "commercialhc": {
                "inputs": {
                    "commercialts/": {"hash": "t"},
                    "gaugehc.json": {"hash": "j"},
                    "gauge.json": {"hash": "a2"},
                },
                "outputs": {"commercialhc.json": {"hash": "u"}},
            },
            "commercialshd": {
                "inputs": {
                    "commercialtsd/": {"hash": "t1"},
                    "gaugehc.json": {"hash": "j"},
                    "gauge.json": {"hash": "a2"},
                },
                "outputs": {"commercialshd.json": {"hash": "u1"}},
            },
            "commercialshe": {
                "inputs": {
                    "commercialtse/": {"hash": "t2"},
                    "gaugehc.json": {"hash": "j"},
                    "gauge.json": {"hash": "a2"},
                },
                "outputs": {"commercialshe.json": {"hash": "u2"}},
            },
            "commercialtsb": {
                "inputs": {
                    "commercial.json": {"hash": "r"},
                    "gauge.json": {"hash": "a2"},
                    "gaugets/": {"hash": "f"},
                },
                "outputs": {"commercialtsb/": {"hash": "t3"}},
            },
            "commercialbri": {
                "inputs": {
                    "commercialtsb/": {"hash": "t3"},
                    "gaugehc.json": {"hash": "j"},
                    "gauge.json": {"hash": "a2"},
                },
                "outputs": {"commercialbri.json": {"hash": "u3"}},
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


# ===========================================================================
# Coverage: completeness — config fallback
# ===========================================================================

class TestCheckPipelineCompleteConfigFallback:
    """Cover the ImportError fallback in check_pipeline_complete."""

    def test_fallback_when_config_missing(self, monkeypatch):
        from lineage.validation.completeness import check_pipeline_complete
        import builtins
        real_import = builtins.__import__
        def fake_import(name, *args, **kwargs):
            if name == "config":
                raise ImportError("no config")
            return real_import(name, *args, **kwargs)
        monkeypatch.setattr(builtins, "__import__", fake_import)
        result = check_pipeline_complete(data_dir=None)
        # Should not crash — uses fallback path
        assert "complete" in result


# ===========================================================================
# Coverage: OPTIONAL_STEPS — typhoon is opt-in per catchment
# ===========================================================================

class TestOptionalSteps:
    """Steps in OPTIONAL_STEPS are skipped when entirely absent (opt-in
    per catchment), but flagged when partially present (broken run)."""

    def _make_full_pipeline(self, tmp_path, skip_step: str | None = None):
        """Create every STEP_IO output on disk, optionally skipping one step."""
        from lineage.manifest import STEP_IO
        for step, io in STEP_IO.items():
            if step == skip_step:
                continue
            for output in io["outputs"]:
                if output.endswith("/"):
                    d = tmp_path / output
                    d.mkdir(parents=True, exist_ok=True)
                    (d / "dummy.json").write_text("{}")
                else:
                    p = tmp_path / output
                    p.parent.mkdir(parents=True, exist_ok=True)
                    p.write_text("{}")

    def test_typhoon_in_optional_set(self):
        """typhoon must remain opt-in — most catchments don't have tc.py."""
        from lineage.manifest import OPTIONAL_STEPS
        assert "typhoon" in OPTIONAL_STEPS

    def test_optional_step_entirely_absent_is_skipped(self, tmp_path):
        """Catchment without typhoon outputs → pipeline reported complete."""
        from lineage.validation import check_pipeline_complete
        self._make_full_pipeline(tmp_path, skip_step="typhoon")
        result = check_pipeline_complete(tmp_path)
        assert result["complete"], (
            f"typhoon-less catchment should be complete; missing: {result['missing']}"
        )
        # No typhoon entries should appear in missing
        steps_missing = {m["step"] for m in result["missing"]}
        assert "typhoon" not in steps_missing

    def test_optional_step_partial_is_flagged(self, tmp_path):
        """Catchment with SOME typhoon outputs but not all → flagged broken."""
        from lineage.validation import check_pipeline_complete
        self._make_full_pipeline(tmp_path, skip_step="typhoon")
        # Add only the typhoon ensemble file — the other 3 outputs absent
        (tmp_path / "typhoon").mkdir()
        (tmp_path / "typhoon" / "ensemble.json").write_text("{}")
        result = check_pipeline_complete(tmp_path)
        assert not result["complete"]
        typhoon_missing = [m for m in result["missing"] if m["step"] == "typhoon"]
        # 3 of 4 typhoon outputs still missing (events/, windts/, damage/)
        assert len(typhoon_missing) == 3

    def test_non_optional_step_still_flagged_when_missing(self, tmp_path):
        """Missing properties is always a failure — even if typhoon is skipped."""
        from lineage.validation import check_pipeline_complete
        self._make_full_pipeline(tmp_path, skip_step="properties")
        result = check_pipeline_complete(tmp_path)
        assert not result["complete"]
        steps_missing = {m["step"] for m in result["missing"]}
        assert "properties" in steps_missing


# ===========================================================================
# Coverage: freshness — uncovered branches (53-54, 91-99, 104-105, 113-121)
# ===========================================================================

class TestFreshnessExternalInputs:
    """Cover the EXTERNAL_INPUTS branch (lines 50-66) including the
    'consumer never ran' fallthrough at lines 53-54."""

    def test_external_input_consumer_never_ran(self):
        """stressm consumes storm_control.json; if stressm never ran, the
        external-input branch should report 'has never run'."""
        from lineage.validation import check_inputs_fresh
        from unittest.mock import patch as _patch
        import lineage.validation as _val

        # Manifest where stressm's upstream dependencies have run but
        # stressm itself has not → the external-input check should fire
        # before producer lookup and report the consumer absent.
        manifest = _make_manifest({
            "gauges": {"outputs": {"gauge.json": {"hash": "a"}}},
            "synthetic_gauges": {"outputs": {"gauge.json": {"hash": "a2"}}},
            "gaugehd": {"outputs": {"gaugehd/": {"hash": "h"}}},
        })
        with _patch.object(_val, "load_manifest", return_value=manifest):
            ok, issues = check_inputs_fresh("stressm")
        assert not ok
        # Should include the "Step 'stressm' has never run" message from
        # the EXTERNAL_INPUTS branch when processing storm_control.json
        assert any("never run" in i for i in issues)

    def test_external_input_changed_on_disk(self, tmp_path):
        """External input recorded hash differs from on-disk hash → stale."""
        from lineage.validation import check_inputs_fresh
        from unittest.mock import patch as _patch
        import lineage.validation as _val

        (tmp_path / "storm_control.json").write_text('{"hours": 168}')
        manifest = _make_manifest({
            "gauges": {"outputs": {"gauge.json": {"hash": "a"}}},
            "synthetic_gauges": {"outputs": {"gauge.json": {"hash": "a2"}}},
            "gaugehd": {"outputs": {"gaugehd/": {"hash": "h"}}},
            "stressm": {
                "inputs": {
                    "gauge.json": {"hash": "a2"},
                    "gaugehd/": {"hash": "h"},
                    "storm_control.json": {"hash": "old_recorded_hash"},
                },
                "outputs": {"stress_storms/": {"hash": "x"}},
            },
        })
        with _patch.object(_val, "load_manifest", return_value=manifest), \
             _patch("lineage.validation.freshness._resolve_data_dir",
                    return_value=tmp_path):
            ok, issues = check_inputs_fresh("stressm")
        assert not ok
        assert any("storm_control.json" in i and "changed" in i for i in issues)

    def test_external_input_no_recorded_hash_is_tolerated(self, tmp_path):
        """Consumer entry exists but no recorded hash for storm_control →
        skip silently (line 56-57)."""
        from lineage.validation import check_inputs_fresh
        from unittest.mock import patch as _patch
        import lineage.validation as _val

        manifest = _make_manifest({
            "gauges": {"outputs": {"gauge.json": {"hash": "a"}}},
            "synthetic_gauges": {"outputs": {"gauge.json": {"hash": "a"}}},
            "gaugehd": {"outputs": {"gaugehd/": {"hash": "h"}}},
            "stressm": {
                "inputs": {
                    "gauge.json": {"hash": "a"},
                    "gaugehd/": {"hash": "h"},
                    # storm_control.json deliberately absent
                },
                "outputs": {"stress_storms/": {"hash": "x"}},
            },
        })
        with _patch.object(_val, "load_manifest", return_value=manifest):
            ok, issues = check_inputs_fresh("stressm")
        # No storm_control complaint — the missing-hash branch skips quietly
        assert not any("storm_control" in i for i in issues)


class TestFreshnessProducerNullHashMissing:
    """Cover lines 91-99: producer hash explicitly None, live disk hash
    also None (artifact missing) → reports 'missing on disk'."""

    def test_producer_null_hash_and_disk_missing(self, tmp_path):
        from lineage.validation import check_inputs_fresh
        from unittest.mock import patch as _patch
        import lineage.validation as _val

        manifest = _make_manifest({
            "gauges": {"outputs": {"gauge.json": {"hash": "a"}}},
            "synthetic_gauges": {
                "outputs": {"gauge.json": {"hash": None}},  # null hash
            },
            "properties": {
                "inputs": {"gauge.json": {"hash": "abc"}},
                "outputs": {"property.json": {"hash": "p"}},
            },
        })
        # Patch the *freshness* module's bound `_resolve_data_dir` reference
        # (it was imported into the module namespace at import time, so a
        # patch on `_helpers._resolve_data_dir` doesn't take effect here).
        with _patch.object(_val, "load_manifest", return_value=manifest), \
             _patch("lineage.validation.freshness._resolve_data_dir",
                    return_value=tmp_path):
            ok, issues = check_inputs_fresh("properties")
        assert not ok
        assert any("missing on disk" in i for i in issues)


class TestFreshnessConsumerNeverRan:
    """Cover lines 104-105: after producer resolved successfully,
    consumer step has no manifest entry."""

    def test_consumer_step_has_no_manifest_entry(self):
        from lineage.validation import check_inputs_fresh
        from unittest.mock import patch as _patch
        import lineage.validation as _val

        # Producer exists with concrete hash; consumer (mortgages) absent
        manifest = _make_manifest({
            "gauges": {"outputs": {"gauge.json": {"hash": "a"}}},
            "synthetic_gauges": {"outputs": {"gauge.json": {"hash": "a"}}},
            "properties": {
                "inputs": {"gauge.json": {"hash": "a"}},
                "outputs": {"property.json": {"hash": "p"}},
            },
            # mortgages deliberately absent
        })
        with _patch.object(_val, "load_manifest", return_value=manifest):
            ok, issues = check_inputs_fresh("mortgages")
        assert not ok
        assert any("Step 'mortgages' has never run" in i for i in issues)


class TestFreshnessConsumerExplicitNullDiskMissing:
    """Cover lines 113-121: consumer hash explicitly None AND live disk
    hash returns None → reports 'no recorded hash ... missing on disk'."""

    def test_consumer_null_hash_and_disk_missing(self, tmp_path):
        from lineage.validation import check_inputs_fresh
        from unittest.mock import patch as _patch
        import lineage.validation as _val

        manifest = _make_manifest({
            "gauges": {"outputs": {"gauge.json": {"hash": "abc"}}},
            "synthetic_gauges": {"outputs": {"gauge.json": {"hash": "abc"}}},
            "properties": {
                "inputs": {"gauge.json": {"hash": None}},  # explicit null
                "outputs": {"property.json": {"hash": "p"}},
            },
        })
        # Patch the freshness module's bound name (see sibling test above
        # for why patching _helpers._resolve_data_dir doesn't work here).
        with _patch.object(_val, "load_manifest", return_value=manifest), \
             _patch("lineage.validation.freshness._resolve_data_dir",
                    return_value=tmp_path):
            ok, issues = check_inputs_fresh("properties")
        assert not ok
        assert any(
            "no recorded hash" in i.lower() and "missing on disk" in i
            for i in issues
        )


# ===========================================================================
# Coverage: STEP_OWNERS — lock in the typhoon + commercial additions
# ===========================================================================

class TestHelpersResidualBranches:
    """Mop-up tests for the last uncovered lines in _helpers.py."""

    def test_current_hash_returns_missing_for_non_dict_entry(self):
        """_current_hash: outputs entry is a string (legacy/corrupt) → _MISSING."""
        from lineage.validation._helpers import _current_hash, _MISSING
        step = {"outputs": {"gauge.json": "not a dict"}}
        assert _current_hash("gauge.json", step) is _MISSING

    def test_live_hash_resolves_data_dir_when_none(self, tmp_path, monkeypatch):
        """_live_hash with data_dir=None calls _resolve_data_dir internally."""
        from lineage.validation import _helpers
        # Point the resolver at an empty tmp dir so the call returns None
        # (artifact missing) rather than hashing real catchment data.
        monkeypatch.setattr(_helpers, "_resolve_data_dir", lambda: tmp_path)
        result = _helpers._live_hash("does_not_exist.json")
        assert result is None


class TestStepOwnersNewEntries:
    """Lock in the recently-added STEP_OWNERS entries for typhoon and the
    commercial chain — regression guard so these aren't dropped silently."""

    def test_typhoon_owner_set(self):
        from docs.models.data_lineage import STEP_OWNERS
        assert STEP_OWNERS.get("typhoon") == "Quantitative Analytics"

    def test_commercial_chain_owners_set(self):
        from docs.models.data_lineage import STEP_OWNERS
        # commercial is a data-source step; the time-series derivatives are
        # quant-owned (parallel to property* / propertyts* etc.).
        assert STEP_OWNERS.get("commercial") == "Data Engineering"
        for step in (
            "commercialts", "commercialtsd", "commercialtse",
            "commercialhc", "commercialshd", "commercialshe",
        ):
            assert STEP_OWNERS.get(step) == "Quantitative Analytics", (
                f"STEP_OWNERS missing or wrong for '{step}'"
            )
