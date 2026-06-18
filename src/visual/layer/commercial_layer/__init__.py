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
