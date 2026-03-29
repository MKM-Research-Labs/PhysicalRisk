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

# Default menu configurations
DEFAULT_PROPERTY_MENU = [
    {"id": "view_details", "label": "🏠 Property Details", "action": "viewPropertyDetails"},
    {"id": "view_mortgage", "label": "💰 Mortgage Details", "action": "viewMortgageDetail"},
    {"id": "view_property_storms", "label": "🌧️ View Storm Scenarios", "action": "viewPropertyStorms"},
    {"id": "view_property_hazard", "label": "📈 Physical Risk Swap", "action": "viewPropertyHazard"},
    {"id": "generate_report", "label": "📊 Generate Property Report", "action": "generateReport"},
    {"id": "generate_mortgage_report", "label": "🏦 Generate Mortgage Report", "action": "generateMortgageReport"}
]

DEFAULT_GAUGE_MENU = [
    {"id": "view_history", "label": "📜 View History", "action": "viewGaugeHistory"},
    {"id": "view_storms", "label": "🌧️ View Storm Scenarios", "action": "viewGaugeStorms"},
    {"id": "view_hazard_curve", "label": "📈 Physical Risk Swap", "action": "viewHazardCurve"},
    {"id": "gauge_blotter", "label": "📋 Gauge Blotter", "action": "showGaugeBlotter"},
    {"id": "generate_gauge_report", "label": "📊 Generate Gauge Report", "action": "generateGaugeReport"}
]


class ContextMenuHandler:
    """Handler for marker context menus."""

    def __init__(self,
                 property_menu: List[Dict] = None,
                 gauge_menu: List[Dict] = None):
        """
        Initialize context menu handler.

        Args:
            property_menu: Custom property menu items
            gauge_menu: Custom gauge menu items
        """
        self.property_menu = property_menu or DEFAULT_PROPERTY_MENU.copy()
        self.gauge_menu = gauge_menu or DEFAULT_GAUGE_MENU.copy()

    def get_js(self) -> str:
        """Generate CSS and JavaScript for context menu functionality."""
        from pathlib import Path
        static_dir = Path(__file__).parent.parent.parent / 'static'
        css_code = (static_dir / 'css' / 'context-menus.css').read_text()
        js_code = (static_dir / 'js' / 'context-menus.js').read_text()
        menu_config = json.dumps({
            'property': self.property_menu,
            'gauge': self.gauge_menu
        })
        return f"<style>{css_code}</style>\n<script>window.__MENU_CONFIG = {menu_config};\n{js_code}</script>"

    def add_to_map(self, folium_map: folium.Map) -> None:
        """Add context menu functionality to a Folium map."""
        folium_map.get_root().html.add_child(folium.Element(self.get_js()))

    def configure(self, property_menu: List[Dict] = None,
                 gauge_menu: List[Dict] = None) -> None:
        """Update menu configuration."""
        if property_menu:
            self.property_menu = property_menu
        if gauge_menu:
            self.gauge_menu = gauge_menu

    def get_statistics(self) -> Dict[str, Any]:
        """Get configuration statistics."""
        return {
            'property_menu_items': len(self.property_menu),
            'gauge_menu_items': len(self.gauge_menu),
            'total_menu_items': len(self.property_menu) + len(self.gauge_menu)
        }
