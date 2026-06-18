# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial 
# research and educational use only. Any commercial use, including 
# but not limited to use in or for products or services offered for sale, 
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

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
