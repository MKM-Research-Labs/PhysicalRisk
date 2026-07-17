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
Unit tests for lineage prerequisite resolution — _outputs_exist()
and resolve_prerequisites() basic tests.
"""

from unittest.mock import patch

import pytest

from tests.data.conftest import make_manifest as _make_manifest


# ---------------------------------------------------------------------------
# _outputs_exist
# ---------------------------------------------------------------------------

class TestOutputsExist:
    """_outputs_exist: check whether step outputs exist on disk."""

    def test_file_output_present(self, tmp_path):
        from lineage.validation import _outputs_exist
        (tmp_path / "gauge.json").write_text("{}")
        assert _outputs_exist("gauges", tmp_path)

    def test_file_output_missing(self, tmp_path):
        from lineage.validation import _outputs_exist
        assert not _outputs_exist("gauges", tmp_path)

    def test_dir_output_present_non_empty(self, tmp_path):
        from lineage.validation import _outputs_exist
        d = tmp_path / "gaugets"
        d.mkdir()
        (d / "GAUGE-001.json").write_text("{}")
        # stressm has multiple outputs; create them all
        (tmp_path / "stress_storms").mkdir()
        (tmp_path / "stress_storms" / "_index.json").write_text("{}")
        (tmp_path / "storm_sequences.json").write_text("{}")
        sg_dir = tmp_path / "sequence_gauge"
        sg_dir.mkdir()
        (sg_dir / "_index.json").write_text("{}")
        (sg_dir / "GAUGE-001.json").write_text("{}")
        assert _outputs_exist("stressm", tmp_path)

    def test_dir_output_empty(self, tmp_path):
        from lineage.validation import _outputs_exist
        (tmp_path / "gaugets").mkdir()
        (tmp_path / "stress_storms").mkdir()
        (tmp_path / "storm_sequences.json").write_text("{}")
        sg_dir = tmp_path / "sequence_gauge"
        sg_dir.mkdir()
        # sequence_gauge/ is empty -> should fail
        assert not _outputs_exist("stressm", tmp_path)

    def test_dir_output_missing(self, tmp_path):
        from lineage.validation import _outputs_exist
        # No gaugets/ directory at all
        assert not _outputs_exist("stressm", tmp_path)

    def test_unknown_step(self, tmp_path):
        from lineage.validation import _outputs_exist
        assert not _outputs_exist("nonexistent", tmp_path)

    def test_partial_outputs_missing(self, tmp_path):
        from lineage.validation import _outputs_exist
        # stressm needs gaugets/, stress_storms/, storm_sequences.json,
        # sequence_gauge/ -- only provide some
        d = tmp_path / "gaugets"
        d.mkdir()
        (d / "GAUGE-001.json").write_text("{}")
        # Missing stress_storms/, storm_sequences.json, etc.
        assert not _outputs_exist("stressm", tmp_path)


# ---------------------------------------------------------------------------
# resolve_prerequisites — basic
# ---------------------------------------------------------------------------

class TestResolvePrerequisites:
    """resolve_prerequisites: detect stale/missing upstream steps."""

    def test_no_deps_returns_empty(self):
        """Root steps (gauges) have no prerequisites."""
        from lineage.validation import resolve_prerequisites
        manifest = _make_manifest({
            "gauges": {"outputs": {"gauge.json": {"hash": "abc"}}}
        })
        with patch("lineage.validation.load_manifest", return_value=manifest):
            result = resolve_prerequisites(["gauges"])
        assert result == []

    def test_all_fresh_returns_empty(self):
        """If all prerequisites are fresh, returns empty list."""
        from lineage.validation import resolve_prerequisites
        manifest = _make_manifest({
            "gauges": {
                "inputs": {},
                "outputs": {"gauge.json": {"hash": "aaa"}},
            },
            "synthetic_gauges": {
                "inputs": {"gauge.json": {"hash": "aaa"}},
                "outputs": {"gauge.json": {"hash": "aaa2"}},
            },
            "properties": {
                "inputs": {"gauge.json": {"hash": "aaa2"}},
                "outputs": {"property.json": {"hash": "bbb"}},
            },
            "gaugehd": {
                "inputs": {"gauge.json": {"hash": "aaa2"}},
                "outputs": {"gaugehd/": {"hash": "ccc"}},
            },
            "stressm": {
                "inputs": {
                    "gauge.json": {"hash": "aaa2"},
                    "gaugehd/": {"hash": "ccc"},
                },
                "outputs": {
                    "gaugets/": {"hash": "ddd"},
                    "stress_storms/": {"hash": "eee"},
                    "storm_sequences.json": {"hash": "fff"},
                    "sequence_gauge/": {"hash": "ggg"},
                },
            },
            "hazard": {
                "inputs": {
                    "gauge.json": {"hash": "aaa2"},
                    "gaugets/": {"hash": "ddd"},
                },
                "outputs": {
                    "gaugehc.json": {"hash": "hhh"},
                    "gaugets/": {"hash": "ddd2"},
                },
            },
        })
        with patch("lineage.validation.load_manifest", return_value=manifest):
            result = resolve_prerequisites(["propertyts"])
        assert result == []

    def test_missing_upstream_no_files(self, tmp_path):
        """Upstream never recorded and outputs missing -> needs to run."""
        from lineage.validation import resolve_prerequisites
        manifest = _make_manifest({})  # nothing ever run
        with patch("lineage.validation.load_manifest", return_value=manifest):
            result = resolve_prerequisites(["properties"], data_dir=tmp_path)
        assert "gauges" in result

    def test_missing_upstream_files_exist(self, tmp_path):
        """Upstream never recorded but outputs exist -> skip it."""
        from lineage.validation import resolve_prerequisites
        manifest = _make_manifest({})
        # Create gauge.json so gauges is considered OK
        (tmp_path / "gauge.json").write_text("{}")
        with patch("lineage.validation.load_manifest", return_value=manifest):
            result = resolve_prerequisites(["properties"], data_dir=tmp_path)
        assert "gauges" not in result

    def test_stale_upstream(self):
        """Upstream recorded but inputs stale -> needs to run."""
        from lineage.validation import resolve_prerequisites
        manifest = _make_manifest({
            "gauges": {
                "outputs": {"gauge.json": {"hash": "new_hash"}},
            },
            "properties": {
                "inputs": {"gauge.json": {"hash": "old_hash"}},
                "outputs": {"property.json": {"hash": "ppp"}},
            },
        })
        with patch("lineage.validation.load_manifest", return_value=manifest):
            result = resolve_prerequisites(["propertyts"])
        # properties is stale, so it needs to re-run
        assert "properties" in result

    def test_transitive_chain(self, tmp_path):
        """Deep chain: if gauges missing, all downstream prereqs needed."""
        from lineage.validation import resolve_prerequisites
        manifest = _make_manifest({})  # nothing ever run
        with patch("lineage.validation.load_manifest", return_value=manifest):
            result = resolve_prerequisites(["propertyts"], data_dir=tmp_path)
        # propertyts depends on properties + hazard
        # hazard depends on synthetic_gauges + stressm
        # stressm depends on synthetic_gauges + gaugehd
        # gaugehd depends on gauges + synthetic_gauges
        assert "gauges" in result
        assert "properties" in result
        assert "gaugehd" in result
        assert "stressm" in result
        assert "hazard" in result
        # Target itself should NOT be in prerequisites
        assert "propertyts" not in result

    def test_topological_order(self, tmp_path):
        """Prerequisites are returned in valid topological order."""
        from lineage.validation import resolve_prerequisites
        manifest = _make_manifest({})
        with patch("lineage.validation.load_manifest", return_value=manifest):
            result = resolve_prerequisites(["propertyts"], data_dir=tmp_path)
        # gauges must come before properties, gaugehd, stressm
        if "gauges" in result and "properties" in result:
            assert result.index("gauges") < result.index("properties")
        if "gauges" in result and "gaugehd" in result:
            assert result.index("gauges") < result.index("gaugehd")
        if "gaugehd" in result and "stressm" in result:
            assert result.index("gaugehd") < result.index("stressm")

    def test_unknown_step_returns_empty(self):
        """Unknown step returns empty list."""
        from lineage.validation import resolve_prerequisites
        with patch("lineage.validation.load_manifest", return_value=_make_manifest({})):
            result = resolve_prerequisites(["nonexistent_step"])
        assert result == []

    def test_multiple_targets(self, tmp_path):
        """Multiple targets: prerequisites are union of both."""
        from lineage.validation import resolve_prerequisites
        manifest = _make_manifest({})
        with patch("lineage.validation.load_manifest", return_value=manifest):
            result = resolve_prerequisites(
                ["propertyts", "blotter"], data_dir=tmp_path
            )
        # blotter needs hazard + counterparties
        # hazard needs gauges + stressm
        # propertyts needs properties + stressm
        assert "gauges" in result
        assert "counterparties" in result

    def test_target_not_in_prerequisites(self, tmp_path):
        """Target steps themselves should never appear in prerequisites."""
        from lineage.validation import resolve_prerequisites
        manifest = _make_manifest({})
        with patch("lineage.validation.load_manifest", return_value=manifest):
            result = resolve_prerequisites(["propertyts"], data_dir=tmp_path)
        assert "propertyts" not in result

    def test_no_data_dir_fallback(self):
        """Without data_dir, missing manifest entries -> prerequisite needed."""
        from lineage.validation import resolve_prerequisites
        manifest = _make_manifest({})
        with patch("lineage.validation.load_manifest", return_value=manifest):
            result = resolve_prerequisites(["properties"], data_dir=None)
        # gauges never ran, no data_dir to check files -> must run
        assert "gauges" in result
