# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

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
