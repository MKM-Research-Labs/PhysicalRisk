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
Data extraction utilities for the visualization system.

Sub-modules:
- extractor: DataExtractor class
- property_extractor: Property data extraction
- rloan_extractor: Residential-loan data extraction
- gauge_extractor: Gauge and flood risk data extraction
- id_extractor: ID extraction from tooltips/popups
"""

from .extractor import DataExtractor  # noqa: F401
from .property_extractor import (  # noqa: F401
    extract_property_info,
    _extract_property_value,
    _calculate_age_factor,
    PropertyDataExtractor,
)
from .rloan_extractor import (  # noqa: F401
    extract_rloan_info,
    _extract_term_years,
    build_rloan_lookup,
    _normalize_rloan_list,
)
from .gauge_extractor import (  # noqa: F401
    extract_gauge_info,
    extract_flood_risk_data,
)
from .id_extractor import (  # noqa: F401
    extract_id_from_tooltip,
    extract_id_from_popup,
)
