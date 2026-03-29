# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""Compose all blotter tab sub-module JavaScript."""

from . import actions, filters, setup, table


def get_js() -> str:
    """Return JavaScript fragment for the trade blotter tab."""
    return (setup.get_js() +
            filters.get_js() +
            table.get_js() +
            actions.get_js())
