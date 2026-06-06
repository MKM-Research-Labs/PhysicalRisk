# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

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
