# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""
Client tab — table rendering sub-module.

Property PRS trade table with columns for property details and pricing.
"""

from visual.interactivity._jsbundle import js_static


def get_js() -> str:
    """Return JavaScript fragment for client table rendering."""
    return js_static('trading/client/table.js')
