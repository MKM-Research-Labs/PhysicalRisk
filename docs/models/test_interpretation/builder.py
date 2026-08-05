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

"""Deterministic (v0) section builders for the assessment PDF.

Each ``_build_*`` returns a list of reportlab flowables. No section is ever
omitted (spec §7): a section with nothing to report renders a single line.
Nothing here interprets — model-dependent judgement is declared under
Uncertainties, not asserted.
"""

import subprocess

from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, Spacer, Table

from ..full_audit._constants import STEEL, _root, _TBL_STYLE_BASE
from ..full_audit.results_json import read_results
from ._constants import (
    AMBER,
    AUDIT_GATE_THRESHOLD,
    AUDIT_METRICS,
    COVERAGE_REPORT_THRESHOLD_PCT,
    GREEN,
    GREY,
    MAX_COVERAGE_ROWS,
    RED,
)

def _git_branch() -> str:
    """Current branch name, or 'unknown' when it cannot be resolved."""
    try:
        r = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, cwd=str(_root), timeout=5,
        )
        if r.returncode == 0:
            return r.stdout.strip() or "unknown"
    except Exception:
        pass
    return "unknown"


def _outcome(junit: dict):
    """(outcome, attention) from the JUnit summary.

    No results at all is ERROR, any failure is FAIL, otherwise PASS. Reviewer
    attention is required for anything other than a clean PASS.
    """
    if junit.get("total", 0) == 0:
        return "ERROR", True
    if junit.get("failed", 0) > 0:
        return "FAIL", True
    return "PASS", False


def _audit_gate():
    """(attention, breaches) from the gated audit metrics.

    Only audits flagged ``gated`` in AUDIT_METRICS raise attention, and only when
    their metric exceeds AUDIT_GATE_THRESHOLD — a regression from zero on a
    genuinely zero-tolerance-and-currently-clean audit. Missing results (the
    audit has not been re-run yet) never gate.
    """
    breaches = []
    for name, label, key, unit, gated in AUDIT_METRICS:
        if not gated:
            continue
        summary = read_results(name)
        if summary is None:
            continue
        val = summary.get(key)
        if isinstance(val, (int, float)) and val > AUDIT_GATE_THRESHOLD:
            breaches.append(f"{label} = {val} {unit}")
    return bool(breaches), breaches


def _p(text, sty):
    return Paragraph(text, sty)


def _build_header(junit, sha, date_iso, branch, sty, attention):
    outcome, _ = _outcome(junit)
    out_col = GREEN if outcome == "PASS" else RED
    att_col = RED if attention else GREEN
    rows = [
        [_p("<b>Date</b>", sty["tbl_cell"]), _p(date_iso, sty["tbl_cell"])],
        [_p("<b>Commit</b>", sty["tbl_cell"]), _p(sha, sty["tbl_cell"])],
        [_p("<b>Branch</b>", sty["tbl_cell"]), _p(branch, sty["tbl_cell"])],
        [_p("<b>Test outcome</b>", sty["tbl_cell"]),
         _p(f'<font color="#{out_col.hexval()[2:]}"><b>{outcome}</b></font>',
            sty["tbl_cell"])],
        [_p("<b>Reviewer attention required</b>", sty["tbl_cell"]),
         _p(f'<font color="#{att_col.hexval()[2:]}"><b>'
            f'{"YES" if attention else "NO"}</b></font>', sty["tbl_cell"])],
    ]
    tbl = Table(rows, colWidths=[60 * mm, 110 * mm])
    tbl.setStyle(_TBL_STYLE_BASE)
    return [
        _p("Test Result Interpretation — Assessment", sty["cover_title"]),
        _p("v0 deterministic spine — no model interpretation in this phase",
           sty["cover_sub"]),
        Spacer(1, 6 * mm), tbl, Spacer(1, 6 * mm),
    ]


