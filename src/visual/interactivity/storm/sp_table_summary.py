# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

"""
Storm portfolio Table tab — Summary sub-tab JS.

Single-view "report card" for the selected storm. Aggregates from the
caches already populated by the other sub-tabs (spData,
spCommercialImpact, spBlotterData, spCommercialData, spTradesData), so
opening Summary does not refetch — it just reads what's there. Anything
not yet loaded gets a kicked-off fetch and the panel re-renders when
the data arrives.
"""

from visual.interactivity._jsbundle import js_static


def get_js() -> str:
    """Return JS fragment for the Summary report card (parent IIFE scope)."""
    return js_static('storm/sp_table_summary.js')
