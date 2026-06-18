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

"""PropertyPopupBuilder class for property information popups."""

from typing import Any, Dict, Optional

import folium

from config.format import property_title_py
from ..popup_builder import PopupBuilder
from .helpers import calculate_ltv_ratio, extract_term_years, calculate_monthly_payment
from .sections import (create_property_section, create_flood_info_section,
                       create_rloan_section)


class PropertyPopupBuilder(PopupBuilder):
    """Builder for property information popups."""

    def __init__(self):
        """Initialize the property popup builder."""
        super().__init__()

    # ------------------------------------------------------------------ #
    # Section creators — delegate to sections.py                         #
    # ------------------------------------------------------------------ #

    def create_property_section(self, prop, property_id, address, coordinates,
                                construction_year, property_age_factor,
                                property_value, has_rloan) -> str:
        """Create the property information section for the popup."""
        return create_property_section(
            self, prop, property_id, address, coordinates,
            construction_year, property_age_factor, property_value, has_rloan
        )

    def create_flood_info_section(self, flood_info) -> str:
        """Create the flood risk information section for the popup."""
        return create_flood_info_section(self, flood_info)

    def create_rloan_section(self, rloan_info, property_value,
                                flood_risk_level) -> str:
        """Create the mortgage information section for the popup."""
        return create_rloan_section(self, rloan_info, property_value, flood_risk_level)

    # ------------------------------------------------------------------ #
    # Private helpers — delegate to helpers.py                           #
    # ------------------------------------------------------------------ #

    def _calculate_ltv_ratio(self, loan_amount, property_value, rloan_financial):
        return calculate_ltv_ratio(loan_amount, property_value, rloan_financial)

    def _extract_term_years(self, rloan_financial, rloan_info):
        return extract_term_years(rloan_financial, rloan_info)

    def _calculate_monthly_payment(self, rloan_financial, loan_amount,
                                   interest_rate, term_years):
        return calculate_monthly_payment(
            rloan_financial, loan_amount, interest_rate, term_years
        )

    # ------------------------------------------------------------------ #
    # Assemblers                                                          #
    # ------------------------------------------------------------------ #

    def create_complete_popup_content(self, prop: Dict[str, Any], property_id: str,
                                      address: Dict[str, Any], coordinates: str,
                                      flood_risk: str, thames_proximity: str,
                                      ground_elevation: Any, elevation_estimated: bool,
                                      property_value: Any, construction_year: Any,
                                      property_age_factor: str, has_rloan: bool,
                                      rloan_info: Optional[Dict[str, Any]] = None,
                                      flood_info: Optional[Dict[str, Any]] = None) -> str:
        """Create the complete popup content by aggregating different sections."""
        addr = address or {}
        prop_address = f"{addr.get('building_number', '')} {addr.get('street_name', '')}".strip()
        prop_label = property_title_py(prop_address, property_id)
        header = self.create_header("Property Analysis", prop_label)

        property_section = self.create_property_section(
            prop, property_id, address, coordinates, construction_year,
            property_age_factor, property_value, has_rloan
        )

        flood_section = self.create_flood_info_section(flood_info) if flood_info else ""

        rloan_section = ""
        if has_rloan and rloan_info:
            rloan_section = self.create_rloan_section(
                rloan_info, property_value,
                flood_info.get('risk_level', 'Unknown') if flood_info else 'Unknown'
            )

        content = header + property_section + flood_section + rloan_section
        return self.create_popup_wrapper(content)

    def build_property_popup(self, prop: Dict[str, Any], property_id: str,
                             address: Dict[str, Any], coordinates: str,
                             flood_risk: str, thames_proximity: str,
                             ground_elevation: Any, elevation_estimated: bool,
                             property_value: Any, construction_year: Any,
                             property_age_factor: str, has_rloan: bool,
                             rloan_info: Optional[Dict[str, Any]] = None,
                             flood_info: Optional[Dict[str, Any]] = None) -> folium.Popup:
        """Build a complete property popup."""
        content = self.create_complete_popup_content(
            prop, property_id, address, coordinates, flood_risk, thames_proximity,
            ground_elevation, elevation_estimated, property_value, construction_year,
            property_age_factor, has_rloan, rloan_info, flood_info,
        )
        return self.build_popup(content)
