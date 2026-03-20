# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

"""Formatting utilities shared across claim report pages."""

from reportlab.lib import colors


def fmt_gbp(value: float) -> str:
    """Format a numeric value as a GBP currency string (e.g. £1,234)."""
    try:
        return f'\xa3{float(value):,.0f}'
    except (TypeError, ValueError):
        return str(value)


def seq_type_color(seq_type: str):
    """Return a reportlab Color for a given sequence type label."""
    mapping = {
        'isolated':  colors.lightblue,
        'doublet':   colors.lightyellow,
        'cluster':   colors.lightsalmon,
        'persistent': colors.mistyrose,
    }
    return mapping.get((seq_type or '').lower(), colors.white)
