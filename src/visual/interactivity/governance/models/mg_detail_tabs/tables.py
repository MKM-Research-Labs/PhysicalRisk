# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""Table-based tabs: remediation, limitations, assumptions, changes, audit."""

from visual.interactivity._jsbundle import js_static


def get_tables_js():
    """Return JS for table-based tab renderers."""
    return js_static('governance/models/mg_detail_tabs/tables.js')
