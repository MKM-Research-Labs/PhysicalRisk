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
from ._catchment import add_catchment_flags


def register_parser(subparsers):
    """Register the 'test' subcommand."""
    sp_test = subparsers.add_parser(
        "test", help="Run tests and produce audit evidence package",
        formatter_class=_HelpFormatter)

    # Catchment selection (--thames / --halong / --catchment-id ...).
    # Pins MKM_CATCHMENT for the test subprocesses so suites run against
    # the chosen catchment instead of the 'thames' default.
    add_catchment_flags(sp_test)

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
    """Run data lineage consistency tests and return summary dict."""
    import json
    import xml.etree.ElementTree as ET

    lineage_xml = os.path.join(audit_dir, 'data_lineage_junit.xml')
    lineage_test_dir = os.path.join(str(project_root), 'tests', 'data')
    import glob as _glob
    lineage_test_files = sorted(
        _glob.glob(os.path.join(lineage_test_dir, 'test_id_consistency_*.py'))
    )

    if not lineage_test_files:
        print('  Skipped: no test_id_consistency_*.py files found')
        return None

    _venv_python = os.path.join(str(project_root), '.venv', 'bin', 'python')
    if not os.path.isfile(_venv_python):
        _venv_python = os.path.join(str(project_root), 'venv', 'bin', 'python')
    _python_exe = _venv_python if os.path.isfile(_venv_python) else sys.executable

    cmd = [
        _python_exe, '-m', 'pytest',
        *lineage_test_files,
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


def _write_combined_junit(batch_xmls, output_path):
    """Merge batch JUnit XML files into a single combined file."""
    import xml.etree.ElementTree as ET

    root = ET.Element('testsuites')
    for xml_path in batch_xmls:
        if not os.path.exists(xml_path):
            continue
        try:
            tree = ET.parse(xml_path)
            for suite in tree.getroot().iter('testsuite'):
                root.append(suite)
        except Exception:
            continue
    try:
        ET.ElementTree(root).write(output_path, encoding='unicode',
                                   xml_declaration=True)
    except Exception:
        pass


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

    # Collect test files and run in batches to prevent a single stuck
    # test from blocking the entire suite.
    BATCH_SIZE = 15   # ~100 tests per batch (avg ~7 tests/file)
    BATCH_TIMEOUT = 1800  # 30 minutes per batch

    import glob as _glob
    test_files = sorted(_glob.glob(os.path.join(e2e_dir, 'test_*.py')))
    if not test_files:
        print('  Skipped: no test_*.py files in tests/e2e/')
        return None

    batches = [test_files[i:i + BATCH_SIZE]
               for i in range(0, len(test_files), BATCH_SIZE)]

    summary = {'total': 0, 'passed': 0, 'failed': 0, 'skipped': 0,
               'status': 'OK', 'failures': []}

    # Remove stale combined XML before batches
    if os.path.exists(e2e_xml):
        os.unlink(e2e_xml)

    # The E2E session fixture _isolated_catchment_dir copies
    # data/input/<catchment>/ (~7 GB for thames) into ``tmp_path_factory``
    # once per pytest invocation. With 4 batches that is 4 × 7 GB ≈ 28 GB
    # of redundant copies, which previously blew through 20 GB of free disk.
    # Wipe pytest's tmp tree between batches so each starts fresh and disk
    # never holds more than one catchment copy at a time.
    import getpass
    import tempfile
    pytest_tmp_root = os.path.join(
        tempfile.gettempdir(), f'pytest-of-{getpass.getuser()}')

    def _wipe_pytest_tmp() -> None:
        if os.path.isdir(pytest_tmp_root):
            shutil.rmtree(pytest_tmp_root, ignore_errors=True)

    all_xml_files = []
    for batch_idx, batch_files in enumerate(batches, 1):
        batch_xml = os.path.join(audit_dir, f'e2e_junit_batch{batch_idx}.xml')
        all_xml_files.append(batch_xml)
        n_files = len(batch_files)
        print(f'  Batch {batch_idx}/{len(batches)} ({n_files} files)...')

        cmd = [
            _pw_python, '-m', 'pytest',
            *batch_files,
            f'--junitxml={batch_xml}',
            '--browser', 'chromium',
            # Only retain Playwright artefacts when a test fails. With ~324
            # E2E tests this prevents trace/video/screenshot files from
            # filling $TMPDIR (previously caused ENOSPC mid-batch).
            '--tracing=retain-on-failure',
            '--video=retain-on-failure',
            '--screenshot=only-on-failure',
            '-v', '--tb=short',
        ]

        try:
            sp.run(cmd, cwd=str(project_root), timeout=BATCH_TIMEOUT)
        except sp.TimeoutExpired:
            print(f'  Batch {batch_idx} timed out (30 min limit) — continuing')
        except Exception as exc:
            print(f'  Batch {batch_idx} error: {exc} — continuing')
        finally:
            # Reclaim the ~7 GB catchment copy + any retained sessions
            # before the next batch starts.
            _wipe_pytest_tmp()

    # Merge all batch XMLs into the combined summary
    for xml_path in all_xml_files:
        if not os.path.exists(xml_path):
            continue
        try:
            tree = ET.parse(xml_path)
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
            print(f'  Warning: could not parse {os.path.basename(xml_path)}: {exc}')

    # Write combined JUnit XML for downstream consumers
    _write_combined_junit(all_xml_files, e2e_xml)

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


def _cleanup_worktree_data(project_root: str) -> None:
    """Remove data/input/ copies inside git worktrees (not the main repo).

    E2E tests spin up a Flask subprocess per worktree and write a full copy of
    data/input/<catchment>/ into each worktree's working tree.  Those copies
    are never tracked by git but can easily reach 6-7 GB each and accumulate
    across sessions.  This function wipes them after every test run.
    """
    try:
        result = sp.run(
            ['git', 'worktree', 'list', '--porcelain'],
            capture_output=True, text=True, cwd=project_root,
        )
        if result.returncode != 0:
            return

        # Parse worktree paths — each block starts with "worktree <path>"
        worktree_paths = [
            line[len('worktree '):].strip()
            for line in result.stdout.splitlines()
            if line.startswith('worktree ')
        ]

        freed_bytes = 0
        cleaned = []
        for wt_path in worktree_paths:
            if os.path.realpath(wt_path) == os.path.realpath(project_root):
                continue  # skip main repo

            # CRITICAL: a worktree's `data/` may be a symlink to shared
            # storage (e.g. an external SSD that every checkout points at).
            # Following it would make the rmtree below delete the REAL shared
            # catchment data, not a disposable per-worktree copy.  Skip any
            # worktree whose data dir is a symlink, or whose resolved
            # data/input path escapes the worktree directory.
            wt_data = os.path.join(wt_path, 'data')
            if os.path.islink(wt_data):
                print(f'  Skipping {wt_path}: data/ is a symlink '
                      f'(would follow to shared storage)')
                continue
            data_input = os.path.join(wt_path, 'data', 'input')
            if not os.path.isdir(data_input):
                continue
            wt_real = os.path.realpath(wt_path)
            if not os.path.realpath(data_input).startswith(wt_real + os.sep):
                print(f'  Skipping {data_input}: resolves outside worktree '
                      f'({os.path.realpath(data_input)})')
                continue
            for catchment in os.listdir(data_input):
                catchment_dir = os.path.join(data_input, catchment)
                if not os.path.isdir(catchment_dir):
                    continue
                # Belt-and-braces: never delete through a per-catchment symlink.
                if os.path.islink(catchment_dir):
                    continue
                try:
                    # du -s equivalent using os.walk
                    size = sum(
                        os.path.getsize(os.path.join(dp, f))
                        for dp, _, fns in os.walk(catchment_dir)
                        for f in fns
                    )
                    shutil.rmtree(catchment_dir)
                    freed_bytes += size
                    cleaned.append(f'{wt_path} → data/input/{catchment}')
                except Exception as exc:
                    print(f'  WARNING: could not remove {catchment_dir}: {exc}')

        if cleaned:
            freed_gb = freed_bytes / (1024 ** 3)
            print(f'Worktree data cleanup: removed {len(cleaned)} data copy/copies '
                  f'({freed_gb:.1f} GB freed)')
            for entry in cleaned:
                print(f'  {entry}')
        else:
            print('Worktree data cleanup: nothing to remove.')

    except Exception as exc:
        print(f'WARNING: worktree data cleanup failed: {exc}')


def _parse_coverage_pct(cov_xml: str):
    """Return line coverage as a percentage from a coverage.xml, or None."""
    if not os.path.exists(cov_xml):
        return None
    try:
        import xml.etree.ElementTree as ET
        root = ET.parse(cov_xml).getroot()
        return float(root.get('line-rate', 0)) * 100
    except Exception:
        return None


def _run_audit_reports(project_root, audit_dir, python_exe, coverage_pct,
                       git_sha, do_pdf):
    """Phase 4: generate the audit doc artefacts — LaTeX/PDF model docs plus
    the modularisation, duplication, hard-coding, lineage and full-audit
    reports. ``python_exe`` (the venv Python) runs the model-doc generator;
    the code analyses run under ``sys.executable``, matching the original."""
    # If unit tests weren't run this time, fall back to an existing coverage xml.
    if coverage_pct is None:
        coverage_pct = _parse_coverage_pct(os.path.join(audit_dir, 'coverage.xml'))
        if coverage_pct is not None:
            print(f' Coverage (from existing xml): {coverage_pct:.1f}%')

    # 4a. Model test documentation (LaTeX)
    print('\nGenerating model documentation...')
    doc_cmd = [python_exe, '-m', 'docs.models.test_results.generator']
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

    # 4b-4f. Code analyses + consolidated audit
    for label, module in (
        ('code modularisation analysis',   'docs.models.project'),
        ('code duplication analysis',      'docs.models.duplication'),
        ('hard-coding parameter audit',    'docs.models.hardcoding'),
        ('embedded JS/CSS audit',          'docs.models.embedded_js'),
        ('data lineage report (BCBS 239)', 'docs.models.data_lineage'),
        ('full audit report',              'docs.models.full_audit'),
    ):
        print(f'\nGenerating {label}...')
        sp.run([sys.executable, '-m', module], cwd=str(project_root))


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

    # ---- Pin catchment for all test subprocesses ----
    # An explicit --<catchment> / --catchment-id flag wins; otherwise we
    # leave any existing MKM_CATCHMENT env var (or the 'thames' default)
    # untouched so non-interactive/CI runs keep working. The child pytest
    # and lineage processes inherit os.environ, so setting it here is
    # enough — no interactive prompt is forced for the test command.
    chosen_catchment = getattr(args, 'catchment_id', None)
    if chosen_catchment:
        available = config.list_catchments()
        if available and chosen_catchment not in available:
            print(f"\n  ✗ Unknown catchment '{chosen_catchment}'.")
            print(f"  Available: {', '.join(available)}")
            return 1
        os.environ['MKM_CATCHMENT'] = chosen_catchment
        config.catchment_id = chosen_catchment
    print(f" Catchment: {os.environ.get('MKM_CATCHMENT', 'thames')}")

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

    # Clean stale worktree data copies before tests start to free disk space
    print('--- Worktree data cleanup (pre-run) ---')
    _cleanup_worktree_data(str(project_root))
    print()

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
        coverage_pct = _parse_coverage_pct(cov_xml)
        if coverage_pct is not None:
            print(f' Coverage: {coverage_pct:.1f}%')

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
        _run_audit_reports(project_root, audit_dir, _python_exe,
                           coverage_pct, git_sha, do_pdf)

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
        ('Embedded JS/CSS PDF',    os.path.join(audit_dir, 'embedded_js_report.pdf')),
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

    # Clean up any worktree data copies created by E2E tests during this run
    print()
    print('--- Worktree data cleanup (post-run) ---')
    _cleanup_worktree_data(str(project_root))
