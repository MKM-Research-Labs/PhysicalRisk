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
Data lineage manifest — records pipeline step execution with content hashes.

Each step records its inputs, outputs, parameters, and timing so that
downstream consumers can verify data freshness (BCBS 239 Principle 3).
"""

from ._core import (
    LINEAGE_PATH,
    hash_file,
    hash_directory,
    load_manifest,
    save_manifest,
    get_current_run_id,
    _hash_artifact,
    pre_hash_inputs,
    record_step,
    repair_manifest,
)
from ._topology import (
    DEPENDENCY_GRAPH,
    EXTERNAL_INPUTS,
    OPTIONAL_STEPS,
    STEP_IO,
)

__all__ = [
    "LINEAGE_PATH",
    "hash_file",
    "hash_directory",
    "load_manifest",
    "save_manifest",
    "get_current_run_id",
    "_hash_artifact",
    "pre_hash_inputs",
    "record_step",
    "repair_manifest",
    "DEPENDENCY_GRAPH",
    "EXTERNAL_INPUTS",
    "OPTIONAL_STEPS",
    "STEP_IO",
]
