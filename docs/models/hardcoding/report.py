# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

"""Entry point: scan src/ and write the hard-coding audit PDF."""

from pathlib import Path

from .scanners import collect_all
from .pdf import create_pdf_report


def main():
    here = Path(__file__).resolve().parent           # docs/models/hardcoding/
    root = here.parent.parent.parent                 # project root

    src_dir   = root / 'src'
    from config import config
    audit_dir = config.get_reports_dir('audit')
    audit_dir.mkdir(parents=True, exist_ok=True)
    output_path = audit_dir / 'hardcoding_report.pdf'

    print("Scanning src/ for hard-coded parameters...")
    findings = collect_all(src_dir, root)

    caps_action   = [f for f in findings['allcaps'] if not f['precision_ok']]
    total_action = (
        len(findings['duplicates'])
        + len(caps_action)
        + len(findings['infra'])
        + len(findings['inline'])
    )
    print(f"  {findings['files_scanned']} files scanned")
    print(f"  {len(findings['duplicates'])} duplicate constants")
    print(f"  {len([f for f in findings['allcaps'] if not f['precision_ok']])} "
          f"ALL_CAPS outside config ({len([f for f in findings['allcaps'] if f['precision_ok']])} "
          f"precision-ok)")
    print(f"  {len(findings['infra'])} infrastructure literals")
    print(f"  {len(findings['inline'])} inline simulation literals")
    print(f"  {total_action} total action items")

    create_pdf_report(findings, output_path, root)
