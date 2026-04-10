# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""Compose all Control tab sub-module JavaScript."""

from . import setup_dom, setup_data


def get_js() -> str:
    """Return JavaScript fragment for the storm control tab."""
    return (
        """
            // ==============================================================
            // Tab 11: Control — Storm Sequence Parameter Control
            // ==============================================================
            var ctrlData = null;
            var ctrlDirty = false;
        """
        + setup_dom.get_js()
        + setup_data.get_js()
    )
