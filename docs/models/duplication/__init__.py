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

"""Code duplication analysis report generator.

Runs jscpd on src/ and produces a PDF summary saved to data/output/audit/.

Usage:
    python -m docs.models.duplication
"""

from ._paths import (
    ROOT_DIR,
    SRC_DIR,
    AUDIT_DIR,
    OUTPUT_PDF,
    MIN_LINES,
    MIN_TOKENS,
)
from .jscpd_runner import _find_node_env, _run_jscpd, _jscpd_version
from .analyse import _analyse
from .pdf import _make_pdf
from .report import main

__all__ = [
    'ROOT_DIR', 'SRC_DIR', 'AUDIT_DIR', 'OUTPUT_PDF', 'MIN_LINES', 'MIN_TOKENS',
    '_find_node_env', '_run_jscpd', '_jscpd_version', '_analyse', '_make_pdf', 'main',
]
