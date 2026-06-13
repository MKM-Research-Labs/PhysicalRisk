# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""Combined JS fragment for the trading stress-test charts."""

from .probability import get_probability_chart_js
from .pnl import get_pnl_chart_js
from .surface import get_surface_table_js


def get_js() -> str:
    """Return JavaScript fragment for stress test charts."""
    return (get_probability_chart_js() +
            get_pnl_chart_js() +
            get_surface_table_js())
