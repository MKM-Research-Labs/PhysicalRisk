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
