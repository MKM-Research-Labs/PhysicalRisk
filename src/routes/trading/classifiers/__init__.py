# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package root __init__.py for full license text)

"""Classifier management endpoints for the Trading Desk."""

from . import summary         # noqa: E402, F401
from . import batch_training  # noqa: E402, F401

# Re-export internals used by tests
from .batch_training import (  # noqa: E402
    _load_timings, _save_timings, _avg_per_gauge_seconds,
    _run_batch_training,
)
from .summary import _compute_data_version  # noqa: E402
