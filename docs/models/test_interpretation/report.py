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

"""PDF assembly and entry point for the v0 assessment report.

Reads ``junit.xml`` + ``coverage.xml`` from the audit dir and renders a
standalone sibling PDF (``assessment_<date>_<sha>.pdf``) using full_audit's
reportlab styling, so it surfaces on the governance audit-reports panel with no
extra wiring. Deterministic — no model involved (spec v0).
"""

from datetime import datetime
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate

from ..full_audit.parsers import _git_sha, _parse_coverage, _parse_junit
from ..full_audit.styles import _styles
from ._constants import AUDIT_DIR, COVERAGE_XML, JUNIT_XML, output_path
from .builder import (
    _audit_gate,
    _build_audit_findings,
    _build_coverage,
    _build_doc_divergence,
    _build_header,
    _build_summary,
    _build_test_outcome,
    _build_uncertainties,
    _git_branch,
    _outcome,
)
from .chrome import _header_footer


def create_assessment_pdf() -> Path:
    """Generate the v0 assessment PDF and return its path."""
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)

    date_iso = datetime.now().date().isoformat()
    sha = _git_sha()
    branch = _git_branch()

    junit = _parse_junit(JUNIT_XML)
    cov = _parse_coverage(COVERAGE_XML)
    sty = _styles()

    # Reviewer attention = a test failure/error OR a gated zero-tolerance audit
    # breaching zero (see builder._audit_gate).
    _, test_attention = _outcome(junit)
    audit_attention, breaches = _audit_gate()
    attention = test_attention or audit_attention

    story = []
    story += _build_header(junit, sha, date_iso, branch, sty, attention)
    story += _build_summary(junit, cov, sty)
    story += _build_test_outcome(junit, sty)
    story += _build_coverage(cov, sty)
    story += _build_audit_findings(sty, breaches)
    story += _build_doc_divergence(sty)
    story += _build_uncertainties(junit, cov, sty)

    out = output_path(date_iso, sha)
    doc = SimpleDocTemplate(
        str(out), pagesize=A4,
        leftMargin=20 * mm, rightMargin=20 * mm,
        topMargin=24 * mm, bottomMargin=14 * mm,
    )
    doc.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)
    return out


def main():
    print("Generating v0 Assessment Report …")
    out = create_assessment_pdf()
    size_kb = out.stat().st_size / 1024
    print(f" Written: {out}  ({size_kb:.1f} KB)")


if __name__ == "__main__":
    main()
