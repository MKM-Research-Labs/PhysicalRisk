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
Copyright Header Audit — License-Header Governance Report.

Scans every first-party ``.py`` and ``.js`` source file and enforces the exact
19-line MKM Research Labs license header from ``docs/shared/copyright.py``.  Any
file whose header is missing or differs is rewritten in place, and the audit
records, per file: (a) the header was wrong, (b) it was replaced, (c) the file
is now compatible.

Output:  data/output/audit/copyright_headers_report.pdf
         data/output/audit/copyright_headers_record.json

Usage:
    python -m docs.models.copyright_headers
"""

from .scanners import (
    canonical_source_path,
    load_canonical_py,
    canonical_lines,
    is_compliant,
    fix_text,
    iter_source_files,
    fix_repo,
)
from .pdf import create_pdf_report
from .report import main

__all__ = [
    'canonical_source_path', 'load_canonical_py', 'canonical_lines',
    'is_compliant', 'fix_text', 'iter_source_files', 'fix_repo',
    'create_pdf_report', 'main',
]
