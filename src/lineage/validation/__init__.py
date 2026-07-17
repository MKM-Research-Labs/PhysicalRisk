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
Lineage validation — staleness detection and prerequisite checks.

Supports BCBS 239 Principle 6 (timeliness) by detecting when upstream data
has changed since a downstream step was last executed.
"""

# Re-export manifest symbols so that test patches targeting
# ``lineage.validation.load_manifest`` etc. land correctly.
from lineage.manifest import (  # noqa: F401
    DEPENDENCY_GRAPH,
    OPTIONAL_STEPS,
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
