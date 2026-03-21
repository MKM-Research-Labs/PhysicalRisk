# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# Use, reproduction, distribution, or modification of this code is subject to
# the terms and conditions of the license agreement provided with this software.

"""
Model Risk Governance Report — Full MRC & Regulatory Audit Evidence.

Usage:
    python -m docs.models.model_risk
"""

from .data import collect_all, AUDIT_DIR, OUTPUT_PDF  # noqa: F401
from .report import create_pdf_report, main  # noqa: F401
