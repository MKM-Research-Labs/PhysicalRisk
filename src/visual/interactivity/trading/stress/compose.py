# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""Compose all stress test tab sub-module JavaScript."""

from . import charts, setup, stats, table, training_ui


def get_js() -> str:
    """Return JavaScript fragment for the stress test tab."""
    return (training_ui.get_js() +
            setup.get_js() +
            charts.get_js() +
            table.get_js() +
            stats.get_js())
