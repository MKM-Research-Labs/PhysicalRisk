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
Inline gauge PDF viewer panel.

Displays generated gauge PDF reports inside an overlay panel
using an embedded iframe with base64-encoded PDF data.
"""

from typing import Any, Dict

import folium

from visual.utils.pdf_viewer import pdf_viewer_js


class GaugePDFPanel:
    """Handler for inline gauge PDF display."""

    def __init__(self,
                 panel_width: str = "850px",
                 panel_height: str = "90vh"):
        self.panel_width = panel_width
        self.panel_height = panel_height

    def get_js(self) -> str:
        """Generate JavaScript for gauge PDF viewer panel."""
        js = pdf_viewer_js(
            namespace="gauge-pdf",
            panel_width=self.panel_width,
            panel_height=self.panel_height,
            default_title="Gauge Report",
            btn_color="#007bff",
            event_name="gaugePdfReady",
            event_id_key="gaugeId",
            display_name_js="window.gaugeDisplayName(entityId)",
        )
        return f"<script>\n{js}\n</script>"

    def add_to_map(self, folium_map: folium.Map) -> None:
        """Add PDF viewer panel to a Folium map."""
        folium_map.get_root().html.add_child(folium.Element(self.get_js()))

    def get_statistics(self) -> Dict[str, Any]:
        return {
            'panel_width': self.panel_width,
            'panel_height': self.panel_height
        }
