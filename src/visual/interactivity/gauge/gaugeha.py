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
Gauge historical data visualization.

Interactive Chart.js overlay panel showing historical water level timeseries
for flood gauges, with flood stage thresholds and exceedance statistics.
Loads real data from the /api/v1/gauges/{id}/history endpoint.

The panel JavaScript lives in ``src/static/js/gaugeha.js``; panel dimensions
are passed through ``window.__GAUGEHA_CONFIG``.
"""

import json
from typing import Any, Dict

import folium

from visual.interactivity._jsbundle import js_static
from visual.interactivity.panel_mixin import FoliumPanelMixin

# CDN dependencies for the Chart.js history panel.
_CHARTJS_CDN = (
    '<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>\n'
    '<script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-annotation@3.0.1/dist/chartjs-plugin-annotation.min.js"></script>\n'
)


class GaugeGraphInteraction(FoliumPanelMixin):
    """Handler for interactive gauge history graphs."""

    def __init__(self,
                 panel_width: str = "700px",
                 panel_height: str = "500px"):
        self.panel_width = panel_width
        self.panel_height = panel_height

    def get_js(self) -> str:
        """Generate JavaScript for gauge graph interaction."""
        cfg = json.dumps({
            'panelWidth': self.panel_width,
            'panelHeight': self.panel_height,
        })
        return (
            _CHARTJS_CDN
            + f"<script>window.__GAUGEHA_CONFIG = {cfg};\n{js_static('gaugeha.js')}</script>"
        )

    # add_to_map, configure, get_statistics inherited from FoliumPanelMixin
