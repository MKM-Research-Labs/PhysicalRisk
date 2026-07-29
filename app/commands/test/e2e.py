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

"""Playwright E2E browser-test runner (batched, headless)."""

import os
import sys
import shutil
import subprocess as sp

from .reports import _write_combined_junit


def _run_e2e_tests(project_root, audit_dir, python_exe):
    """Run Playwright e2e tests headless and return summary dict."""
    import json
    import xml.etree.ElementTree as ET

    # All E2E artefacts (combined + per-batch JUnit, results JSON) live in a
    # dedicated audit/e2e/ subfolder to keep the audit root uncluttered.
    e2e_out_dir = os.path.join(audit_dir, 'e2e')
    os.makedirs(e2e_out_dir, exist_ok=True)
    e2e_xml = os.path.join(e2e_out_dir, 'e2e_junit.xml')
    e2e_dir = os.path.join(str(project_root), 'tests', 'e2e')

    if not os.path.isdir(e2e_dir):
        print('  Skipped: tests/e2e/ directory not found')
        return None

    # Check if playwright Python package is installed.
    # Use sys.executable (the Python that launched phys.py) rather than the
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
            report_path = os.path.join(e2e_out_dir, 'e2e_results.json')
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
            report_path = os.path.join(e2e_out_dir, 'e2e_results.json')
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
        batch_xml = os.path.join(e2e_out_dir, f'e2e_junit_batch{batch_idx}.xml')
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
    report_path = os.path.join(e2e_out_dir, 'e2e_results.json')
    try:
        with open(report_path, 'w') as f:
            json.dump(summary, f, indent=2)
    except Exception:
        pass

    return summary
