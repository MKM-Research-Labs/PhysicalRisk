# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""Panel data loading — loadHazardData() async function."""

from visual.interactivity._jsbundle import js_static

from config.format import gauge_title_js as _gauge_title_js

_GAUGE_TITLE = _gauge_title_js('gName', 'gaugeId')


def get_data_js() -> str:
    """Return JS that defines the loadHazardData() async function."""
    return (js_static('gauge/gaugehc/panel_data.js').replace('__GAUGE_TITLE__', _GAUGE_TITLE))
