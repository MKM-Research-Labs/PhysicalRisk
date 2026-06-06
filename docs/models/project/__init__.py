# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

"""
Code File Size Analysis — Project Modularisation Reports.

Produces two artefacts:

  large_file_report.pdf   — PDF scanning root/src/ for files exceeding 300
                            lines.  Written to data/output/audit/.

  large_test_report.txt   — Plain-text equivalent scanning root/tests/ for
                            files exceeding 300 lines.  Written to
                            data/output/audit/.

Usage:
    python -m docs.models.project
"""

from ._constants import (
    CODE_EXTENSIONS,
    EXCLUDED_FOLDERS,
    MIN_LINES,
    FileInfo,
    InitIssue,
)
from .analysis import count_lines, analyze_code_files, analyze_init_files
from .pdf import _add_init_audit_section, create_pdf_report
from .report import generate_txt_report, main

__all__ = [
    'CODE_EXTENSIONS', 'EXCLUDED_FOLDERS', 'MIN_LINES', 'FileInfo', 'InitIssue',
    'count_lines', 'analyze_code_files', 'analyze_init_files',
    '_add_init_audit_section', 'create_pdf_report', 'generate_txt_report', 'main',
]
