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

"""Test suite detail, coverage analysis, and modularisation sections.

Split into cohesive submodules; the public surface (the ``_build_*`` section
builders imported by ``report.py`` / the package ``__init__``) is unchanged.
"""

from .detail import (
    _build_test_detail, _build_unit_failures, _build_skipped_tests, _short_msg,
)
from .coverage import _build_coverage
from .modularisation import _build_modularisation, _build_init_audit
from .copyright_headers import _build_copyright_headers
from .path_definitions import _build_path_definitions
from .data_access import _build_data_access
from .json_files import _build_json_files
from .database_usage import _build_database_usage
from .model_chain import _build_model_chain

__all__ = [
    '_build_test_detail', '_build_unit_failures', '_build_skipped_tests',
    '_short_msg', '_build_coverage', '_build_modularisation', '_build_init_audit',
    '_build_copyright_headers', '_build_path_definitions', '_build_data_access',
    '_build_json_files', '_build_database_usage', '_build_model_chain',
]