def _build_summary(junit, cov, sty):
    total = junit.get("total", 0)
    passed = junit.get("passed", 0)
    failed = junit.get("failed", 0)
    skipped = junit.get("skipped", 0)
    rate = cov.get("line_rate", 0.0) * 100
    text = (
        f"{total} tests: {passed} passed, {failed} failed, {skipped} skipped. "
        f"Overall line coverage {rate:.2f}%. This is a deterministic v0 report — "
        f"figures are transcribed from the runner artefacts, not interpreted. "
        f"Whether any change here is a regression, an intended expectation "
        f"change, or a documentation divergence is out of scope until v1/v2 "
        f"(see Uncertainties)."
    )
    return [_p("Summary", sty["h2"]), _p(text, sty["body"]), Spacer(1, 4 * mm)]


def _build_test_outcome(junit, sty):
    out = [_p("Test outcome", sty["h2"])]
    if junit.get("total", 0) == 0:
        out.append(_p("No test results found in the runner artefacts — the "
                      "suite did not run or did not emit junit.xml.", sty["body"]))
        return out + [Spacer(1, 4 * mm)]
    if junit.get("failed", 0) == 0:
        out.append(_p(f"All {junit['passed']} executed tests passed; no "
                      f"failures to interpret.", sty["body"]))
        return out + [Spacer(1, 4 * mm)]

    out.append(_p("v0 reports failures at package granularity (per-test "
                  "assertion detail arrives with v1). Packages with failures:",
                  sty["body"]))
    rows = [[_p("<b>Package</b>", sty["tbl_hdr"]),
             _p("<b>Failed</b>", sty["tbl_hdr"]),
             _p("<b>Total</b>", sty["tbl_hdr"])]]
    for pkg, c in sorted(junit.get("by_package", {}).items()):
        if c.get("fail", 0) > 0:
            rows.append([_p(pkg, sty["tbl_cell"]),
                         _p(str(c["fail"]), sty["tbl_cell_r"]),
                         _p(str(c["total"]), sty["tbl_cell_r"])])
    tbl = Table(rows, colWidths=[110 * mm, 30 * mm, 30 * mm])
    tbl.setStyle(_TBL_STYLE_BASE)
    return out + [Spacer(1, 2 * mm), tbl, Spacer(1, 4 * mm)]


def _build_coverage(cov, sty):
    out = [_p("Coverage", sty["h2"])]
    out.append(_p("v0 has no stored baseline, so this is not a delta — it lists "
                  "the lowest-covered packages as a standing snapshot. Coverage "
                  "figures on Python 3.13.1 may be deflated by a sys.monitoring "
                  "tracer defect; treat swings with caution (see Uncertainties).",
                  sty["small"]))
    low = [r for r in cov.get("by_package", [])
           if r[1] < COVERAGE_REPORT_THRESHOLD_PCT]
    if not low:
        return out + [_p("No package below "
                         f"{COVERAGE_REPORT_THRESHOLD_PCT:.0f}%.", sty["body"]),
                      Spacer(1, 4 * mm)]
    shown = low[:MAX_COVERAGE_ROWS]
    rows = [[_p("<b>Package</b>", sty["tbl_hdr"]),
             _p("<b>Coverage %</b>", sty["tbl_hdr"]),
             _p("<b>Lines</b>", sty["tbl_hdr"])]]
    for name, pct, valid, covered in shown:
        col = GREEN if pct >= 99 else (AMBER if pct >= 90 else RED)
        rows.append([
            _p(name, sty["tbl_cell"]),
            _p(f'<font color="#{col.hexval()[2:]}">{pct:.1f}</font>',
               sty["tbl_cell_r"]),
            _p(f"{covered}/{valid}", sty["tbl_cell_r"]),
        ])
    tbl = Table(rows, colWidths=[110 * mm, 30 * mm, 30 * mm])
    tbl.setStyle(_TBL_STYLE_BASE)
    out += [Spacer(1, 2 * mm), tbl]
    if len(low) > len(shown):
        out.append(_p(f"Showing {len(shown)} of {len(low)} packages below "
                      f"threshold (lowest first); {len(low) - len(shown)} not "
                      f"shown.", sty["small"]))
    return out + [Spacer(1, 4 * mm)]


