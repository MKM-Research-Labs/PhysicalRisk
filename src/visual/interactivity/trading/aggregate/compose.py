# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""Compose aggregate view tab JavaScript."""

from . import map_view


def get_js() -> str:
    """Return JavaScript fragment for the aggregate view tab."""
    return map_view.get_js()
