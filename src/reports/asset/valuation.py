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

"""Render the Valuation section of an asset."""

from typing import Any, Dict, List

from ._helpers import section_block


def render_valuation(valuation: Dict[str, Any], page, currency_symbol: str = "£") -> List:
    """Build the valuation table.

    ``currency_symbol`` lets the caller choose the prefix (£ for GBP,
    $ for USD, etc.) without this util needing to know the active
    catchment. Defaults to £ for backward compatibility with the
    existing thames property report.
    """
    value = valuation.get("PropertyValue")
    rows = [
        ("Property Value",
            page._format_currency(value, currency_symbol)
            if isinstance(value, (int, float)) else None),
        ("Valuation Date",   valuation.get("ValuationDate")),
        ("Valuation Method", valuation.get("ValuationMethod")),
    ]
    return section_block(
        "Valuation",
        page,
        rows,
        style="financial",
        header=("Metric", "Value"),
    )
