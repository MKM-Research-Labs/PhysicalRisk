# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""Combined JS fragment for the PRS cashflow engine and chart rendering."""

from .engine import get_engine_js
from .renderer import get_renderer_js


def get_js() -> str:
    """Return JS fragment for PRS cashflow engine and chart rendering."""
    return get_engine_js() + get_renderer_js()
