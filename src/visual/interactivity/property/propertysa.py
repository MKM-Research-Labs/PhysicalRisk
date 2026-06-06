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
Property storm scenario analysis visualization.

Interactive Chart.js tabbed panel showing property flood depth distribution,
worst-storm rankings, flood history, and mortgage impact.
Loads data from the /api/v1/properties/{id}/storms endpoint.

The JavaScript fragment lives in the companion ``propertysa.js`` file;
panel dimensions and sub-module fragments are substituted in at render time.

Sub-modules:
- psa_charts: Distribution (Tab 0) and Worst Storms (Tab 2)
- psa_timeline: Flood Timeline hydrograph (Tab 1)
- psa_impact: Flood History (Tab 3) and Mortgage Impact (Tab 4)
"""

from typing import Any, Dict

import folium

from visual.interactivity._jsbundle import js_sibling

from . import psa_charts, psa_impact, psa_timeline


class PropertyStormAnalysis:
    """Handler for interactive property storm analysis dashboard."""

    def __init__(self,
                 panel_width: str = "780px",
                 panel_height: str = "560px"):
        self.panel_width = panel_width
        self.panel_height = panel_height

    def get_js(self) -> str:
        """Generate JavaScript for property storm analysis panel."""
        return (
            js_sibling(__file__)
            .replace("__PANEL_W__", self.panel_width)
            .replace("__PANEL_H__", self.panel_height)
            .replace("__PSA_CHARTS_JS__", psa_charts.get_js())
            .replace("__PSA_TIMELINE_JS__", psa_timeline.get_js())
            .replace("__PSA_IMPACT_JS__", psa_impact.get_js())
        )

    def add_to_map(self, folium_map: folium.Map) -> None:
        """Add property storm analysis to a Folium map."""
        folium_map.get_root().html.add_child(folium.Element(self.get_js()))

    def get_statistics(self) -> Dict[str, Any]:
        return {
            'panel_width': self.panel_width,
            'panel_height': self.panel_height,
        }
