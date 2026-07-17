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

"""
Property details panel for map markers.

Displays full property information in an overlay panel,
loaded from the /api/v1/properties/{id} endpoint.

The panel JavaScript lives in ``src/static/js/propertydetails.js``; panel
dimensions are passed via ``window.__PROPDETAILS_CONFIG``.
"""

import json
from typing import Any, Dict

import folium

from visual.interactivity._jsbundle import js_static


class PropertyDetailsPanel:
    """Handler for interactive property details popup."""

    def __init__(self,
                 panel_width: str = "620px",
                 panel_height: str = "560px"):
        self.panel_width = panel_width
        self.panel_height = panel_height

    def get_js(self) -> str:
        """Generate JavaScript for property details panel."""
        cfg = json.dumps({
            'panelWidth': self.panel_width,
            'panelHeight': self.panel_height,
        })
        return f"<script>window.__PROPDETAILS_CONFIG = {cfg};\n{js_static('propertydetails.js')}</script>"

    def add_to_map(self, folium_map: folium.Map) -> None:
        """Add property details panel to a Folium map."""
        folium_map.get_root().html.add_child(folium.Element(self.get_js()))

    def get_statistics(self) -> Dict[str, Any]:
        return {
            'panel_width': self.panel_width,
            'panel_height': self.panel_height,
        }
