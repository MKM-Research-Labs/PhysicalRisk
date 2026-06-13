# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

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