def _build_audit_findings(sty, breaches):
    out = [_p("Audit findings", sty["h2"])]
    out.append(_p("Deterministic snapshot of the run's audit metrics, read from "
                  "each audit's results JSON. † marks a gated, zero-tolerance "
                  "audit whose non-zero value raises reviewer attention; the rest "
                  "are reported, not gated — v0 has no baseline to separate a new "
                  "violation from a standing backlog.", sty["small"]))
    rows = [[_p("<b>Audit</b>", sty["tbl_hdr"]),
             _p("<b>Metric</b>", sty["tbl_hdr"]),
             _p("<b>Value</b>", sty["tbl_hdr"])]]
    any_present = False
    for name, label, key, unit, gated in AUDIT_METRICS:
        summary = read_results(name)
        tag = " †" if gated else ""
        if summary is None:
            val_txt = (f'<font color="#{GREY.hexval()[2:]}">pending next run'
                       f'</font>')
        else:
            any_present = True
            val = summary.get(key)
            numeric = isinstance(val, (int, float))
            val_str = f"{val:g}" if numeric else str(val)
            breached = gated and numeric and val > AUDIT_GATE_THRESHOLD
            col = RED if breached else (GREEN if gated else STEEL)
            val_txt = f'<font color="#{col.hexval()[2:]}">{val_str} {unit}</font>'
        rows.append([_p(label + tag, sty["tbl_cell"]),
                     _p(key.replace("_", " "), sty["tbl_cell"]),
                     _p(val_txt, sty["tbl_cell_r"])])
    tbl = Table(rows, colWidths=[70 * mm, 65 * mm, 35 * mm])
    tbl.setStyle(_TBL_STYLE_BASE)
    out += [Spacer(1, 2 * mm), tbl]
    if breaches:
        out.append(_p("<b>Gated audit non-zero</b> — raises reviewer attention: "
                      + "; ".join(breaches) + ".", sty["body"]))
    if not any_present:
        out.append(_p("No audit results JSON present yet — these populate once "
                      "the audit generators have run (next overnight run).",
                      sty["small"]))
    return out + [Spacer(1, 4 * mm)]


def _build_doc_divergence(sty):
    return [
        _p("Documentation divergence", sty["h2"]),
        _p("Deferred to v2. This section requires read access to the model "
           "documentation tree and a model to judge divergence; it is the "
           "highest-value and highest-risk section and ships last.", sty["body"]),
        Spacer(1, 4 * mm),
    ]


def _build_uncertainties(junit, cov, sty):
    items = [
        "v0 is deterministic: it does not judge whether a failure is a "
        "regression or an intended expectation change.",
        "No baseline coverage delta is computed in v0; the Coverage section is a "
        "snapshot, not a change.",
        "Documentation divergence is deferred to v2 (no docs access at v0).",
        "Audit metrics are a snapshot: only gated (zero-tolerance, currently-"
        "clean) audits raise attention; standing backlogs (e.g. __init__ "
        "substantive code, hard-coding) are reported, not gated, until v1 "
        "compares against the previous nightly.",
        "Coverage may be under-reported on Python 3.13.1 (sys.monitoring tracer "
        "defect); a large swing not localised to changed files is an environment "
        "signal, not a finding.",
    ]
    if junit.get("total", 0) == 0:
        items.insert(0, "No JUnit results were parsed — the outcome above is "
                        "ERROR by absence, which may itself be a runner problem.")
    out = [_p("Uncertainties", sty["h2"])]
    for it in items:
        out.append(_p(f"• {it}", sty["body"]))
    return out + [Spacer(1, 2 * mm)]
