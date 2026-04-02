# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""Panel DOM construction — createPanel() JS function."""


def get_create_panel_js() -> str:
    """Return JS that defines the createPanel() function."""
    return """
            // ================================================================
            // Panel creation
            // ================================================================
            function createPanel() {
                if (hazardPanel) return hazardPanel;

                hazardPanel = document.createElement('div');
                hazardPanel.id = 'hazard-curve-panel';
                hazardPanel.style.cssText =
                    'position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);' +
                    'width:' + PANEL_W + ';height:' + PANEL_H + ';' +
                    'max-width:1400px;max-height:900px;min-width:600px;min-height:400px;' +
                    'background:white;border:1px solid #ccc;border-radius:8px;' +
                    'box-shadow:0 4px 20px rgba(0,0,0,0.3);z-index:2000;' +
                    'display:none;flex-direction:column;font-family:Arial,sans-serif;' +
                    'resize:both;overflow:hidden;';

                // Header
                var header = document.createElement('div');
                header.style.cssText =
                    'display:flex;justify-content:space-between;align-items:center;' +
                    'padding:10px 16px;border-bottom:1px solid #eee;background:#f8f9fa;' +
                    'border-radius:8px 8px 0 0;';

                var leftHeader = document.createElement('div');
                leftHeader.style.cssText = 'display:flex;align-items:center;gap:12px;';

                var title = document.createElement('span');
                title.id = 'hazard-panel-title';
                title.style.cssText = 'font-weight:bold;font-size:14px;color:#333;';

                leftHeader.appendChild(title);

                var closeBtn = document.createElement('button');
                closeBtn.innerHTML = '&times;';
                closeBtn.style.cssText =
                    'border:none;background:none;font-size:24px;cursor:pointer;' +
                    'color:#666;padding:0 8px;line-height:1;';
                closeBtn.onclick = hidePanel;

                header.appendChild(leftHeader);
                header.appendChild(closeBtn);

                // Tab bar
                var tabBar = document.createElement('div');
                tabBar.id = 'hazard-tab-bar';
                tabBar.style.cssText =
                    'display:flex;gap:0;border-bottom:1px solid #ddd;padding:0;background:#f8f9fa;' +
                    'border-radius:0;overflow:hidden;';

                var tabs = ['PRS Pricing', 'Hazard Curve', 'Return Period', 'Flood Probability', 'Historical', 'Stress Test'];
                tabs.forEach(function(name, i) {
                    var tab = document.createElement('button');
                    tab.className = 'hazard-tab';
                    tab.dataset.tab = i;
                    tab.textContent = name;
                    tab.style.cssText =
                        'padding:6px 14px;border:none;cursor:pointer;' +
                        'font-size:11px;font-weight:600;' +
                        (i === 0 ? 'background:#1976d2;color:white;' : 'background:#f5f5f5;color:#555;');
                    tab.onclick = function() { switchTab(i); };
                    tabBar.appendChild(tab);
                });

                // Gauge Blotter button — after last tab, muted until trades confirmed
                var blotterBtn = document.createElement('button');
                blotterBtn.id = 'hazard-blotter-link';
                blotterBtn.textContent = '\u21D2 Gauge Blotter';
                blotterBtn.style.cssText =
                    'padding:6px 14px;border:none;font-size:11px;font-weight:600;' +
                    'margin-left:auto;cursor:default;' +
                    'background:#f5f5f5;color:#bbb;';
                blotterBtn.disabled = true;
                blotterBtn.onclick = function() {
                    if (blotterBtn.disabled) return;
                    var gaugeId = hazardPanel.dataset.gaugeId || '';
                    var gaugeName = hazardPanel.dataset.gaugeName || '';
                    if (gaugeId && window.showGaugeBlotter) {
                        hidePanel();
                        window.showGaugeBlotter(gaugeId, gaugeName);
                    }
                };
                tabBar.appendChild(blotterBtn);

                // Controls area (for PRS inputs on Tab 3)
                var controls = document.createElement('div');
                controls.id = 'hazard-controls';
                controls.style.cssText = 'padding:0;display:none;border-bottom:1px solid #eee;';

                // Chart container
                var chartBox = document.createElement('div');
                chartBox.id = 'hazard-chart-container';
                chartBox.style.cssText = 'flex:1;padding:12px 16px;position:relative;min-height:0;';

                var canvas = document.createElement('canvas');
                canvas.id = 'hazard-chart';
                chartBox.appendChild(canvas);

                // Stats bar
                var statsBar = document.createElement('div');
                statsBar.id = 'hazard-stats-bar';
                statsBar.style.cssText =
                    'padding:8px 16px;border-top:1px solid #eee;font-size:12px;color:#555;' +
                    'display:flex;gap:16px;flex-wrap:wrap;';

                // Footer
                var footer = document.createElement('div');
                footer.id = 'hazard-footer';
                footer.style.cssText =
                    'display:flex;justify-content:space-between;align-items:center;' +
                    'padding:8px 16px;border-top:1px solid #eee;background:#f8f9fa;' +
                    'border-radius:0 0 8px 8px;font-size:12px;';

                var statusSpan = document.createElement('span');
                statusSpan.id = 'hazard-status';
                statusSpan.style.color = '#666';
                footer.appendChild(statusSpan);

                hazardPanel.appendChild(header);
                hazardPanel.appendChild(tabBar);
                hazardPanel.appendChild(controls);
                hazardPanel.appendChild(chartBox);
                hazardPanel.appendChild(statsBar);
                hazardPanel.appendChild(footer);
                document.body.appendChild(hazardPanel);

                return hazardPanel;
            }
"""
