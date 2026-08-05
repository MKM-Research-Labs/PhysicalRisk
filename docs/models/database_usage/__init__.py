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

"""Standalone database-usage audit report.

Reuses the 4.6 scanner (``docs.models.full_audit.sections_tests.database_usage``)
so the standalone PDF and the consolidated full-audit subsection report identical
numbers. Invoke via ``python -m docs.models.database_usage``."""

from datetime import datetime

from docs.models.full_audit.sections_tests.database_usage import scan_repo
from .pdf import create_pdf_report


def main():
    from config import config
    root = config.get_project_root()

    audit_dir = config.get_reports_dir('audit')
    audit_dir.mkdir(parents=True, exist_ok=True)
    output_path = audit_dir / 'database_usage_report.pdf'

    print('Scanning first-party source for database-seam usage...')
    scan = scan_repo(root)
    print(f"  {scan['scanned']} files scanned")
    print(f"  {len(scan['caller_files'])} module(s) call the database seam "
          f"({len(scan['calls'])} call sites)")
    print(f"  {len(scan['used_funcs'])}/{len(scan['api_names'])} public API "
          f"symbols used ({len(scan['unused_funcs'])} never called)")
    print(f"  {len(scan['json_io_files'])} module(s) still on .json "
          f"(the 4.5 complement); {len(scan['both_files'])} do both")

    from ..full_audit.results_json import write_results
    write_results('database_usage', {
        'files_scanned': scan['scanned'],
        'seam_caller_modules': len(scan['caller_files']),
        'call_sites': len(scan['calls']),
        'api_used': len(scan['used_funcs']),
        'api_total': len(scan['api_names']),
        'json_only_modules': len(scan['json_io_files']),
        'both_modules': len(scan['both_files']),
    })
    generated = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    create_pdf_report(scan, output_path, root, generated)
    size_kb = output_path.stat().st_size / 1024
    print(f' Written: {output_path}  ({size_kb:.1f} KB)')
    return output_path
