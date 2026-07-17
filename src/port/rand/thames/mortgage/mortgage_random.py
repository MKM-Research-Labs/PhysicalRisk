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

"""Thames mortgage random value generators — entry point module."""

from .constants import (  # noqa: F401
    EMPLOYMENT_TYPES, MORTGAGE_TYPE_WEIGHTS, MORTGAGE_TYPES,
    RATE_TYPE_WEIGHTS, RATE_TYPES, REPAYMENT_TYPES, UK_LENDERS,
)
from .financials import (  # noqa: F401
    _determine_occupancy_type, calculate_mortgage_financials,
    determine_mortgage_type, estimate_property_value, generate_financial_data,
)
from .generators import (  # noqa: F401
    generate_boolean_value, generate_date_value, generate_decimal_value,
    generate_field_value, generate_integer_value, generate_menu_value,
    generate_text_value,
)
from .quality import quality_consistency_check  # noqa: F401
