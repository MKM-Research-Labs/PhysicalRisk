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

"""Audit-package manifest and freshness reporting.

The package summary used to report ``[OK]`` for any artefact that merely
*existed*. That hid a real failure for four weeks: four doc generators died on
import when the theme migration gave them a ``src`` import they could not
resolve, and the summary kept reporting their August PDFs as current because
the files were still on disk.

Existence is not evidence. An artefact is only evidence of *this* run if it was
written during it, so each entry declares the phase that produces it and is
compared against the run's start time. An artefact whose phase did not run this
invocation is reported as carried over from an earlier run, which is honest
rather than alarming; one whose phase *did* run but which was not rewritten is
STALE, and that is a defect.
"""

import os

# Filesystem timestamp granularity, plus a little slack for a generator that
# starts writing fractionally before the clock is read. Well under the gap
# between a current artefact and a carried-over one, which is hours or weeks.
_TOLERANCE_S = 2.0


def artefact_manifest(audit_dir, junit_xml, cov_xml, cov_html, assessment_path):
    """Return ``[(label, path, phase), ...]`` for the audit package.

    ``phase`` names the run phase that writes the artefact, so freshness is
    only asserted when that phase actually ran.
    """
    def _p(name):
        return os.path.join(audit_dir, name)

    return [
        ('JUnit XML',                junit_xml,                        'unit'),
        ('Coverage XML',             cov_xml,                          'unit'),
        ('Coverage HTML',            cov_html,                         'unit'),
        ('Data Lineage Results',     _p('data_lineage_results.json'),  'lineage'),
        ('Data Lineage JUnit',       _p('data_lineage_junit.xml'),     'lineage'),
        ('E2E Results',              os.path.join(audit_dir, 'e2e', 'e2e_results.json'), 'e2e'),
        ('E2E JUnit',                os.path.join(audit_dir, 'e2e', 'e2e_junit.xml'),    'e2e'),
        # LaTeX compilation is opt-in via --pdf; the audit phase alone writes
        # only the .tex, so this must not be judged against the audit phase.
        ('Test Report PDF',          _p('test_report.pdf'),            'pdf'),
        ('Large File Report PDF',    _p('large_file_report.pdf'),      'audit'),
        ('Large Test Report TXT',    _p('large_test_report.txt'),      'audit'),
        ('Init Audit Report PDF',    _p('init_audit_report.pdf'),      'audit'),
        ('Init Audit Results JSON',  _p('init_audit_results.json'),    'audit'),
        ('Code Duplication PDF',     _p('code_duplication_report.pdf'), 'audit'),
        ('Hard-Coding Audit PDF',    _p('hardcoding_report.pdf'),      'audit'),
        ('Embedded JS/CSS PDF',      _p('embedded_js_report.pdf'),     'audit'),
        ('JSON-File Audit PDF',      _p('json_files_report.pdf'),      'audit'),
        ('Database-Usage Audit PDF', _p('database_usage_report.pdf'),  'audit'),
        ('Data Lineage PDF',         _p('data_lineage_report.pdf'),    'audit'),
        ('Model Risk Report PDF',    _p('model_risk_report.pdf'),      'audit'),
        ('Full Audit Report PDF',    _p('full_audit_report.pdf'),      'audit'),
        ('Assessment PDF',           assessment_path,                  'audit'),
    ]


def classify(path, phase, run_started, phases_run):
    """Return ``(status, note)`` for one artefact.

    ``MISSING`` — absent.
    ``STALE``   — its phase ran but it was not rewritten: the generator failed.
    ``OK``      — written during this run, or carried over from an earlier one
                  because its phase did not run.
    """
    if not os.path.exists(path):
        return 'MISSING', ''

    try:
        age = os.path.getmtime(path)
    except OSError:
        return 'MISSING', ''

    written_this_run = age >= (run_started - _TOLERANCE_S)
    if written_this_run:
        return 'OK', ''
    if phase in phases_run:
        return 'STALE', _describe_age(run_started - age)
    return 'OK', f'{phase} phase not run; from an earlier run'


def _describe_age(seconds):
    """Human-readable age, coarse on purpose — hours vs weeks is the signal."""
    if seconds < 3600:
        return f'not rewritten this run ({int(seconds // 60)} min old)'
    if seconds < 86400:
        return f'not rewritten this run ({int(seconds // 3600)} h old)'
    return f'not rewritten this run ({int(seconds // 86400)} days old)'


def report_artefacts(artefacts, run_started, phases_run):
    """Print the package contents. Return the list of STALE labels."""
    stale = []
    for label, path, phase in artefacts:
        status, note = classify(path, phase, run_started, phases_run)
        size = ''
        if status != 'MISSING' and os.path.isfile(path):
            size = f' ({os.path.getsize(path) / 1024:.1f} KB)'
        suffix = f'  — {note}' if note else ''
        print(f' [{status}] {label}: {path}{size}{suffix}')
        if status == 'STALE':
            stale.append(label)
    return stale
