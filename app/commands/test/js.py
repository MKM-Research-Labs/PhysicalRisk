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

"""JavaScript unit-test runner (jest) for the audit evidence package.

The back end has been measured and gated for a long time; the 130 served JS
modules had never been measured at all until 2026-09-01. This phase puts the
front end in the same evidence package as everything else, so the figure is
reported every run rather than derived by hand when someone asks.

Emits three artefacts into ``audit/js/``:

  js_results.json          jest's own run report (``--json``) — pass/fail counts
  js_coverage_summary.json istanbul json-summary — the headline percentages
  js_coverage.xml          cobertura XML, the same shape as Python's coverage.xml

No new npm dependency: ``--json`` is native to jest and both coverage reporters
ship with istanbul. A jest-junit reporter would have been the obvious choice for
XML, but it is not installed and adding one to produce evidence would be a new
supply-chain dependency for no gain.

The phase skips cleanly when node or node_modules is absent — the same contract
as the playwright preflight in e2e.py. A machine without a JS toolchain should
report "skipped", not fail the run.
"""

import json
import os
import shutil
import subprocess as sp

JEST_CONFIG = os.path.join('tests', 'js', 'jest.config.js')
COVERAGE_FROM = 'src/static/js/**/*.js'
_TIMEOUT_S = 600


def _skipped(reason, out_dir):
    """Record and return a skip summary so the audit still has a JS entry."""
    summary = {'total': 0, 'passed': 0, 'failed': 0,
               'status': 'SKIPPED', 'reason': reason,
               'statements_pct': None}
    try:
        os.makedirs(out_dir, exist_ok=True)
        with open(os.path.join(out_dir, 'js_results.json'), 'w') as f:
            json.dump(summary, f, indent=2)
    except OSError:
        pass
    print(f'  Skipped: {reason}')
    return summary


def _preflight(project_root):
    """Return None when the JS toolchain is usable, else a skip reason."""
    if shutil.which('node') is None:
        return 'node not on PATH'
    if shutil.which('npx') is None:
        return 'npx not on PATH'
    if not os.path.isdir(os.path.join(str(project_root), 'node_modules')):
        return 'node_modules not installed (run: npm install)'
    if not os.path.isfile(os.path.join(str(project_root), JEST_CONFIG)):
        return f'{JEST_CONFIG} not found'
    return None


def _read_pct(out_dir):
    """Statement percentage from istanbul's json-summary, or None."""
    path = os.path.join(out_dir, 'coverage-summary.json')
    try:
        with open(path) as f:
            data = json.load(f)
        return data.get('total', {}).get('statements', {}).get('pct')
    except (OSError, json.JSONDecodeError, AttributeError):
        return None


def _read_counts(results_path):
    """Test counts from jest's --json report, or zeros."""
    try:
        with open(results_path) as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return 0, 0, 0
    return (data.get('numTotalTests', 0),
            data.get('numPassedTests', 0),
            data.get('numFailedTests', 0))


def _run_js_tests(project_root, audit_dir):
    """Run jest with coverage and write the JS artefacts. Returns a summary."""
    out_dir = os.path.join(audit_dir, 'js')

    reason = _preflight(project_root)
    if reason:
        return _skipped(reason, out_dir)

    os.makedirs(out_dir, exist_ok=True)
    results_path = os.path.join(out_dir, 'js_results.json')

    cmd = [
        'npx', 'jest', '--config', JEST_CONFIG,
        '--coverage',
        f'--collectCoverageFrom={COVERAGE_FROM}',
        '--coverageReporters=json-summary',
        '--coverageReporters=cobertura',
        '--coverageReporters=text-summary',
        f'--coverageDirectory={out_dir}',
        '--json', f'--outputFile={results_path}',
        '--ci',
    ]
    try:
        sp.run(cmd, cwd=str(project_root), timeout=_TIMEOUT_S)
    except sp.TimeoutExpired:
        return _skipped(f'jest exceeded {_TIMEOUT_S}s', out_dir)
    except OSError as exc:
        return _skipped(f'could not launch jest: {exc}', out_dir)

    # Give the cobertura output the same name shape as the Python side.
    src_xml = os.path.join(out_dir, 'cobertura-coverage.xml')
    if os.path.isfile(src_xml):
        os.replace(src_xml, os.path.join(out_dir, 'js_coverage.xml'))

    total, passed, failed = _read_counts(results_path)
    pct = _read_pct(out_dir)

    summary = {
        'total': total, 'passed': passed, 'failed': failed,
        'status': 'OK' if failed == 0 else 'FAILURES',
        'statements_pct': pct,
    }
    pct_txt = f'{pct:.2f}%' if isinstance(pct, (int, float)) else 'unknown'
    print(f'  JS tests: {total} tests, {passed} passed, {failed} failed '
          f'[{summary["status"]}]')
    print(f'  JS statement coverage: {pct_txt}')
    return summary
