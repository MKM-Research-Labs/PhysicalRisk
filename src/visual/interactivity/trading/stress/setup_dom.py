# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""Stress Test — DOM construction for the stress view."""

from config.format import percentile_selector_html as _pct_html

from visual.interactivity._jsbundle import js_static


def get_js() -> str:
    """Return JavaScript for createStressView() DOM builder."""
    return js_static('trading/stress/setup_dom.js').replace(
        '__PCT_HTML__', _pct_html('td-stress-pct', 'td-stress-storm'))
