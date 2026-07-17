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

"""End-of-run PDF report generation + final lineage validation."""

from config import config


def run_pdf_reports(args, output_dir, run_all):
    """Generate the port PDF + PRS portfolio PDF reports."""
    if not (args.pdf or run_all):
        return
    try:
        from reports.port import PortReportGenerator
        # Port/PRS deliverables are not part of the `app.py test` audit
        # sequence — keep them out of the audit root, under audit/archive/.
        archive_dir = config.get_output_dir() / 'audit' / 'archive'
        archive_dir.mkdir(parents=True, exist_ok=True)
        pdf_path = archive_dir / f'port_{config.catchment_id}.pdf'
        gen = PortReportGenerator(input_dir=output_dir, output_path=pdf_path)
        result_path = gen.generate()
        print(f"\n  PDF report: {result_path}")
    except Exception as e:
        print(f"\n  PDF report failed: {e}")
        return

    # PRS portfolio report
    try:
        from reports.port.prs_report import PRSPortfolioReport
        prs_path = archive_dir / 'prs_portfolio_report.pdf'
        prs_gen = PRSPortfolioReport(input_dir=output_dir, output_path=prs_path)
        prs_result = prs_gen.generate()
        print(f"  PRS report: {prs_result}")
    except Exception as e:
        print(f"  PRS report failed: {e}")


def run_lineage_chain_validation():
    """Print stale-step warnings at end of run."""
    try:
        from lineage.validation import validate_full_chain
        chain = validate_full_chain()
        if not chain["is_consistent"]:
            print(f"\n  ⚠ Data lineage: {len(chain['stale_steps'])} stale step(s)")
            for s in chain["stale_steps"]:
                print(f"    - {s}")
        else:
            print(f"\n  ✓ Data lineage: all steps consistent")
    except Exception:
        pass
