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
GaugeStormAnalysis panel — assembles the full 3-tab gauge storm panel.

Composes sub-module JavaScript (gsa_distribution, gsa_timeline)
into a single IIFE and attaches it to the Folium map.
"""

from typing import Any, Dict

import folium

from config.format import gauge_title_js as _gauge_title_js
from . import gsa_distribution, gsa_timeline


class GaugeStormAnalysis:
    """Handler for interactive gauge storm analysis dashboard."""

    def __init__(self,
                 panel_width: str = "780px",
                 panel_height: str = "560px"):
        self.panel_width = panel_width
        self.panel_height = panel_height

    def get_js(self) -> str:
        """Generate JavaScript for gauge storm analysis panel."""
        return f"""
        <script>
        (function() {{
            var PANEL_W = '{self.panel_width}';
            var PANEL_H = '{self.panel_height}';
            var currentChart = null;
            var stormPanel = null;
            var stormData = null;

            // ==============================================================
            // Sub-module code
            // ==============================================================
{gsa_distribution.get_js()}
{gsa_timeline.get_js()}

            // ================================================================
            // Panel creation
            // ================================================================
            function createPanel() {{
                if (stormPanel) return stormPanel;

                stormPanel = document.createElement('div');
                stormPanel.id = 'storm-analysis-panel';
                stormPanel.style.cssText =
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
                title.id = 'storm-panel-title';
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
                tabBar.id = 'storm-tab-bar';
                tabBar.style.cssText =
                    'display:flex;gap:0;border-bottom:2px solid #eee;padding:0 16px;background:#fafafa;';

                var tabs = ['Distribution', 'Flood Timeline', 'Worst Storms'];
                tabs.forEach(function(name, i) {{
                    var tab = document.createElement('button');
                    tab.className = 'storm-tab';
                    tab.dataset.tab = i;
                    tab.textContent = name;
                    tab.style.cssText =
                        'padding:8px 16px;border:none;background:none;cursor:pointer;' +
                        'font-size:12px;font-weight:600;color:#888;border-bottom:2px solid transparent;' +
                        'margin-bottom:-2px;transition:all 0.2s;';
                    tab.onclick = function() {{ switchTab(i); }};
                    tabBar.appendChild(tab);
                }});

                // Distribution controls (slider for Tab 0)
                var distControls = document.createElement('div');
                distControls.id = 'storm-dist-controls';
                distControls.style.cssText =
                    'padding:6px 16px;display:none;border-bottom:1px solid #eee;font-size:12px;';

                // Controls area (for storm selector dropdown on Tab 1)
                var controls = document.createElement('div');
                controls.id = 'storm-controls';
                controls.style.cssText =
                    'padding:6px 16px;display:none;border-bottom:1px solid #eee;font-size:12px;';

                // Chart container
                var chartBox = document.createElement('div');
                chartBox.id = 'storm-chart-container';
                chartBox.style.cssText = 'flex:1;padding:12px 16px;position:relative;min-height:0;';

                var canvas = document.createElement('canvas');
                canvas.id = 'storm-chart';
                chartBox.appendChild(canvas);

                // Stats bar
                var statsBar = document.createElement('div');
                statsBar.id = 'storm-stats-bar';
                statsBar.style.cssText =
                    'padding:8px 16px;border-top:1px solid #eee;font-size:12px;color:#555;' +
                    'display:flex;gap:16px;flex-wrap:wrap;';

                // Footer
                var footer = document.createElement('div');
                footer.id = 'storm-footer';
                footer.style.cssText =
                    'display:flex;justify-content:space-between;align-items:center;' +
                    'padding:8px 16px;border-top:1px solid #eee;background:#f8f9fa;' +
                    'border-radius:0 0 8px 8px;font-size:12px;';

                var statusSpan = document.createElement('span');
                statusSpan.id = 'storm-status';
                statusSpan.style.color = '#666';
                footer.appendChild(statusSpan);

                stormPanel.appendChild(header);
                stormPanel.appendChild(tabBar);
                stormPanel.appendChild(distControls);
                stormPanel.appendChild(controls);
                stormPanel.appendChild(chartBox);
                stormPanel.appendChild(statsBar);
                stormPanel.appendChild(footer);
                document.body.appendChild(stormPanel);

                return stormPanel;
            }}

            // ================================================================
            // Tab switching
            // ================================================================
            var activeTab = 0;

            function switchTab(idx) {{
                activeTab = idx;
                var tabs = document.querySelectorAll('.storm-tab');
                tabs.forEach(function(t, i) {{
                    t.style.color = i === idx ? '#1976D2' : '#888';
                    t.style.borderBottomColor = i === idx ? '#1976D2' : 'transparent';
                }});

                var distCtrl = document.getElementById('storm-dist-controls');
                distCtrl.style.display = idx === 0 ? 'block' : 'none';
                var controls = document.getElementById('storm-controls');
                controls.style.display = idx === 1 ? 'block' : 'none';

                if (!stormData) return;
                if (idx === 0) renderDistribution();
                else if (idx === 1) renderTimeline();
                else if (idx === 2) renderWorstStorms();
            }}

            // ================================================================
            // Show / Hide
            // ================================================================
            function showPanel(gaugeId) {{
                console.log('[GaugeStorm] Opening panel for', gaugeId);
                var panel = createPanel();
                panel.dataset.gaugeId = gaugeId;
                document.getElementById('storm-panel-title').textContent = 'Loading: ' + gaugeId;
                document.getElementById('storm-status').textContent = 'Loading...';
                panel.style.display = 'flex';

                activeTab = 0;
                switchTab(0);
                loadStormData(gaugeId);
            }}

            function hidePanel() {{
                if (stormPanel) stormPanel.style.display = 'none';
                if (currentChart) {{ currentChart.destroy(); currentChart = null; }}
                stormData = null;
                console.log('[GaugeStorm] Panel closed');
            }}

            // ================================================================
            // Data loading
            // ================================================================
            async function loadStormData(gaugeId) {{
                var status = document.getElementById('storm-status');
                status.textContent = 'Loading...';

                try {{
                    var cfg = window.__BACKEND_CONFIG || {{}};
                    var baseUrl = cfg.url || '';
                    var url = baseUrl + '/api/v1/gauges/' + gaugeId + '/storms';

                    var response = await fetch(url, {{mode: 'cors'}});
                    if (!response.ok) throw new Error('HTTP ' + response.status);

                    var data = await response.json();
                    if (data.status !== 'success') throw new Error(data.message || 'Failed');

                    stormData = data;
                    console.log('[GaugeStorm] Loaded', data.storm_responses.num_storms, 'storm responses for', gaugeId);

                    // Update title with gauge name
                    var gName = data.gauge_name || '';
                    var titleEl = document.getElementById('storm-panel-title');
                    if (titleEl) {{
                        titleEl.textContent = {_gauge_title_js('gName', 'gaugeId')};
                    }}

                    buildDistSlider();
                    buildStormSelector();
                    switchTab(activeTab);
                    status.textContent = data.storm_responses.num_storms + ' storms';
                }} catch (error) {{
                    console.error('[GaugeStorm] Load error:', error);
                    status.textContent = 'Error: ' + error.message;
                    if (window.showError) window.showError('Failed to load storm data');
                }}
            }}

            // ================================================================
            // Event listeners
            // ================================================================
            document.addEventListener('gaugeStormRequested', function(e) {{
                if (e.detail && e.detail.gaugeId) showPanel(e.detail.gaugeId);
            }});

            window.GaugeStormAnalysis = {{
                show: showPanel,
                hide: hidePanel
            }};

            console.log('Gauge storm analysis ready');
        }})();
        </script>
        """

    def add_to_map(self, folium_map: folium.Map) -> None:
        """Add gauge storm analysis to a Folium map."""
        folium_map.get_root().html.add_child(folium.Element(self.get_js()))

    def configure(self,
                  panel_width: str = None,
                  panel_height: str = None) -> None:
        """Update configuration."""
        if panel_width:
            self.panel_width = panel_width
        if panel_height:
            self.panel_height = panel_height

    def get_statistics(self) -> Dict[str, Any]:
        """Get configuration statistics."""
        return {
            'panel_width': self.panel_width,
            'panel_height': self.panel_height,
        }
