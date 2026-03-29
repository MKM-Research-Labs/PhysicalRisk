# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""StormPortfolioPanel — top-level class composing all sub-modules."""

from typing import Any, Dict

import folium

from .. import sp_sim, sp_table, sp_var, sp_visual
from . import chrome, control, utilities


class StormPortfolioPanel:
    """Handler for portfolio storm impact panel."""

    def __init__(self,
                 panel_width: str = "960px",
                 panel_height: str = "640px"):
        self.panel_width = panel_width
        self.panel_height = panel_height

    def get_js(self) -> str:
        """Generate JavaScript for storm portfolio impact panel."""
        return f"""
        <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-annotation@3.0.1/dist/chartjs-plugin-annotation.min.js"></script>
        <script>
        (function() {{
            var PANEL_W = '{self.panel_width}';
            var PANEL_H = '{self.panel_height}';
            var spPanel = null;
            var spActiveTab = 'table';

{utilities.get_js()}

            // ==============================================================
            // Sub-module code (state vars + functions)
            // ==============================================================
{sp_table.get_js()}
{sp_var.get_js()}
{sp_visual.get_js()}
{sp_sim.get_js()}

{chrome.get_js()}

{control.get_js()}
        }})();
        </script>
        """

    def add_to_map(self, folium_map: folium.Map) -> None:
        """Add storm portfolio panel to a Folium map."""
        folium_map.get_root().html.add_child(folium.Element(self.get_js()))

    def get_statistics(self) -> Dict[str, Any]:
        return {
            "panel_width": self.panel_width,
            "panel_height": self.panel_height,
        }
