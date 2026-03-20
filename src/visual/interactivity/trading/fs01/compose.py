# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""Compose FS01 risk matrix tab JavaScript."""

from . import grid


def get_js() -> str:
    """Return JavaScript fragment for the FS01 risk matrix tab."""
    return grid.get_js()
