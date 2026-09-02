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
    map_inline_to_modules,
    merge_intervals,
    normalise_url,
    shipped_modules,
)
from docs.models.js_coverage.report import build_report, load_sessions


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
        """The Folium console inlines its front end; those scripts report the
        page URL and must not be blamed on a served module."""
        page = "http://127.0.0.1:5013/visualization"
        assert normalise_url(page, page) == "<inline>"

    def test_inline_scripts_are_kept_apart_by_script_id(self):
        """Byte offsets are per-script. Bucketing every inline script under one
        key unions incomparable address spaces — the first real run did that
        and produced a single 769,420-byte interval that read as 100%."""
        page = "http://127.0.0.1:5013/visualization"
        a = normalise_url(page, page, "3")
        b = normalise_url(page, page, "8")
        assert a != b, "distinct inline scripts must not share a bucket"
        assert a == "<inline#3>" and b == "<inline#8>"

    def test_served_module_ignores_script_id(self):
        """A real file is identified by path; its script id is irrelevant."""
        url = "http://x/static/js/theme.js"
        assert normalise_url(url, "", "42") == "src/static/js/theme.js"

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


class TestInlineOffsetMapping:
    """The console inlines its whole front end into one anonymous script, so
    coverage can only reach a file by locating that file's text in the blob."""

    MOD_A = "function alpha() { return 1; }\n" + "// pad alpha\n" * 40
    MOD_B = "function beta() { return 2; }\n" + "// pad beta\n" * 40

    def _blob(self):
        return "HEADER;\n" + self.MOD_A + self.MOD_B + "FOOTER;\n"

    def test_attributes_a_covered_span_to_the_right_module(self):
        blob = self._blob()
        start = blob.find(self.MOD_A)
        # the whole of module A executed, nothing else
        out = map_inline_to_modules(
            blob, [(start, start + len(self.MOD_A))],
            {"a.js": self.MOD_A, "b.js": self.MOD_B})
        assert out["a.js"]["covered"] == [[0, len(self.MOD_A)]]
        assert out["a.js"]["total"] == len(self.MOD_A)
        assert out["b.js"]["covered"] == []

    def test_offsets_are_rebased_to_the_module(self):
        """A span at blob offset N inside a module starting at K must report
        N-K, or every module would look covered from its first byte."""
        blob = self._blob()
        start = blob.find(self.MOD_B)
        out = map_inline_to_modules(
            blob, [(start + 10, start + 20)], {"b.js": self.MOD_B})
        assert out["b.js"]["covered"] == [[10, 20]]

    def test_span_crossing_a_boundary_is_clipped(self):
        """A covered range spanning two modules must not credit either with
        bytes belonging to the other."""
        blob = self._blob()
        a0 = blob.find(self.MOD_A)
        b0 = blob.find(self.MOD_B)
        out = map_inline_to_modules(
            blob, [(a0 + len(self.MOD_A) - 5, b0 + 5)],
            {"a.js": self.MOD_A, "b.js": self.MOD_B})
        assert out["a.js"]["covered"] == [[len(self.MOD_A) - 5, len(self.MOD_A)]]
        assert out["b.js"]["covered"] == [[0, 5]]

    def test_absent_module_is_omitted_not_guessed(self):
        """Templated fragments are substituted at render time and never appear
        verbatim. They must be missing, not reported at zero."""
        out = map_inline_to_modules(
            self._blob(), [(0, 10)], {"missing.js": "nowhere to be found" * 20})
        assert "missing.js" not in out

    def test_shipped_modules_reads_the_served_tree(self):
        mods = shipped_modules()
        assert mods, "no served JS modules found"
        assert all(p.startswith("src/static/js/") for p in mods)
        # the loader strips the licence header before inlining, so the text we
        # match against must not carry it either
        assert not any(v.lstrip().startswith("// Copyright") for v in mods.values())
