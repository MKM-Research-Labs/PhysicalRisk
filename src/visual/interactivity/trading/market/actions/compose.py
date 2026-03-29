# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""Compose all market tab action sub-module JavaScript."""

from . import commit, curve_history, inputs, new_trade, pl_history, reset


def get_js() -> str:
    """Return JS fragment for all market tab actions."""
    return (inputs.get_js() +
            reset.get_js() +
            commit.get_js() +
            new_trade.get_js() +
            pl_history.get_js() +
            curve_history.get_js())
