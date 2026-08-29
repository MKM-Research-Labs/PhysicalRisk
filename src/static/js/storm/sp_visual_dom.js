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

            var spSimData = null;
            var spSimChart = null;
            var simGaugeColors = ['var(--accent-mid)', 'var(--series-2)', 'var(--peril-wind)', 'var(--series-4)', 'var(--green-dark)', 'var(--series-6)', 'var(--series-7)', 'var(--gold-dark)'];

            // ================================================================
            // Visual tab — DOM creation
            // ================================================================
            function createVisView() {
                var view = document.createElement('div');
                view.id = 'sp-vis-view';
                view.style.cssText = 'display:none;flex-direction:column;flex:1;overflow:hidden;';

                // Gauge filter toolbar
                var filterRow = document.createElement('div');
                filterRow.id = 'sp-vis-filter-row';
                filterRow.style.cssText = 'padding:6px 16px;border-bottom:1px solid var(--line-soft);display:flex;align-items:center;gap:10px;background:var(--raised);';

                var filterLabel = document.createElement('span');
                filterLabel.style.cssText = 'font-size:11px;font-weight:600;color:var(--text-2);';
                filterLabel.textContent = 'Gauges:';

                var gaugeDropWrap = document.createElement('div');
                gaugeDropWrap.style.cssText = 'position:relative;';
                var gaugeBtn = document.createElement('button');
                gaugeBtn.id = 'sp-vis-gauge-btn';
                gaugeBtn.textContent = 'All Gauges';
                gaugeBtn.style.cssText = 'padding:3px 10px;font-size:11px;border:1px solid var(--line-strong);border-radius:4px;background:var(--panel);cursor:pointer;min-width:120px;text-align:left;';
                gaugeBtn.onclick = function() {
                    var dd = document.getElementById('sp-vis-gauge-dropdown');
                    dd.style.display = dd.style.display === 'none' ? 'block' : 'none';
                };
                var gaugeDropdown = document.createElement('div');
                gaugeDropdown.id = 'sp-vis-gauge-dropdown';
                gaugeDropdown.style.cssText = 'display:none;position:absolute;top:100%;left:0;z-index:100;background:var(--panel);border:1px solid var(--line-strong);border-radius:4px;box-shadow:var(--shadow-ghost);max-height:240px;overflow-y:auto;min-width:200px;padding:4px 0;';
                gaugeDropWrap.appendChild(gaugeBtn);
                gaugeDropWrap.appendChild(gaugeDropdown);

                var allBtn = document.createElement('button');
                allBtn.textContent = 'Show All';
                allBtn.style.cssText = 'padding:3px 10px;font-size:10px;border:1px solid var(--line-strong);border-radius:3px;background:var(--accent-soft);cursor:pointer;';
                allBtn.onclick = function() { toggleAllGauges(true); };
                var noneBtn = document.createElement('button');
                noneBtn.textContent = 'Hide All';
                noneBtn.style.cssText = 'padding:3px 10px;font-size:10px;border:1px solid var(--line-strong);border-radius:3px;background:var(--panel);cursor:pointer;';
                noneBtn.onclick = function() { toggleAllGauges(false); };

                var propsIndicator = document.createElement('span');
                propsIndicator.style.cssText = 'margin-left:auto;font-size:11px;color:var(--red);font-weight:600;display:flex;align-items:center;gap:4px;';
                propsIndicator.innerHTML = '<span style="display:inline-block;width:12px;height:3px;background:var(--red);border-radius:1px;"></span> Properties Flooded';

                filterRow.appendChild(filterLabel);
                filterRow.appendChild(gaugeDropWrap);
                filterRow.appendChild(allBtn);
                filterRow.appendChild(noneBtn);
                filterRow.appendChild(propsIndicator);

                var chartWrap = document.createElement('div');
                chartWrap.id = 'sp-sim-chart-wrap';
                chartWrap.style.cssText = 'flex:1;padding:12px 16px;position:relative;';

                var stats = document.createElement('div');
                stats.id = 'sp-sim-stats';
                stats.style.cssText = 'padding:10px 16px;border-top:1px solid var(--line-soft);display:flex;gap:10px;flex-wrap:wrap;';

                view.appendChild(filterRow);
                view.appendChild(chartWrap);
                view.appendChild(stats);
                return view;
            }
