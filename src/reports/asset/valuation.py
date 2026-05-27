# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

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
