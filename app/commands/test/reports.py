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

"""JUnit-XML parsing and audit report-file writers."""

import os


def _write_failures_report(junit_xml_path: str, audit_dir: str) -> None:
    """Parse junit.xml and write test_failures_report.json for the audit tab header."""
    import json
    import xml.etree.ElementTree as ET
    from datetime import datetime

    report_path = os.path.join(audit_dir, 'test_failures_report.json')

    summary = {'total': 0, 'passed': 0, 'failed': 0, 'skipped': 0}
    failures = []
    skipped = []

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
                    classname = tc.get('classname', '')
                    # pytest puts the skip reason in @message (and/or the body).
                    reason = (skip_el.get('message', '') or
                              (skip_el.text or '')).strip()
                    if reason.startswith('Skipped: '):
                        reason = reason[len('Skipped: '):]
                    skipped.append({
                        'name': tc.get('name', ''),
                        'class': classname.split('.')[-1],
                        'file': classname.replace('.', '/') + '.py',
                        'reason': reason.split('\n')[0].strip() or '(no reason given)',
                    })
                else:
                    summary['passed'] += 1
        except Exception as exc:
            print(f' Warning: could not parse junit.xml for failures report: {exc}')

    report = {
        'generated_at': datetime.now().isoformat(),
        'summary': summary,
        'failures': failures,
        'skipped': skipped,
    }
    try:
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        print(f' Updated test_failures_report.json ({summary["total"]} tests, '
              f'{summary["failed"]} failures, {summary["skipped"]} skipped)')
    except Exception as exc:
        print(f' Warning: could not write test_failures_report.json: {exc}')


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
