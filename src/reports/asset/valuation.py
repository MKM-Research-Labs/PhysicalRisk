# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial 
# research and educational use only. Any commercial use, including 
# but not limited to use in or for products or services offered for sale, 
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

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
