# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

"""Async data loading — loadData() JS function."""

from visual.interactivity._jsbundle import js_static


def get_js() -> str:
    """Return JS for the loadData() async function."""
    return js_static('property/propertyhc/panel_data.js')
