# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

"""
Storm portfolio Table tab — Loan/Mortgage sub-tab JS.

Combined debt view across residential mortgages and commercial loans
with separate Flood / Wind LTV + Remaining columns. Wind columns are
populated by the (pending) wind damage model — until then they mirror
the pre-shock LTV/term and the Wind-LTV header reads "(pending)".
"""


def get_js() -> str:
    """Return JS fragment for the Loan/Mortgage sub-tab (parent IIFE scope)."""
    return """
            // ================================================================
            // Loan/Mortgage — combined debt view
            // ================================================================
            //
            // Row shape:
            //   { asset_id, asset_class, address, outstanding_balance,
            //     flood_ltv, flood_remaining,
            //     wind_ltv,  wind_remaining }
            //
            // Post-flood LTV comes from spData (residential) and
            // spCommercialImpact (commercial) when a storm is selected —
            // both already carry post_damage_ltv. Pre-shock LTV is used as
            // the fallback when no flooding has occurred for the asset.
            // ================================================================

            function _mortgageRows() {
                var rows = [];
                var floodById = {};

                // Index post-flood LTV/term by asset id, residential first
                if (spData && spData.properties) {
                    spData.properties.forEach(function(p) {
                        floodById[p.property_id] = {
                            outstanding_balance: p.outstanding_balance,
                            post_damage_ltv: p.post_damage_ltv,
                            remaining_term_months: p.remaining_term_months,
                            negative_equity: p.negative_equity,
                        };
                    });
                }
                if (spCommercialImpact && spCommercialImpact.assets) {
                    spCommercialImpact.assets.forEach(function(a) {
                        floodById[a.property_id] = {
                            outstanding_balance: a.outstanding_balance,
                            post_damage_ltv: a.post_damage_ltv,
                            remaining_term_months: a.remaining_term_months,
                            negative_equity: a.negative_equity,
                        };
                    });
                }

                // Residential debt
                if (spBlotterData && spBlotterData.properties) {
                    spBlotterData.properties.forEach(function(p) {
                        if (!p.outstanding_balance) return;  // unmortgaged
                        var f = floodById[p.property_id] || {};
                        rows.push({
                            asset_id: p.property_id,
                            asset_class: 'residential',
                            address: p.property_address,
                            outstanding_balance: p.outstanding_balance,
                            flood_ltv: (f.post_damage_ltv != null) ? f.post_damage_ltv : p.current_ltv,
                            flood_remaining: p.remaining_term_months,
                            wind_ltv: null,
                            wind_remaining: null,
                            negative_equity: f.negative_equity || false,
                        });
                    });
                }

                // Commercial debt
                if (spCommercialData && spCommercialData.assets) {
                    spCommercialData.assets.forEach(function(a) {
                        if (!a.outstanding_balance) return;
                        var f = floodById[a.property_id] || {};
                        rows.push({
                            asset_id: a.property_id,
                            asset_class: 'commercial',
                            address: a.property_address,
                            outstanding_balance: a.outstanding_balance,
                            flood_ltv: (f.post_damage_ltv != null) ? f.post_damage_ltv : a.current_ltv,
                            flood_remaining: a.remaining_term_months,
                            wind_ltv: null,
                            wind_remaining: null,
                            negative_equity: f.negative_equity || false,
                        });
                    });
                }

                return rows;
            }

            function loadMortgageData() {
                var summary = document.getElementById('sp-summary');
                var container = document.getElementById('sp-table-container');
                var pending = [];
                if (!spBlotterData) pending.push(
                    fetch(getBaseUrl() + '/api/v1/propertyts/blotter', {mode:'cors'})
                        .then(function(r){return r.json();})
                        .then(function(d){ if (d.status === 'success') spBlotterData = d; })
                );
                if (!spCommercialData) pending.push(
                    fetch(getBaseUrl() + '/api/v1/commercial/blotter', {mode:'cors'})
                        .then(function(r){return r.json();})
                        .then(function(d){ if (d.status === 'success') spCommercialData = d; })
                );
                if (pending.length) {
                    container.innerHTML = '<div style="padding:24px;text-align:center;color:#999;">Loading debt portfolio...</div>';
                    Promise.all(pending).then(_renderMortgageTab);
                } else {
                    _renderMortgageTab();
                }
            }

            function _renderMortgageTab() {
                var rows = _mortgageRows();
                _renderMortgageSummary(rows);
                _renderMortgageTable(rows);
            }

            function _renderMortgageSummary(rows) {
                var summary = document.getElementById('sp-summary');
                var totalOS = rows.reduce(function(a,r){return a + (r.outstanding_balance||0);}, 0);
                var resCount = rows.filter(function(r){return r.asset_class === 'residential';}).length;
                var comCount = rows.filter(function(r){return r.asset_class === 'commercial';}).length;
                var negEq = rows.filter(function(r){return r.negative_equity;}).length;
                var cards = [
                    { label: 'Mortgages', value: resCount, color: '#1976d2' },
                    { label: 'Commercial Loans', value: comCount, color: '#1976d2' },
                    { label: 'Outstanding', value: fmtGBP(totalOS), color: '#7b1fa2' },
                    { label: 'Impaired (Flood)', value: negEq, color: negEq > 0 ? '#d32f2f' : '#388e3c' },
                ];
                summary.innerHTML = '';
                cards.forEach(function(card) {
                    var div = document.createElement('div');
                    div.style.cssText = 'flex:1;min-width:120px;padding:8px 12px;border-radius:6px;background:#f5f5f5;border-left:3px solid ' + card.color + ';';
                    div.innerHTML = '<div style="font-size:10px;color:#888;text-transform:uppercase;letter-spacing:0.5px;">' + card.label + '</div>' +
                        '<div style="font-size:16px;font-weight:700;color:' + card.color + ';margin-top:2px;">' + card.value + '</div>';
                    summary.appendChild(div);
                });
            }

            function _renderMortgageTable(rows) {
                var container = document.getElementById('sp-table-container');
                if (!rows.length) {
                    container.innerHTML = '<div style="padding:24px;text-align:center;color:#999;">No loans or mortgages in portfolio.</div>';
                    return;
                }

                var table = document.createElement('table');
                table.style.cssText = 'width:100%;border-collapse:collapse;font-size:11px;';

                // Two-row header so the Flood / Wind groups read clearly.
                var thead = document.createElement('thead');
                thead.innerHTML =
                    '<tr style="background:#fafafa;">' +
                      '<th rowspan="2" style="padding:6px 8px;text-align:left;border-bottom:2px solid #ddd;font-size:10px;color:#555;position:sticky;top:0;background:#fafafa;">Asset</th>' +
                      '<th rowspan="2" style="padding:6px 8px;text-align:left;border-bottom:2px solid #ddd;font-size:10px;color:#555;position:sticky;top:0;background:#fafafa;">Address</th>' +
                      '<th rowspan="2" style="padding:6px 8px;text-align:right;border-bottom:2px solid #ddd;font-size:10px;color:#555;position:sticky;top:0;background:#fafafa;">O/S</th>' +
                      '<th colspan="2" style="padding:6px 8px;text-align:center;border-bottom:1px solid #ddd;border-left:1px solid #eee;font-size:10px;color:#555;background:#eaf3ff;position:sticky;top:0;">Flood</th>' +
                      '<th colspan="2" style="padding:6px 8px;text-align:center;border-bottom:1px solid #ddd;border-left:1px solid #eee;font-size:10px;color:#555;background:#fff4e6;position:sticky;top:0;">Wind (pending)</th>' +
                    '</tr>' +
                    '<tr style="background:#fafafa;">' +
                      '<th style="padding:4px 8px;text-align:right;border-bottom:2px solid #ddd;border-left:1px solid #eee;font-size:10px;color:#555;background:#eaf3ff;">LTV</th>' +
                      '<th style="padding:4px 8px;text-align:right;border-bottom:2px solid #ddd;font-size:10px;color:#555;background:#eaf3ff;">Remaining</th>' +
                      '<th style="padding:4px 8px;text-align:right;border-bottom:2px solid #ddd;border-left:1px solid #eee;font-size:10px;color:#555;background:#fff4e6;">LTV</th>' +
                      '<th style="padding:4px 8px;text-align:right;border-bottom:2px solid #ddd;font-size:10px;color:#555;background:#fff4e6;">Remaining</th>' +
                    '</tr>';
                table.appendChild(thead);

                var tbody = document.createElement('tbody');
                rows.forEach(function(r, idx) {
                    var tr = document.createElement('tr');
                    if (r.negative_equity) tr.style.background = '#ffebee';
                    else if (r.asset_class === 'commercial') tr.style.background = '#f3f7ff';
                    else if (idx % 2 === 1) tr.style.background = '#fafafa';

                    function cell(text, align, color, bold) {
                        var td = document.createElement('td');
                        td.textContent = text;
                        td.style.cssText = 'padding:5px 8px;text-align:' + (align||'right') + ';border-bottom:1px solid #f0f0f0;white-space:nowrap;';
                        if (color) td.style.color = color;
                        if (bold) td.style.fontWeight = 'bold';
                        return td;
                    }
                    tr.appendChild(cell(r.asset_id, 'left'));
                    tr.appendChild(cell(r.address || '\\u2014', 'left'));
                    tr.appendChild(cell(fmtGBP(r.outstanding_balance), 'right'));
                    var floodLtvBad = r.flood_ltv != null && r.flood_ltv > 100;
                    tr.appendChild(cell(r.flood_ltv != null ? fmtPct(r.flood_ltv) : '\\u2014', 'right', floodLtvBad ? '#d32f2f' : null, floodLtvBad));
                    tr.appendChild(cell(fmtMonths(r.flood_remaining), 'right'));
                    tr.appendChild(cell(r.wind_ltv != null ? fmtPct(r.wind_ltv) : '\\u2014', 'right'));
                    tr.appendChild(cell(r.wind_remaining != null ? fmtMonths(r.wind_remaining) : '\\u2014', 'right'));
                    tbody.appendChild(tr);
                });
                table.appendChild(tbody);

                container.innerHTML = '';
                container.appendChild(table);
            }
"""
