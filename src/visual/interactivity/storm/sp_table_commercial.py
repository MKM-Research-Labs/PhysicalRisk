# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

"""
Storm portfolio Table tab — Commercial sub-tab JS.

Loads /api/v1/commercial/blotter and renders a summary card row plus a
sortable commercial-asset table.  The JS fragment is concatenated into
the parent ``sp_table.get_js()`` IIFE.
"""


def get_js() -> str:
    """Return JS fragment for the Commercial sub-tab (parent IIFE scope)."""
    return """
            // ================================================================
            // Commercial — asset list
            // ================================================================
            function loadCommercialData() {
                var summary = document.getElementById('sp-summary');
                var container = document.getElementById('sp-table-container');
                summary.innerHTML = '<div style="padding:4px;color:#888;font-size:11px;">Loading commercial assets...</div>';
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
                            summary.innerHTML = '<div style="color:red;">Error loading commercial</div>';
                        }
                    })
                    .catch(function(err) {
                        summary.innerHTML = '<div style="color:red;">Failed to load commercial</div>';
                        console.error('[StormPortfolio] Commercial error:', err);
                    });
            }

            function renderCommercialSummary(data) {
                var summary = document.getElementById('sp-summary');
                var s = data.summary || {};
                var cards = [
                    { label: 'Assets', value: s.num_assets || 0, color: '#1976d2' },
                    { label: 'Total Value', value: fmtGBP(s.total_property_value || 0), color: '#388e3c' },
                    { label: 'Loan Exposure', value: fmtGBP(s.total_loan_exposure || 0), color: '#7b1fa2' },
                ];
                summary.innerHTML = '';
                cards.forEach(function(c) {
                    var card = document.createElement('div');
                    card.style.cssText = 'flex:1;min-width:120px;padding:8px 12px;border-radius:6px;background:#f5f5f5;border-left:3px solid ' + c.color + ';';
                    card.innerHTML = '<div style="font-size:10px;color:#888;text-transform:uppercase;letter-spacing:0.5px;">' + c.label + '</div>' +
                        '<div style="font-size:16px;font-weight:700;color:' + c.color + ';margin-top:2px;">' + c.value + '</div>';
                    summary.appendChild(card);
                });
            }

            function renderCommercialTable(assets) {
                var container = document.getElementById('sp-table-container');
                var cols = [
                    { key: 'property_id', label: 'Asset', fmt: function(v) { return v; } },
                    { key: 'property_address', label: 'Address', fmt: function(v) { return v || '\\u2014'; } },
                    { key: 'commercial_type', label: 'Type', fmt: function(v) { return v || '\\u2014'; } },
                    { key: 'anchor_tenant', label: 'Anchor Tenant', fmt: function(v) { return v || '\\u2014'; } },
                    { key: 'property_value', label: 'Value', fmt: fmtGBP },
                    { key: 'river_distance_km', label: 'River Dist (km)', fmt: function(v) { return (v !== null && v !== undefined) ? v.toFixed(2) : '\\u2014'; } },
                    { key: 'elevation_m', label: 'Elevation (m)', fmt: function(v) { return (v !== null && v !== undefined) ? (typeof v === 'number' ? v.toFixed(2) : v) : '\\u2014'; } },
                    { key: 'ea_flood_zone', label: 'Flood Zone', fmt: function(v) { return v || '\\u2014'; } },
                    { key: 'outstanding_balance', label: 'Loan', fmt: fmtGBP },
                    { key: 'current_ltv', label: 'LTV', fmt: fmtPct },
                    { key: 'remaining_term_months', label: 'Remaining', fmt: fmtMonths },
                ];
                var leftAlignKeys = {
                    property_id: 1, property_address: 1, commercial_type: 1,
                    anchor_tenant: 1, ea_flood_zone: 1,
                };

                var table = document.createElement('table');
                table.style.cssText = 'width:100%;border-collapse:collapse;font-size:11px;';

                var thead = document.createElement('thead');
                var tr = document.createElement('tr');
                cols.forEach(function(col) {
                    var th = document.createElement('th');
                    th.textContent = col.label;
                    th.style.cssText = 'padding:6px 8px;text-align:right;border-bottom:2px solid #ddd;background:#fafafa;white-space:nowrap;font-size:10px;color:#555;position:sticky;top:0;';
                    if (leftAlignKeys[col.key]) th.style.textAlign = 'left';
                    tr.appendChild(th);
                });
                thead.appendChild(tr);
                table.appendChild(thead);

                var tbody = document.createElement('tbody');
                (assets || []).forEach(function(a, idx) {
                    var row = document.createElement('tr');
                    if (a.current_ltv > 90) {
                        row.style.background = '#ffebee';
                    } else if (a.current_ltv > 75) {
                        row.style.background = '#fff3e0';
                    } else if (idx % 2 === 1) {
                        row.style.background = '#fafafa';
                    }
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
                        td.style.cssText = 'padding:5px 8px;border-bottom:1px solid #f0f0f0;text-align:right;white-space:nowrap;';
                        if (leftAlignKeys[col.key]) td.style.textAlign = 'left';
                        if (col.key === 'current_ltv' && a.current_ltv > 90) {
                            td.style.color = '#d32f2f';
                            td.style.fontWeight = 'bold';
                        }
                        row.appendChild(td);
                    });
                    tbody.appendChild(row);
                });
                table.appendChild(tbody);

                container.innerHTML = '';
                container.appendChild(table);
            }
"""
