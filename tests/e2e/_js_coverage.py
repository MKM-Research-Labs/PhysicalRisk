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


# A fragment must be at least this long before we trust a text match. Short
# files could appear verbatim inside a longer one and be attributed twice.
_MIN_MATCH_BYTES = 200


def shipped_modules():
    """``{repo-relative path: inlined text}`` for every served JS module.

    The text is what the page actually receives — the loader strips each file's
    leading ``//`` licence block before inlining — so it is matched against the
    blob in exactly the form it was embedded.
    """
    from config import config
    from visual.interactivity._jsbundle import _strip_inlined_header

    js_dir = pathlib.Path(config.get_static_dir()) / "js"
    root = pathlib.Path(config.get_project_root())
    out = {}
    for f in sorted(js_dir.rglob("*.js")):
        try:
            text = _strip_inlined_header(f.read_text(encoding="utf-8"))
        except OSError:
            continue
        if len(text) >= _MIN_MATCH_BYTES:
            out[str(f.relative_to(root))] = text
    return out


def map_inline_to_modules(source, intervals, modules):
    """Attribute an inline blob's covered ranges to the modules inside it.

    The console inlines its whole front end, so V8 reports one anonymous script
    rather than 126 files and coverage cannot be attributed by URL. Each module
    is located by its own text within the blob, and the blob's covered
    intervals are clipped to that span and rebased to module-relative offsets.

    Returns ``{path: {"covered": [[s, e], ...], "total": int}}``. Modules that
    do not appear verbatim — templated fragments whose placeholders are
    substituted at render time — are simply absent, never guessed at.
    """
    found = {}
    for path, text in modules.items():
        start = source.find(text)
        if start == -1:
            continue
        end = start + len(text)
        rel = [(max(s, start) - start, min(e, end) - start)
               for s, e in intervals if e > start and s < end]
        found[path] = {"covered": [list(i) for i in merge_intervals(rel)],
                       "total": len(text)}
    return found


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
            # Needed for Debugger.getScriptSource, which is how an inline
            # blob is mapped back to the modules concatenated into it.
            self._cdp.send("Debugger.enable")
            self._cdp.send(
                "Profiler.startPreciseCoverage",
                {"callCount": False, "detailed": True},
            )
            return True
        except Exception:
            self._cdp = None
            return False

    def _script_source(self, script_id):
        """Source text of a parsed script, or "" if it cannot be fetched."""
        if not script_id:
            return ""
        try:
            return self._cdp.send(
                "Debugger.getScriptSource", {"scriptId": str(script_id)}
            ).get("scriptSource", "")
        except Exception:
            return ""

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

        try:
            modules = shipped_modules()
        except Exception:
            modules = {}

        out = {}
        for entry in result.get("result", []):
            path = normalise_url(entry.get("url", ""), page_url,
                                 str(entry.get("scriptId", "")))
            intervals, total = covered_intervals(entry)
            if total <= 0:
                continue

            # An inline blob is the console's whole front end concatenated.
            # Resolve it to the modules inside rather than reporting one
            # anonymous script that can never be attributed to a file.
            if path.startswith("<inline") and modules:
                source = self._script_source(entry.get("scriptId"))
                if source:
                    for mod, rec in map_inline_to_modules(
                            source, intervals, modules).items():
                        prev = out.setdefault(mod, {"covered": [], "total": 0})
                        prev["covered"] = merge_intervals(
                            [tuple(i) for i in prev["covered"]]
                            + [tuple(i) for i in rec["covered"]])
                        prev["total"] = max(prev["total"], rec["total"])

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
