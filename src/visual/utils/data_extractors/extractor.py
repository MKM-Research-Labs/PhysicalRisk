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

"""DataExtractor — namespace collector for all data extraction functions."""

from .property_extractor import (
    extract_property_info,
    _extract_property_value,
    _calculate_age_factor,
    PropertyDataExtractor,
)
from .rloan_extractor import (
    extract_rloan_info,
    _extract_term_years,
    build_rloan_lookup,
    _normalize_rloan_list,
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
    extract_rloan_info = staticmethod(extract_rloan_info)
    extract_gauge_info = staticmethod(extract_gauge_info)
    extract_flood_risk_data = staticmethod(extract_flood_risk_data)
    extract_id_from_tooltip = staticmethod(extract_id_from_tooltip)
    extract_id_from_popup = staticmethod(extract_id_from_popup)
    build_rloan_lookup = staticmethod(build_rloan_lookup)
    _extract_property_value = staticmethod(_extract_property_value)
    _extract_term_years = staticmethod(_extract_term_years)
    _calculate_age_factor = staticmethod(_calculate_age_factor)
    _normalize_rloan_list = staticmethod(_normalize_rloan_list)
