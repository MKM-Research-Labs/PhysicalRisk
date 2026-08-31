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

            function _getStormLabel(stormId) {
                var sel = document.getElementById('sp-storm-select');
                if (sel) {
                    for (var i = 0; i < sel.options.length; i++) {
                        if (sel.options[i].value === stormId) return sel.options[i].textContent;
                    }
                }
                return stormId;
            }

            function loadSimData(stormId) {
                if (!stormId) return;
                console.log('[StormPortfolio] Loading simulation for', stormId);
                var wrap = document.getElementById('sp-sim-chart-wrap');
                wrap.innerHTML = '<div style="padding:var(--space-inset);text-align:center;color:var(--muted);">Loading simulation data...</div>';
                var stats = document.getElementById('sp-sim-stats');
                stats.innerHTML = '';
                var statsBar = document.getElementById('sp-stats-bar');
                statsBar.innerHTML = '<span>Loading simulation...</span>';

                var stormLabel = _getStormLabel(stormId);

                var baseUrl = getBaseUrl();
                fetch(baseUrl + '/api/v1/propertyts/animate/' + stormId, {mode: 'cors'})
                    .then(function(r) { return r.json(); })
                    .then(function(data) {
                        if (data.status !== 'success') {
                            wrap.innerHTML = '<div style="padding:var(--space-inset);text-align:center;color:var(--red);">Error: ' + (data.message || 'Unknown') + '</div>';
                            return;
                        }
                        spSimData = data;
                        spSimData._stormLabel = stormLabel;
                        console.log('[StormPortfolio] Simulation loaded:', data.n_frames, 'frames,', data.n_properties_affected, 'properties');
                        document.getElementById('sp-panel-title').textContent =
                            'Storm Simulation — ' + stormLabel;
                        renderSimChart(data);
                        renderSimStats(data);

                        statsBar.innerHTML =
                            '<span>Storm: <b>' + stormLabel + '</b></span>' +
                            '<span>Duration: <b>' + data.n_frames + '</b> hours</span>' +
                            '<span>Properties: <b>' + data.n_properties_affected + '</b></span>';
                    })
                    .catch(function(err) {
                        wrap.innerHTML = '<div style="padding:var(--space-inset);text-align:center;color:var(--red);">Failed to load simulation</div>';
                        console.error('Sim error:', err);
                    });
            }

            function renderSimStats(data) {
                var stats = document.getElementById('sp-sim-stats');
                var frames = data.frames || [];

                var peakHour = 0;
                var peakFlooded = 0;
                var maxDepth = 0;
                var floodingHours = 0;
                frames.forEach(function(f) {
                    var nf = f.stats ? f.stats.properties_flooded : 0;
                    if (nf > peakFlooded) {
                        peakFlooded = nf;
                        peakHour = f.hour;
                    }
                    if (nf > 0) floodingHours++;
                    (f.properties || []).forEach(function(p) {
                        if (p.depth_m > maxDepth) maxDepth = p.depth_m;
                    });
                });

                var cards = [
                    { label: 'Properties Affected', value: data.n_properties_affected, color: 'var(--accent)' },
                    { label: 'Peak Hour', value: 'Hour ' + peakHour + ' (' + peakFlooded + ' flooded)', color: 'var(--red)' },
                    { label: 'Max Flood Depth', value: maxDepth.toFixed(2) + 'm', color: 'var(--amber)' },
                    { label: 'Flooding Duration', value: floodingHours + ' hours', color: 'var(--purple)' },
                ];

                stats.innerHTML = '';
                var row = document.createElement('div');
                row.style.cssText = 'display:flex;gap:var(--space-5);width:100%;';
                cards.forEach(function(c) {
                    var card = document.createElement('div');
                    card.style.cssText = 'flex:1;min-width:120px;padding:var(--space-4) var(--space-6);border-radius:var(--radius-md);background:var(--sunken);border-left:3px solid ' + c.color + ';';
                    card.innerHTML = '<div style="font-size:var(--size-xxs);color:var(--muted);text-transform:uppercase;letter-spacing:0.5px;">' + c.label + '</div>' +
                        '<div style="font-size:var(--size-14);font-weight:700;color:' + c.color + ';margin-top:var(--space-1);">' + c.value + '</div>';
                    row.appendChild(card);
                });
                stats.appendChild(row);
            }
