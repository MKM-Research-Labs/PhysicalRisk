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
