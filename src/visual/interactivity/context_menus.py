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
    {"id": "view_mortgage", "label": "💰 Mortgage Details", "action": "viewRLoanDetail"},
    {"id": "loan_pricer", "label": "🧮 Loan Pricer", "action": "viewLoanPricer"},
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
        """Generate CSS and JavaScript for context menu functionality."""
        from pathlib import Path
        static_dir = Path(__file__).parent.parent.parent / 'static'
        css_code = (static_dir / 'css' / 'context-menus.css').read_text()
        js_code = (static_dir / 'js' / 'context-menus.js').read_text()
        menu_config = json.dumps({
            'property': self.property_menu,
            'gauge': self.gauge_menu,
            'commercial': self.commercial_menu,
        })
        nav_js = self._build_nav_menus_js()
        return (
            f"<style>{css_code}</style>\n"
            f"<script>window.__MENU_CONFIG = {menu_config};\n{js_code}</script>\n"
            f"{nav_js}"
        )

    def _build_nav_menus_js(self) -> str:
        """Generate JS for top-left gauge/property navigation dropdowns.

        Reuses the same menu-item definitions (self.gauge_menu, self.property_menu)
        that the right-click context menus use.  Data comes from the startup
        preloader globals (_tdPreGauges, _prePropertyTS).
        """
        gauge_items = json.dumps(self.gauge_menu)
        property_items = json.dumps(self.property_menu)

        return f"""
        <style>
        #nav-menu-container {{
            position: fixed; top: 10px; left: 60px; z-index: 1500;
            display: flex; gap: 6px; align-items: center;
            font-family: Arial, sans-serif;
        }}
        #nav-menu-container select {{
            padding: 5px 8px; font-size: 11px; border: 1px solid #bbb;
            border-radius: 4px; background: white; color: #333;
            box-shadow: 0 1px 4px rgba(0,0,0,0.15); cursor: pointer;
            max-width: 220px;
        }}
        #nav-menu-container select:focus {{ outline: none; border-color: #1976d2; }}
        #nav-action-bar {{
            display: flex; gap: 3px;
        }}
        #nav-action-bar button {{
            padding: 4px 8px; font-size: 10px; border: 1px solid #ccc;
            border-radius: 3px; background: #f8f9fa; cursor: pointer;
            color: #333; white-space: nowrap;
        }}
        #nav-action-bar button:hover {{ background: #e3f2fd; border-color: #1976d2; }}
        </style>
        <script>
        (function() {{
            var gaugeMenuItems = {gauge_items};
            var propertyMenuItems = {property_items};

            var container = document.createElement('div');
            container.id = 'nav-menu-container';

            // Gauge select
            var gSel = document.createElement('select');
            gSel.id = 'nav-gauge-select';
            gSel.innerHTML = '<option value="">Gauges</option>';

            // Property select
            var pSel = document.createElement('select');
            pSel.id = 'nav-prop-select';
            pSel.innerHTML = '<option value="">Properties</option>';

            // Action bar (hidden until selection)
            var actionBar = document.createElement('div');
            actionBar.id = 'nav-action-bar';

            container.appendChild(gSel);
            container.appendChild(pSel);
            container.appendChild(actionBar);
            document.body.appendChild(container);

            function showActions(entityId, entityLabel, menuItems) {{
                actionBar.innerHTML = '';
                if (!entityId) return;
                menuItems.forEach(function(mi) {{
                    var btn = document.createElement('button');
                    btn.textContent = mi.label;
                    btn.onclick = function() {{
                        if (window[mi.action]) window[mi.action](entityId, entityLabel);
                    }};
                    actionBar.appendChild(btn);
                }});
            }}

            gSel.onchange = function() {{
                pSel.value = '';
                var gid = gSel.value;
                var label = gSel.options[gSel.selectedIndex].text;
                showActions(gid, label, gaugeMenuItems);
            }};

            pSel.onchange = function() {{
                gSel.value = '';
                var pid = pSel.value;
                showActions(pid, pid, propertyMenuItems);
            }};

            // Populate when preloader data arrives
            function populateGauges() {{
                if (!window._tdPreGauges || !window._tdPreGauges.gauges) return false;
                var gauges = window._tdPreGauges.gauges
                    .filter(function(g) {{ return g.gaugeId && g.gaugeId.indexOf('SYNTH') !== 0; }})
                    .sort(function(a, b) {{ return (a.name || a.gaugeId).localeCompare(b.name || b.gaugeId); }});
                gSel.innerHTML = '<option value="">Gauges (' + gauges.length + ')</option>';
                gauges.forEach(function(g) {{
                    var opt = document.createElement('option');
                    opt.value = g.gaugeId;
                    opt.textContent = g.name || g.gaugeId;
                    gSel.appendChild(opt);
                }});
                return true;
            }}

            function populateProperties() {{
                if (!window._prePropertyTS || !window._prePropertyTS.data || !window._prePropertyTS.data.properties) return false;
                var props = window._prePropertyTS.data.properties
                    .sort(function(a, b) {{ return (a.property_id || '').localeCompare(b.property_id || ''); }});
                pSel.innerHTML = '<option value="">Properties (' + props.length + ')</option>';
                props.forEach(function(p) {{
                    var opt = document.createElement('option');
                    opt.value = p.property_id;
                    opt.textContent = window.propertyDisplayName(p.property_id);
                    pSel.appendChild(opt);
                }});
                return true;
            }}

            var tries = 0;
            var poll = setInterval(function() {{
                tries++;
                var gDone = populateGauges();
                var pDone = populateProperties();
                if ((gDone && pDone) || tries > 120) clearInterval(poll);
            }}, 500);
        }})();
        </script>
        """

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
