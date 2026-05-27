# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Top-level convenience for generating a commercial report.

Mirrors src/reports/property/property_generator.py — loads the data,
locates the matching loan record, hands to CommercialReportGenerator.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from .generator import CommercialReportGenerator

logger = logging.getLogger(__name__)


def _load_commercial_record(
    property_id: str,
    catchment_input_dir: Path,
) -> Optional[Dict[str, Any]]:
    """Find a single commercial record by PropertyID."""
    commercial_path = catchment_input_dir / "commercial.json"
    if not commercial_path.exists():
        logger.error("commercial.json not found at %s", commercial_path)
        return None
    with open(commercial_path) as f:
        data = json.load(f)
    for record in data.get("commercial_assets", []):
        rec_pid = (record.get("CommercialAsset", {})
                         .get("Header", {})
                         .get("PropertyID"))
        if rec_pid == property_id:
            return record
    return None


def _load_loan_record(
    property_id: str,
    catchment_input_dir: Path,
) -> Optional[Dict[str, Any]]:
    """Find the commercial loan linked to the given PropertyID."""
    loan_path = catchment_input_dir / "commercial_loan.json"
    if not loan_path.exists():
        return None
    with open(loan_path) as f:
        data = json.load(f)
    for record in data.get("commercial_loans", []):
        rec_pid = (record.get("Mortgage", {})
                         .get("Header", {})
                         .get("PropertyID"))
        if rec_pid == property_id:
            return record
    return None


def generate_commercial_report(
    property_id: str,
    output_dir: Optional[Path] = None,
    open_pdf: bool = False,
) -> Optional[Path]:
    """Generate a commercial PDF report for the given asset.

    Reads commercial.json and commercial_loan.json from the active
    catchment's input dir. Returns the PDF path on success, None if
    the commercial record can't be found.
    """
    from config import config

    input_dir = config.get_input_dir()
    commercial = _load_commercial_record(property_id, input_dir)
    if commercial is None:
        logger.error("No commercial record for %s in %s", property_id, input_dir)
        return None
    loan = _load_loan_record(property_id, input_dir)

    generator = CommercialReportGenerator(output_dir=output_dir)
    pdf_path = generator.generate_report(commercial, loan)

    if open_pdf:
        try:
            from reports.utils.open_pdf import open_pdf_file
            open_pdf_file(pdf_path)
        except Exception as exc:
            logger.warning("Could not open PDF: %s", exc)

    return pdf_path
