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
Trader's Workstation panel.

Leaflet control button (top-right, capital Pi symbol) that opens a full
trading desk with 10 tabs:
  1. Client      - property PRS trade blotter
  2. Blotter     - trade list with deltas, P&L, close-out
  3. Market      - hazard curve adjustment (market-making)
  4. FS01        - gauge x maturity FS01 risk matrix
  5. Aggregate   - net FS01 exposure map with scaled circles
  6. EOD         - end-of-day submit, P&L history, charts
  7. Curves      - historical hazard term structure evolution
  8. Stress      - gauge-level stress testing (CDS-in-stress)
  9. Port Stress - portfolio-wide storm stress assessment

Sub-packages (one per tab header):
- blotter/: Trade blotter tab
- market/: Market-making tab
- fs01/: Portfolio risk grid tab
- aggregate/: Aggregate view tab
- eod/: EOD tab
- curves/: Curve history tab
- stress/: Stress test tab
- port_stress/: Portfolio stress tab
"""

from typing import Any, Dict

import folium

from visual.interactivity._jsbundle import js_static
from .. import client, blotter, market, fs01, aggregate, eod, curves, stress, port_stress, classifiers, preloader
from . import panel_create, panel_tabs, panel_lifecycle

# CDN dependencies for the Chart.js trading desk panel.
_CHARTJS_CDN = (
    '<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>\n'
    '<script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-annotation@3.0.1/dist/chartjs-plugin-annotation.min.js"></script>\n'
    '<script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-dragdata@2.3.0/dist/chartjs-plugin-dragdata.min.js"></script>\n'
)


class TradingDeskPanel:
    """Handler for trader's workstation panel."""

    def __init__(self,
                 panel_width: str = "90vw",
                 panel_height: str = "85vh"):
        self.panel_width = panel_width
        self.panel_height = panel_height

    def get_js(self) -> str:
        """Generate JavaScript for the trading desk panel.

        The IIFE shell lives in ``src/static/js/tradingdesk-panel.js``; panel
        dimensions and every sub-module fragment are spliced in via
        ``__TOKEN__`` placeholders.
        """
        js = (
            js_static('tradingdesk-panel.js')
            .replace('__PANEL_W__', self.panel_width)
            .replace('__PANEL_H__', self.panel_height)
            .replace('__TD_PRELOADER_JS__', preloader.get_js())
            .replace('__TD_CLIENT_JS__', client.get_js())
            .replace('__TD_BLOTTER_JS__', blotter.get_js())
            .replace('__TD_MARKET_JS__', market.get_js())
            .replace('__TD_FS01_JS__', fs01.get_js())
            .replace('__TD_AGGREGATE_JS__', aggregate.get_js())
            .replace('__TD_EOD_JS__', eod.get_js())
            .replace('__TD_CURVES_JS__', curves.get_js())
            .replace('__TD_STRESS_JS__', stress.get_js())
            .replace('__TD_PORT_STRESS_JS__', port_stress.get_js())
            .replace('__TD_CLASSIFIERS_JS__', classifiers.get_js())
            .replace('__TD_PANEL_CREATE_JS__', panel_create.get_js())
            .replace('__TD_PANEL_TABS_JS__', panel_tabs.get_js())
            .replace('__TD_PANEL_LIFECYCLE_JS__', panel_lifecycle.get_js())
        )
        return f"{_CHARTJS_CDN}<script>\n{js}\n</script>"

    def add_to_map(self, folium_map: folium.Map) -> None:
        """Add trading desk panel to a Folium map."""
        folium_map.get_root().html.add_child(folium.Element(self.get_js()))

    def get_statistics(self) -> Dict[str, Any]:
        return {
            "panel_width": self.panel_width,
            "panel_height": self.panel_height,
        }
