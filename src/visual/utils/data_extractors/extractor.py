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

"""DataExtractor — namespace collector for all data extraction functions."""

from .property_extractor import (
    extract_property_info,
    _extract_property_value,
    _calculate_age_factor,
    PropertyDataExtractor,
)
from .mortgage_extractor import (
    extract_mortgage_info,
    _extract_term_years,
    build_mortgage_lookup,
    _normalize_mortgage_list,
)
from .gauge_extractor import (
    extract_gauge_info,
    extract_flood_risk_data,
)
from .id_extractor import (
    extract_id_from_tooltip,
    extract_id_from_popup,
)


class DataExtractor:
    """Utility class for extracting data from complex nested structures."""

    extract_property_info = staticmethod(extract_property_info)
    extract_mortgage_info = staticmethod(extract_mortgage_info)
    extract_gauge_info = staticmethod(extract_gauge_info)
    extract_flood_risk_data = staticmethod(extract_flood_risk_data)
    extract_id_from_tooltip = staticmethod(extract_id_from_tooltip)
    extract_id_from_popup = staticmethod(extract_id_from_popup)
    build_mortgage_lookup = staticmethod(build_mortgage_lookup)
    _extract_property_value = staticmethod(_extract_property_value)
    _extract_term_years = staticmethod(_extract_term_years)
    _calculate_age_factor = staticmethod(_calculate_age_factor)
    _normalize_mortgage_list = staticmethod(_normalize_mortgage_list)
