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

"""Collect V8 precise JS coverage from the e2e browser session.

The e2e suite drives a real Chromium against the real front end, so a large
share of the 159 served JS modules executes during a run — but nothing has ever
measured it. Jest reports ~2% statement coverage, which is the *unit-test*
figure and says nothing about what e2e exercises.

This collector attaches a CDP session to the shared e2e page and asks V8 for
byte-range coverage (``Profiler.takePreciseCoverage``). Each batch writes its
own JSON; ``tools/coverage/js_coverage_report.py`` unions them into one report.

Opt-in via ``MKM_E2E_JS_COVERAGE=1`` — the profiler adds overhead and must not
perturb an ordinary run.

Byte ranges, not statements: V8 reports character offsets, so the figure is
"share of shipped bytes executed". It is not directly comparable to coverage.py
statement coverage, and must not be presented as if it were.
"""

import json
import os
import pathlib

ENV_FLAG = "MKM_E2E_JS_COVERAGE"


def enabled() -> bool:
    """True when JS coverage collection has been explicitly requested."""
    return os.environ.get(ENV_FLAG, "").strip().lower() in {"1", "true", "yes"}


def merge_intervals(intervals):
    """Merge overlapping/adjacent ``(start, end)`` pairs into a minimal set.

    Used both to compact one session's covered ranges and to union several
    sessions together, so a byte counts once however many batches touched it.
    """
    if not intervals:
        return []
    ordered = sorted(intervals)
    merged = [list(ordered[0])]
    for start, end in ordered[1:]:
        if start <= merged[-1][1]:
            if end > merged[-1][1]:
                merged[-1][1] = end
        else:
            merged.append([start, end])
    return [tuple(m) for m in merged]


def covered_intervals(entry):
    """Reduce one V8 script entry to its covered ``(start, end)`` byte ranges.

    V8 block coverage nests: a child range with ``count == 0`` carves an
    uncovered hole out of its covered parent. Sorting by ``(start asc, end
    desc)`` puts parents before their children, so writing marks in that order
    lets the innermost range win — which is what V8's semantics require.
    """
    ranges = []
    for fn in entry.get("functions", []):
        for r in fn.get("ranges", []):
            ranges.append((r["startOffset"], r["endOffset"], r["count"]))
    if not ranges:
        return [], 0

    total = max(end for _, end, _ in ranges)
    if total <= 0:
        return [], 0

    marks = bytearray(total)
    for start, end, count in sorted(ranges, key=lambda t: (t[0], -t[1])):
        start = max(0, min(start, total))
        end = max(0, min(end, total))
        if end > start:
            marks[start:end] = (b"\x01" if count > 0 else b"\x00") * (end - start)

    intervals, run_start = [], None
    for i, m in enumerate(marks):
        if m and run_start is None:
            run_start = i
        elif not m and run_start is not None:
            intervals.append((run_start, i))
            run_start = None
    if run_start is not None:
        intervals.append((run_start, total))
    return intervals, total


def normalise_url(url, page_url="", script_id=""):
    """Map a script URL to a repo-relative path, or a bucket name.

    Inline scripts report the *page* URL (the Folium console inlines its front
    end), so they cannot be attributed to a file. They must also be kept apart
    from EACH OTHER: byte offsets are per-script, so merging two inline scripts
    under one key unions incomparable address spaces. The first run of this
    collector did exactly that and reported a single interval spanning 769,420
    bytes — which read as 100% coverage and meant nothing. The script id keeps
    them distinct.
    """
    if not url:
        return f"<inline#{script_id}>" if script_id else "<inline>"
    marker = "/static/js/"
    idx = url.find(marker)
    if idx == -1:
        if page_url and url.split("?")[0] == page_url.split("?")[0]:
            return f"<inline#{script_id}>" if script_id else "<inline>"
        return f"<external:{url.split('?')[0]}>"
    return "src/static/js/" + url[idx + len(marker):].split("?")[0]


class JsCoverageCollector:
    """Attach V8 precise coverage to a Playwright page for one pytest session."""

    def __init__(self, page):
        self._page = page
        self._cdp = None

    def start(self):
        """Begin collecting. Never raises — coverage must not fail a run."""
        try:
            self._cdp = self._page.context.new_cdp_session(self._page)
            self._cdp.send("Profiler.enable")
            self._cdp.send(
                "Profiler.startPreciseCoverage",
                {"callCount": False, "detailed": True},
            )
            return True
        except Exception:
            self._cdp = None
            return False

    def collect(self):
        """Return ``{path: {"covered": [[s, e], ...], "total": int}}``."""
        if self._cdp is None:
            return {}
        try:
            result = self._cdp.send("Profiler.takePreciseCoverage")
            self._cdp.send("Profiler.stopPreciseCoverage")
        except Exception:
            return {}

        try:
            page_url = self._page.url
        except Exception:
            page_url = ""

        out = {}
        for entry in result.get("result", []):
            path = normalise_url(entry.get("url", ""), page_url,
                                 str(entry.get("scriptId", "")))
            intervals, total = covered_intervals(entry)
            if total <= 0:
                continue
            prev = out.setdefault(path, {"covered": [], "total": 0})
            prev["covered"] = merge_intervals(
                [tuple(i) for i in prev["covered"]] + intervals
            )
            prev["total"] = max(prev["total"], total)
        return {
            k: {"covered": [list(i) for i in v["covered"]], "total": v["total"]}
            for k, v in out.items()
        }

    def write(self, out_dir, name):
        """Write this session's coverage to ``out_dir/name.json``."""
        data = self.collect()
        if not data:
            return None
        path = pathlib.Path(out_dir)
        path.mkdir(parents=True, exist_ok=True)
        target = path / f"{name}.json"
        target.write_text(json.dumps(data, indent=1))
        return target
