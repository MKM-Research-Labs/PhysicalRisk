# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""Compose all market tab sub-module JavaScript."""

from . import setup, render, actions


def get_js() -> str:
    """Return JavaScript fragment for the market tab."""
    return (setup.get_js() +
            render.get_js() +
            actions.get_js())
