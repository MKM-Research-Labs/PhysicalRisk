# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

"""Standalone __init__.py substantive-code audit report package.

  python -m docs.models.init_audit

writes init_audit_report.pdf and init_audit_results.json to data/output/audit/.
"""

from .report import main

__all__ = ['main']
