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

"""Thames mortgage random value generators."""

from .constants import (EMPLOYMENT_TYPES, MORTGAGE_TYPE_WEIGHTS, MORTGAGE_TYPES,  # noqa: F401
                        RATE_TYPE_WEIGHTS, RATE_TYPES, REPAYMENT_TYPES, UK_LENDERS)
from .financials import (calculate_mortgage_financials, determine_mortgage_type,  # noqa: F401
                         estimate_property_value, generate_financial_data)
from .generators import (generate_boolean_value, generate_date_value,  # noqa: F401
                         generate_decimal_value, generate_field_value,
                         generate_integer_value, generate_menu_value,
                         generate_text_value)
from .quality import quality_consistency_check  # noqa: F401
from . import mortgage_random  # noqa: F401
