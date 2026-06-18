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
