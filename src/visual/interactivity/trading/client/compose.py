# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""Compose all client tab sub-module JavaScript."""

from . import setup, table


def get_js() -> str:
    """Return JavaScript fragment for the client (property PRS) tab."""
    return setup.get_js() + table.get_js()
