# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

"""
Lineage validation — staleness detection and prerequisite checks.

Supports BCBS 239 Principle 6 (timeliness) by detecting when upstream data
has changed since a downstream step was last executed.
"""

# Re-export manifest symbols so that test patches targeting
# ``lineage.validation.load_manifest`` etc. land correctly.
from lineage.manifest import (  # noqa: F401
    DEPENDENCY_GRAPH,
    STEP_IO,
    hash_directory,
    hash_file,
    load_manifest,
)

from lineage.validation._helpers import (  # noqa: F401
    _find_producer,
    _outputs_exist,
)
from lineage.validation.freshness import (  # noqa: F401
    check_inputs_fresh,
    check_step_prerequisites,
    get_stale_downstream,
)
from lineage.validation.prerequisites import resolve_prerequisites  # noqa: F401
from lineage.validation.completeness import (  # noqa: F401
    check_pipeline_complete,
    validate_full_chain,
)
