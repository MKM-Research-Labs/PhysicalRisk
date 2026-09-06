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

            function addMapControl() {
                function findMap() {
                    var mapKey = Object.keys(window).find(function(k) { return k.startsWith('map_'); });
                    if (mapKey) return window[mapKey];
                    return null;
                }

                function tryAdd() {
                    var map = findMap();
                    if (!map) {
                        setTimeout(tryAdd, 500);
                        return;
                    }

                    var TradingControl = L.Control.extend({
                        options: { position: 'topright' },
                        onAdd: function() {
                            var container = L.DomUtil.create('div', 'leaflet-bar leaflet-control');
                            var btn = L.DomUtil.create('a', '', container);
                            btn.href = '#';
                            btn.title = "Trader's Workstation";
                            btn.setAttribute('role', 'button');
                            btn.innerHTML = '<span style="font-size:var(--size-18);font-weight:bold;font-family:serif;">&Pi;</span>';
                            btn.style.cssText = 'display:flex;align-items:center;justify-content:center;width:30px;height:30px;cursor:pointer;background:var(--panel);';

                            L.DomEvent.disableClickPropagation(container);
                            L.DomEvent.on(btn, 'click', function(e) {
                                L.DomEvent.preventDefault(e);
                                showPanel();
                            });
                            return container;
                        }
                    });

                    new TradingControl().addTo(map);
                }

                setTimeout(tryAdd, 1000);
            }

            // ==============================================================
            // Panel creation
            // ==============================================================
            function createPanel() {
                if (tdPanel) return tdPanel;

                tdPanel = document.createElement('div');
                tdPanel.id = 'trading-desk-panel';
                tdPanel.style.cssText =
                    'position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);' +
                    'width:' + PANEL_W + ';height:' + PANEL_H + ';' +
                    'max-width:1400px;max-height:900px;min-width:600px;min-height:400px;' +
                    'background:var(--panel);border:1px solid var(--divider);border-radius:var(--radius-lg);' +
                    'box-shadow:var(--shadow-toast);z-index:2000;' +
                    'display:none;flex-direction:column;font-family:Arial,sans-serif;' +
                    'resize:both;overflow:hidden;';

                // Header with tabs
                var header = document.createElement('div');
                header.style.cssText =
                    'display:flex;justify-content:space-between;align-items:center;' +
                    'padding:var(--space-5) var(--space-8);border-bottom:1px solid var(--line-soft);background:var(--wash);' +
                    'border-radius:var(--radius-lg) var(--radius-lg) 0 0;';

                var leftHeader = document.createElement('div');
                leftHeader.style.cssText = 'display:flex;align-items:center;gap:var(--space-8);';

                var piIcon = document.createElement('span');
                piIcon.innerHTML = '&Pi;';
                piIcon.style.cssText = 'font-size:22px;font-weight:bold;font-family:serif;color:var(--accent-mid);';

                var title = document.createElement('span');
                title.style.cssText = 'font-weight:bold;font-size:var(--size-14);color:var(--text);';
                title.textContent = "Trader's Workstation";

                var toggleWrap = document.createElement('div');
                toggleWrap.style.cssText = 'display:flex;border:1px solid var(--line-strong);border-radius:var(--radius-4);overflow:hidden;';

                var tabs = [
                    {id: 'client', label: 'Client'},
                    {id: 'blotter', label: 'Blotter'},
                    {id: 'market', label: 'Market'},
                    {id: 'risk', label: 'FS01'},
                    {id: 'map', label: 'Aggregate'},
                    {id: 'eod', label: 'EOD'},
                    {id: 'curves', label: 'Curves'},
                    {id: 'stress', label: 'Stress'},
                    {id: 'portstress', label: 'Port Stress'},
                    {id: 'classifiers', label: 'Classifiers'}
                ];

                tabs.forEach(function(tab) {
                    var btn = document.createElement('button');
                    btn.id = 'td-tab-' + tab.id;
                    btn.textContent = tab.label;
                    btn.style.cssText = 'padding:var(--space-2) var(--space-7);font-size:var(--size-xs);border:none;cursor:pointer;font-weight:600;' +
                        (tab.id === 'blotter' ? 'background:var(--accent);color:var(--inverse);' : 'background:var(--sunken);color:var(--text-2);');
                    btn.onclick = function() {
                        // Remembered so a preload callback landing
                        // afterwards does not switch away from it.
                        window._tdTabClickedDuringOpen = tab.id;
                        switchTab(tab.id);
                    };
                    toggleWrap.appendChild(btn);
                });

                leftHeader.appendChild(piIcon);
                leftHeader.appendChild(title);
                leftHeader.appendChild(toggleWrap);

                var closeBtn = document.createElement('button');
                closeBtn.innerHTML = '&times;';
                closeBtn.style.cssText =
                    'border:none;background:none;font-size:var(--size-24);cursor:pointer;color:var(--text-3);padding:0 var(--space-4);line-height:1;';
                closeBtn.onclick = hidePanel;

                header.appendChild(leftHeader);
                header.appendChild(closeBtn);

                // Tab views
                var clientView = createClientView();
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
                statsBar.style.cssText = 'padding:var(--space-3) var(--space-8);border-top:1px solid var(--line-soft);font-size:var(--size-xxs);color:var(--muted-2);background:var(--control);border-radius:0 0 var(--radius-lg) var(--radius-lg);text-align:right;';
                statsBar.textContent = 'MKM Research Labs \u2014 Physical Risk Trading Desk';

                tdPanel.appendChild(header);
                tdPanel.appendChild(clientView);
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
            }
