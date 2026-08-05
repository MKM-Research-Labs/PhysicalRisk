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

"""Entry point: scan all non-test source and write the embedded JS/CSS audit PDF."""

from pathlib import Path

from .scanners import collect_all_repo
from .pdf import create_pdf_report


def main():
    from config import config
    root = config.get_project_root()
    audit_dir = config.get_reports_dir('audit')
    audit_dir.mkdir(parents=True, exist_ok=True)
    output_path = audit_dir / 'embedded_js_report.pdf'

    print("Scanning all non-test source for embedded JS/CSS...")
    findings = collect_all_repo(root)

    total = (len(findings['scripts']) + len(findings['styles'])
             + len(findings['factories']))
    print(f"  {findings['files_scanned']} files scanned")
    print(f"  {len(findings['scripts'])} inline <script> blocks")
    print(f"  {len(findings['styles'])} inline <style> blocks")
    print(f"  {len(findings['factories'])} JS factory strings")
    print(f"  {total} total action items across {findings['files_flagged']} files")

    from ..full_audit.results_json import write_results
    write_results('embedded_js', {
        'files_scanned': findings['files_scanned'],
        'inline_scripts': len(findings['scripts']),
        'inline_styles': len(findings['styles']),
        'js_factories': len(findings['factories']),
        'total_action_items': total,
        'files_flagged': findings['files_flagged'],
    })
    create_pdf_report(findings, output_path, root)
