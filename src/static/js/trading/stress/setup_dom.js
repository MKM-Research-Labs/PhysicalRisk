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

            function createStressView() {
                var view = document.createElement('div');
                view.id = 'td-stress-view';
                view.style.cssText = 'flex:1;display:none;flex-direction:column;overflow:hidden;';

                // Selector bar: gauge + storm dropdowns
                var selectorBar = document.createElement('div');
                selectorBar.id = 'td-stress-selector-bar';
                selectorBar.style.cssText = 'padding:8px 16px;border-bottom:1px solid var(--line-soft);display:flex;align-items:center;gap:12px;background:var(--header-from);flex-shrink:0;';
                selectorBar.innerHTML =
                    '<span style="font-size:11px;font-weight:600;color:var(--text);">Gauge:</span>' +
                    '<select id="td-stress-gauge" style="padding:4px 8px;font-size:11px;border:1px solid var(--divider);border-radius:3px;min-width:240px;max-width:300px;">' +
                        '<option value="">Loading gauges...</option>' +
                    '</select>' +
                    '<span style="font-size:11px;font-weight:600;color:var(--text);margin-left:8px;">Storm:</span>' +
                    '<select id="td-stress-storm" style="padding:4px 8px;font-size:11px;border:1px solid var(--divider);border-radius:3px;min-width:300px;max-width:420px;">' +
                        '<option value="">Select gauge first</option>' +
                    '</select>' +
                    '__PCT_HTML__' +
                    '<span id="td-stress-storm-info" style="font-size:10px;color:var(--text-3);flex:1;"></span>' +
                    '<button id="td-stress-sim-btn" onclick="tdStressOpenGauge(document.getElementById(\'td-stress-gauge\').value)" ' +
                        'style="padding:4px 12px;font-size:11px;font-weight:600;border:1px solid var(--accent-mid);' +
                        'border-radius:3px;background:var(--accent-soft);color:var(--accent-mid);cursor:pointer;white-space:nowrap;">' +
                        'Storm Simulation</button>';
                view.appendChild(selectorBar);

                // Main content: table (left) + chart (right)
                var body = document.createElement('div');
                body.style.cssText = 'flex:1;display:flex;overflow:hidden;min-height:0;';

                // Left: trade table
                var tableWrap = document.createElement('div');
                tableWrap.id = 'td-stress-table-wrap';
                tableWrap.style.cssText = 'width:42%;overflow-y:auto;border-right:1px solid var(--line-soft);padding:8px;font-size:11px;';
                tableWrap.innerHTML = '<div style="color:var(--muted-2);text-align:center;padding:40px 0;">Select a gauge and storm to run stress test</div>';
                body.appendChild(tableWrap);

                // Right: chart with sub-tabs
                var chartPane = document.createElement('div');
                chartPane.style.cssText = 'flex:1;display:flex;flex-direction:column;min-width:0;overflow:hidden;';

                // Chart sub-tabs
                var chartTabs = document.createElement('div');
                chartTabs.id = 'td-stress-chart-tabs';
                chartTabs.style.cssText = 'display:flex;gap:0;border-bottom:1px solid var(--line-strong);background:var(--wash);flex-shrink:0;position:relative;z-index:2;';
                chartTabs.innerHTML =
                    '<div id="td-stress-ctab-0" style="padding:5px 14px;font-size:10px;font-weight:600;cursor:pointer;border-bottom:2px solid var(--accent-mid);color:var(--accent-mid);">Flood Probability</div>' +
                    '<div id="td-stress-ctab-1" style="padding:5px 14px;font-size:10px;font-weight:600;cursor:pointer;border-bottom:2px solid transparent;color:var(--muted-2);">Stress P&amp;L</div>' +
                    '<div id="td-stress-ctab-2" style="padding:5px 14px;font-size:10px;font-weight:600;cursor:pointer;border-bottom:2px solid transparent;color:var(--muted-2);">Surface</div>';
                chartPane.appendChild(chartTabs);

                // Chart canvas
                var chartWrap = document.createElement('div');
                chartWrap.id = 'td-stress-chart-wrap';
                chartWrap.style.cssText = 'flex:1;padding:8px;min-width:0;position:relative;overflow:hidden;';
                chartWrap.innerHTML = '<canvas id="td-stress-chart-canvas" style="width:100%;height:100%;"></canvas>';
                chartPane.appendChild(chartWrap);

                body.appendChild(chartPane);
                view.appendChild(body);

                // Stats/links bar at bottom
                var statsBar = document.createElement('div');
                statsBar.id = 'td-stress-stats-bar';
                statsBar.style.cssText = 'padding:6px 16px;border-top:1px solid var(--line-soft);font-size:10px;color:var(--text-3);background:var(--control);display:flex;align-items:center;gap:16px;flex-shrink:0;';
                statsBar.innerHTML = '<span style="color:var(--muted-2);">Run a stress scenario to see results</span>';
                view.appendChild(statsBar);

                return view;
            }
