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

"""Union per-batch e2e JS coverage into a single report.

The e2e suite runs as ~22 separate pytest sessions (``phys.py test --e2e``
batches three files at a time), each writing its own
``audit/e2e/js_coverage/session-<pid>.json``. This unions them so a byte
executed in any batch counts once.

**Inline resolution:** the console inlines its whole front end, so V8 reports
one anonymous script rather than 126 files. The collector locates each module's
text within that blob and rebases its covered ranges, which is what makes the
per-file numbers below possible at all. Any ``<inline#...>`` bucket that
survives is the residue nothing matched — templated fragments and third-party
snippets — and is reported separately rather than folded into the percentage.

**Why the shipped-file enumeration matters:** V8 only reports scripts the
browser actually loaded. A module never fetched by any test does not appear in
the profiler output at all — so a percentage computed over "scripts V8 told us
about" silently excludes the very files with no coverage, and reads far higher
than the truth. Every ``src/static/js/**/*.js`` is therefore seeded at zero
first, and profiler data is folded in on top.

Byte ranges, not statements: this measures the share of shipped bytes executed.
It is NOT comparable to coverage.py statement coverage — do not put the two
side by side without saying so.
"""

import argparse
import json
import pathlib
import sys

# Same bootstrap as the sibling generators (full_audit, data_lineage): these run
# as `python -m docs.models.<pkg>`, which does not put the repo root on sys.path.
ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from config import config  # noqa: E402
from tests.e2e._js_coverage import merge_intervals  # noqa: E402
DEFAULT_IN = config.get_output_dir() / "audit" / "e2e" / "js_coverage"
JS_DIR = ROOT / "src" / "static" / "js"

# Concat fragments, not standalone modules: the JS-300-line split emits these
# to be assembled by the Python loader, so they are never fetched as scripts
# and would otherwise sit at 0% for ever, dragging the denominator.
FRAGMENT_MARKERS = ("/template/_part", "/_part")


def shipped_files():
    """Every served JS module, as repo-relative paths, fragments excluded."""
    out = {}
    for p in sorted(JS_DIR.rglob("*.js")):
        rel = str(p.relative_to(ROOT))
        if any(m in "/" + rel for m in FRAGMENT_MARKERS):
            continue
        try:
            out[rel] = len(p.read_bytes())
        except OSError:
            continue
    return out


def load_sessions(in_dir):
    """Union every session JSON in *in_dir* into ``{path: (intervals, total)}``."""
    merged = {}
    files = sorted(pathlib.Path(in_dir).glob("*.json"))
    for f in files:
        try:
            data = json.loads(f.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        for path, rec in data.items():
            intervals = [tuple(i) for i in rec.get("covered", [])]
            total = rec.get("total", 0)
            prev_intervals, prev_total = merged.get(path, ([], 0))
            merged[path] = (
                merge_intervals(prev_intervals + intervals),
                max(prev_total, total),
            )
    return merged, len(files)


def build_report(in_dir):
    """Combine profiler output with the shipped-file list."""
    merged, n_sessions = load_sessions(in_dir)
    rows, buckets = [], {}

    for path, size in shipped_files().items():
        intervals, v8_total = merged.get(path, ([], 0))
        covered = sum(e - s for s, e in intervals)
        total = v8_total or size
        rows.append({
            "path": path,
            "covered": covered,
            "total": total,
            "pct": (100.0 * covered / total) if total else 0.0,
            "loaded": path in merged,
        })

    for path, (intervals, total) in merged.items():
        if path.startswith("<"):
            buckets[path] = {
                "covered": sum(e - s for s, e in intervals), "total": total,
            }

    rows.sort(key=lambda r: (r["pct"], -r["total"]))
    tot_cov = sum(r["covered"] for r in rows)
    tot_all = sum(r["total"] for r in rows)
    return {
        "sessions": n_sessions,
        "files": len(rows),
        "files_never_loaded": sum(1 for r in rows if not r["loaded"]),
        "covered_bytes": tot_cov,
        "total_bytes": tot_all,
        "pct": (100.0 * tot_cov / tot_all) if tot_all else 0.0,
        "rows": rows,
        "buckets": buckets,
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--in-dir", default=str(DEFAULT_IN))
    ap.add_argument("--json-out", default="")
    ap.add_argument("--top", type=int, default=25)
    args = ap.parse_args(argv)

    rep = build_report(args.in_dir)
    if rep["sessions"] == 0:
        print(f"No session data in {args.in_dir}.")
        print("Run: MKM_E2E_JS_COVERAGE=1 python phys.py test --e2e")
        return 1

    print(f"e2e JS coverage — {rep['sessions']} session(s), "
          f"{rep['files']} shipped modules")
    print(f"  {rep['covered_bytes']:,} / {rep['total_bytes']:,} bytes = "
          f"{rep['pct']:.2f}%")
    print(f"  never loaded by any test: {rep['files_never_loaded']} "
          f"of {rep['files']}")
    if rep["buckets"]:
        print("  unattributed residue (inline blobs, external CDN), "
              "excluded from the percentage above:")
        for name, b in sorted(rep["buckets"].items()):
            print(f"    {name}: {b['covered']:,} / {b['total']:,} bytes")
    print(f"\nLowest {args.top}:")
    for r in rep["rows"][:args.top]:
        flag = "" if r["loaded"] else "  (never loaded)"
        print(f"  {r['pct']:6.2f}%  {r['path']}{flag}")

    if args.json_out:
        pathlib.Path(args.json_out).write_text(json.dumps(rep, indent=1))
        print(f"\nWrote {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
