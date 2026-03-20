# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""Compose curves tab JavaScript."""

from . import curve_view


def get_js() -> str:
    """Return JavaScript fragment for the curves tab."""
    return curve_view.get_js()
