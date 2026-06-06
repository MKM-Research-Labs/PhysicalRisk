# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""Overall Risk Rating tab — composite assessment with MRC override."""

from visual.interactivity._jsbundle import js_static


def get_js():
    """Return JS fragment for risk rating interactive features."""
    return js_static('governance/models/mg_validation/risk_rating.js')
