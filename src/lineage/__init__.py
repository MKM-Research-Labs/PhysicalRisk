# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

"""
Data lineage tracking for BCBS 239 compliance.

Provides manifest recording, staleness validation, and provenance queries
for the portfolio generation pipeline.
"""

from lineage.manifest import (
    DEPENDENCY_GRAPH,
    STEP_IO,
    get_current_run_id,
    hash_directory,
    hash_file,
    load_manifest,
    record_step,
    save_manifest,
)
from lineage.query import (
    get_file_lineage,
    get_step_lineage,
    trace_data_point,
)
from lineage.validation import (
    check_inputs_fresh,
    check_pipeline_complete,
    check_step_prerequisites,
    get_stale_downstream,
    resolve_prerequisites,
    validate_full_chain,
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
