# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""Version history tab — timeline view of model versions."""

from visual.interactivity._jsbundle import js_static


def get_version_history_js():
    """Return JS for renderVersionHistoryTab."""
    return js_static('governance/models/mg_detail_tabs/version_history.js')
