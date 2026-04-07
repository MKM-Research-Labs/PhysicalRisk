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

#
# This software is provided under license by MKM Research Labs.
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.
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

from .. import client, blotter, market, fs01, aggregate, eod, curves, stress, port_stress, classifiers, preloader
from . import panel_create, panel_tabs, panel_lifecycle


class TradingDeskPanel:
    """Handler for trader's workstation panel."""

    def __init__(self,
                 panel_width: str = "90vw",
                 panel_height: str = "85vh"):
        self.panel_width = panel_width
        self.panel_height = panel_height

    def get_js(self) -> str:
        """Generate JavaScript for the trading desk panel."""
        return f"""
        <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-annotation@3.0.1/dist/chartjs-plugin-annotation.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-dragdata@2.3.0/dist/chartjs-plugin-dragdata.min.js"></script>
        <script>
        (function() {{
            var PANEL_W = '{self.panel_width}';
            var PANEL_H = '{self.panel_height}';
            var tdPanel = null;
            var tdActiveTab = 'blotter';

            // ==============================================================
            // Shared utilities
            // ==============================================================
            function getBaseUrl() {{
                var cfg = window.__BACKEND_CONFIG || {{}};
                return cfg.url || '';
            }}

            function fmtGBP(v) {{
                if (v == null || v === 0) return '\\u2014';
                var sign = v < 0 ? '-' : '';
                var abs = Math.abs(v);
                return sign + '\\u00a3' + abs.toLocaleString('en-GB', {{minimumFractionDigits: 0, maximumFractionDigits: 0}});
            }}

            function fmtBps(v) {{
                if (v == null) return '\\u2014';
                return v.toFixed(1) + ' bps';
            }}

            // ==============================================================
            // Sub-module code
            // ==============================================================
{preloader.get_js()}
{client.get_js()}
{blotter.get_js()}
{market.get_js()}
{fs01.get_js()}
{aggregate.get_js()}
{eod.get_js()}
{curves.get_js()}
{stress.get_js()}
{port_stress.get_js()}
{classifiers.get_js()}

{panel_create.get_js()}
{panel_tabs.get_js()}
{panel_lifecycle.get_js()}
        }})();
        </script>
        """

    def add_to_map(self, folium_map: folium.Map) -> None:
        """Add trading desk panel to a Folium map."""
        folium_map.get_root().html.add_child(folium.Element(self.get_js()))

    def get_statistics(self) -> Dict[str, Any]:
        return {
            "panel_width": self.panel_width,
            "panel_height": self.panel_height,
        }
