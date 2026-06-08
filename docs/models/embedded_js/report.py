# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

"""Entry point: scan all non-test source and write the embedded JS/CSS audit PDF."""

from pathlib import Path

from .scanners import collect_all_repo
from .pdf import create_pdf_report


def main():
    here = Path(__file__).resolve().parent           # docs/models/embedded_js/
    root = here.parent.parent.parent                 # project root

    from config import config
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

    create_pdf_report(findings, output_path, root)
