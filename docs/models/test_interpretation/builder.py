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
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, Spacer, Table

from ..full_audit._constants import NAVY, STEEL, _root, _TBL_STYLE_BASE
from ._constants import (
    AMBER,
    COVERAGE_REPORT_THRESHOLD_PCT,
    GREEN,
    MAX_COVERAGE_ROWS,
    RED,
)

# Running-header label — this is a sibling of the full audit, not the full audit
# itself, so it must not reuse full_audit's "Full Audit Report" header.
_HEADER_LABEL = "Test Interpretation — Assessment"


def _header_footer(canvas, doc):
    """Assessment-specific running header/footer (mirrors full_audit's styling
    with the correct document label)."""
    canvas.saveState()
    w, h = A4
    canvas.setFillColor(NAVY)
    canvas.rect(0, h - 20 * mm, w, 20 * mm, fill=1, stroke=0)
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica-Bold", 9)
    canvas.drawString(20 * mm, h - 12 * mm, "MKM Physical Risk Platform")
    canvas.setFont("Helvetica", 9)
    canvas.drawRightString(
        w - 20 * mm, h - 12 * mm,
        f'{_HEADER_LABEL}  |  {datetime.now().strftime("%d %B %Y")}')
    canvas.setFillColor(STEEL)
    canvas.rect(0, 0, w, 8 * mm, fill=1, stroke=0)
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica", 7.5)
    canvas.drawString(
        20 * mm, 2.5 * mm,
        "CONFIDENTIAL — MKM Research Labs  |  SR 11-7 / SS1/23 Model Governance")
    canvas.drawRightString(w - 20 * mm, 2.5 * mm, f"Page {doc.page}")
    canvas.restoreState()


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


def _p(text, sty):
    return Paragraph(text, sty)


def _build_header(junit, sha, date_iso, branch, sty):
    outcome, attention = _outcome(junit)
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


def _build_audit_findings(sty):
    return [
        _p("Audit findings", sty["h2"]),
        _p("Deferred. full_audit currently emits a human PDF, not a "
           "machine-readable finding set; a structured (JSON) output mode is the "
           "v0 prerequisite for this section. See full_audit_report.pdf in this "
           "directory for the current audit.", sty["body"]),
        Spacer(1, 4 * mm),
    ]


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
        "Audit findings await a structured full_audit output mode.",
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
