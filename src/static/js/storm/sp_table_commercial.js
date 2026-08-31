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

            function loadCommercialData() {
                var summary = document.getElementById('sp-summary');
                var container = document.getElementById('sp-table-container');
                summary.innerHTML = '<div style="padding:var(--space-2);color:var(--muted);font-size:var(--size-xs);">Loading commercial assets...</div>';
                container.innerHTML = '';

                if (spCommercialData) {
                    renderCommercialSummary(spCommercialData);
                    renderCommercialTable(spCommercialData.assets);
                    return;
                }

                var baseUrl = getBaseUrl();
                fetch(baseUrl + '/api/v1/commercial/blotter', {mode: 'cors'})
                    .then(function(r) { return r.json(); })
                    .then(function(data) {
                        if (data.status === 'success') {
                            spCommercialData = data;
                            renderCommercialSummary(data);
                            renderCommercialTable(data.assets);
                        } else {
                            summary.innerHTML = '<div style="color:var(--red);">Error loading commercial</div>';
                        }
                    })
                    .catch(function(err) {
                        summary.innerHTML = '<div style="color:var(--red);">Failed to load commercial</div>';
                        console.error('[StormPortfolio] Commercial error:', err);
                    });
            }

            function renderCommercialSummary(data) {
                var summary = document.getElementById('sp-summary');
                var s = data.summary || {};
                var cards = [
                    { label: 'Assets', value: s.num_assets || 0, color: 'var(--accent)' },
                    { label: 'Total Value', value: fmtGBP(s.total_property_value || 0), color: 'var(--green)' },
                ];
                summary.innerHTML = '';
                cards.forEach(function(c) {
                    var card = document.createElement('div');
                    card.style.cssText = 'flex:1;min-width:120px;padding:var(--space-4) var(--space-6);border-radius:var(--radius-md);background:var(--sunken);border-left:3px solid ' + c.color + ';';
                    card.innerHTML = '<div style="font-size:var(--size-xxs);color:var(--muted);text-transform:uppercase;letter-spacing:0.5px;">' + c.label + '</div>' +
                        '<div style="font-size:var(--size-lg);font-weight:700;color:' + c.color + ';margin-top:var(--space-1);">' + c.value + '</div>';
                    summary.appendChild(card);
                });
            }

            function renderCommercialTable(assets) {
                var container = document.getElementById('sp-table-container');
                // Loan / LTV / Remaining moved to the Loan/Mortgage tab.
                var cols = [
                    { key: 'property_id', label: 'Asset', fmt: function(v) { return v; } },
                    { key: 'property_address', label: 'Address', fmt: function(v) { return v || '\u2014'; } },
                    { key: 'commercial_type', label: 'Type', fmt: function(v) { return v || '\u2014'; } },
                    { key: 'anchor_tenant', label: 'Anchor Tenant', fmt: function(v) { return v || '\u2014'; } },
                    { key: 'property_value', label: 'Value', fmt: fmtGBP },
                    { key: 'river_distance_km', label: 'River Dist (km)', fmt: function(v) { return (v !== null && v !== undefined) ? v.toFixed(2) : '\u2014'; } },
                    { key: 'elevation_m', label: 'Elevation (m)', fmt: function(v) { return (v !== null && v !== undefined) ? (typeof v === 'number' ? v.toFixed(2) : v) : '\u2014'; } },
                    { key: 'ea_flood_zone', label: 'Flood Zone', fmt: function(v) { return v || '\u2014'; } },
                ];
                var leftAlignKeys = {
                    property_id: 1, property_address: 1, commercial_type: 1,
                    anchor_tenant: 1, ea_flood_zone: 1,
                };

                var table = document.createElement('table');
                table.style.cssText = 'width:100%;border-collapse:collapse;font-size:var(--size-xs);';

                var thead = document.createElement('thead');
                var tr = document.createElement('tr');
                cols.forEach(function(col) {
                    var th = document.createElement('th');
                    th.textContent = col.label;
                    th.style.cssText = 'padding:var(--space-3) var(--space-4);text-align:right;border-bottom:2px solid var(--line-strong);background:var(--raised);white-space:nowrap;font-size:var(--size-xxs);color:var(--text-2);position:sticky;top:0;';
                    if (leftAlignKeys[col.key]) th.style.textAlign = 'left';
                    tr.appendChild(th);
                });
                thead.appendChild(tr);
                table.appendChild(thead);

                var tbody = document.createElement('tbody');
                (assets || []).forEach(function(a, idx) {
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
                    })(a.property_id);

                    cols.forEach(function(col) {
                        var td = document.createElement('td');
                        td.textContent = col.fmt(a[col.key]);
                        td.style.cssText = 'padding:var(--space-3) var(--space-4);border-bottom:1px solid var(--code);text-align:right;white-space:nowrap;';
                        if (leftAlignKeys[col.key]) td.style.textAlign = 'left';
                        row.appendChild(td);
                    });
                    tbody.appendChild(row);
                });
                table.appendChild(tbody);

                container.innerHTML = '';
                container.appendChild(table);
            }
