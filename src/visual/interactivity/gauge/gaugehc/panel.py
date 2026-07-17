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
GaugeHazardCurve panel — assembles the full 6-tab gauge hazard panel.

Composes sub-module JavaScript (ghc_hazard, ghc_return, ghc_prs,
ghc_historical, ghc_stress) into a single IIFE and attaches it to
the Folium map.
"""

from typing import Any, Dict

import folium

from . import ghc_hazard, ghc_return, ghc_prs, ghc_historical, ghc_stress
from .panel_create import get_create_panel_js
from .panel_nav import get_nav_js
from visual.interactivity._jsbundle import js_static
from visual.interactivity.panel_mixin import FoliumPanelMixin
from .panel_data import get_data_js


class GaugeHazardCurve(FoliumPanelMixin):
    """Handler for interactive gauge hazard curve dashboard."""

    def __init__(self,
                 panel_width: str = "1100px",
                 panel_height: str = "750px"):
        self.panel_width = panel_width
        self.panel_height = panel_height

    def get_js(self) -> str:
        """Generate JavaScript for gauge hazard curve panel.

        The IIFE shell lives in ``src/static/js/gaugehc-panel.js``; panel
        dimensions and the sub-module fragments are spliced in via
        ``__TOKEN__`` placeholders.
        """
        js = (
            js_static('gaugehc-panel.js')
            .replace('__PANEL_W__', self.panel_width)
            .replace('__PANEL_H__', self.panel_height)
            .replace('__GHC_HAZARD_JS__', ghc_hazard.get_js())
            .replace('__GHC_RETURN_JS__', ghc_return.get_js())
            .replace('__GHC_PRS_JS__', ghc_prs.get_js())
            .replace('__GHC_HISTORICAL_JS__', ghc_historical.get_js())
            .replace('__GHC_STRESS_JS__', ghc_stress.get_js())
            .replace('__GHC_CREATE_PANEL_JS__', get_create_panel_js())
            .replace('__GHC_NAV_JS__', get_nav_js())
            .replace('__GHC_DATA_JS__', get_data_js())
        )
        return f"<script>\n{js}\n</script>"

    # add_to_map, configure, get_statistics inherited from FoliumPanelMixin
