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
Data lineage tracking for BCBS 239 compliance.

Provides manifest recording, staleness validation, and provenance queries
for the portfolio generation pipeline.
"""

from lineage.manifest import (
    DEPENDENCY_GRAPH,
    STEP_IO,
    hash_file,
    hash_directory,
    load_manifest,
    save_manifest,
    get_current_run_id,
    record_step,
)
from lineage.validation import (
    check_inputs_fresh,
    check_pipeline_complete,
    check_step_prerequisites,
    get_stale_downstream,
    resolve_prerequisites,
    validate_full_chain,
)
from lineage.query import (
    trace_data_point,
    get_file_lineage,
    get_step_lineage,
)

__all__ = [
    "DEPENDENCY_GRAPH",
    "STEP_IO",
    "hash_file",
    "hash_directory",
    "load_manifest",
    "save_manifest",
    "get_current_run_id",
    "record_step",
    "check_inputs_fresh",
    "check_pipeline_complete",
    "check_step_prerequisites",
    "get_stale_downstream",
    "resolve_prerequisites",
    "validate_full_chain",
    "trace_data_point",
    "get_file_lineage",
    "get_step_lineage",
]
