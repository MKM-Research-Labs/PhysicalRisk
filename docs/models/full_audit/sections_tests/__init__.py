# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

"""Test suite detail, coverage analysis, and modularisation sections.

Split into cohesive submodules; the public surface (the ``_build_*`` section
builders imported by ``report.py`` / the package ``__init__``) is unchanged.
"""

from .detail import (
    _build_test_detail, _build_unit_failures, _build_skipped_tests, _short_msg,
)
from .coverage import _build_coverage
from .modularisation import _build_modularisation, _build_init_audit

__all__ = [
    '_build_test_detail', '_build_unit_failures', '_build_skipped_tests',
    '_short_msg', '_build_coverage', '_build_modularisation', '_build_init_audit',
]
