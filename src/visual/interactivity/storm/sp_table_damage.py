# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

"""
Storm portfolio Table tab — Flood Damage sub-tab JS.

Combined residential + commercial per-storm damage table.  The
residential rows come from the propertyts portfolio-impact endpoint
(already loaded into ``spData`` by the storm-change handler in
sp_table.py); the commercial rows are fetched on demand from the
matching commercial endpoint and cached in ``spCommercialImpact``.
"""

from visual.interactivity._jsbundle import js_static


def get_js() -> str:
    """Return JS fragment for the Flood Damage sub-tab (parent IIFE scope)."""
    return js_static('storm/sp_table_damage.js')
