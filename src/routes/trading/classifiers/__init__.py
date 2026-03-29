# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package root __init__.py for full license text)

"""Classifier management endpoints for the Trading Desk."""

from . import (
    batch_training,  # noqa: E402, F401
    summary,  # noqa: E402, F401
)

# Re-export internals used by tests
from .batch_training import (  # noqa: E402
    _avg_per_gauge_seconds as _avg_per_gauge_seconds,
)
from .batch_training import (
    _load_timings as _load_timings,
)
from .batch_training import (
    _run_batch_training as _run_batch_training,
)
from .batch_training import (
    _save_timings as _save_timings,
)
from .summary import _compute_data_version as _compute_data_version  # noqa: E402
