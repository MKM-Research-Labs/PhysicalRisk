# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

"""
Storm portfolio Table tab — Wind Damage sub-tab JS.

Mirrors the Flood Damage sub-tab. Fetches per-storm wind impact from
``/api/v1/propertyts/<storm_id>/wind-impact`` and renders via the shared
``_renderDamageTable`` plumbing. Non-typhoon storms produce an empty
state ("No typhoon paired with this storm").
"""

from visual.interactivity._jsbundle import js_static


def get_js() -> str:
    """Return JS fragment for the Wind Damage sub-tab (parent IIFE scope)."""
    return js_static('storm/sp_table_wind.js')
