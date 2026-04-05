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
term structures, 6-component PRS pricing, and Basis Explorer with
storm journey visualisation (Gauge -> SHE -> SHD -> Property).

Sub-modules:
- phc_hazard: Hazard Curve tab (exceedance probability, GEV)
- phc_term: Term Structure tab (survival probability, hazard rates)
- phc_prs: PRS Pricing tab (controls, pricer, cashflows, commit)
- phc_basis: Basis Analysis (legacy, retained for backward compat)
- phc_basis_gauge: Basis Explorer — Gauge sub-tab
- phc_basis_she: Basis Explorer — SHE sub-tab
- phc_basis_shd: Basis Explorer — SHD sub-tab
- phc_basis_property: Basis Explorer — Property sub-tab
"""

from typing import Any, Dict

import folium

from visual.interactivity.panel_mixin import FoliumPanelMixin
from . import phc_hazard, phc_term, phc_prs, phc_basis
from . import phc_basis_gauge, phc_basis_she, phc_basis_shd, phc_basis_property


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
{phc_basis_gauge.get_js()}
{phc_basis_she.get_js()}
{phc_basis_shd.get_js()}
{phc_basis_property.get_js()}

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

                // Basis summary strip — always visible, shows the storm journey
                var basisStrip = document.createElement('div');
                basisStrip.id = 'phc-basis-strip';
                basisStrip.style.cssText =
                    'display:none;padding:6px 16px;background:#f0f4f8;border-bottom:1px solid #e0e0e0;' +
                    'font-size:11px;color:#555;';

                // Tab bar
                var tabBar = document.createElement('div');
                tabBar.id = 'phc-tab-bar';
                tabBar.style.cssText =
                    'display:flex;gap:0;border-bottom:2px solid #eee;padding:0 16px;background:#fafafa;';

                var tabs = ['Hazard Curve', 'Term Structure', 'PRS Pricing', 'Basis Explorer'];
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
                phcPanel.appendChild(basisStrip);
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

            // Basis Explorer state
            var basisActiveSubTab = 0;
            var basisSelectedStorm = null;
            var basisSubTabNames = ['Gauge', 'SHE', 'SHD', 'Property'];

            function ensureCanvas() {{
                var container = document.getElementById('phc-chart-container');
                container.style.display = '';
                container.style.flexDirection = '';
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

                // Remove basis sub-tab bar if switching away
                var existingSubBar = document.getElementById('phc-basis-subtab-bar');
                if (idx !== 3 && existingSubBar) {{
                    existingSubBar.remove();
                }}

                if (!phcData) return;

                if (idx !== 0 && idx !== 2 && idx !== 3) ensureCanvas();

                if (idx === 0) renderHazardCurve();
                else if (idx === 1) renderTermStructure();
                else if (idx === 2) renderPRSPricing();
                else if (idx === 3) renderBasisExplorer();
            }}

            // ==============================================================
            // Basis Explorer — nested sub-tab management
            // ==============================================================
            function renderBasisExplorer() {{
                // Create sub-tab bar if not present
                var subBar = document.getElementById('phc-basis-subtab-bar');
                if (!subBar) {{
                    subBar = document.createElement('div');
                    subBar.id = 'phc-basis-subtab-bar';
                    subBar.style.cssText =
                        'display:flex;gap:0;border-bottom:1px solid #e0e0e0;padding:0 16px;' +
                        'background:#f0f4f8;';

                    basisSubTabNames.forEach(function(name, i) {{
                        var btn = document.createElement('button');
                        btn.className = 'phc-basis-subtab';
                        btn.dataset.subtab = i;
                        btn.textContent = name;
                        btn.style.cssText =
                            'padding:6px 14px;border:none;background:none;cursor:pointer;' +
                            'font-size:11px;font-weight:600;color:#888;border-bottom:2px solid transparent;' +
                            'margin-bottom:-1px;transition:all 0.2s;';
                        btn.onclick = function() {{
                            basisActiveSubTab = i;
                            renderBasisSubTab(i);
                        }};
                        subBar.appendChild(btn);
                    }});

                    // Insert after controls area
                    var controls = document.getElementById('phc-controls');
                    controls.parentNode.insertBefore(subBar, controls.nextSibling);
                }}

                renderBasisSubTab(basisActiveSubTab);
            }}

            function renderBasisSubTab(idx) {{
                basisActiveSubTab = idx;

                // Update sub-tab styling
                var subTabs = document.querySelectorAll('.phc-basis-subtab');
                subTabs.forEach(function(t, i) {{
                    t.style.color = i === idx ? '#1565C0' : '#888';
                    t.style.borderBottomColor = i === idx ? '#1565C0' : 'transparent';
                }});

                // Destroy any existing charts before rendering
                if (basisGaugeChart) {{ basisGaugeChart.destroy(); basisGaugeChart = null; }}
                if (basisSHEChart) {{ basisSHEChart.destroy(); basisSHEChart = null; }}
                if (basisSHDChart) {{ basisSHDChart.destroy(); basisSHDChart = null; }}
                if (basisPropertyChart) {{ basisPropertyChart.destroy(); basisPropertyChart = null; }}
                if (currentChart) {{ currentChart.destroy(); currentChart = null; }}

                // Set container to flex-column for basis layouts
                var container = document.getElementById('phc-chart-container');
                container.style.display = 'flex';
                container.style.flexDirection = 'column';

                if (idx === 0) renderBasisGauge();
                else if (idx === 1) renderBasisSHE();
                else if (idx === 2) renderBasisSHD();
                else if (idx === 3) renderBasisProperty();
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
                if (basisGaugeChart) {{ basisGaugeChart.destroy(); basisGaugeChart = null; }}
                if (basisSHEChart) {{ basisSHEChart.destroy(); basisSHEChart = null; }}
                if (basisSHDChart) {{ basisSHDChart.destroy(); basisSHDChart = null; }}
                if (basisPropertyChart) {{ basisPropertyChart.destroy(); basisPropertyChart = null; }}
                var subBar = document.getElementById('phc-basis-subtab-bar');
                if (subBar) subBar.remove();
                basisSelectedStorm = null;
                basisActiveSubTab = 0;
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
                                '<p style="margin-top:16px;font-size:12px;color:#aaa;">' +
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

                    // Fetch SHE/SHD flood counts and gauge severe count for basis strip
                    try {{
                        var [sheResp, shdResp, stormsResp] = await Promise.all([
                            fetch(baseUrl + '/api/v1/properties/' + propertyId + '/she', {{mode: 'cors'}}),
                            fetch(baseUrl + '/api/v1/properties/' + propertyId + '/shd', {{mode: 'cors'}}),
                            fetch(baseUrl + '/api/v1/properties/' + propertyId + '/storms', {{mode: 'cors'}}),
                        ]);
                        if (sheResp.ok) {{
                            var sheData = await sheResp.json();
                            if (sheData.status === 'success') phcData._she = sheData.data;
                        }}
                        if (shdResp.ok) {{
                            var shdData = await shdResp.json();
                            if (shdData.status === 'success') phcData._shd = shdData.data;
                        }}
                        if (stormsResp.ok) {{
                            var stormsData = await stormsResp.json();
                            if (stormsData.status === 'success') {{
                                phcData._severe_at_gauge = (stormsData.summary || {{}}).severe_at_nearest_gauge || 0;
                                phcData._storms_data = stormsData;
                            }}
                        }}
                    }} catch (basisErr) {{
                        console.warn('SHE/SHD/storms data not available:', basisErr.message);
                    }}

                    console.log('[PropertyHazard] Loaded hazard data for', propertyId, '(' + phcData.flood_count + ' floods)');
                    buildPRSControls();
                    populateBasisStrip();
                    switchTab(activeTab);
                    var spread = (phcData.term_structure || {{}}).severe ? phcData.term_structure.severe.prs_spread_bps[0] : 0;
                    // Gauge severe count from storms endpoint
                    var gaugeSevere = phcData._severe_at_gauge || 0;
                    var propFloods = phcData.flood_count || 0;
                    var basisEvents = gaugeSevere - propFloods;
                    status.textContent = gaugeSevere + ' gauge severe \\u2192 ' + propFloods + ' property floods | basis: ' + basisEvents + ' events | spread: ' + spread.toFixed(1) + 'bp';
                }} catch (error) {{
                    console.error('[PropertyHazard] Load error:', error);
                    status.textContent = 'Error: ' + error.message;
                    if (window.showError) window.showError('Could not connect to server');
                }}
            }}

            // ==============================================================
            // Basis summary strip — storm journey at a glance
            // ==============================================================
            function populateBasisStrip() {{
                var strip = document.getElementById('phc-basis-strip');
                if (!strip || !phcData) return;

                var ng0 = (phcData.nearest_gauges || [])[0] || {{}};
                var gaugeSevere = phcData._severe_at_gauge || 0;
                var propFloods = phcData.flood_count || 0;
                var sd = phcData.spread_decomposition || {{}};
                // Gauge spread from GEV severe count — consistent with waterfall
                var gaugeSpread = gaugeSevere > 0 ? (gaugeSevere / 20000 * 10000) : (sd.gauge_spread_bps || 0);
                var propSpread = propFloods > 0 ? (propFloods / 20000 * 10000) : 0;

                // Physical measurements
                var stormsGauges = (phcData._storms_data || {{}}).nearest_gauges || [];
                var stormGauge0 = stormsGauges.find(function(sg) {{ return sg.gauge_id === ng0.gauge_id; }}) || {{}};
                var gaugeName = stormGauge0.gauge_name || (ng0.gauge_id || '').substring(0, 18);
                var gaugeElev = ng0.gauge_elevation_m || 0;
                var propElev = phcData.elevation_m || 0;
                var distKm = ng0.distance_km || 0;
                var floorLevel = phcData.floor_level_m || 0;
                var elevDiff = propElev - gaugeElev;
                var effectiveDiff = elevDiff + floorLevel - 0.5;

                // Storm counts at each stage
                var storms = phcData.storm_details || [];
                var gaugeCount = storms.filter(function(s) {{ return s.exceeded_severe; }}).length || gaugeSevere;
                var sheCount = phcData._she ? (phcData._she.flood_count || 0) : '\\u2014';
                var shdCount = phcData._shd ? (phcData._shd.flood_count || 0) : '\\u2014';

                var chipStyle = 'display:inline-flex;align-items:center;gap:4px;padding:4px 10px;' +
                    'border-radius:12px;font-weight:600;font-size:11px;';
                var arrowStyle = 'color:#bbb;font-size:16px;margin:0 4px;';
                var countStyle = 'font-size:15px;font-weight:700;';
                var labelStyle = 'font-size:9px;color:#888;text-transform:uppercase;letter-spacing:0.3px;line-height:1.2;';
                var detailStyle = 'font-size:9px;color:#999;line-height:1.1;';

                strip.innerHTML =
                    '<div style="display:flex;align-items:center;gap:2px;">' +

                    // Gauge
                    '<div style="' + chipStyle + 'background:#FFEBEE;color:#C62828;flex-direction:column;min-width:70px;text-align:center;">' +
                    '<span style="' + countStyle + '">' + gaugeCount + '</span>' +
                    '<span style="' + labelStyle + '">gauge severe</span>' +
                    '<span style="' + detailStyle + '">' + gaugeSpread.toFixed(0) + 'bp</span>' +
                    '</div>' +

                    '<span style="' + arrowStyle + '">\\u2192</span>' +

                    // SHE (elevation)
                    '<div style="' + chipStyle + 'background:#FFF3E0;color:#E65100;flex-direction:column;min-width:70px;text-align:center;">' +
                    '<span style="' + countStyle + '">' + sheCount + '</span>' +
                    '<span style="' + labelStyle + '">SHE</span>' +
                    '<span style="' + detailStyle + '">+' + elevDiff.toFixed(1) + 'm</span>' +
                    '</div>' +

                    '<span style="' + arrowStyle + '">\\u2192</span>' +

                    // SHD (distance)
                    '<div style="' + chipStyle + 'background:#E8F5E9;color:#2E7D32;flex-direction:column;min-width:70px;text-align:center;">' +
                    '<span style="' + countStyle + '">' + shdCount + '</span>' +
                    '<span style="' + labelStyle + '">SHD</span>' +
                    '<span style="' + detailStyle + '">' + distKm.toFixed(1) + 'km</span>' +
                    '</div>' +

                    '<span style="' + arrowStyle + '">\\u2192</span>' +

                    // Property
                    '<div style="' + chipStyle + 'background:#E3F2FD;color:#1565C0;flex-direction:column;min-width:70px;text-align:center;">' +
                    '<span style="' + countStyle + '">' + propFloods + '</span>' +
                    '<span style="' + labelStyle + '">property</span>' +
                    '<span style="' + detailStyle + '">' + propSpread.toFixed(1) + 'bp</span>' +
                    '</div>' +

                    // Separator + spread summary
                    '<div style="margin-left:12px;padding-left:12px;border-left:1px solid #ddd;font-size:10px;color:#666;line-height:1.5;">' +
                    '<div><b>Gauge:</b> ' + gaugeName + '</div>' +
                    '<div><b>Spread:</b> ' + gaugeSpread.toFixed(1) + 'bp \\u2192 ' + propSpread.toFixed(1) + 'bp</div>' +
                    '<div><b>Basis:</b> ' + (gaugeSpread - propSpread).toFixed(1) + 'bp</div>' +
                    '</div>' +

                    '</div>';

                strip.style.display = 'block';
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
