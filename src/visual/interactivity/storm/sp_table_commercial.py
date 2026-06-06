# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

"""
Storm portfolio Table tab — Commercial sub-tab JS.

Loads /api/v1/commercial/blotter and renders a summary card row plus a
sortable commercial-asset table.  The JS fragment is concatenated into
the parent ``sp_table.get_js()`` IIFE.
"""

from visual.interactivity._jsbundle import js_static


def get_js() -> str:
    """Return JS fragment for the Commercial sub-tab (parent IIFE scope)."""
    return js_static('storm/sp_table_commercial.js')
