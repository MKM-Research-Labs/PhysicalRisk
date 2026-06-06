# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""Panel chrome: creation, tab switching, show/hide, storm change handler."""

from visual.interactivity._jsbundle import js_static

from config.format import percentile_selector_html as _pct_html


def get_js() -> str:
    """Return JS for panel creation, tabs, show/hide."""
    _pct = _pct_html('sp-pct-sel', 'sp-storm-select')
    return js_static('storm/stormportfolio/chrome.js').replace('__SP_PCT_HTML__', _pct)
