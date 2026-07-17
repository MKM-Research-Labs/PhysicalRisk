# Copyright (c) 2022-2026 MKM Research Labs.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

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
