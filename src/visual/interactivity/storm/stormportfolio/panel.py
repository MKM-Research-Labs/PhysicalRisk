# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""StormPortfolioPanel — top-level class composing all sub-modules."""

from typing import Any, Dict

import folium

from visual.interactivity._jsbundle import js_static
from .. import sp_table, sp_var, sp_visual, sp_sim, sp_control
from . import utilities, chrome, control

# CDN dependencies for the Chart.js portfolio panel.
_CHARTJS_CDN = (
    '<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>\n'
    '<script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-annotation@3.0.1/dist/chartjs-plugin-annotation.min.js"></script>\n'
)


class StormPortfolioPanel:
    """Handler for portfolio storm impact panel."""

    def __init__(self,
                 panel_width: str = "960px",
                 panel_height: str = "640px"):
        self.panel_width = panel_width
        self.panel_height = panel_height

    def get_js(self) -> str:
        """Generate JavaScript for storm portfolio impact panel.

        The IIFE shell lives in ``src/static/js/stormportfolio-panel.js``;
        panel dimensions and every sub-module fragment are spliced in via
        ``__TOKEN__`` placeholders.
        """
        js = (
            js_static('stormportfolio-panel.js')
            .replace('__PANEL_W__', self.panel_width)
            .replace('__PANEL_H__', self.panel_height)
            .replace('__SP_UTILITIES_JS__', utilities.get_js())
            .replace('__SP_TABLE_JS__', sp_table.get_js())
            .replace('__SP_VAR_JS__', sp_var.get_js())
            .replace('__SP_VISUAL_JS__', sp_visual.get_js())
            .replace('__SP_SIM_JS__', sp_sim.get_js())
            .replace('__SP_CONTROL_JS__', sp_control.get_js())
            .replace('__SP_CHROME_JS__', chrome.get_js())
            .replace('__SP_PANEL_CONTROL_JS__', control.get_js())
        )
        return f"{_CHARTJS_CDN}<script>\n{js}\n</script>"

    def add_to_map(self, folium_map: folium.Map) -> None:
        """Add storm portfolio panel to a Folium map."""
        folium_map.get_root().html.add_child(folium.Element(self.get_js()))

    def get_statistics(self) -> Dict[str, Any]:
        return {
            "panel_width": self.panel_width,
            "panel_height": self.panel_height,
        }
