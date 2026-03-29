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
trading desk with 8 tabs:
  1. Blotter     - trade list with deltas, P&L, close-out
  2. Market      - hazard curve adjustment (market-making)
  3. FS01        - gauge x maturity FS01 risk matrix
  4. Aggregate   - net FS01 exposure map with scaled circles
  5. EOD         - end-of-day submit, P&L history, charts
  6. Curves      - historical hazard term structure evolution
  7. Stress      - gauge-level stress testing (CDS-in-stress)
  8. Port Stress - portfolio-wide storm stress assessment

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

from . import aggregate, blotter, classifiers, curves, eod, fs01, market, port_stress, preloader, stress


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
{blotter.get_js()}
{market.get_js()}
{fs01.get_js()}
{aggregate.get_js()}
{eod.get_js()}
{curves.get_js()}
{stress.get_js()}
{port_stress.get_js()}
{classifiers.get_js()}

            // ==============================================================
            // Map control button — capital Pi symbol
            // ==============================================================
            function addMapControl() {{
                function findMap() {{
                    var mapKey = Object.keys(window).find(function(k) {{ return k.startsWith('map_'); }});
                    if (mapKey) return window[mapKey];
                    return null;
                }}

                function tryAdd() {{
                    var map = findMap();
                    if (!map) {{
                        setTimeout(tryAdd, 500);
                        return;
                    }}

                    var TradingControl = L.Control.extend({{
                        options: {{ position: 'topright' }},
                        onAdd: function() {{
                            var container = L.DomUtil.create('div', 'leaflet-bar leaflet-control');
                            var btn = L.DomUtil.create('a', '', container);
                            btn.href = '#';
                            btn.title = "Trader's Workstation";
                            btn.setAttribute('role', 'button');
                            btn.innerHTML = '<span style="font-size:18px;font-weight:bold;font-family:serif;">&Pi;</span>';
                            btn.style.cssText = 'display:flex;align-items:center;justify-content:center;width:30px;height:30px;cursor:pointer;background:white;';

                            L.DomEvent.disableClickPropagation(container);
                            L.DomEvent.on(btn, 'click', function(e) {{
                                L.DomEvent.preventDefault(e);
                                showPanel();
                            }});
                            return container;
                        }}
                    }});

                    new TradingControl().addTo(map);
                }}

                setTimeout(tryAdd, 1000);
            }}

            // ==============================================================
            // Panel creation
            // ==============================================================
            function createPanel() {{
                if (tdPanel) return tdPanel;

                tdPanel = document.createElement('div');
                tdPanel.id = 'trading-desk-panel';
                tdPanel.style.cssText =
                    'position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);' +
                    'width:' + PANEL_W + ';height:' + PANEL_H + ';' +
                    'max-width:1400px;max-height:900px;min-width:600px;min-height:400px;' +
                    'background:white;border:1px solid #ccc;border-radius:8px;' +
                    'box-shadow:0 4px 20px rgba(0,0,0,0.3);z-index:2000;' +
                    'display:none;flex-direction:column;font-family:Arial,sans-serif;' +
                    'resize:both;overflow:hidden;';

                // Header with tabs
                var header = document.createElement('div');
                header.style.cssText =
                    'display:flex;justify-content:space-between;align-items:center;' +
                    'padding:10px 16px;border-bottom:1px solid #eee;background:#f8f9fa;' +
                    'border-radius:8px 8px 0 0;';

                var leftHeader = document.createElement('div');
                leftHeader.style.cssText = 'display:flex;align-items:center;gap:16px;';

                var piIcon = document.createElement('span');
                piIcon.innerHTML = '&Pi;';
                piIcon.style.cssText = 'font-size:22px;font-weight:bold;font-family:serif;color:#1565c0;';

                var title = document.createElement('span');
                title.style.cssText = 'font-weight:bold;font-size:14px;color:#333;';
                title.textContent = "Trader's Workstation";

                var toggleWrap = document.createElement('div');
                toggleWrap.style.cssText = 'display:flex;border:1px solid #ddd;border-radius:4px;overflow:hidden;';

                var tabs = [
                    {{id: 'blotter', label: 'Blotter'}},
                    {{id: 'market', label: 'Market'}},
                    {{id: 'risk', label: 'FS01'}},
                    {{id: 'map', label: 'Aggregate'}},
                    {{id: 'eod', label: 'EOD'}},
                    {{id: 'curves', label: 'Curves'}},
                    {{id: 'stress', label: 'Stress'}},
                    {{id: 'portstress', label: 'Port Stress'}},
                    {{id: 'classifiers', label: 'Classifiers'}}
                ];

                tabs.forEach(function(tab) {{
                    var btn = document.createElement('button');
                    btn.id = 'td-tab-' + tab.id;
                    btn.textContent = tab.label;
                    btn.style.cssText = 'padding:4px 14px;font-size:11px;border:none;cursor:pointer;font-weight:600;' +
                        (tab.id === 'blotter' ? 'background:#1976d2;color:white;' : 'background:#f5f5f5;color:#555;');
                    btn.onclick = function() {{ switchTab(tab.id); }};
                    toggleWrap.appendChild(btn);
                }});

                leftHeader.appendChild(piIcon);
                leftHeader.appendChild(title);
                leftHeader.appendChild(toggleWrap);

                var closeBtn = document.createElement('button');
                closeBtn.innerHTML = '&times;';
                closeBtn.style.cssText =
                    'border:none;background:none;font-size:24px;cursor:pointer;color:#666;padding:0 8px;line-height:1;';
                closeBtn.onclick = hidePanel;

                header.appendChild(leftHeader);
                header.appendChild(closeBtn);

                // Tab views
                var blotterView = createBlotterView();
                var marketView = createMarketView();
                var riskView = createRiskView();
                var mapView = createMapView();
                var eodView = createEodView();
                var curvesView = createCurvesView();
                var stressView = createStressView();
                var portStressView = createPortStressView();
                var classifiersView = createClassifiersView();

                // Stats bar
                var statsBar = document.createElement('div');
                statsBar.id = 'td-stats-bar';
                statsBar.style.cssText = 'padding:6px 16px;border-top:1px solid #eee;font-size:10px;color:#999;background:#f9f9f9;border-radius:0 0 8px 8px;text-align:right;';
                statsBar.textContent = 'MKM Research Labs \\u2014 Physical Risk Trading Desk';

                tdPanel.appendChild(header);
                tdPanel.appendChild(blotterView);
                tdPanel.appendChild(marketView);
                tdPanel.appendChild(riskView);
                tdPanel.appendChild(mapView);
                tdPanel.appendChild(eodView);
                tdPanel.appendChild(curvesView);
                tdPanel.appendChild(stressView);
                tdPanel.appendChild(portStressView);
                tdPanel.appendChild(classifiersView);
                tdPanel.appendChild(statsBar);
                document.body.appendChild(tdPanel);
                return tdPanel;
            }}

            // ==============================================================
            // Tab switching
            // ==============================================================
            function switchTab(tab) {{
                tdActiveTab = tab;

                var views = ['blotter', 'market', 'risk', 'map', 'eod', 'curves', 'stress', 'portstress', 'classifiers'];
                views.forEach(function(v) {{
                    var el = document.getElementById('td-' + v + '-view');
                    var btn = document.getElementById('td-tab-' + v);
                    if (el) el.style.display = 'none';
                    if (btn) {{
                        btn.style.background = '#f5f5f5';
                        btn.style.color = '#555';
                    }}
                }});

                var activeEl = document.getElementById('td-' + tab + '-view');
                var activeBtn = document.getElementById('td-tab-' + tab);
                if (activeEl) activeEl.style.display = 'flex';
                if (activeBtn) {{
                    activeBtn.style.background = '#1976d2';
                    activeBtn.style.color = 'white';
                }}

                // Load data for each tab
                if (tab === 'blotter') loadBlotterData();
                else if (tab === 'market') {{
                    // Pass blotter gauge filter for continuity
                    var gaugeHint = tdBlotterFilters.gauge_id || null;
                    loadMarketData(gaugeHint);
                }}
                else if (tab === 'risk') loadRiskData();
                else if (tab === 'map') loadMapData();
                else if (tab === 'eod') loadEodData();
                else if (tab === 'curves') tdLoadCurveGauges();
                else if (tab === 'stress') {{
                    // Gauge hint: blotter filter > market selection > first blotter trade
                    // Blotter filter is the most recent explicit user selection and must win.
                    var stressHint = (tdBlotterFilters && tdBlotterFilters.gauge_id ? tdBlotterFilters.gauge_id : null) ||
                        tdSelectedGauge ||
                        (tdBlotterData && tdBlotterData.length > 0 ? tdBlotterData[0].gauge_id : null);
                    loadStressData(stressHint);
                }}
                else if (tab === 'portstress') loadPortStressData();
                else if (tab === 'classifiers') loadClassifiersData();
            }}

            // ==============================================================
            // Show / hide
            // ==============================================================
            function showPanel() {{
                console.log('[TradingDesk] Opening panel');
                if (window._tdPreloadDone) {{
                    // Data already cached — open immediately
                    _tdOpenPanel();
                }} else {{
                    // First open: preload all datasets with progress popup
                    _tdRunPreload(function() {{
                        _tdOpenPanel();
                    }});
                }}
            }}

            function _tdOpenPanel() {{
                createPanel();
                tdPanel.style.display = 'flex';
                tdActiveTab = 'blotter';
                switchTab('blotter');
            }}

            function hidePanel() {{
                if (tdPanel) tdPanel.style.display = 'none';
                console.log('[TradingDesk] Panel closed');
                // Cleanup
                if (typeof tdCleanupMap === 'function') tdCleanupMap();
                if (typeof tdCleanupMarketCharts === 'function') tdCleanupMarketCharts();
                if (typeof tdCleanupEodCharts === 'function') tdCleanupEodCharts();
                if (typeof tdCleanupCurveCharts === 'function') tdCleanupCurveCharts();
                if (typeof tdCleanupStressCharts === 'function') tdCleanupStressCharts();
                if (typeof psCleanupCharts === 'function') psCleanupCharts();
                if (typeof clCleanupCharts === 'function') clCleanupCharts();
            }}

            // Global entry points
            window.TradingDesk = {{ show: showPanel, hide: hidePanel }};
            window.showTradingDesk = showPanel;

            // Add map control button on load
            addMapControl();
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
