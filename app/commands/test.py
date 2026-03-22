#!/usr/bin/env python3

# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial 
# research and educational use only. Any commercial use, including 
# but not limited to use in or for products or services offered for sale, 
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Test command - Audit evidence package generation.

Runs the full pytest suite under tests/ and produces:
  - JUnit XML
  - Coverage XML + HTML
  - LaTeX / PDF model documentation
All artefacts are written to data/output/audit/.
"""

import os
import sys
import shutil
import subprocess as sp

from config import config


def register_parser(subparsers):
    """Register the 'test' subcommand."""
    sp_test = subparsers.add_parser(
        "test", help="Run tests and produce full audit evidence package")
    sp_test.add_argument(
        "--audit", action="store_true",
        help="Produce JUnit XML + coverage + LaTeX report in data/output/audit/")
    sp_test.add_argument(
        "--test", action="store_true",
        help="Run pytest suite only (JUnit XML + coverage), skip doc generators")
    sp_test.add_argument(
        "--code", action="store_true",
        help="Run doc generators only (modularisation, duplication, hardcoding, full audit), skip pytest")
    sp_test.add_argument(
        "--pdf", action="store_true",
        help="Compile LaTeX report to PDF")
    sp_test.add_argument(
        "--model", nargs="+",
        help="Filter by model alias (e.g. MP GH TD)")
    sp_test.set_defaults(func=cmd_test)


def _write_failures_report(junit_xml_path: str, audit_dir: str) -> None:
    """Parse junit.xml and write test_failures_report.json for the audit tab header."""
    import json
    import xml.etree.ElementTree as ET
    from datetime import datetime

    report_path = os.path.join(audit_dir, 'test_failures_report.json')

    summary = {'total': 0, 'passed': 0, 'failed': 0, 'skipped': 0}
    failures = []

    if os.path.exists(junit_xml_path):
        try:
            tree = ET.parse(junit_xml_path)
            xml_root = tree.getroot()
            for tc in xml_root.findall('.//testcase'):
                summary['total'] += 1
                failure_el = tc.find('failure')
                if failure_el is None:
                    failure_el = tc.find('error')
                skip_el = tc.find('skipped')
                if failure_el is not None:
                    summary['failed'] += 1
                    classname = tc.get('classname', '')
                    name = tc.get('name', '')
                    # Derive file path from classname (e.g. tests.models.hazard → tests/models/hazard)
                    file_path = classname.replace('.', '/') + '.py'
                    failures.append({
                        'name': name,
                        'class': classname.split('.')[-1],
                        'file': file_path,
                        'longrepr': failure_el.text or '',
                    })
                elif skip_el is not None:
                    summary['skipped'] += 1
                else:
                    summary['passed'] += 1
        except Exception as exc:
            print(f' Warning: could not parse junit.xml for failures report: {exc}')

    report = {
        'generated_at': datetime.now().isoformat(),
        'summary': summary,
        'failures': failures,
    }
    try:
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        print(f' Updated test_failures_report.json ({summary["total"]} tests, {summary["failed"]} failures)')
    except Exception as exc:
        print(f' Warning: could not write test_failures_report.json: {exc}')


def _run_data_lineage_tests(project_root, audit_dir):
    """Run data/test_id_consistency.py and return summary dict."""
    import json
    import xml.etree.ElementTree as ET

    lineage_xml = os.path.join(audit_dir, 'data_lineage_junit.xml')
    lineage_test = os.path.join(str(project_root), 'tests', 'data', 'test_id_consistency.py')

    if not os.path.exists(lineage_test):
        print('  Skipped: tests/data/test_id_consistency.py not found')
        return None

    _venv_python = os.path.join(str(project_root), 'venv', 'bin', 'python')
    _python_exe = _venv_python if os.path.isfile(_venv_python) else sys.executable

    cmd = [
        _python_exe, '-m', 'pytest',
        lineage_test,
        f'--junitxml={lineage_xml}',
        '-v', '--tb=short', '-q',
    ]
    result = sp.run(cmd, cwd=str(project_root), capture_output=True, text=True, timeout=300)

    summary = {'total': 0, 'passed': 0, 'failed': 0, 'skipped': 0, 'failures': []}

    if os.path.exists(lineage_xml):
        try:
            tree = ET.parse(lineage_xml)
            xml_root = tree.getroot()
            for tc in xml_root.findall('.//testcase'):
                summary['total'] += 1
                failure_el = tc.find('failure')
                if failure_el is None:
                    failure_el = tc.find('error')
                skip_el = tc.find('skipped')
                if failure_el is not None:
                    summary['failed'] += 1
                    summary['failures'].append({
                        'name': tc.get('name', ''),
                        'classname': tc.get('classname', ''),
                        'message': (failure_el.get('message', '') or
                                    (failure_el.text or '')[:300]),
                    })
                elif skip_el is not None:
                    summary['skipped'] += 1
                else:
                    summary['passed'] += 1
        except Exception as exc:
            print(f'  Warning: could not parse data_lineage_junit.xml: {exc}')

    status = 'PASS' if summary['failed'] == 0 else 'FAIL'
    print(f'  Data lineage: {summary["total"]} checks, '
          f'{summary["passed"]} passed, {summary["failed"]} failed, '
          f'{summary["skipped"]} skipped [{status}]')

    # Persist results for the PDF generator
    report_path = os.path.join(audit_dir, 'data_lineage_results.json')
    try:
        with open(report_path, 'w') as f:
            json.dump(summary, f, indent=2)
    except Exception:
        pass

    return summary


def _run_e2e_tests(project_root, audit_dir, python_exe):
    """Run Playwright e2e tests headless and return summary dict."""
    import json
    import xml.etree.ElementTree as ET

    e2e_xml = os.path.join(audit_dir, 'e2e_junit.xml')
    e2e_dir = os.path.join(str(project_root), 'tests', 'e2e')

    if not os.path.isdir(e2e_dir):
        print('  Skipped: tests/e2e/ directory not found')
        return None

    # Check if playwright Python package is installed
    check = sp.run(
        [python_exe, '-c', 'import playwright'],
        capture_output=True, cwd=str(project_root),
    )
    if check.returncode != 0:
        print('  Skipped: playwright not installed (pip install playwright && playwright install)')
        summary = {
            'total': 0, 'passed': 0, 'failed': 0, 'skipped': 0,
            'status': 'SKIPPED', 'reason': 'playwright not installed',
            'failures': [],
        }
        report_path = os.path.join(audit_dir, 'e2e_results.json')
        try:
            with open(report_path, 'w') as f:
                json.dump(summary, f, indent=2)
        except Exception:
            pass
        return summary

    # Ensure Chromium browser binary is installed (the pip package alone
    # is not enough — the binary must be downloaded separately).
    # Quick sanity check: try to launch a browser context.  If the binary
    # is missing playwright raises BrowserNotInstalled / Error.
    browser_check = sp.run(
        [python_exe, '-c',
         'from playwright.sync_api import sync_playwright; '
         'p = sync_playwright().start(); '
         'b = p.chromium.launch(headless=True); b.close(); p.stop()'],
        capture_output=True, text=True, cwd=str(project_root),
        timeout=30,
    )
    needs_install = browser_check.returncode != 0
    if needs_install:
        print('  Installing Chromium browser for Playwright...')
        install_result = sp.run(
            [python_exe, '-m', 'playwright', 'install', 'chromium'],
            capture_output=True, text=True, cwd=str(project_root),
        )
        if install_result.returncode != 0:
            msg = (install_result.stderr or install_result.stdout or '')[:300]
            print(f'  Warning: Chromium install failed: {msg}')
            summary = {
                'total': 0, 'passed': 0, 'failed': 0, 'skipped': 0,
                'status': 'SKIPPED',
                'reason': f'Chromium install failed: {msg[:200]}',
                'failures': [],
            }
            report_path = os.path.join(audit_dir, 'e2e_results.json')
            try:
                with open(report_path, 'w') as f:
                    json.dump(summary, f, indent=2)
            except Exception:
                pass
            return summary
        print('  Chromium installed successfully.')

    # Omit --headed to run headless (default for pytest-playwright)
    cmd = [
        python_exe, '-m', 'pytest',
        e2e_dir,
        f'--junitxml={e2e_xml}',
        '--browser', 'chromium',
        '-v', '--tb=short', '-q',
    ]

    try:
        result = sp.run(cmd, cwd=str(project_root), capture_output=True, text=True, timeout=600)
    except sp.TimeoutExpired:
        print('  E2E tests timed out (10 min limit)')
        return {'total': 0, 'passed': 0, 'failed': 0, 'skipped': 0,
                'status': 'TIMEOUT', 'reason': 'timed out after 600s', 'failures': []}
    except Exception as exc:
        print(f'  E2E tests failed to run: {exc}')
        return {'total': 0, 'passed': 0, 'failed': 0, 'skipped': 0,
                'status': 'ERROR', 'reason': str(exc), 'failures': []}

    summary = {'total': 0, 'passed': 0, 'failed': 0, 'skipped': 0,
               'status': 'OK', 'failures': []}

    if os.path.exists(e2e_xml):
        try:
            tree = ET.parse(e2e_xml)
            xml_root = tree.getroot()
            for tc in xml_root.findall('.//testcase'):
                summary['total'] += 1
                failure_el = tc.find('failure')
                if failure_el is None:
                    failure_el = tc.find('error')
                skip_el = tc.find('skipped')
                if failure_el is not None:
                    summary['failed'] += 1
                    summary['failures'].append({
                        'name': tc.get('name', ''),
                        'classname': tc.get('classname', ''),
                        'message': (failure_el.get('message', '') or
                                    (failure_el.text or '')[:500]),
                    })
                elif skip_el is not None:
                    summary['skipped'] += 1
                else:
                    summary['passed'] += 1
        except Exception as exc:
            print(f'  Warning: could not parse e2e_junit.xml: {exc}')

    if summary['failed'] > 0:
        summary['status'] = 'FAIL'

    status_str = summary['status']
    print(f'  E2E tests: {summary["total"]} tests, '
          f'{summary["passed"]} passed, {summary["failed"]} failed, '
          f'{summary["skipped"]} skipped [{status_str}]')

    # Persist results for the PDF generator
    report_path = os.path.join(audit_dir, 'e2e_results.json')
    try:
        with open(report_path, 'w') as f:
            json.dump(summary, f, indent=2)
    except Exception:
        pass

    return summary


def cmd_test(args):
    """Run tests and produce a full audit evidence package."""
    project_root = config.get_project_root()

    # All artefacts land in data/output/audit/
    audit_dir = os.path.join(str(project_root), 'data', 'output', 'audit')
    os.makedirs(audit_dir, exist_ok=True)

    junit_xml = os.path.join(audit_dir, 'junit.xml')
    cov_html  = os.path.join(audit_dir, 'coverage')
    cov_xml   = os.path.join(audit_dir, 'coverage.xml')

    # Determine which phases to run
    run_tests = getattr(args, 'test', False)
    run_code  = getattr(args, 'code', False)
    run_all   = getattr(args, 'audit', False) or (not run_tests and not run_code)

    do_tests = run_all or run_tests
    do_code  = run_all or run_code

    # ------------------------------------------------------------------
    # 1. Capture git commit SHA
    # ------------------------------------------------------------------
    git_sha = None
    try:
        result = sp.run(
            ['git', 'rev-parse', 'HEAD'],
            capture_output=True, text=True, cwd=str(project_root),
        )
        if result.returncode == 0:
            git_sha = result.stdout.strip()
    except FileNotFoundError:
        pass

    print('=' * 60)
    print('MKM Research Labs — Audit Evidence Package')
    print('=' * 60)
    if git_sha:
        print(f' Git SHA : {git_sha[:12]}')
    print(f' Output  : {audit_dir}')
    phases = []
    if do_tests:
        phases.append('tests')
    if do_code:
        phases.append('code')
    print(f' Phases  : {", ".join(phases)}')
    print()

    pytest_ok = True
    coverage_pct = None
    data_lineage_results = None
    e2e_results = None

    if do_tests:
        # ------------------------------------------------------------------
        # 1b. Pre-flight: Data lineage consistency checks (BCBS 239 P3)
        # ------------------------------------------------------------------
        print('Running data lineage consistency checks (pre-flight)...')
        data_lineage_results = _run_data_lineage_tests(project_root, audit_dir)
        if data_lineage_results and data_lineage_results.get('failed', 0) > 0:
            print()
            print('  WARNING: Data lineage checks FAILED.')
            print('  Pipeline data is inconsistent — audit results may be unreliable.')
            print('  Regenerate data in order: port --gauge → port --stressm → port --hazard → port --blotter')
            print()

        # ------------------------------------------------------------------
        # 2. Run pytest against the full tests/ tree at project root
        # ------------------------------------------------------------------
        print('Running test suite with coverage...')

        tests_dir = os.path.join(str(project_root), 'tests')

        # Prefer the project venv's Python so pytest and all dependencies
        # are available regardless of which Python launched this script.
        _venv_python = os.path.join(str(project_root), 'venv', 'bin', 'python')
        _python_exe = _venv_python if os.path.isfile(_venv_python) else sys.executable

        e2e_dir = os.path.join(tests_dir, 'e2e')
        pytest_cmd = [
            _python_exe, '-m', 'pytest',
            tests_dir,
            f'--ignore={e2e_dir}',
            f'--junitxml={junit_xml}',
            '--cov=src',
            f'--cov-report=html:{cov_html}',
            f'--cov-report=xml:{cov_xml}',
            '--cov-report=term-missing:skip-covered',
            '-q', '--tb=short',
        ]

        model_filter = getattr(args, 'model', None)
        if model_filter:
            pytest_cmd.extend(['--model'] + model_filter)

        pytest_result = sp.run(pytest_cmd, cwd=str(project_root))
        pytest_ok = pytest_result.returncode == 0
        print()

        # ------------------------------------------------------------------
        # 3. Parse coverage percentage from coverage.xml
        # ------------------------------------------------------------------
        if os.path.exists(cov_xml):
            try:
                import xml.etree.ElementTree as ET
                tree = ET.parse(cov_xml)
                root = tree.getroot()
                line_rate = float(root.get('line-rate', 0))
                coverage_pct = line_rate * 100
                print(f' Coverage: {coverage_pct:.1f}%')
            except Exception:
                pass

        # ------------------------------------------------------------------
        # 3b. Write test_failures_report.json
        # ------------------------------------------------------------------
        _write_failures_report(junit_xml, audit_dir)

        # ------------------------------------------------------------------
        # 3c. E2E browser tests (Playwright)
        # ------------------------------------------------------------------
        print('\nRunning E2E browser tests (Playwright)...')
        e2e_results = _run_e2e_tests(project_root, audit_dir, _python_exe)

    elif os.path.exists(cov_xml):
        # code-only run: read existing coverage.xml so doc generators get the %
        try:
            import xml.etree.ElementTree as ET
            tree = ET.parse(cov_xml)
            root = tree.getroot()
            line_rate = float(root.get('line-rate', 0))
            coverage_pct = line_rate * 100
            print(f' Coverage (from existing xml): {coverage_pct:.1f}%')
        except Exception:
            pass

    if do_code:
        # ------------------------------------------------------------------
        # 4. Generate LaTeX / PDF documentation via existing generator
        # ------------------------------------------------------------------
        print('\nGenerating model documentation...')
        doc_cmd = [_python_exe, '-m', 'docs.models.test_results.generator']

        if getattr(args, 'pdf', False):
            doc_cmd.append('--pdf')
        if git_sha:
            doc_cmd.extend(['--git-sha', git_sha])
        if coverage_pct is not None:
            doc_cmd.extend(['--coverage-pct', f'{coverage_pct:.2f}'])

        # Include E2E browser test results in the report
        e2e_xml = os.path.join(audit_dir, 'e2e_junit.xml')
        if os.path.exists(e2e_xml):
            doc_cmd.extend(['--e2e-junit', e2e_xml])

        sp.run(doc_cmd, cwd=str(project_root))

        # ------------------------------------------------------------------
        # 5. Copy generated PDF into audit directory
        # ------------------------------------------------------------------
        _test_report_pdf = os.path.join(
            str(project_root),
            'docs', 'models', 'test_results', 'test_results', 'test_report.pdf')
        if os.path.exists(_test_report_pdf):
            dest = os.path.join(audit_dir, 'test_report.pdf')
            shutil.copy2(_test_report_pdf, dest)
            print(f' Copied test_report.pdf → {dest}')

        # ------------------------------------------------------------------
        # 6. Generate code modularisation analysis report
        # ------------------------------------------------------------------
        print('\nGenerating code modularisation analysis...')
        sp.run(
            [sys.executable, '-m', 'docs.models.project'],
            cwd=str(project_root),
        )

        # ------------------------------------------------------------------
        # 7. Generate code duplication report
        # ------------------------------------------------------------------
        print('\nGenerating code duplication analysis...')
        sp.run(
            [sys.executable, '-m', 'docs.models.duplication'],
            cwd=str(project_root),
        )

        # ------------------------------------------------------------------
        # 7b. Generate hard-coding audit report
        # ------------------------------------------------------------------
        print('\nGenerating hard-coding parameter audit...')
        sp.run(
            [sys.executable, '-m', 'docs.models.hardcoding'],
            cwd=str(project_root),
        )

        # ------------------------------------------------------------------
        # 7c. Generate data lineage report (BCBS 239)
        # ------------------------------------------------------------------
        print('\nGenerating data lineage report (BCBS 239)...')
        sp.run(
            [sys.executable, '-m', 'docs.models.data_lineage'],
            cwd=str(project_root),
        )

        # ------------------------------------------------------------------
        # 7d. Generate full consolidated audit report
        # ------------------------------------------------------------------
        print('\nGenerating full audit report...')
        sp.run(
            [sys.executable, '-m', 'docs.models.full_audit'],
            cwd=str(project_root),
        )

    # ------------------------------------------------------------------
    # 8. Print audit package summary
    # ------------------------------------------------------------------
    print('\n' + '=' * 60)
    print('Audit Package Contents')
    print('=' * 60)
    artefacts = [
        ('JUnit XML',              junit_xml),
        ('Coverage XML',           cov_xml),
        ('Coverage HTML',          cov_html),
        ('Data Lineage Results',   os.path.join(audit_dir, 'data_lineage_results.json')),
        ('Data Lineage JUnit',     os.path.join(audit_dir, 'data_lineage_junit.xml')),
        ('E2E Results',            os.path.join(audit_dir, 'e2e_results.json')),
        ('E2E JUnit',              os.path.join(audit_dir, 'e2e_junit.xml')),
        ('Test Report PDF',        os.path.join(audit_dir, 'test_report.pdf')),
        ('Large File Report PDF',  os.path.join(audit_dir, 'large_file_report.pdf')),
        ('Large Test Report TXT',  os.path.join(audit_dir, 'large_test_report.txt')),
        ('Code Duplication PDF',   os.path.join(audit_dir, 'code_duplication_report.pdf')),
        ('Hard-Coding Audit PDF',  os.path.join(audit_dir, 'hardcoding_report.pdf')),
        ('Data Lineage PDF',       os.path.join(audit_dir, 'data_lineage_report.pdf')),
        ('Full Audit Report PDF',  os.path.join(audit_dir, 'full_audit_report.pdf')),
    ]
    for label, path in artefacts:
        exists = os.path.exists(path)
        size = ''
        if exists and os.path.isfile(path):
            size = f' ({os.path.getsize(path) / 1024:.1f} KB)'
        status = 'OK' if exists else 'MISSING'
        print(f' [{status}] {label}: {path}{size}')
    print()
    if do_tests:
        print('Status:', 'ALL PASS' if pytest_ok else 'TEST FAILURES — see junit.xml')
