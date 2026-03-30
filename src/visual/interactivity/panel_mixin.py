# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""Shared mixin for Folium interactive panel classes."""

from typing import Any, Dict

import folium


class FoliumPanelMixin:
    """Mixin providing add_to_map, configure, and get_statistics for panels.

    Subclasses must define ``get_js() -> str`` and expose
    ``self.panel_width`` / ``self.panel_height`` attributes.
    """

    def add_to_map(self, folium_map: folium.Map) -> None:
        """Add panel JS/HTML to a Folium map."""
        folium_map.get_root().html.add_child(folium.Element(self.get_js()))

    def configure(self,
                  panel_width: str = None,
                  panel_height: str = None) -> None:
        """Update configuration."""
        if panel_width:
            self.panel_width = panel_width
        if panel_height:
            self.panel_height = panel_height

    def get_statistics(self) -> Dict[str, Any]:
        """Get configuration statistics."""
        return {
            'panel_width': self.panel_width,
            'panel_height': self.panel_height,
        }
