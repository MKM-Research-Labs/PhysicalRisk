// Copyright (c) 2022-2026 MKM Research Labs.
//
// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files (the "Software"), to deal
// in the Software without restriction, including without limitation the rights
// to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
// copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions:
//
// The above copyright notice and this permission notice shall be included in all
// copies or substantial portions of the Software.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
// SOFTWARE.

            function createPanel() {
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
                tabs.forEach(function(name, i) {
                    var tab = document.createElement('button');
                    tab.className = 'phc-tab';
                    tab.dataset.tab = i;
                    tab.textContent = name;
                    tab.style.cssText =
                        'padding:8px 14px;border:none;background:none;cursor:pointer;' +
                        'font-size:12px;font-weight:600;color:#888;border-bottom:2px solid transparent;' +
                        'margin-bottom:-2px;transition:all 0.2s;';
                    tab.onclick = function() { switchTab(i); };
                    tabBar.appendChild(tab);
                });

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
            }
