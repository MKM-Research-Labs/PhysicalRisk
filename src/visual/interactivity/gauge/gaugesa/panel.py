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
GaugeStormAnalysis panel — assembles the full 3-tab gauge storm panel.

Composes sub-module JavaScript (gsa_distribution, gsa_timeline)
into a single IIFE and attaches it to the Folium map.
"""

from typing import Any, Dict

import folium

from config.format import gauge_title_js as _gauge_title_js
from visual.interactivity._jsbundle import js_static
from visual.interactivity.panel_mixin import FoliumPanelMixin
from . import gsa_distribution, gsa_timeline


class GaugeStormAnalysis(FoliumPanelMixin):
    """Handler for interactive gauge storm analysis dashboard."""

    def __init__(self,
                 panel_width: str = "780px",
                 panel_height: str = "560px"):
        self.panel_width = panel_width
        self.panel_height = panel_height

    def get_js(self) -> str:
        """Generate JavaScript for gauge storm analysis panel.

        The panel JavaScript lives in ``src/static/js/gaugesa.js``; panel
        dimensions, the sub-module fragments and the gauge-title expression
        are spliced in via ``__TOKEN__`` placeholders.
        """
        js = (
            js_static('gaugesa.js')
            .replace('__PANEL_W__', self.panel_width)
            .replace('__PANEL_H__', self.panel_height)
            .replace('__GSA_DISTRIBUTION_JS__', gsa_distribution.get_js())
            .replace('__GSA_TIMELINE_JS__', gsa_timeline.get_js())
            .replace('__GAUGE_TITLE_EXPR__', _gauge_title_js('gName', 'gaugeId'))
        )
        return f"<script>\n{js}\n</script>"

    # add_to_map, configure, get_statistics inherited from FoliumPanelMixin
