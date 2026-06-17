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

#
# This software is provided under license by MKM Research Labs.
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Context menu functionality for interactive map markers.

Provides right-click context menus for property and gauge markers.
"""

import json
from typing import Any, Dict, List

import folium

from visual.interactivity._jsbundle import js_static, css_static

# Default menu configurations
DEFAULT_PROPERTY_MENU = [
    {"id": "view_details", "label": "🏠 Property Details", "action": "viewPropertyDetails"},
    {"id": "view_mortgage", "label": "💰 Mortgage Details", "action": "viewRLoanDetail"},
    {"id": "loan_pricer", "label": "🧮 Loan Pricer", "action": "viewLoanPricer"},
    {"id": "loan_calculator", "label": "🧮 Loan Calculator", "action": "openLoanCalculator"},
    {"id": "view_property_storms", "label": "🌧️ View Storm Scenarios", "action": "viewPropertyStorms"},
    {"id": "view_property_hazard", "label": "📈 Physical Risk Swap", "action": "viewPropertyHazard"},
    {"id": "generate_report", "label": "📊 Generate Property Report", "action": "generateReport"},
    {"id": "generate_mortgage_report", "label": "🏦 Generate Mortgage Report", "action": "generateRLoanReport"}
]

DEFAULT_GAUGE_MENU = [
    {"id": "view_history", "label": "📜 View History", "action": "viewGaugeHistory"},
    {"id": "view_storms", "label": "🌧️ View Storm Scenarios", "action": "viewGaugeStorms"},
    {"id": "view_hazard_curve", "label": "📈 Physical Risk Swap", "action": "viewHazardCurve"},
    {"id": "gauge_blotter", "label": "📋 Gauge Blotter", "action": "showGaugeBlotter"},
    {"id": "generate_gauge_report", "label": "📊 Generate Gauge Report", "action": "generateGaugeReport"}
]

# Commercial assets mirror the property menu but use commercial / loan
# vocabulary. Backend handlers will be plumbed in alongside storm scenarios;
# until then the actions fire and the JS shows the not-yet-wired warning.
DEFAULT_COMMERCIAL_MENU = [
    {"id": "view_details", "label": "🏢 Commercial Details", "action": "viewCommercialDetails"},
    {"id": "view_loan", "label": "💰 Loan Details", "action": "viewCLoanDetails"},
    {"id": "loan_pricer", "label": "🧮 Loan Pricer", "action": "viewCommercialLoanPricer"},
    {"id": "loan_calculator", "label": "🧮 Loan Calculator", "action": "openCommercialLoanCalculator"},
    {"id": "view_commercial_storms", "label": "🌧️ View Storm Scenarios", "action": "viewCommercialStorms"},
    {"id": "view_commercial_hazard", "label": "📈 Physical Risk Swap", "action": "viewCommercialHazard"},
    {"id": "generate_commercial_report", "label": "📊 Generate Commercial Report", "action": "generateCommercialReport"},
    {"id": "generate_cloan_report", "label": "🏦 Generate Loan Report", "action": "generateCLoanReport"}
]


class ContextMenuHandler:
    """Handler for marker context menus."""

    def __init__(self,
                 property_menu: List[Dict] = None,
                 gauge_menu: List[Dict] = None,
                 commercial_menu: List[Dict] = None):
        """
        Initialize context menu handler.

        Args:
            property_menu: Custom property menu items
            gauge_menu: Custom gauge menu items
            commercial_menu: Custom commercial menu items
        """
        self.property_menu = property_menu or DEFAULT_PROPERTY_MENU.copy()
        self.gauge_menu = gauge_menu or DEFAULT_GAUGE_MENU.copy()
        self.commercial_menu = commercial_menu or DEFAULT_COMMERCIAL_MENU.copy()

    def get_js(self) -> str:
        """Generate CSS and JavaScript for context menu functionality.

        The top-left gauge/property navigation dropdowns are intentionally not
        rendered (gauge/property browsing now lives in the CDM Asset Review
        workstream). ``_build_nav_menus_js`` is retained so the dropdowns can be
        restored by re-appending its output here.
        """
        css_code = css_static('context-menus.css')
        js_code = js_static('context-menus.js')
        menu_config = json.dumps({
            'property': self.property_menu,
            'gauge': self.gauge_menu,
            'commercial': self.commercial_menu,
        })
        return (
            f"<style>{css_code}</style>\n"
            f"<script>window.__MENU_CONFIG = {menu_config};\n{js_code}</script>\n"
        )

    def _build_nav_menus_js(self) -> str:
        """Generate JS for top-left gauge/property navigation dropdowns.

        Retained but no longer wired into ``get_js`` — see that method. Reuses
        the same menu-item definitions (self.gauge_menu, self.property_menu)
        that the right-click context menus use.  Data comes from the startup
        preloader globals (_tdPreGauges, _prePropertyTS).
        """
        nav_config = json.dumps({
            'gauge': self.gauge_menu,
            'property': self.property_menu,
        })
        return (
            f"<style>{css_static('nav-menus.css')}</style>\n"
            f"<script>window.__NAV_MENU_CONFIG = {nav_config};\n{js_static('nav-menus.js')}</script>"
        )

    def add_to_map(self, folium_map: folium.Map) -> None:
        """Add context menu functionality to a Folium map."""
        folium_map.get_root().html.add_child(folium.Element(self.get_js()))

    def configure(self, property_menu: List[Dict] = None,
                 gauge_menu: List[Dict] = None,
                 commercial_menu: List[Dict] = None) -> None:
        """Update menu configuration."""
        if property_menu:
            self.property_menu = property_menu
        if gauge_menu:
            self.gauge_menu = gauge_menu
        if commercial_menu:
            self.commercial_menu = commercial_menu

    def get_statistics(self) -> Dict[str, Any]:
        """Get configuration statistics."""
        return {
            'property_menu_items': len(self.property_menu),
            'gauge_menu_items': len(self.gauge_menu),
            'commercial_menu_items': len(self.commercial_menu),
            'total_menu_items': (len(self.property_menu)
                                  + len(self.gauge_menu)
                                  + len(self.commercial_menu)),
        }
