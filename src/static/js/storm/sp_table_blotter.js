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

            function loadBlotterData() {
                var summary = document.getElementById('sp-summary');
                var container = document.getElementById('sp-table-container');
                summary.innerHTML = '<div style="padding:4px;color:var(--muted);font-size:11px;">Loading REIT portfolio...</div>';
                container.innerHTML = '';

                if (spBlotterData) {
                    renderBlotterSummary(spBlotterData);
                    renderBlotterTable(spBlotterData.properties);
                    return;
                }

                var baseUrl = getBaseUrl();
                fetch(baseUrl + '/api/v1/propertyts/blotter', {mode: 'cors'})
                    .then(function(r) { return r.json(); })
                    .then(function(data) {
                        if (data.status === 'success') {
                            spBlotterData = data;
                            renderBlotterSummary(data);
                            renderBlotterTable(data.properties);
                        } else {
                            summary.innerHTML = '<div style="color:var(--red);">Error loading blotter</div>';
                        }
                    })
                    .catch(function(err) {
                        summary.innerHTML = '<div style="color:var(--red);">Failed to load blotter</div>';
                        console.error('[StormPortfolio] Blotter error:', err);
                    });
            }

            function renderBlotterSummary(data) {
                var summary = document.getElementById('sp-summary');
                var s = data.summary || {};
                var cards = [
                    { label: 'Properties', value: s.num_properties || 0, color: 'var(--accent)' },
                    { label: 'Total Value', value: fmtGBP(s.total_property_value || 0), color: 'var(--green)' },
                ];
                summary.innerHTML = '';
                cards.forEach(function(c) {
                    var card = document.createElement('div');
                    card.style.cssText = 'flex:1;min-width:120px;padding:8px 12px;border-radius:6px;background:var(--sunken);border-left:3px solid ' + c.color + ';';
                    card.innerHTML = '<div style="font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:0.5px;">' + c.label + '</div>' +
                        '<div style="font-size:16px;font-weight:700;color:' + c.color + ';margin-top:2px;">' + c.value + '</div>';
                    summary.appendChild(card);
                });
            }

            function renderBlotterTable(properties) {
                var container = document.getElementById('sp-table-container');
                // Mortgage / LTV / Remaining moved to the Loan/Mortgage tab.
                var blotterCols = [
                    { key: 'property_id', label: 'Property', fmt: function(v) { return v; } },
                    { key: 'property_address', label: 'Address', fmt: function(v) { return v || '\u2014'; } },
                    { key: 'property_value', label: 'Value', fmt: fmtGBP },
                    { key: 'river_distance_km', label: 'River Dist (km)', fmt: function(v) { return (v !== null && v !== undefined) ? v.toFixed(2) : '\u2014'; } },
                    { key: 'elevation_m', label: 'Elevation (m)', fmt: function(v) { return (v !== null && v !== undefined) ? (typeof v === 'number' ? v.toFixed(2) : v) : '\u2014'; } },
                    { key: 'ea_flood_zone', label: 'Flood Zone', fmt: function(v) { return v || '\u2014'; } },
                ];

                var table = document.createElement('table');
                table.style.cssText = 'width:100%;border-collapse:collapse;font-size:11px;';

                var thead = document.createElement('thead');
                var tr = document.createElement('tr');
                blotterCols.forEach(function(col) {
                    var th = document.createElement('th');
                    th.textContent = col.label;
                    th.style.cssText = 'padding:6px 8px;text-align:right;border-bottom:2px solid var(--line-strong);background:var(--raised);white-space:nowrap;font-size:10px;color:var(--text-2);position:sticky;top:0;';
                    if (col.key === 'property_id' || col.key === 'property_address' || col.key === 'ea_flood_zone') th.style.textAlign = 'left';
                    tr.appendChild(th);
                });
                thead.appendChild(tr);
                table.appendChild(thead);

                var tbody = document.createElement('tbody');
                (properties || []).forEach(function(p, idx) {
                    var row = document.createElement('tr');
                    if (idx % 2 === 1) row.style.background = Theme.value('raised');
                    row.style.cursor = 'pointer';
                    row.onmouseenter = function() { this.style.opacity = '0.8'; };
                    row.onmouseleave = function() { this.style.opacity = '1'; };
                    row.onclick = (function(pid) {
                        return function() {
                            hidePanel();
                            if (window.PropertyStormAnalysis && window.PropertyStormAnalysis.show) {
                                window.PropertyStormAnalysis.show(pid);
                            } else {
                                document.dispatchEvent(new CustomEvent('propertyStormRequested', {
                                    detail: { propertyId: pid }, bubbles: true
                                }));
                            }
                        };
                    })(p.property_id);

                    blotterCols.forEach(function(col) {
                        var td = document.createElement('td');
                        td.textContent = col.fmt(p[col.key]);
                        td.style.cssText = 'padding:5px 8px;border-bottom:1px solid var(--code);text-align:right;white-space:nowrap;';
                        if (col.key === 'property_id' || col.key === 'property_address' || col.key === 'ea_flood_zone') td.style.textAlign = 'left';
                        row.appendChild(td);
                    });
                    tbody.appendChild(row);
                });
                table.appendChild(tbody);

                container.innerHTML = '';
                container.appendChild(table);
            }
