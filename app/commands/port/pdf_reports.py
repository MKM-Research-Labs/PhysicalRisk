# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see auth.py for full license text)

"""End-of-run PDF report generation + final lineage validation."""

from config import config


def run_pdf_reports(args, output_dir, run_all):
    """Generate the port PDF + PRS portfolio PDF reports."""
    if not (args.pdf or run_all):
        return
    try:
        from reports.port import PortReportGenerator
        audit_dir = config.get_output_dir() / 'audit'
        audit_dir.mkdir(parents=True, exist_ok=True)
        pdf_path = audit_dir / f'port_{config.catchment_id}.pdf'
        gen = PortReportGenerator(input_dir=output_dir, output_path=pdf_path)
        result_path = gen.generate()
        print(f"\n  PDF report: {result_path}")
    except Exception as e:
        print(f"\n  PDF report failed: {e}")
        return

    # PRS portfolio report
    try:
        from reports.port.prs_report import PRSPortfolioReport
        prs_path = audit_dir / 'prs_portfolio_report.pdf'
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
