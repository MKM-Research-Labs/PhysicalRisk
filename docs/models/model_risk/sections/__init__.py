# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# Use, reproduction, distribution, or modification of this code is subject to
# the terms and conditions of the license agreement provided with this software.

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
