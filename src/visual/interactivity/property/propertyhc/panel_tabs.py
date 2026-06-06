# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

"""Tab switching — ensureCanvas(), switchTab(), renderBasisExplorer(), renderBasisSubTab()."""

from visual.interactivity._jsbundle import js_static


def get_js() -> str:
    """Return JS for tab switching and Basis Explorer sub-tab management."""
    return js_static('property/propertyhc/panel_tabs.js')
