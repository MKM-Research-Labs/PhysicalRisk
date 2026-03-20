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

"""
Portfolio Storm Impact panel.

Leaflet control button (top-right) that opens a panel showing portfolio-wide
damage for a selected storm scenario. Displays property valuations, flood
damage, mortgage exposure, post-damage LTV, and negative equity flags.

Sub-modules:
- sp_table: Table tab (summary cards, sortable property table, data loading)
- sp_var: VaR tab (loss distribution histogram, VaR/ES metrics)
- sp_visual: Visual tab (multi-line chart, gauge dropdown)
- sp_sim: Sim tab (embedded Leaflet map animation)
"""

from typing import Any, Dict

import folium

from . import sp_table, sp_var, sp_visual, sp_sim


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

            // ==============================================================
            // Shared utilities
            // ==============================================================
            function getBaseUrl() {{
                var cfg = window.__BACKEND_CONFIG || {{}};
                return cfg.url || '';
            }}

            function fmtGBP(v) {{
                if (v == null || v === 0) return '\u2014';
                return '\u00a3' + v.toLocaleString('en-GB', {{minimumFractionDigits: 0, maximumFractionDigits: 0}});
            }}

            function fmtPct(v) {{
                if (v == null) return '\u2014';
                return v.toFixed(1) + '%';
            }}

            function fmtDepth(v) {{
                if (v == null) return '\u2014';
                return v.toFixed(2) + 'm';
            }}

            function fmtMonths(v) {{
                if (!v) return '\u2014';
                var yrs = Math.floor(v / 12);
                var mos = v % 12;
                return yrs + 'y ' + mos + 'm';
            }}

            // Color helpers for sim map
            function spGaugeColor(status) {{
                if (status === 'severe') return '#d32f2f';
                if (status === 'warning') return '#f57c00';
                if (status === 'alert') return '#fbc02d';
                return '#4caf50';
            }}
            function spWavefrontColor(p) {{
                if (p.peak || (p.flooded && p.depth_m >= 1.0)) return '#d32f2f';
                if (p.flooded) return '#ff9800';
                if (p.arrived) return '#2196f3';
                return '#90caf9';
            }}

            // ==============================================================
            // Sub-module code (state vars + functions)
            // ==============================================================
{sp_table.get_js()}
{sp_var.get_js()}
{sp_visual.get_js()}
{sp_sim.get_js()}

            // ==============================================================
            // Map control button
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

                    var PortfolioControl = L.Control.extend({{
                        options: {{ position: 'topright' }},
                        onAdd: function() {{
                            var container = L.DomUtil.create('div', 'leaflet-bar leaflet-control');
                            var btn = L.DomUtil.create('a', '', container);
                            btn.href = '#';
                            btn.title = 'Portfolio Storm Impact';
                            btn.setAttribute('role', 'button');
                            btn.innerHTML = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#333" stroke-width="2"><path d="M2 12c1-3 3-5 5-5s3 2 5 2 3-2 5-2 4 2 5 5"/><path d="M2 17c1-3 3-5 5-5s3 2 5 2 3-2 5-2 4 2 5 5"/></svg>';
                            btn.style.cssText = 'display:flex;align-items:center;justify-content:center;width:30px;height:30px;cursor:pointer;background:white;';

                            L.DomEvent.disableClickPropagation(container);
                            L.DomEvent.on(btn, 'click', function(e) {{
                                L.DomEvent.preventDefault(e);
                                showPanel();
                            }});
                            return container;
                        }}
                    }});

                    new PortfolioControl().addTo(map);
                }}

                setTimeout(tryAdd, 1000);
            }}

            // ==============================================================
            // Panel creation
            // ==============================================================
            function createPanel() {{
                if (spPanel) return spPanel;

                spPanel = document.createElement('div');
                spPanel.id = 'storm-portfolio-panel';
                spPanel.style.cssText =
                    'position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);' +
                    'width:' + PANEL_W + ';height:' + PANEL_H + ';' +
                    'background:white;border:1px solid #ccc;border-radius:8px;' +
                    'box-shadow:0 4px 20px rgba(0,0,0,0.3);z-index:2000;' +
                    'display:none;flex-direction:column;font-family:Arial,sans-serif;';

                // Header with tabs
                var header = document.createElement('div');
                header.style.cssText =
                    'display:flex;justify-content:space-between;align-items:center;' +
                    'padding:10px 16px;border-bottom:1px solid #eee;background:#f8f9fa;' +
                    'border-radius:8px 8px 0 0;';

                var leftHeader = document.createElement('div');
                leftHeader.style.cssText = 'display:flex;align-items:center;gap:16px;';
                var title = document.createElement('span');
                title.id = 'sp-panel-title';
                title.style.cssText = 'font-weight:bold;font-size:14px;color:#333;';
                title.textContent = 'Portfolio Storm Impact';

                var toggleWrap = document.createElement('div');
                toggleWrap.style.cssText = 'display:flex;border:1px solid #ddd;border-radius:4px;overflow:hidden;';
                var tabBtn = document.createElement('button');
                tabBtn.id = 'sp-tab-table';
                tabBtn.textContent = 'Table';
                tabBtn.style.cssText = 'padding:3px 12px;font-size:11px;border:none;cursor:pointer;background:#1976d2;color:white;';
                tabBtn.onclick = function() {{ switchTab('table'); }};
                var simBtn = document.createElement('button');
                simBtn.id = 'sp-tab-sim';
                simBtn.textContent = 'Sim';
                simBtn.style.cssText = 'padding:3px 12px;font-size:11px;border:none;cursor:pointer;background:white;color:#333;';
                simBtn.onclick = function() {{ switchTab('sim'); }};
                var visBtn = document.createElement('button');
                visBtn.id = 'sp-tab-vis';
                visBtn.textContent = 'Visual';
                visBtn.style.cssText = 'padding:3px 12px;font-size:11px;border:none;cursor:pointer;background:white;color:#333;';
                visBtn.onclick = function() {{ switchTab('vis'); }};
                var varBtn = document.createElement('button');
                varBtn.id = 'sp-tab-var';
                varBtn.textContent = 'VaR';
                varBtn.style.cssText = 'padding:3px 12px;font-size:11px;border:none;cursor:pointer;background:white;color:#333;';
                varBtn.onclick = function() {{ switchTab('var'); }};
                toggleWrap.appendChild(tabBtn);
                toggleWrap.appendChild(simBtn);
                toggleWrap.appendChild(visBtn);
                toggleWrap.appendChild(varBtn);

                leftHeader.appendChild(title);
                leftHeader.appendChild(toggleWrap);

                var closeBtn = document.createElement('button');
                closeBtn.innerHTML = '&times;';
                closeBtn.style.cssText =
                    'border:none;background:none;font-size:24px;cursor:pointer;color:#666;padding:0 8px;line-height:1;';
                closeBtn.onclick = hidePanel;
                header.appendChild(leftHeader);
                header.appendChild(closeBtn);

                // Shared storm selector row
                var selectorRow = document.createElement('div');
                selectorRow.id = 'sp-selector-row';
                selectorRow.style.cssText = 'padding:8px 16px;border-bottom:1px solid #eee;display:flex;align-items:center;gap:12px;background:#fafafa;';
                var selLabel = document.createElement('span');
                selLabel.textContent = 'Storm:';
                selLabel.style.cssText = 'font-size:12px;font-weight:600;color:#555;';
                var stormSelect = document.createElement('select');
                stormSelect.id = 'sp-storm-select';
                stormSelect.style.cssText = 'flex:1;padding:4px 8px;font-size:12px;border:1px solid #ddd;border-radius:4px;';
                stormSelect.onchange = function() {{ onStormChanged(this.value); }};
                selectorRow.appendChild(selLabel);
                selectorRow.appendChild(stormSelect);

                // Tab views from sub-modules
                var tableView = createTableView();
                var simView = createSimView();
                var visView = createVisView();
                var varView = createVarView();

                // Stats bar (shared)
                var statsBar = document.createElement('div');
                statsBar.id = 'sp-stats-bar';
                statsBar.style.cssText = 'padding:8px 16px;border-top:1px solid #eee;display:flex;gap:20px;font-size:11px;color:#666;background:#f9f9f9;border-radius:0 0 8px 8px;';

                spPanel.appendChild(header);
                spPanel.appendChild(selectorRow);
                spPanel.appendChild(tableView);
                spPanel.appendChild(simView);
                spPanel.appendChild(visView);
                spPanel.appendChild(varView);
                spPanel.appendChild(statsBar);
                document.body.appendChild(spPanel);
                return spPanel;
            }}

            // ==============================================================
            // Tab switching
            // ==============================================================
            function switchTab(tab) {{
                spActiveTab = tab;
                var tableEl = document.getElementById('sp-table-view');
                var simEl = document.getElementById('sp-sim-view');
                var visEl = document.getElementById('sp-vis-view');
                var varEl = document.getElementById('sp-var-view');
                var btnTable = document.getElementById('sp-tab-table');
                var btnSim = document.getElementById('sp-tab-sim');
                var btnVis = document.getElementById('sp-tab-vis');
                var btnVar = document.getElementById('sp-tab-var');

                tableEl.style.display = 'none';
                simEl.style.display = 'none';
                visEl.style.display = 'none';
                varEl.style.display = 'none';

                [btnTable, btnSim, btnVis, btnVar].forEach(function(b) {{
                    b.style.background = 'white';
                    b.style.color = '#333';
                }});

                if (tab !== 'sim' && spSimPlaying) {{
                    spStopAnim();
                }}

                if (tab === 'table') {{
                    tableEl.style.display = 'flex';
                    btnTable.style.background = '#1976d2';
                    btnTable.style.color = 'white';
                }} else if (tab === 'sim') {{
                    simEl.style.display = 'flex';
                    btnSim.style.background = '#1976d2';
                    btnSim.style.color = 'white';
                    var ss = document.getElementById('sp-storm-select');
                    var sid = ss ? ss.value : '';
                    if (sid) {{
                        setTimeout(function() {{
                            initSimMap();
                            loadSimMapData(sid);
                        }}, 50);
                    }}
                }} else if (tab === 'vis') {{
                    visEl.style.display = 'flex';
                    btnVis.style.background = '#1976d2';
                    btnVis.style.color = 'white';
                    var ss2 = document.getElementById('sp-storm-select');
                    var sid2 = ss2 ? ss2.value : '';
                    if (sid2 && (!spSimData || spSimData.storm_id !== sid2)) {{
                        loadSimData(sid2);
                    }}
                }} else {{
                    varEl.style.display = 'flex';
                    btnVar.style.background = '#1976d2';
                    btnVar.style.color = 'white';
                    if (!spVarData) loadVarData();
                }}
            }}

            // ==============================================================
            // Storm change handler (shared across all tabs)
            // ==============================================================
            function onStormChanged(stormId) {{
                if (!stormId) return;
                spSimData = null;
                spSimMapData = null;
                loadPortfolioImpact(stormId);
                if (spActiveTab === 'sim') {{
                    spStopAnim();
                    setTimeout(function() {{
                        initSimMap();
                        loadSimMapData(stormId);
                    }}, 50);
                }} else if (spActiveTab === 'vis') {{
                    loadSimData(stormId);
                }}
            }}

            // ==============================================================
            // Show / hide
            // ==============================================================
            function showPanel() {{
                console.log('[StormPortfolio] Opening panel');
                createPanel();
                spPanel.style.display = 'flex';
                spActiveTab = 'table';
                switchTab('table');
                loadStormList();
            }}

            function hidePanel() {{
                if (spPanel) spPanel.style.display = 'none';
                console.log('[StormPortfolio] Panel closed');
                spStopAnim();
                if (spSimMap) {{
                    spSimMap.remove();
                    spSimMap = null;
                }}
                spSimMapData = null;
                if (spVarChart) {{
                    spVarChart.destroy();
                    spVarChart = null;
                }}
                if (spSimChart) {{
                    spSimChart.destroy();
                    spSimChart = null;
                }}
                spVarData = null;
                spSimData = null;
            }}

            // Global entry point
            window.showStormPortfolio = showPanel;

            // Add map control button on load
            addMapControl();
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
