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

"""Unit tests for the e2e JS coverage collector and report tool.

These cover the pure functions — V8 range reduction, interval union and URL
normalisation. The browser-attached parts are exercised by the e2e run itself.
"""

import json

import pytest

from tests.e2e._js_coverage import (
    covered_intervals,
    enabled,
    merge_intervals,
    normalise_url,
)
from tools.coverage.js_coverage_report import build_report, load_sessions


class TestMergeIntervals:
    def test_empty(self):
        assert merge_intervals([]) == []

    def test_disjoint_preserved(self):
        assert merge_intervals([(0, 5), (10, 15)]) == [(0, 5), (10, 15)]

    def test_overlapping_merged(self):
        assert merge_intervals([(0, 10), (5, 15)]) == [(0, 15)]

    def test_adjacent_merged(self):
        assert merge_intervals([(0, 5), (5, 10)]) == [(0, 10)]

    def test_nested_absorbed(self):
        assert merge_intervals([(0, 20), (5, 10)]) == [(0, 20)]

    def test_unsorted_input(self):
        assert merge_intervals([(10, 15), (0, 5), (3, 11)]) == [(0, 15)]


class TestCoveredIntervals:
    def test_no_functions(self):
        assert covered_intervals({}) == ([], 0)

    def test_fully_covered(self):
        entry = {"functions": [
            {"ranges": [{"startOffset": 0, "endOffset": 100, "count": 3}]}]}
        assert covered_intervals(entry) == ([(0, 100)], 100)

    def test_uncovered_yields_nothing(self):
        entry = {"functions": [
            {"ranges": [{"startOffset": 0, "endOffset": 100, "count": 0}]}]}
        assert covered_intervals(entry) == ([], 100)

    def test_nested_zero_carves_hole(self):
        """V8 nests ranges: a count==0 child is an uncovered hole in its
        covered parent. The inner range must win."""
        entry = {"functions": [{"ranges": [
            {"startOffset": 0, "endOffset": 100, "count": 1},
            {"startOffset": 40, "endOffset": 60, "count": 0},
        ]}]}
        intervals, total = covered_intervals(entry)
        assert total == 100
        assert intervals == [(0, 40), (60, 100)]

    def test_covered_child_inside_uncovered_parent(self):
        entry = {"functions": [{"ranges": [
            {"startOffset": 0, "endOffset": 100, "count": 0},
            {"startOffset": 20, "endOffset": 30, "count": 5},
        ]}]}
        assert covered_intervals(entry) == ([(20, 30)], 100)

    def test_ranges_clamped_to_total(self):
        entry = {"functions": [{"ranges": [
            {"startOffset": 0, "endOffset": 50, "count": 1},
            {"startOffset": -10, "endOffset": 20, "count": 1},
        ]}]}
        intervals, total = covered_intervals(entry)
        assert total == 50
        assert intervals == [(0, 50)]


class TestNormaliseUrl:
    def test_served_module(self):
        assert normalise_url(
            "http://127.0.0.1:5013/static/js/property/phc_prs_tables.js"
        ) == "src/static/js/property/phc_prs_tables.js"

    def test_query_string_stripped(self):
        assert normalise_url(
            "http://x/static/js/theme.js?v=9"
        ) == "src/static/js/theme.js"

    def test_empty_is_inline(self):
        assert normalise_url("") == "<inline>"

    def test_page_url_is_inline(self):
        """The Folium console inlines much of its front end; those scripts
        report the page URL and must not be blamed on a served module."""
        page = "http://127.0.0.1:5013/visualization"
        assert normalise_url(page, page) == "<inline>"

    def test_external_bucketed(self):
        assert normalise_url(
            "https://cdn.example.com/leaflet.js"
        ) == "<external:https://cdn.example.com/leaflet.js>"


class TestEnabled:
    @pytest.mark.parametrize("val,want", [
        ("1", True), ("true", True), ("YES", True),
        ("0", False), ("", False), ("no", False),
    ])
    def test_flag(self, monkeypatch, val, want):
        monkeypatch.setenv("MKM_E2E_JS_COVERAGE", val)
        assert enabled() is want

    def test_absent(self, monkeypatch):
        monkeypatch.delenv("MKM_E2E_JS_COVERAGE", raising=False)
        assert enabled() is False


class TestReport:
    def test_no_sessions(self, tmp_path):
        merged, n = load_sessions(tmp_path)
        assert merged == {} and n == 0

    def test_bad_json_skipped(self, tmp_path):
        (tmp_path / "broken.json").write_text("{not json")
        merged, n = load_sessions(tmp_path)
        assert merged == {} and n == 1

    def test_union_across_sessions(self, tmp_path):
        """A byte executed in two batches counts once."""
        (tmp_path / "a.json").write_text(json.dumps(
            {"src/static/js/x.js": {"covered": [[0, 50]], "total": 100}}))
        (tmp_path / "b.json").write_text(json.dumps(
            {"src/static/js/x.js": {"covered": [[40, 90]], "total": 100}}))
        merged, n = load_sessions(tmp_path)
        assert n == 2
        assert merged["src/static/js/x.js"] == ([(0, 90)], 100)

    def test_never_loaded_files_counted(self, tmp_path):
        """The whole point: modules V8 never reported must still land in the
        denominator at 0%, or the percentage flatters itself."""
        rep = build_report(tmp_path)
        assert rep["files"] > 0
        assert rep["files_never_loaded"] == rep["files"]
        assert rep["pct"] == 0.0
