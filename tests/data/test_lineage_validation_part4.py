# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""
Unit tests for lineage validation — completeness, full chain (part 4).
"""

from unittest.mock import patch

import pytest

from tests.data.conftest import make_manifest as _make_manifest


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
