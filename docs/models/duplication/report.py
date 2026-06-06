# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

"""Entry point: run jscpd, analyse, and write the PDF report."""

import sys
from datetime import datetime


def main():
    # Resolve through the package namespace so callers (and tests) can patch
    # _run_jscpd / AUDIT_DIR / OUTPUT_PDF on the package itself.
    import docs.models.duplication as pkg

    print('Running jscpd on src/ …')
    try:
        report = pkg._run_jscpd()
    except Exception as e:
        print(f'ERROR running jscpd: {e}')
        sys.exit(1)

    print('Analysing results …')
    analysis = pkg._analyse(report)
    total = analysis['total']
    print(f"  Files: {total.get('sources', 0)}  |  "
          f"Lines: {total.get('lines', 0):,}  |  "
          f"Clones: {analysis['num_clones']}  |  "
          f"Dup%: {total.get('percentage', 0):.1f}%")

    print('Generating PDF …')
    run_at = datetime.now()
    pdf_bytes = pkg._make_pdf(analysis, run_at)

    pkg.AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    pkg.OUTPUT_PDF.write_bytes(pdf_bytes)
    print(f'PDF saved → {pkg.OUTPUT_PDF}')
    print(f'Size: {len(pdf_bytes) / 1024:.1f} KB')
