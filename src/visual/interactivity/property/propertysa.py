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
Property storm scenario analysis visualization.

Interactive Chart.js tabbed panel showing property flood depth distribution,
worst-storm rankings, flood history, and mortgage impact.
Loads data from the /api/v1/properties/{id}/storms endpoint.

Sub-modules:
- psa_charts: Distribution (Tab 0) and Worst Storms (Tab 2)
- psa_timeline: Flood Timeline hydrograph (Tab 1)
- psa_impact: Flood History (Tab 3) and Mortgage Impact (Tab 4)
"""

from typing import Any, Dict

import folium

from . import psa_charts, psa_impact, psa_timeline


class PropertyStormAnalysis:
    """Handler for interactive property storm analysis dashboard."""

    def __init__(self,
                 panel_width: str = "780px",
                 panel_height: str = "560px"):
        self.panel_width = panel_width
        self.panel_height = panel_height

    def get_js(self) -> str:
        """Generate JavaScript for property storm analysis panel."""
        return f"""
        <script>
        (function() {{
            var PANEL_W = '{self.panel_width}';
            var PANEL_H = '{self.panel_height}';
            var currentChart = null;
            var propStormPanel = null;
            var propStormData = null;
            var propMortgageData = null;
            var activeTab = 0;

            // ==============================================================
            // Sub-module code (state vars + functions)
            // ==============================================================
{psa_charts.get_js()}
{psa_timeline.get_js()}
{psa_impact.get_js()}

            // ================================================================
            // Panel creation
            // ================================================================
            function createPanel() {{
                if (propStormPanel) return propStormPanel;

                propStormPanel = document.createElement('div');
                propStormPanel.id = 'prop-storm-panel';
                propStormPanel.style.cssText =
                    'position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);' +
                    'width:' + PANEL_W + ';height:' + PANEL_H + ';' +
                    'background:white;border:1px solid #ccc;border-radius:8px;' +
                    'box-shadow:0 4px 20px rgba(0,0,0,0.3);z-index:2000;' +
                    'display:none;flex-direction:column;font-family:Arial,sans-serif;';

                // Header
                var header = document.createElement('div');
                header.style.cssText =
                    'display:flex;justify-content:space-between;align-items:center;' +
                    'padding:10px 16px;border-bottom:1px solid #eee;background:#f8f9fa;' +
                    'border-radius:8px 8px 0 0;';

                var title = document.createElement('span');
                title.id = 'prop-storm-title';
                title.style.cssText = 'font-weight:bold;font-size:14px;color:#333;';

                var rightHeader = document.createElement('div');
                rightHeader.style.cssText = 'display:flex;align-items:center;gap:10px;';

                var status = document.createElement('span');
                status.id = 'prop-storm-status';
                status.style.cssText = 'font-size:11px;color:#888;';

                var closeBtn = document.createElement('button');
                closeBtn.innerHTML = '&times;';
                closeBtn.style.cssText =
                    'border:none;background:none;font-size:24px;cursor:pointer;' +
                    'color:#666;padding:0 8px;line-height:1;';
                closeBtn.onclick = hidePanel;

                rightHeader.appendChild(status);
                rightHeader.appendChild(closeBtn);
                header.appendChild(title);
                header.appendChild(rightHeader);

                // Tab bar
                var tabBar = document.createElement('div');
                tabBar.id = 'prop-storm-tab-bar';
                tabBar.style.cssText =
                    'display:flex;gap:0;border-bottom:2px solid #eee;padding:0 16px;background:#fafafa;';

                var tabs = ['Distribution', 'Flood Timeline', 'Worst Storms', 'Flood History', 'Mortgage Impact', 'Insurance Report', 'PRS Pricing'];
                tabs.forEach(function(name, i) {{
                    var tab = document.createElement('button');
                    tab.className = 'prop-storm-tab';
                    tab.textContent = name;
                    tab.dataset.idx = i;
                    if (i === 5) {{
                        // Insurance Report: fetch PDF and show in popup
                        tab.style.cssText =
                            'padding:8px 14px;border:none;background:none;cursor:pointer;' +
                            'font-size:12px;font-weight:600;color:#c62828;' +
                            'border-bottom:2px solid transparent;margin-bottom:-2px;margin-left:8px;';
                        tab.title = 'View flood damage claim report';
                        tab.onclick = async function() {{
                            var propId = document.getElementById('prop-storm-panel') &&
                                         document.getElementById('prop-storm-panel').dataset.propertyId;
                            if (!propId) return;
                            var cfg = window.__BACKEND_CONFIG || {{}};
                            var baseUrl = cfg.url || '';
                            tab.textContent = 'Loading...';
                            try {{
                                var resp = await fetch(baseUrl + '/api/v1/properties/' + propId + '/claim-report', {{mode: 'cors'}});
                                if (!resp.ok) throw new Error('HTTP ' + resp.status);
                                var blob = await resp.blob();
                                var reader = new FileReader();
                                reader.onload = function() {{
                                    var base64 = reader.result.split(',')[1];
                                    if (window.PropertyPDFPanel && typeof window.PropertyPDFPanel.show === 'function') {{
                                        window.PropertyPDFPanel.show(propId, base64);
                                    }} else {{
                                        window.open(baseUrl + '/api/v1/properties/' + propId + '/claim-report', '_blank');
                                    }}
                                    tab.textContent = 'Insurance Report';
                                }};
                                reader.readAsDataURL(blob);
                            }} catch (err) {{
                                console.error('Claim report error:', err);
                                if (window.showError) window.showError('Failed to load claim report: ' + err.message);
                                tab.textContent = 'Insurance Report';
                            }}
                        }};
                    }} else if (i === 6) {{
                        // PRS Pricing: open PRS Pricer panel
                        tab.style.cssText =
                            'padding:8px 14px;border:none;background:none;cursor:pointer;' +
                            'font-size:12px;font-weight:600;color:#1565c0;' +
                            'border-bottom:2px solid transparent;margin-bottom:-2px;margin-left:4px;';
                        tab.title = 'Open PRS pricing workflow';
                        tab.onclick = function() {{
                            var propId = document.getElementById('prop-storm-panel') &&
                                         document.getElementById('prop-storm-panel').dataset.propertyId;
                            if (propId && window.viewPropertyHazard) {{
                                window.viewPropertyHazard(propId);
                            }}
                        }};
                    }} else {{
                        tab.style.cssText =
                            'padding:8px 16px;border:none;background:none;cursor:pointer;' +
                            'font-size:12px;font-weight:500;color:#666;' +
                            'border-bottom:2px solid transparent;margin-bottom:-2px;';
                        tab.onclick = function() {{ switchTab(i); }};
                    }}
                    tabBar.appendChild(tab);
                }});

                // Content area
                var content = document.createElement('div');
                content.id = 'prop-storm-content';
                content.style.cssText = 'flex:1;padding:12px 16px;overflow-y:auto;position:relative;';

                propStormPanel.appendChild(header);
                propStormPanel.appendChild(tabBar);
                propStormPanel.appendChild(content);
                document.body.appendChild(propStormPanel);
                return propStormPanel;
            }}

            var pendingStormId = null;

            function switchTab(idx, stormId) {{
                activeTab = idx;
                document.querySelectorAll('.prop-storm-tab').forEach(function(t, i) {{
                    t.style.color = i === idx ? '#1976d2' : '#666';
                    t.style.borderBottomColor = i === idx ? '#1976d2' : 'transparent';
                    t.style.fontWeight = i === idx ? '700' : '500';
                }});
                if (!propStormData) return;
                if (idx === 0) renderDistribution();
                else if (idx === 1) renderTimeline(stormId || null);
                else if (idx === 2) renderWorstStorms();
                else if (idx === 3) renderFloodHistory();
                else if (idx === 4) renderMortgageImpact();
            }}

            // ================================================================
            // Show / hide / load
            // ================================================================
            function showPanel(propertyId) {{
                console.log('[PropertyStorm] Opening panel for', propertyId);
                var panel = createPanel();
                panel.dataset.propertyId = propertyId;
                document.getElementById('prop-storm-title').textContent = 'Property Storm Scenarios: ' + propertyId;
                document.getElementById('prop-storm-status').textContent = 'Loading...';
                panel.style.display = 'flex';
                activeTab = 0;
                switchTab(0);
                loadData(propertyId);
            }}

            function hidePanel() {{
                if (propStormPanel) propStormPanel.style.display = 'none';
                if (currentChart) {{ currentChart.destroy(); currentChart = null; }}
                console.log('[PropertyStorm] Panel closed');
            }}

            async function loadData(propertyId) {{
                var status = document.getElementById('prop-storm-status');
                status.textContent = 'Loading...';
                propMortgageData = null;
                try {{
                    var cfg = window.__BACKEND_CONFIG || {{}};
                    var baseUrl = cfg.url || '';
                    var url = baseUrl + '/api/v1/properties/' + propertyId + '/storms';
                    var response = await fetch(url, {{mode: 'cors'}});
                    if (!response.ok) throw new Error('HTTP ' + response.status);
                    var data = await response.json();
                    if (data.status !== 'success') throw new Error(data.message || 'Failed');
                    propStormData = data;
                    var allEvents = data.flood_events || [];
                    var nPropertyFloods = allEvents.filter(function(e) {{ return e.flooded; }}).length;
                    var summary = data.summary || {{}};
                    console.log('[PropertyStorm] Loaded', allEvents.length, 'events,', nPropertyFloods, 'property floods for', propertyId);
                    var severeCount = summary.severe_at_nearest_gauge || summary.floods_at_nearest_gauge || 0;
                    status.textContent = severeCount + ' gauge severe, ' + nPropertyFloods + ' property floods';

                    // Fetch mortgage data for mortgage impact tab
                    try {{
                        var mortUrl = baseUrl + '/api/v1/properties/' + propertyId + '/mortgage';
                        var mortResp = await fetch(mortUrl, {{mode: 'cors'}});
                        if (mortResp.ok) {{
                            var mortData = await mortResp.json();
                            if (mortData.status === 'success') propMortgageData = mortData.mortgage;
                        }}
                    }} catch(e) {{ /* mortgage data optional */ }}

                    switchTab(activeTab);
                }} catch (error) {{
                    console.error('Property storm data error:', error);
                    status.textContent = 'Error: ' + error.message;
                    if (window.showError) window.showError('Failed to load property storm data');
                }}
            }}

            // ================================================================
            // Event listeners
            // ================================================================
            document.addEventListener('propertyStormRequested', function(e) {{
                if (e.detail && e.detail.propertyId) showPanel(e.detail.propertyId);
            }});

            window.PropertyStormAnalysis = {{
                show: showPanel,
                hide: hidePanel,
                switchTab: switchTab
            }};
            window.propStormSwitchTab = switchTab;

            console.log('Property storm analysis ready');
        }})();
        </script>
        """

    def add_to_map(self, folium_map: folium.Map) -> None:
        """Add property storm analysis to a Folium map."""
        folium_map.get_root().html.add_child(folium.Element(self.get_js()))

    def get_statistics(self) -> Dict[str, Any]:
        return {
            'panel_width': self.panel_width,
            'panel_height': self.panel_height,
        }
