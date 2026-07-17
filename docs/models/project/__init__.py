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
from .analysis import (
    count_lines, analyze_code_files, analyze_repo_files, analyze_init_files,
)
from .pdf import _add_init_audit_section, create_pdf_report
from .report import generate_txt_report, main

__all__ = [
    'CODE_EXTENSIONS', 'EXCLUDED_FOLDERS', 'MIN_LINES', 'FileInfo', 'InitIssue',
    'count_lines', 'analyze_code_files', 'analyze_repo_files', 'analyze_init_files',
    '_add_init_audit_section', 'create_pdf_report', 'generate_txt_report', 'main',
]
