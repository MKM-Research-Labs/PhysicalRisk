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

"""Render the Header section of an asset (PropertyID, UPRN, CatchmentID …)."""

from typing import Any, Dict, List

from ._helpers import auto_rows, section_block

_HEADER_FIELDS = [
    ("PropertyID",     "Property ID"),
    ("UPRN",           "UPRN"),
    ("USRN",           "USRN"),
    ("CatchmentID",    "Catchment"),
    ("propertyType",   "Property Type"),
    ("propertyStatus", "Status"),
]


def render_header(header: Dict[str, Any], page) -> List:
    """Build the header identity table from the asset's Header dict."""
    return section_block(
        "Asset Identity",
        page,
        auto_rows(header, _HEADER_FIELDS),
        style="standard",
        header=("Identifier", "Value"),
    )
