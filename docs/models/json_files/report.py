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

"""Entry point: scan first-party source and write the standalone json-file PDF.

Invoke via ``python -m docs.models.json_files``. Reuses the §4.5 scanner so the
standalone report and the consolidated full-audit subsection report identical
numbers."""

from datetime import datetime

from docs.models.full_audit.sections_tests.json_files import scan_repo
from .pdf import create_pdf_report


def main():
    from config import config
    root = config.get_project_root()

    audit_dir = config.get_reports_dir('audit')
    audit_dir.mkdir(parents=True, exist_ok=True)
    output_path = audit_dir / 'json_files_report.pdf'

    print('Scanning first-party source for .json file I/O...')
    scan = scan_repo(root)
    print(f"  {scan['scanned']} files scanned")
    print(f"  {len(scan['io_files'])} I/O backlog file(s) "
          f"({scan['reads']} load, {scan['writes']} create/update)")
    print(f"  {scan['refs']} bare path reference(s)")

    generated = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    create_pdf_report(scan, output_path, root, generated)
    size_kb = output_path.stat().st_size / 1024
    print(f' Written: {output_path}  ({size_kb:.1f} KB)')
    return output_path
