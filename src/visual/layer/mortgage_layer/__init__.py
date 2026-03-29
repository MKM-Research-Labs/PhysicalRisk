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
Mortgage layer package for mortgage risk visualization.

Sub-modules:
- layer: MortgageLayer class
- circles: risk circle and LTV indicator drawing
- popup: popup HTML generation
- stats: portfolio statistics
"""

from .circles import add_ltv_indicators, add_mortgage_risk_circles, get_mortgage_risk_color  # noqa: F401
from .layer import MortgageLayer  # noqa: F401
from .popup import create_mortgage_circle_popup  # noqa: F401
from .stats import get_mortgage_statistics  # noqa: F401

__all__ = [
    'MortgageLayer',
    'add_mortgage_risk_circles',
    'add_ltv_indicators',
    'get_mortgage_risk_color',
    'create_mortgage_circle_popup',
    'get_mortgage_statistics',
]
