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
Unit tests for lineage validation — staleness, prerequisites (part 1).
"""

from unittest.mock import patch

import pytest

from tests.data.conftest import make_manifest as _make_manifest


class TestCheckInputsFresh:
    """check_inputs_fresh: detect stale inputs."""

    def test_unknown_step(self):
        from lineage.validation import check_inputs_fresh
        with patch("lineage.validation.load_manifest", return_value=_make_manifest({})):
            ok, issues = check_inputs_fresh("nonexistent_step")
        assert not ok
        assert "Unknown step" in issues[0]

    def test_root_step_always_fresh(self):
        """Root steps (gauges, counterparties) have no inputs → always fresh."""
        from lineage.validation import check_inputs_fresh
        manifest = _make_manifest({"gauges": {"outputs": {"gauge.json": {"hash": "abc"}}}})
        with patch("lineage.validation.load_manifest", return_value=manifest):
            ok, issues = check_inputs_fresh("gauges")
        assert ok
        assert issues == []

    def test_fresh_when_hashes_match(self):
        from lineage.validation import check_inputs_fresh
        # properties' producer of gauge.json is synthetic_gauges (latest writer)
        manifest = _make_manifest({
            "gauges": {
                "outputs": {"gauge.json": {"hash": "abc000"}},
            },
            "synthetic_gauges": {
                "inputs": {"gauge.json": {"hash": "abc000"}},
                "outputs": {"gauge.json": {"hash": "abc123"}},
            },
            "properties": {
                "inputs": {"gauge.json": {"hash": "abc123"}},
                "outputs": {"property.json": {"hash": "def456"}},
            },
        })
        with patch("lineage.validation.load_manifest", return_value=manifest):
            ok, issues = check_inputs_fresh("properties")
        assert ok
        assert issues == []

    def test_stale_when_hashes_differ(self):
        from lineage.validation import check_inputs_fresh
        manifest = _make_manifest({
            "gauges": {
                "outputs": {"gauge.json": {"hash": "v0"}},
            },
            "synthetic_gauges": {
                "inputs": {"gauge.json": {"hash": "v0"}},
                "outputs": {"gauge.json": {"hash": "new_hash_12345"}},
            },
            "properties": {
                "inputs": {"gauge.json": {"hash": "old_hash_12345"}},
                "outputs": {"property.json": {"hash": "xxx"}},
            },
        })
        with patch("lineage.validation.load_manifest", return_value=manifest):
            ok, issues = check_inputs_fresh("properties")
        assert not ok
        assert "stale" in issues[0].lower()

    def test_producer_never_run(self):
        from lineage.validation import check_inputs_fresh
        manifest = _make_manifest({
            "properties": {
                "inputs": {"gauge.json": {"hash": "abc"}},
                "outputs": {},
            },
        })
        with patch("lineage.validation.load_manifest", return_value=manifest):
            ok, issues = check_inputs_fresh("properties")
        assert not ok
        assert "never run" in issues[0].lower()

    def test_consumer_never_run(self):
        from lineage.validation import check_inputs_fresh
        manifest = _make_manifest({
            "gauges": {
                "outputs": {"gauge.json": {"hash": "abc123"}},
            },
        })
        with patch("lineage.validation.load_manifest", return_value=manifest):
            ok, issues = check_inputs_fresh("properties")
        assert not ok
        assert "never run" in issues[0].lower()

    def test_no_hash_recorded_for_producer_output(self):
        from lineage.validation import check_inputs_fresh
        manifest = _make_manifest({
            "gauges": {
                "outputs": {"gauge.json": {"hash": "abc"}},
            },
            "synthetic_gauges": {
                "outputs": {"gauge.json": {"type": "file"}},  # no hash key
            },
            "properties": {
                "inputs": {"gauge.json": {"hash": "abc"}},
                "outputs": {},
            },
        })
        with patch("lineage.validation.load_manifest", return_value=manifest):
            ok, issues = check_inputs_fresh("properties")
        assert not ok
        assert "No hash recorded" in issues[0]

    def test_consumer_has_no_hash_for_input(self):
        from lineage.validation import check_inputs_fresh
        manifest = _make_manifest({
            "gauges": {
                "outputs": {"gauge.json": {"hash": "abc000"}},
            },
            "synthetic_gauges": {
                "outputs": {"gauge.json": {"hash": "abc123"}},
            },
            "properties": {
                "inputs": {"gauge.json": {}},  # empty — no hash
                "outputs": {},
            },
        })
        with patch("lineage.validation.load_manifest", return_value=manifest):
            ok, issues = check_inputs_fresh("properties")
        assert not ok
        assert "no recorded hash" in issues[0].lower()


class TestCheckStepPrerequisites:
    """check_step_prerequisites: all upstream steps must exist."""

    def test_all_present(self):
        from lineage.validation import check_step_prerequisites
        # properties depends on synthetic_gauges (which depends on gauges)
        manifest = _make_manifest({
            "gauges": {}, "synthetic_gauges": {}, "properties": {},
        })
        with patch("lineage.validation.load_manifest", return_value=manifest):
            ok, missing = check_step_prerequisites("properties")
        assert ok
        assert missing == []

    def test_missing_upstream(self):
        from lineage.validation import check_step_prerequisites
        manifest = _make_manifest({})
        with patch("lineage.validation.load_manifest", return_value=manifest):
            ok, missing = check_step_prerequisites("properties")
        assert not ok
        # properties' direct upstream is synthetic_gauges after the fix
        assert "synthetic_gauges" in missing


class TestGetStaleDownstream:
    """get_stale_downstream: BFS over dependency graph."""

    def test_gauges_affects_many(self):
        from lineage.validation import get_stale_downstream
        downstream = get_stale_downstream("gauges")
        assert "properties" in downstream
        assert "gaugehd" in downstream
        assert "stressm" in downstream

    def test_leaf_has_no_downstream(self):
        from lineage.validation import get_stale_downstream
        downstream = get_stale_downstream("blotter")
        assert downstream == []

    def test_mid_chain(self):
        from lineage.validation import get_stale_downstream
        downstream = get_stale_downstream("stressm")
        assert "hazard" in downstream
        assert "propertyts" in downstream
