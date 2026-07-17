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
Property popup creation functionality.

Sub-modules:
- builder: PropertyPopupBuilder class
- sections: HTML section builders (property, flood, mortgage)
- helpers: LTV, term, monthly payment calculations
"""

from .builder import PropertyPopupBuilder  # noqa: F401
from .helpers import calculate_ltv_ratio, extract_term_years, calculate_monthly_payment  # noqa: F401
from .sections import (  # noqa: F401
    create_property_section,
    create_flood_info_section,
    create_rloan_section,
)

__all__ = [
    'PropertyPopupBuilder',
    'calculate_ltv_ratio',
    'extract_term_years',
    'calculate_monthly_payment',
    'create_property_section',
    'create_flood_info_section',
    'create_rloan_section',
]
