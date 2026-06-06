# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""Shared HTML helper functions (sectionHeader, infoRow)."""

from visual.interactivity._jsbundle import js_static


def get_helpers_js():
    """Return JS for shared HTML helpers."""
    return js_static('governance/models/mg_detail_tabs/helpers.js')
