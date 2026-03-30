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
Property hazard curve and PRS pricing visualization.

Interactive Chart.js tabbed panel showing property-level hazard curves,
term structures, 6-component PRS pricing, and basis analysis against
nearest gauges.

Sub-modules:
- phc_hazard: Hazard Curve tab (exceedance probability, GEV)
- phc_term: Term Structure tab (survival probability, hazard rates)
- phc_prs: PRS Pricing tab (controls, pricer, cashflows, commit)
- phc_basis: Basis Analysis tab (gauge basis bar chart)
"""

from typing import Any, Dict

import folium

from visual.interactivity.panel_mixin import FoliumPanelMixin
from . import phc_hazard, phc_term, phc_prs, phc_basis


class PropertyHazardCurvePanel(FoliumPanelMixin):
    """Handler for interactive property hazard curve / PRS pricing dashboard."""

    def __init__(self,
                 panel_width: str = "1100px",
                 panel_height: str = "750px"):
        self.panel_width = panel_width
        self.panel_height = panel_height

    def get_js(self) -> str:
        """Generate JavaScript for property hazard curve panel."""
        return f"""
        <script>
        (function() {{
            var PANEL_W = '{self.panel_width}';
            var PANEL_H = '{self.panel_height}';
            var currentChart = null;
            var phcPanel = null;
            var phcData = null;
            var counterpartyData = [];

            // ==============================================================
            // Sub-module code (state vars + functions)
            // ==============================================================
{phc_hazard.get_js()}
{phc_term.get_js()}
{phc_prs.get_js()}
{phc_basis.get_js()}

            // ==============================================================
            // Panel creation
            // ==============================================================
            function createPanel() {{
                if (phcPanel) return phcPanel;

                phcPanel = document.createElement('div');
                phcPanel.id = 'property-hc-panel';
                phcPanel.style.cssText =
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
                title.id = 'phc-panel-title';
                title.style.cssText = 'font-weight:bold;font-size:14px;color:#333;';

                var closeBtn = document.createElement('button');
                closeBtn.innerHTML = '&times;';
                closeBtn.style.cssText =
                    'border:none;background:none;font-size:24px;cursor:pointer;' +
                    'color:#666;padding:0 8px;line-height:1;';
                closeBtn.onclick = hidePanel;

                header.appendChild(title);
                header.appendChild(closeBtn);

                // Tab bar
                var tabBar = document.createElement('div');
                tabBar.id = 'phc-tab-bar';
                tabBar.style.cssText =
                    'display:flex;gap:0;border-bottom:2px solid #eee;padding:0 16px;background:#fafafa;';

                var tabs = ['Hazard Curve', 'Term Structure', 'PRS Pricing', 'Basis Analysis'];
                tabs.forEach(function(name, i) {{
                    var tab = document.createElement('button');
                    tab.className = 'phc-tab';
                    tab.dataset.tab = i;
                    tab.textContent = name;
                    tab.style.cssText =
                        'padding:8px 14px;border:none;background:none;cursor:pointer;' +
                        'font-size:12px;font-weight:600;color:#888;border-bottom:2px solid transparent;' +
                        'margin-bottom:-2px;transition:all 0.2s;';
                    tab.onclick = function() {{ switchTab(i); }};
                    tabBar.appendChild(tab);
                }});

                // Controls area (for PRS inputs on Tab 2)
                var controls = document.createElement('div');
                controls.id = 'phc-controls';
                controls.style.cssText = 'padding:0;display:none;border-bottom:1px solid #eee;';

                // Chart container
                var chartBox = document.createElement('div');
                chartBox.id = 'phc-chart-container';
                chartBox.style.cssText = 'flex:1;padding:12px 16px;position:relative;min-height:0;';

                var canvas = document.createElement('canvas');
                canvas.id = 'phc-chart';
                chartBox.appendChild(canvas);

                // Stats bar
                var statsBar = document.createElement('div');
                statsBar.id = 'phc-stats-bar';
                statsBar.style.cssText =
                    'padding:8px 16px;border-top:1px solid #eee;font-size:12px;color:#555;' +
                    'display:flex;gap:16px;flex-wrap:wrap;';

                // Footer
                var footer = document.createElement('div');
                footer.id = 'phc-footer';
                footer.style.cssText =
                    'display:flex;justify-content:space-between;align-items:center;' +
                    'padding:8px 16px;border-top:1px solid #eee;background:#f8f9fa;' +
                    'border-radius:0 0 8px 8px;font-size:12px;';

                var statusSpan = document.createElement('span');
                statusSpan.id = 'phc-status';
                statusSpan.style.color = '#666';
                footer.appendChild(statusSpan);

                phcPanel.appendChild(header);
                phcPanel.appendChild(tabBar);
                phcPanel.appendChild(controls);
                phcPanel.appendChild(chartBox);
                phcPanel.appendChild(statsBar);
                phcPanel.appendChild(footer);
                document.body.appendChild(phcPanel);

                return phcPanel;
            }}

            // ==============================================================
            // Tab switching
            // ==============================================================
            var activeTab = 0;

            function ensureCanvas() {{
                var container = document.getElementById('phc-chart-container');
                if (!document.getElementById('phc-chart') || document.getElementById('phc-chart').tagName !== 'CANVAS') {{
                    container.innerHTML = '';
                    var canvas = document.createElement('canvas');
                    canvas.id = 'phc-chart';
                    container.appendChild(canvas);
                }}
            }}

            function switchTab(idx) {{
                activeTab = idx;
                var tabs = document.querySelectorAll('.phc-tab');
                tabs.forEach(function(t, i) {{
                    t.style.color = i === idx ? '#1976D2' : '#888';
                    t.style.borderBottomColor = i === idx ? '#1976D2' : 'transparent';
                }});

                var controls = document.getElementById('phc-controls');
                controls.style.display = idx === 2 ? 'block' : 'none';

                if (!phcData) return;

                if (idx !== 2) ensureCanvas();

                if (idx === 0) renderHazardCurve();
                else if (idx === 1) renderTermStructure();
                else if (idx === 2) renderPRSPricing();
                else if (idx === 3) renderBasisAnalysis();
            }}

            // ==============================================================
            // Show / Hide
            // ==============================================================
            function showPanel(propertyId) {{
                console.log('[PropertyHazard] Opening panel for', propertyId);
                var panel = createPanel();
                panel.dataset.propertyId = propertyId;
                document.getElementById('phc-panel-title').textContent = 'PRS Pricer: ' + propertyId;
                document.getElementById('phc-status').textContent = 'Loading...';
                panel.style.display = 'flex';

                activeTab = 0;
                switchTab(0);
                loadData(propertyId);
            }}

            function hidePanel() {{
                if (phcPanel) phcPanel.style.display = 'none';
                if (currentChart) {{ currentChart.destroy(); currentChart = null; }}
                phcData = null;
                console.log('[PropertyHazard] Panel closed');
            }}

            // ==============================================================
            // Data loading
            // ==============================================================
            async function loadData(propertyId) {{
                var status = document.getElementById('phc-status');
                status.textContent = 'Loading...';

                try {{
                    var cfg = window.__BACKEND_CONFIG || {{}};
                    var baseUrl = cfg.url || '';
                    var url = baseUrl + '/api/v1/properties/' + propertyId + '/hazard';

                    var response = await fetch(url, {{mode: 'cors'}});
                    var result = await response.json();

                    if (!response.ok || result.status !== 'success') {{
                        var msg = result.message || ('HTTP ' + response.status);
                        status.textContent = msg;
                        var content = document.getElementById('phc-chart-container');
                        if (content) {{
                            content.innerHTML =
                                '<div style="text-align:center;padding:60px 20px;color:#888;">' +
                                '<p style="font-size:16px;font-weight:600;margin-bottom:12px;">No Hazard Curve Data</p>' +
                                '<p>' + msg + '</p>' +
                                '<p style="margin-top:16px;font-size:12px;color:#aaa;">Properties need \\u2265 3 flood events for GEV fitting.<br>' +
                                'Try re-running: <code>python app.py port --propertyts --propertyhc</code></p></div>';
                        }}
                        return;
                    }}

                    phcData = result.data;

                    // Fetch counterparties for PRS tab
                    try {{
                        var ctpyResp = await fetch(baseUrl + '/api/v1/counterparties', {{mode: 'cors'}});
                        if (ctpyResp.ok) {{
                            var ctpyData = await ctpyResp.json();
                            if (ctpyData.status === 'success') {{
                                counterpartyData = ctpyData.counterparties || [];
                            }}
                        }}
                    }} catch (ctpyErr) {{
                        console.warn('Counterparty data not available:', ctpyErr.message);
                    }}

                    console.log('[PropertyHazard] Loaded hazard data for', propertyId, '(' + phcData.flood_count + ' floods)');
                    buildPRSControls();
                    switchTab(activeTab);
                    var method = phcData.has_gev ? 'GEV' : 'Floor (' + (phcData.min_spread_bps || 2) + 'bp)';
                    status.textContent = propertyId + ' | ' + phcData.flood_count + ' floods | ' + method;
                }} catch (error) {{
                    console.error('[PropertyHazard] Load error:', error);
                    status.textContent = 'Error: ' + error.message;
                    if (window.showError) window.showError('Could not connect to server');
                }}
            }}

            // ==============================================================
            // Event listeners
            // ==============================================================
            document.addEventListener('propertyHazardRequested', function(e) {{
                if (e.detail && e.detail.propertyId) showPanel(e.detail.propertyId);
            }});

            document.addEventListener('keydown', function(e) {{
                if (e.key === 'Escape' && phcPanel && phcPanel.style.display !== 'none') {{
                    hidePanel();
                }}
            }});

            window.PropertyHazardCurvePanel = {{
                show: showPanel,
                hide: hidePanel
            }};

            console.log('Property hazard curve panel ready');
        }})();
        </script>
        """

    # add_to_map, configure, get_statistics inherited from FoliumPanelMixin
