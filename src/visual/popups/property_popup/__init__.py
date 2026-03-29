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
Property popup creation functionality.

Sub-modules:
- builder: PropertyPopupBuilder class
- sections: HTML section builders (property, flood, mortgage, risk)
- helpers: LTV, term, monthly payment calculations
- risk: risk summary and colour logic
"""

from .builder import PropertyPopupBuilder  # noqa: F401
from .helpers import calculate_ltv_ratio, calculate_monthly_payment, extract_term_years  # noqa: F401
from .risk import get_mortgage_risk_summary, get_overall_risk_color  # noqa: F401
from .sections import (  # noqa: F401
    create_flood_info_section,
    create_mortgage_risk_section,
    create_mortgage_section,
    create_property_section,
)

__all__ = [
    'PropertyPopupBuilder',
    'calculate_ltv_ratio',
    'extract_term_years',
    'calculate_monthly_payment',
    'get_mortgage_risk_summary',
    'get_overall_risk_color',
    'create_property_section',
    'create_flood_info_section',
    'create_mortgage_section',
    'create_mortgage_risk_section',
]
