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

import argparse
import os
import sys
import shutil
import subprocess as sp

from config import config


def register_parser(subparsers):
    """Register the 'test' subcommand."""
    sp_test = subparsers.add_parser(
        "test", help="Run tests and produce audit evidence package",
        formatter_class=_HelpFormatter)

    # Suite selectors — pick any combination
    suites = sp_test.add_argument_group("suite selectors (pick any combination)")
    suites.add_argument(
        "--unit", action="store_true",
        help="Unit/model tests with coverage (~7 000 tests)")
    suites.add_argument(
        "--e2e", action="store_true",
        help="Playwright E2E browser tests (~300 tests)")
    suites.add_argument(
        "--lineage", action="store_true",
        help="Data lineage consistency checks (BCBS 239)")
    suites.add_argument(
        "--all", action="store_true", dest="run_all",
        help="All three suites (default when no suite flag given)")

    # Output options
    outputs = sp_test.add_argument_group("output options")
    outputs.add_argument(
        "--audit", action="store_true",
        help="Generate audit reports (modularisation, duplication, hardcoding, full audit)")
    outputs.add_argument(
        "--pdf", action="store_true",
        help="Compile LaTeX reports to PDF")
    outputs.add_argument(
        "--params", action="store_true",
        help="Generate parameter inventory report")
    outputs.add_argument(
        "--check-deps", action="store_true",
        help="Verify required Python dependencies are installed")
    outputs.add_argument(
        "--model", nargs="+",
        help="Filter unit tests by model alias (e.g. MP GH TD)")

    # Hidden backward-compat aliases (deprecated)
    sp_test.add_argument("--test", action="store_true", dest="_compat_test",
                         help=argparse.SUPPRESS)
    sp_test.add_argument("--code", action="store_true", dest="_compat_code",
                         help=argparse.SUPPRESS)

    sp_test.set_defaults(func=cmd_test)


