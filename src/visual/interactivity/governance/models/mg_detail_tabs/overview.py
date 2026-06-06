# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""Overview tab — model details, governance status, testing, dependencies."""

from visual.interactivity._jsbundle import js_static


def get_overview_js():
    """Return JS for renderOverviewTab."""
    return js_static('governance/models/mg_detail_tabs/overview.js')
