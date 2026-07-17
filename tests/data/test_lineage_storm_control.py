# Copyright (c) 2022-2026 MKM Research Labs.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Lineage tests for storm_control.json — external config input tracking.

Verifies that:
- storm_control.json is declared as an input to the stressm step
- storm_control.json is registered as an EXTERNAL_INPUT
- Freshness checks detect changes to storm_control.json on disk
- The structural graph test allows external inputs
"""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from tests.data.conftest import make_manifest as _make_manifest


# ---------------------------------------------------------------------------
# STEP_IO registration
# ---------------------------------------------------------------------------

class TestStormControlInStepIO:
    """storm_control.json must be declared in lineage topology."""

    def test_stressm_inputs_include_storm_control(self):
        """manifest.py: stressm step must list storm_control.json as input."""
        from lineage.manifest import STEP_IO
        inputs = STEP_IO["stressm"]["inputs"]
        assert "storm_control.json" in inputs, (
            f"storm_control.json missing from stressm inputs: {inputs}"
        )

    def test_storm_control_is_external_input(self):
        """manifest.py: storm_control.json must be in EXTERNAL_INPUTS."""
        from lineage.manifest import EXTERNAL_INPUTS
        assert "storm_control.json" in EXTERNAL_INPUTS

    def test_external_inputs_not_produced_by_any_step(self):
        """No pipeline step should list an external input as an output."""
        from lineage.manifest import EXTERNAL_INPUTS, STEP_IO
        for ext in EXTERNAL_INPUTS:
            for step_name, io in STEP_IO.items():
                assert ext not in io["outputs"], (
                    f"External input '{ext}' is listed as output of "
                    f"step '{step_name}' — it should not be produced "
                    f"by any pipeline step."
                )


# ---------------------------------------------------------------------------
# Freshness — external input handling
# ---------------------------------------------------------------------------

class TestStormControlFreshness:
    """Freshness check must compare storm_control.json against disk."""

    def test_fresh_when_hash_unchanged(self, tmp_path):
        """External input is fresh when disk hash matches recorded hash."""
        from lineage.validation import freshness as _freshness_mod
        from lineage.manifest import hash_file

        # Write storm_control.json
        sc_path = tmp_path / "storm_control.json"
        sc_path.write_text('{"version": "1.0.0", "sections": {}}')
        sc_hash = hash_file(sc_path)

        # Write other stressm inputs
        (tmp_path / "gauge.json").write_text('{}')
        gaugehd = tmp_path / "gaugehd"
        gaugehd.mkdir()
        (gaugehd / "g.json").write_text('{}')
        from lineage.manifest import hash_directory
        gauge_hash = hash_file(tmp_path / "gauge.json")
        gaugehd_hash, _ = hash_directory(gaugehd)

        manifest = _make_manifest({
            "synthetic_gauges": {
                "inputs": {},
                "outputs": {"gauge.json": {"hash": gauge_hash}},
            },
            "gaugehd": {
                "inputs": {},
                "outputs": {"gaugehd/": {"hash": gaugehd_hash}},
            },
            "stressm": {
                "inputs": {
                    "storm_control.json": {"hash": sc_hash},
                    "gauge.json": {"hash": gauge_hash},
                    "gaugehd/": {"hash": gaugehd_hash},
                },
                "outputs": {"gaugets/": {"hash": "xxx"}},
            },
        })

        import lineage.validation as _val
        with patch.object(_freshness_mod, "_resolve_data_dir",
                          return_value=tmp_path), \
             patch.object(_val, "load_manifest",
                          return_value=manifest):
            ok, issues = _freshness_mod.check_inputs_fresh("stressm")

        storm_control_issues = [i for i in issues if "storm_control" in i]
        assert not storm_control_issues, (
            f"Unexpected storm_control issues: {storm_control_issues}"
        )

    def test_stale_when_hash_changed(self, tmp_path):
        """External input is stale when disk hash differs from recorded."""
        from lineage.validation import freshness as _freshness_mod

        # Write storm_control.json with new content
        sc_path = tmp_path / "storm_control.json"
        sc_path.write_text('{"version": "2.0.0", "sections": {}}')

        # Also write gauge.json + gaugehd/ so the other stressm inputs
        # don't generate noise (they need producers in the manifest)
        (tmp_path / "gauge.json").write_text('{}')
        gaugehd = tmp_path / "gaugehd"
        gaugehd.mkdir()
        (gaugehd / "g.json").write_text('{}')

        from lineage.manifest import hash_file, hash_directory
        gauge_hash = hash_file(tmp_path / "gauge.json")
        gaugehd_hash, _ = hash_directory(gaugehd)

        manifest = _make_manifest({
            "synthetic_gauges": {
                "inputs": {},
                "outputs": {"gauge.json": {"hash": gauge_hash}},
            },
            "gaugehd": {
                "inputs": {},
                "outputs": {"gaugehd/": {"hash": gaugehd_hash}},
            },
            "stressm": {
                "inputs": {
                    "storm_control.json": {"hash": "old_hash_abc123"},
                    "gauge.json": {"hash": gauge_hash},
                    "gaugehd/": {"hash": gaugehd_hash},
                },
                "outputs": {"gaugets/": {"hash": "xxx"}},
            },
        })

        import lineage.validation as _val
        with patch.object(_freshness_mod, "_resolve_data_dir",
                          return_value=tmp_path), \
             patch.object(_val, "load_manifest",
                          return_value=manifest):
            ok, issues = _freshness_mod.check_inputs_fresh("stressm")

        storm_control_issues = [i for i in issues if "storm_control" in i]
        assert storm_control_issues, (
            f"Expected staleness issue for storm_control.json but got: {issues}"
        )
        assert "changed on disk" in storm_control_issues[0].lower()

    def test_skip_when_never_recorded(self, tmp_path):
        """If storm_control.json hash was never recorded, skip (no error)."""
        from lineage.validation import freshness as _freshness_mod

        # Write other stressm inputs
        (tmp_path / "gauge.json").write_text('{}')
        gaugehd = tmp_path / "gaugehd"
        gaugehd.mkdir()
        (gaugehd / "g.json").write_text('{}')
        from lineage.manifest import hash_file, hash_directory
        gauge_hash = hash_file(tmp_path / "gauge.json")
        gaugehd_hash, _ = hash_directory(gaugehd)

        manifest = _make_manifest({
            "synthetic_gauges": {
                "inputs": {},
                "outputs": {"gauge.json": {"hash": gauge_hash}},
            },
            "gaugehd": {
                "inputs": {},
                "outputs": {"gaugehd/": {"hash": gaugehd_hash}},
            },
            "stressm": {
                "inputs": {
                    "gauge.json": {"hash": gauge_hash},
                    "gaugehd/": {"hash": gaugehd_hash},
                },  # no storm_control.json hash recorded
                "outputs": {"gaugets/": {"hash": "xxx"}},
            },
        })

        import lineage.validation as _val
        with patch.object(_freshness_mod, "_resolve_data_dir",
                          return_value=tmp_path), \
             patch.object(_val, "load_manifest",
                          return_value=manifest):
            ok, issues = _freshness_mod.check_inputs_fresh("stressm")

        storm_control_issues = [i for i in issues if "storm_control" in i]
        assert not storm_control_issues


# ---------------------------------------------------------------------------
# Hash recording
# ---------------------------------------------------------------------------

class TestStormControlHashing:
    """storm_control.json should be hashable for lineage recording."""

    def test_hash_storm_control_json(self, tmp_path):
        """hash_file produces valid SHA-256 for storm_control.json."""
        from lineage.manifest import hash_file
        sc_path = tmp_path / "storm_control.json"
        content = json.dumps({"version": "1.0.0", "sections": {}})
        sc_path.write_text(content)
        h = hash_file(sc_path)
        assert len(h) == 64  # SHA-256 hex
        assert h.isalnum()

    def test_hash_changes_with_content(self, tmp_path):
        """Different content should produce different hashes."""
        from lineage.manifest import hash_file
        sc_path = tmp_path / "storm_control.json"
        sc_path.write_text('{"version": "1.0.0"}')
        h1 = hash_file(sc_path)
        sc_path.write_text('{"version": "2.0.0"}')
        h2 = hash_file(sc_path)
        assert h1 != h2

    def test_pre_hash_includes_storm_control(self, tmp_path):
        """pre_hash_inputs should hash storm_control.json when present."""
        from lineage.manifest import pre_hash_inputs
        sc_path = tmp_path / "storm_control.json"
        sc_path.write_text('{"version": "1.0.0"}')
        result = pre_hash_inputs({"storm_control.json": str(sc_path)})
        assert "storm_control.json" in result
        assert result["storm_control.json"]["type"] == "file"
        assert len(result["storm_control.json"]["hash"]) == 64