class _HelpFormatter(argparse.RawDescriptionHelpFormatter,
                      argparse.ArgumentDefaultsHelpFormatter):
    """Combined formatter for nicer help output."""
    pass


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

    _venv_python = os.path.join(str(project_root), '.venv', 'bin', 'python')
    if not os.path.isfile(_venv_python):
        _venv_python = os.path.join(str(project_root), 'venv', 'bin', 'python')
    _python_exe = _venv_python if os.path.isfile(_venv_python) else sys.executable

    cmd = [
        _python_exe, '-m', 'pytest',
        lineage_test,
        f'--junitxml={lineage_xml}',
        '-v', '--tb=short',
    ]
    result = sp.run(cmd, cwd=str(project_root), timeout=300)

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

    # Check if playwright Python package is installed.
    # Use sys.executable (the Python that launched app.py) rather than the
    # venv python — playwright is typically installed in the user's base env.
    _pw_python = sys.executable
    check = sp.run(
        [_pw_python, '-c', 'import playwright'],
        capture_output=True, cwd=str(project_root),
    )
    if check.returncode != 0:
        # Fall back to venv python in case playwright is there instead
        check2 = sp.run(
            [python_exe, '-c', 'import playwright'],
            capture_output=True, cwd=str(project_root),
        )
        if check2.returncode != 0:
            print(f'  Skipped: playwright not installed')
            print(f'    Checked: {_pw_python}')
            print(f'    Checked: {python_exe}')
            print(f'    Fix: pip install playwright && playwright install')
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
        else:
            # playwright found in venv python, use that
            _pw_python = python_exe

    # Ensure Chromium browser binary is installed (the pip package alone
    # is not enough — the binary must be downloaded separately).
    # Quick sanity check: try to launch a browser context.  If the binary
    # is missing playwright raises BrowserNotInstalled / Error.
    browser_check = sp.run(
        [_pw_python, '-c',
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
            [_pw_python, '-m', 'playwright', 'install', 'chromium'],
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

    # Run e2e tests with verbose output streamed to terminal
    cmd = [
        _pw_python, '-m', 'pytest',
        e2e_dir,
        f'--junitxml={e2e_xml}',
        '--browser', 'chromium',
        '-v', '--tb=short',
    ]

    try:
        result = sp.run(cmd, cwd=str(project_root), timeout=6000)
    except sp.TimeoutExpired:
        print('  E2E tests timed out (100 min limit)')
        return {'total': 0, 'passed': 0, 'failed': 0, 'skipped': 0,
                'status': 'TIMEOUT', 'reason': 'timed out after 1800s', 'failures': []}
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


def _check_deps():
    """Verify required Python dependencies are installed."""
    required = [
        "flask", "flask_cors", "folium", "pandas", "numpy",
        "geopandas", "reportlab", "scipy", "sklearn",
        "rasterio", "geopy", "shapely", "matplotlib", "seaborn"
    ]

    print("Checking Python dependencies...")
    missing = []
    for package in required:
        try:
            __import__(package)
            print(f"  ✓ {package}")
        except ImportError:
            missing.append(package)
            print(f"  ✗ {package}")

    if missing:
        print(f"\nMissing packages: {missing}")
        print(f"Install with: pip install {' '.join(missing)}")
        return 1
    print("\n✓ All dependencies satisfied")
    return 0


def _resolve_python(project_root):
    """Return the project venv Python if available, else sys.executable."""
    for venv_dir in ('.venv', 'venv'):
        candidate = os.path.join(str(project_root), venv_dir, 'bin', 'python')
        if os.path.isfile(candidate):
            return candidate
    return sys.executable


def cmd_test(args):
    """Run tests and produce audit evidence package.

    Suite selectors: --unit, --e2e, --lineage, --all
    Output options:  --audit, --pdf, --params, --check-deps
    Filters:         --model X Y Z
    """
    # ---- Backward compatibility for deprecated flags ----
    if getattr(args, '_compat_test', False):
        print('WARNING: --test is deprecated, use --unit instead', file=sys.stderr)
        args.unit = True
    if getattr(args, '_compat_code', False):
        print('WARNING: --code is deprecated, use --audit instead', file=sys.stderr)
        args.audit = True

    # ---- Handle --check-deps early exit ----
    if getattr(args, 'check_deps', False):
        return _check_deps()

    # ---- Handle --params early exit ----
    if getattr(args, 'params', False):
        print('Generating parameter inventory...')
        cmd = [sys.executable, '-m', 'docs.models.parameter_inventory.generator']
        if getattr(args, 'pdf', False):
            cmd.append('--pdf')
        project_root = config.get_project_root()
        result = sp.run(cmd, cwd=str(project_root))
        return result.returncode

    project_root = config.get_project_root()

    # All artefacts land in data/output/audit/
    audit_dir = str(config.get_reports_dir('audit'))
    os.makedirs(audit_dir, exist_ok=True)

    junit_xml = os.path.join(audit_dir, 'junit.xml')
    cov_html  = os.path.join(audit_dir, 'coverage')
    cov_xml   = os.path.join(audit_dir, 'coverage.xml')

    # ---- Resolve which suites and outputs to run ----
    has_suite = (getattr(args, 'unit', False) or getattr(args, 'e2e', False)
                 or getattr(args, 'lineage', False) or getattr(args, 'run_all', False))
    has_output = getattr(args, 'audit', False)

    if not has_suite and not has_output:
        # No flags at all → default to everything
        args.run_all = True
        args.audit = True

    do_unit    = getattr(args, 'run_all', False) or getattr(args, 'unit', False)
    do_e2e     = getattr(args, 'run_all', False) or getattr(args, 'e2e', False)
    do_lineage = getattr(args, 'run_all', False) or getattr(args, 'lineage', False)
    do_audit   = getattr(args, 'audit', False)
    do_pdf     = getattr(args, 'pdf', False)

    # ---- Capture git commit SHA ----
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

    # ---- Banner ----
    print('=' * 60)
    print('MKM Research Labs — Test & Audit')
    print('=' * 60)
    if git_sha:
        print(f' Git SHA : {git_sha[:12]}')
    print(f' Output  : {audit_dir}')
    phases = []
    if do_lineage:
        phases.append('lineage')
    if do_unit:
        phases.append('unit')
    if do_e2e:
        phases.append('e2e')
    if do_audit:
        phases.append('audit reports')
    print(f' Phases  : {", ".join(phases)}')
    print()

    _python_exe = _resolve_python(project_root)
    pytest_ok = True
    coverage_pct = None
    data_lineage_results = None
    e2e_results = None

    # ------------------------------------------------------------------
    # 1. Data lineage consistency checks (BCBS 239 P3)
    # ------------------------------------------------------------------
    if do_lineage:
        print('Running data lineage consistency checks...')
        data_lineage_results = _run_data_lineage_tests(project_root, audit_dir)
        if data_lineage_results and data_lineage_results.get('failed', 0) > 0:
            print()
            print('  WARNING: Data lineage checks FAILED.')
            print('  Pipeline data is inconsistent — audit results may be unreliable.')
            print('  Regenerate data in order: port --gauge → port --stressm → port --hazard → port --blotter')
            print()

    # ------------------------------------------------------------------
    # 2. Unit / model tests with coverage
    # ------------------------------------------------------------------
    if do_unit:
        print('Running unit/model tests with coverage...')

        tests_dir = os.path.join(str(project_root), 'tests')
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

        # Parse coverage percentage
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

        # Write test failures report
        _write_failures_report(junit_xml, audit_dir)

    # ------------------------------------------------------------------
    # 3. E2E browser tests (Playwright)
    # ------------------------------------------------------------------
    if do_e2e:
        print('\nRunning E2E browser tests (Playwright)...')
        e2e_results = _run_e2e_tests(project_root, audit_dir, _python_exe)

    # ------------------------------------------------------------------
    # 4. Audit reports (doc generators)
    # ------------------------------------------------------------------
    if do_audit:
        # If we didn't run unit tests this time, try to read existing coverage
        if coverage_pct is None and os.path.exists(cov_xml):
            try:
                import xml.etree.ElementTree as ET
                tree = ET.parse(cov_xml)
                root = tree.getroot()
                line_rate = float(root.get('line-rate', 0))
                coverage_pct = line_rate * 100
                print(f' Coverage (from existing xml): {coverage_pct:.1f}%')
            except Exception:
                pass

        # 4a. Model test documentation (LaTeX)
        print('\nGenerating model documentation...')
        doc_cmd = [_python_exe, '-m', 'docs.models.test_results.generator']
        if do_pdf:
            doc_cmd.append('--pdf')
        if git_sha:
            doc_cmd.extend(['--git-sha', git_sha])
        if coverage_pct is not None:
            doc_cmd.extend(['--coverage-pct', f'{coverage_pct:.2f}'])
        e2e_xml = os.path.join(audit_dir, 'e2e_junit.xml')
        if os.path.exists(e2e_xml):
            doc_cmd.extend(['--e2e-junit', e2e_xml])
        sp.run(doc_cmd, cwd=str(project_root))

        # Copy generated PDF into audit directory
        _test_report_pdf = os.path.join(
            str(project_root),
            'docs', 'models', 'test_results', 'test_results', 'test_report.pdf')
        if os.path.exists(_test_report_pdf):
            dest = os.path.join(audit_dir, 'test_report.pdf')
            shutil.copy2(_test_report_pdf, dest)
            print(f' Copied test_report.pdf → {dest}')

        # 4b. Code modularisation analysis
        print('\nGenerating code modularisation analysis...')
        sp.run([sys.executable, '-m', 'docs.models.project'], cwd=str(project_root))

        # 4c. Code duplication report
        print('\nGenerating code duplication analysis...')
        sp.run([sys.executable, '-m', 'docs.models.duplication'], cwd=str(project_root))

        # 4d. Hard-coding parameter audit
        print('\nGenerating hard-coding parameter audit...')
        sp.run([sys.executable, '-m', 'docs.models.hardcoding'], cwd=str(project_root))

        # 4e. Data lineage report (BCBS 239)
        print('\nGenerating data lineage report (BCBS 239)...')
        sp.run([sys.executable, '-m', 'docs.models.data_lineage'], cwd=str(project_root))

        # 4f. Full consolidated audit report
        print('\nGenerating full audit report...')
        sp.run([sys.executable, '-m', 'docs.models.full_audit'], cwd=str(project_root))

    # ------------------------------------------------------------------
    # 5. Summary
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
    if do_unit:
        print('Status:', 'ALL PASS' if pytest_ok else 'TEST FAILURES — see junit.xml')
