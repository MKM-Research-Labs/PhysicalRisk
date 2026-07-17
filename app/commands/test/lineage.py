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

"""Data-lineage consistency check runner (BCBS 239 P3)."""

import os
import sys
import subprocess as sp


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
