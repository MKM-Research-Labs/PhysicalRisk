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

"""Section builders for the model risk governance report."""

from .cover import build_cover
from .executive import build_exec_summary
from .inventory import build_model_inventory
from .validation import build_validation_status
from .mrc import build_mrc_activity
from .remediation import build_remediation
from .bcbs239 import build_bcbs239
from .raci import build_raci
from .testing import build_test_evidence
from .audit_trail import build_audit_trail
from .documents import build_document_inventory
from .recommendations import build_recommendations

__all__ = [
    'build_cover',
    'build_exec_summary',
    'build_model_inventory',
    'build_validation_status',
    'build_mrc_activity',
    'build_remediation',
    'build_bcbs239',
    'build_raci',
    'build_test_evidence',
    'build_audit_trail',
    'build_document_inventory',
    'build_recommendations',
]
