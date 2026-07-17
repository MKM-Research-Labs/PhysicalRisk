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

"""
Commercial asset layer for the visualization system.

Adds commercial-asset markers (office / multifamily / hotel / retail /
mixed-use / etc.) to the Folium map. Each marker uses a distinct icon
per CommercialType and a purple colour palette to distinguish from the
residential layer (which is green/orange/red by flood frequency).

Sub-modules:
- layer: CommercialLayer class
- popup: commercial marker popup HTML
- stats: per-type counts + total valuation
"""

from .layer import CommercialLayer  # noqa: F401
from .popup import create_commercial_popup  # noqa: F401
from .stats import get_commercial_statistics  # noqa: F401

__all__ = [
    "CommercialLayer",
    "create_commercial_popup",
    "get_commercial_statistics",
]
