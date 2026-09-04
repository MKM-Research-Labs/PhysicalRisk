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
        ('JS Test Results',          os.path.join(audit_dir, 'js', 'js_results.json'),    'js'),
        ('JS Coverage Summary',      os.path.join(audit_dir, 'js', 'coverage-summary.json'), 'js'),
        ('JS Coverage XML',          os.path.join(audit_dir, 'js', 'js_coverage.xml'),   'js'),
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


def run_verdict(do_unit, pytest_ok, stale, js_results):
    """Print the Status line and return the process exit code.

    Three independent failures. The unit verdict: pytest returns non-zero for a
    failing test or a missed coverage gate (without --unit there is no verdict
    and ``pytest_ok`` stays True). Stale artefacts: one its phase should have
    rewritten but did not means a failed generator, and a package that passes an
    earlier run off as this one. And a failing JS suite, on the same footing as
    the Python one — a front end that fails its own tests is not a passing build.

    A fourth: the JS coverage ratchet. It fails in both directions — below the
    baseline is a regression, above it is a gain that has not been locked in —
    so it is reported separately from a failing JS test, which is a different
    problem with a different fix.

    MISSING does not fail: an artefact whose phase never ran is absent by
    design, and a skipped JS phase (no node_modules) reports SKIPPED with zero
    failures and no coverage figure, so it cannot fail a run on a machine
    without a JS toolchain.
    """
    js_failed = int(js_results.get('failed', 0)) if js_results else 0
    js_coverage_ok = js_results.get('coverage_ok', True) if js_results else True

    problems = []
    if do_unit and not pytest_ok:
        problems.append('TEST FAILURES — see junit.xml')
    if js_failed:
        problems.append(f'{js_failed} JS TEST FAILURES — see audit/js/')
    if not js_coverage_ok:
        problems.append(
            f'JS COVERAGE RATCHET — {js_results.get("coverage_message", "")}')
    if stale:
        problems.append(
            f'{len(stale)} STALE ARTEFACT(S) — evidence package incomplete')

    if problems:
        print('Status:', '; '.join(problems))
    elif do_unit:
        print('Status: ALL PASS')

    return 0 if (pytest_ok and not stale and not js_failed
                 and js_coverage_ok) else 1
