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

            function loadBasisData(stormId) {
                var summary = document.getElementById('sp-summary');
                var container = document.getElementById('sp-table-container');
                summary.innerHTML = '<div style="padding:4px;color:#888;font-size:11px;">Loading basis data...</div>';
                container.innerHTML = '';

                var baseUrl = getBaseUrl();
                fetch(baseUrl + '/api/v1/propertyts/' + stormId + '/basis', {mode: 'cors'})
                    .then(function(r) { return r.json(); })
                    .then(function(data) {
                        if (data.status === 'success') {
                            spBasisData = data;
                            renderBasisSummary(data.summary);
                            renderBasisTable(data.gauges);
                        } else {
                            summary.innerHTML = '';
                            container.innerHTML = '<div style="padding:40px;text-align:center;color:#999;font-size:13px;">No basis data for this storm</div>';
                        }
                    })
                    .catch(function(err) {
                        summary.innerHTML = '';
                        container.innerHTML = '<div style="padding:20px;color:red;">Failed to load basis data</div>';
                        console.error('[StormPortfolio] Basis error:', err);
                    });
            }

            function renderBasisSummary(s) {
                var summary = document.getElementById('sp-summary');
                var transmColor = (s.portfolio_transmission_pct || 0) >= 50 ? '#d32f2f' : '#388e3c';
                var cards = [
                    { label: 'Synthetic Gauges', value: s.num_synthetic_gauges || 0, color: '#1976d2' },
                    { label: 'Gauges Severe', value: s.gauges_severe || 0, color: '#d32f2f' },
                    { label: 'With Flooding', value: s.gauges_with_flooding || 0, color: '#f57c00' },
                    { label: 'Basis Only', value: s.gauges_basis_only || 0, color: '#7b1fa2' },
                    { label: 'Properties Flooded', value: (s.total_flooded || 0) + ' / ' + (s.total_properties || 0), color: '#1565c0' },
                    { label: 'Transmission', value: (s.portfolio_transmission_pct || 0) + '%', color: transmColor },
                ];
                summary.innerHTML = '';
                cards.forEach(function(c) {
                    var card = document.createElement('div');
                    card.style.cssText = 'flex:1;min-width:100px;padding:8px 12px;border-radius:6px;background:#f5f5f5;border-left:3px solid ' + c.color + ';';
                    card.innerHTML = '<div style="font-size:10px;color:#888;text-transform:uppercase;letter-spacing:0.5px;">' + c.label + '</div>' +
                        '<div style="font-size:16px;font-weight:700;color:' + c.color + ';margin-top:2px;">' + c.value + '</div>';
                    summary.appendChild(card);
                });
            }

            function renderBasisTable(gauges) {
                var container = document.getElementById('sp-table-container');
                var basisCols = [
                    { key: 'gauge_name', label: 'Gauge', fmt: function(v) { return v; } },
                    { key: 'threshold', label: 'Threshold', fmt: function(v) { return v ? v.charAt(0).toUpperCase() + v.slice(1) : '\u2014'; } },
                    { key: 'peak_wse_m', label: 'Peak (m)', fmt: function(v) { return v ? v.toFixed(2) : '\u2014'; } },
                    { key: 'severe_m', label: 'Severe (m)', fmt: function(v) { return v ? v.toFixed(2) : '\u2014'; } },
                    { key: 'properties_linked', label: 'Linked', fmt: function(v) { return v; } },
                    { key: 'properties_flooded', label: 'Flooded', fmt: function(v) { return v; } },
                    { key: 'properties_not_flooded', label: 'Not Flooded', fmt: function(v) { return v; } },
                    { key: 'transmission_pct', label: 'Transmission', fmt: function(v) { return v + '%'; } },
                    { key: 'avg_retention', label: 'Avg Retention', fmt: function(v) { return v ? (v * 100).toFixed(1) + '%' : '\u2014'; } },
                    { key: 'avg_flood_depth_m', label: 'Avg Depth', fmt: fmtDepth },
                    { key: 'real_gauge_peak_m', label: 'Real Gauge (m)', fmt: function(v) { return v ? v.toFixed(2) : '\u2014'; } },
                ];

                var table = document.createElement('table');
                table.style.cssText = 'width:100%;border-collapse:collapse;font-size:11px;';

                var thead = document.createElement('thead');
                var tr = document.createElement('tr');
                basisCols.forEach(function(col) {
                    var th = document.createElement('th');
                    th.textContent = col.label;
                    th.style.cssText = 'padding:6px 8px;text-align:right;border-bottom:2px solid #ddd;background:#fafafa;white-space:nowrap;font-size:10px;color:#555;position:sticky;top:0;cursor:pointer;';
                    if (col.key === 'gauge_name' || col.key === 'threshold') th.style.textAlign = 'left';
                    tr.appendChild(th);
                });
                thead.appendChild(tr);
                table.appendChild(thead);

                var tbody = document.createElement('tbody');
                (gauges || []).forEach(function(g) {
                    var row = document.createElement('tr');

                    // Row colour by threshold
                    if (g.threshold === 'severe' && g.properties_flooded === 0) {
                        row.style.background = '#f3e5f5';  // purple tint — basis risk
                    } else if (g.threshold === 'severe') {
                        row.style.background = '#ffebee';  // red tint — severe with flooding
                    } else if (g.threshold === 'warning') {
                        row.style.background = '#fff3e0';  // orange tint
                    }

                    basisCols.forEach(function(col) {
                        var td = document.createElement('td');
                        var val = g[col.key];
                        td.textContent = col.fmt(val);
                        td.style.cssText = 'padding:5px 8px;border-bottom:1px solid #f0f0f0;text-align:right;white-space:nowrap;';
                        if (col.key === 'gauge_name' || col.key === 'threshold') td.style.textAlign = 'left';

                        // Colour coding
                        if (col.key === 'threshold') {
                            var tc = Theme.ramp('trigger_level');
                            td.style.color = tc[val] || Theme.value('text');
                            td.style.fontWeight = 'bold';
                        }
                        if (col.key === 'transmission_pct') {
                            td.style.color = val >= 50 ? '#d32f2f' : (val > 0 ? '#f57c00' : '#388e3c');
                            td.style.fontWeight = 'bold';
                        }
                        if (col.key === 'properties_flooded' && val > 0) td.style.color = '#d32f2f';
                        if (col.key === 'properties_not_flooded' && val > 0 && g.threshold === 'severe') {
                            td.style.color = '#7b1fa2';  // basis risk highlight
                            td.style.fontWeight = 'bold';
                        }

                        row.appendChild(td);
                    });
                    tbody.appendChild(row);
                });
                table.appendChild(tbody);

                if (!gauges || gauges.length === 0) {
                    var emptyRow = document.createElement('tr');
                    var emptyTd = document.createElement('td');
                    emptyTd.colSpan = basisCols.length;
                    emptyTd.style.cssText = 'padding:40px;text-align:center;color:#999;';
                    emptyTd.textContent = 'No gauge data for this storm';
                    emptyRow.appendChild(emptyTd);
                    tbody.appendChild(emptyRow);
                }

                container.innerHTML = '';
                container.appendChild(table);
            }
