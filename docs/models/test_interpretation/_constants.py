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

"""Paths and thresholds for the v0 assessment generator.

The audit dir and palette are reused from ``full_audit`` so both reports share a
single config-sourced location and look-and-feel.

NOTE (coding-rule 1 — parameters live in the config package): ``OUTPUT_PATTERN``,
``COVERAGE_REPORT_THRESHOLD_PCT`` and ``MAX_COVERAGE_ROWS`` are defined here for
the v0 draft only. Before merge they should migrate into the ``config`` package
alongside ``get_reports_dir()`` so the interpretation agent has the single
configuration source the spec (§8) requires. They are named here — not inlined
at their use sites — to make that migration a one-file change.
"""

from ..full_audit._constants import (
    AUDIT_DIR,
    NAVY,
    GREEN,
    AMBER,
    RED,
    GREY,
)

# Runner artefacts (spec §5) — already written into the audit dir by the local
# audit pipeline; full_audit parses the same two files.
JUNIT_XML = AUDIT_DIR / "junit.xml"
COVERAGE_XML = AUDIT_DIR / "coverage.xml"
FULL_AUDIT_PDF_NAME = "full_audit_report.pdf"

# Output (spec §7 — standalone sibling PDF in the audit dir).
OUTPUT_PATTERN = "assessment_{date}_{sha}.pdf"

# Below this line-coverage %, a package is listed in the Coverage section. v0 has
# no baseline, so this is a "lowest-covered" filter, not a delta gate.
COVERAGE_REPORT_THRESHOLD_PCT = 100.0

# Cap on rows in the Coverage table; truncation is stated in the report, never
# silent (no silent caps).
MAX_COVERAGE_ROWS = 15

# Audit metrics shown in the Audit findings section. Each row:
#   (results_name, label, summary_key, unit, gated)
# ``results_name`` is the <name>_results.json the audit writes; ``gated`` marks
# the genuinely zero-tolerance-AND-currently-clean audits whose breach raises
# "Reviewer attention" (a regression from zero). Audits with standing backlogs
# (init __init__, hardcoding, path-defs) are reported, not gated — v0 has no
# baseline to tell a new violation from the known backlog; that is a v1 concern.
AUDIT_METRICS = (
    ('init_audit',     '__init__ substantive code', 'files_with_substantive_code', 'files',       False),
    ('hardcoding',     'Hard-coded parameters',     'total_action_items',          'action items', False),
    ('embedded_js',    'Embedded JS/CSS in Python', 'total_action_items',          'action items', True),
    ('json_files',     'JSON I/O backlog',          'io_backlog_files',            'files',        True),
    ('database_usage',  'Modules still on .json',    'json_only_modules',          'modules',      False),
    ('duplication',     'Code duplication',          'duplication_pct',            '%',            False),
    ('path_definitions','Path-definition violations','violations',                 'sites',        True),
    ('model_chain',     'Model-chain inconsistencies','inconsistencies',           'findings',     False),
    ('data_lineage',    'Data lineage failures',     'failed',                     'checks',       True),
)

# Gate threshold: a gated audit whose metric exceeds this raises attention.
AUDIT_GATE_THRESHOLD = 0

__all__ = [
    "AUDIT_DIR",
    "NAVY",
    "GREEN",
    "AMBER",
    "RED",
    "GREY",
    "JUNIT_XML",
    "COVERAGE_XML",
    "FULL_AUDIT_PDF_NAME",
    "OUTPUT_PATTERN",
    "COVERAGE_REPORT_THRESHOLD_PCT",
    "MAX_COVERAGE_ROWS",
    "AUDIT_METRICS",
    "AUDIT_GATE_THRESHOLD",
    "output_path",
]


def output_path(date_iso: str, short_sha: str):
    """Resolve the assessment PDF path in the audit dir (spec §7 filename)."""
    return AUDIT_DIR / OUTPUT_PATTERN.format(date=date_iso, sha=short_sha)
