# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

"""
Storm portfolio Table tab — Loan/Mortgage sub-tab JS.

Combined debt view across residential mortgages and commercial loans.
Flood damage and wind damage are summed per asset (capped at the asset
value) and the resulting post-damage value is used to recompute LTV.
Both flood and wind damage are sourced live from the per-storm impact
endpoints; the Wind side is empty when the storm has no typhoon link.
"""


def get_js() -> str:
    """Return JS fragment for the Loan/Mortgage sub-tab (parent IIFE scope)."""
    return """
            // ================================================================
            // Loan/Mortgage — combined debt view (flood + wind)
            // ================================================================
            //
            // Row shape (combined):
            //   { asset_id, asset_class, address, value,
            //     outstanding_balance, current_ltv, remaining_term_months,
            //     flood_damage, wind_damage, combined_damage,
            //     combined_ratio, post_damage_value, combined_ltv,
            //     impaired }
            //
            // Damage sources:
            //   flood: spData (residential) + spCommercialImpact (commercial)
            //   wind:  spWindData (single endpoint covers both classes)
            // Asset value + outstanding balance come from spBlotterData /
            // spCommercialData (full portfolio, including unaffected assets).
            // ================================================================

            function _combinedRows() {
                var rows = [];
                var floodById = {};
                var windById = {};

                // Index flood damage by asset id
                if (spData && spData.properties) {
                    spData.properties.forEach(function(p) {
                        floodById[p.property_id] = {
                            damage_amount: p.damage_amount || 0,
                            damage_ratio:  p.damage_ratio  || 0,
                        };
                    });
                }
                if (spCommercialImpact && spCommercialImpact.assets) {
                    spCommercialImpact.assets.forEach(function(a) {
                        floodById[a.property_id] = {
                            damage_amount: a.damage_amount || 0,
                            damage_ratio:  a.damage_ratio  || 0,
                        };
                    });
                }

                // Index wind damage by asset id (covers both residential + commercial)
                if (spWindData && spWindData.rows) {
                    spWindData.rows.forEach(function(w) {
                        windById[w.asset_id] = {
                            damage_amount: w.damage_amount || 0,
                            damage_ratio:  w.damage_ratio  || 0,
                            peak_wind_ms:  w.peak_wind_ms,
                        };
                    });
                }

                function pushRow(asset_id, asset_class, address, value,
                                 outstanding, current_ltv, remaining) {
                    if (!outstanding) return;  // unmortgaged
                    var flood = floodById[asset_id] || {damage_amount:0, damage_ratio:0};
                    var wind  = windById[asset_id]  || {damage_amount:0, damage_ratio:0};
                    var combined_damage = Math.min(
                        (flood.damage_amount || 0) + (wind.damage_amount || 0),
                        value || 0
                    );
                    var combined_ratio = value > 0 ? combined_damage / value : 0;
                    var post_damage_value = Math.max((value || 0) - combined_damage, 0);
                    var combined_ltv;
                    if (post_damage_value > 0) {
                        combined_ltv = (outstanding / post_damage_value) * 100;
                    } else if (combined_damage > 0) {
                        combined_ltv = 999;  // total loss — display sentinel
                    } else {
                        combined_ltv = current_ltv;
                    }
                    rows.push({
                        asset_id: asset_id,
                        asset_class: asset_class,
                        address: address,
                        value: value,
                        outstanding_balance: outstanding,
                        current_ltv: current_ltv,
                        remaining_term_months: remaining,
                        flood_damage: flood.damage_amount || 0,
                        wind_damage: wind.damage_amount || 0,
                        combined_damage: combined_damage,
                        combined_ratio: combined_ratio,
                        post_damage_value: post_damage_value,
                        combined_ltv: combined_ltv,
                        impaired: combined_ltv >= 100,
                    });
                }

                if (spBlotterData && spBlotterData.properties) {
                    spBlotterData.properties.forEach(function(p) {
                        pushRow(p.property_id, 'residential', p.property_address,
                                p.property_value, p.outstanding_balance,
                                p.current_ltv, p.remaining_term_months);
                    });
                }
                if (spCommercialData && spCommercialData.assets) {
                    spCommercialData.assets.forEach(function(a) {
                        pushRow(a.property_id, 'commercial', a.property_address,
                                a.property_value, a.outstanding_balance,
                                a.current_ltv, a.remaining_term_months);
                    });
                }

                // Worst combined LTV first.
                rows.sort(function(a,b){ return (b.combined_ltv||0) - (a.combined_ltv||0); });
                return rows;
            }

            function loadMortgageData() {
                var summary = document.getElementById('sp-summary');
                var container = document.getElementById('sp-table-container');
                var sid = (document.getElementById('sp-storm-select') || {}).value || '';

                // Fetches needed before render: portfolio blotters + wind impact
                // for the current storm. Flood damage rides on spData /
                // spCommercialImpact which are loaded by loadPortfolioImpact +
                // loadCommercialImpact in the parent damage tab.
                var pending = [];
                // Each fetch is wrapped in its own .catch so one missing
                // endpoint can't hang the Promise.all and leave the tab on
                // the spinner forever.
                if (!spBlotterData) pending.push(
                    fetch(getBaseUrl() + '/api/v1/propertyts/blotter', {mode:'cors'})
                        .then(function(r){return r.json();})
                        .then(function(d){ if (d && d.status === 'success') spBlotterData = d; })
                        .catch(function(err){ console.warn('blotter fetch failed', err); })
                );
                if (!spCommercialData) pending.push(
                    fetch(getBaseUrl() + '/api/v1/commercial/blotter', {mode:'cors'})
                        .then(function(r){return r.json();})
                        .then(function(d){ if (d && d.status === 'success') spCommercialData = d; })
                        .catch(function(err){ console.warn('commercial blotter fetch failed', err); })
                );
                if (sid && (!spWindData || spWindData.storm_id !== sid)) pending.push(
                    fetch(getBaseUrl() + '/api/v1/propertyts/' + sid + '/wind-impact', {mode:'cors'})
                        .then(function(r){return r.json();})
                        .then(function(d){ if (d && d.status === 'success') spWindData = d; })
                        .catch(function(err){ console.warn('wind-impact fetch failed', err); })
                );
                // Commercial flood impact — same path as sp_table_summary
                // and sp_table_damage use.
                if (sid && (!spCommercialImpact || spCommercialImpact.storm_id !== sid)) pending.push(
                    fetch(getBaseUrl() + '/api/v1/commercial/' + sid + '/portfolio-impact', {mode:'cors'})
                        .then(function(r){return r.json();})
                        .then(function(d){
                            if (d && d.status === 'success') {
                                d.storm_id = sid;
                                spCommercialImpact = d;
                            }
                        })
                        .catch(function(err){ console.warn('commercial portfolio-impact fetch failed', err); })
                );

                if (pending.length) {
                    container.innerHTML = '<div style="padding:24px;text-align:center;color:#999;">Loading debt portfolio…</div>';
                    Promise.all(pending).then(_renderMortgageTab);
                } else {
                    _renderMortgageTab();
                }
            }

            function _renderMortgageTab() {
                var rows = _combinedRows();
                _renderMortgageSummary(rows);
                _renderMortgageTable(rows);
            }

            function _renderMortgageSummary(rows) {
                var summary = document.getElementById('sp-summary');
                var totalOS = rows.reduce(function(a,r){return a + (r.outstanding_balance||0);}, 0);
                var impaired = rows.filter(function(r){return r.impaired;}).length;
                var floodImpaired = rows.filter(function(r){return r.flood_damage > 0;}).length;
                var windImpaired = rows.filter(function(r){return r.wind_damage > 0;}).length;
                var cards = [
                    { label: 'Loans Outstanding', value: rows.length, color: '#1976d2' },
                    { label: 'Outstanding £', value: fmtGBP(totalOS), color: '#7b1fa2' },
                    { label: 'Flood-Damaged', value: floodImpaired, color: floodImpaired > 0 ? '#1565c0' : '#888' },
                    { label: 'Wind-Damaged', value: windImpaired, color: windImpaired > 0 ? '#bf360c' : '#888' },
                    { label: 'Impaired (Combined)', value: impaired, color: impaired > 0 ? '#d32f2f' : '#388e3c' },
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
                    container.innerHTML = '<div style="padding:24px;text-align:center;color:#999;">No loans outstanding in portfolio.</div>';
                    return;
                }

                var table = document.createElement('table');
                table.style.cssText = 'width:100%;border-collapse:collapse;font-size:11px;';

                // Three-group header so the maths reads left-to-right:
                //   Pre-damage  →  Damage subtractions  →  Post-damage
                // Pre: Value + Loan O/S       (green)
                // Damage: Flood £ + Wind £    (orange)
                // Post: Residual + LTV + Remaining (blue)
                var thead = document.createElement('thead');
                thead.innerHTML =
                    '<tr style="background:#fafafa;">' +
                      '<th rowspan="2" style="padding:6px 8px;text-align:left;border-bottom:2px solid #ddd;font-size:10px;color:#555;position:sticky;top:0;background:#fafafa;">Asset</th>' +
                      '<th rowspan="2" style="padding:6px 8px;text-align:left;border-bottom:2px solid #ddd;font-size:10px;color:#555;position:sticky;top:0;background:#fafafa;">Address</th>' +
                      '<th colspan="2" style="padding:6px 8px;text-align:center;border-bottom:1px solid #ddd;border-left:1px solid #eee;font-size:10px;color:#555;background:#f1f8e9;position:sticky;top:0;">Pre-Damage</th>' +
                      '<th colspan="2" style="padding:6px 8px;text-align:center;border-bottom:1px solid #ddd;border-left:1px solid #eee;font-size:10px;color:#555;background:#fff4e6;position:sticky;top:0;">Damage (\\u2212)</th>' +
                      '<th colspan="3" style="padding:6px 8px;text-align:center;border-bottom:1px solid #ddd;border-left:1px solid #eee;font-size:10px;color:#555;background:#eaf3ff;position:sticky;top:0;">Post-Damage</th>' +
                    '</tr>' +
                    '<tr style="background:#fafafa;">' +
                      '<th style="padding:4px 8px;text-align:right;border-bottom:2px solid #ddd;border-left:1px solid #eee;font-size:10px;color:#555;background:#f1f8e9;">Value</th>' +
                      '<th style="padding:4px 8px;text-align:right;border-bottom:2px solid #ddd;font-size:10px;color:#555;background:#f1f8e9;">Loan O/S</th>' +
                      '<th style="padding:4px 8px;text-align:right;border-bottom:2px solid #ddd;border-left:1px solid #eee;font-size:10px;color:#555;background:#fff4e6;">Flood</th>' +
                      '<th style="padding:4px 8px;text-align:right;border-bottom:2px solid #ddd;font-size:10px;color:#555;background:#fff4e6;">Wind</th>' +
                      '<th style="padding:4px 8px;text-align:right;border-bottom:2px solid #ddd;border-left:1px solid #eee;font-size:10px;color:#555;background:#eaf3ff;">Residual Value</th>' +
                      '<th style="padding:4px 8px;text-align:right;border-bottom:2px solid #ddd;font-size:10px;color:#555;background:#eaf3ff;">LTV</th>' +
                      '<th style="padding:4px 8px;text-align:right;border-bottom:2px solid #ddd;font-size:10px;color:#555;background:#eaf3ff;">Remaining</th>' +
                    '</tr>';
                table.appendChild(thead);

                var tbody = document.createElement('tbody');
                rows.forEach(function(r, idx) {
                    var tr = document.createElement('tr');
                    if (r.impaired) tr.style.background = '#ffebee';
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
                    // Pre-damage: original Value + Loan O/S
                    tr.appendChild(cell(fmtGBP(r.value || 0), 'right'));
                    tr.appendChild(cell(fmtGBP(r.outstanding_balance), 'right'));
                    // Damage subtractions
                    tr.appendChild(cell(r.flood_damage > 0 ? fmtGBP(r.flood_damage) : '\\u2014', 'right'));
                    tr.appendChild(cell(r.wind_damage > 0 ? fmtGBP(r.wind_damage) : '\\u2014', 'right'));
                    // Post-damage residual: Value − Flood − Wind, floored at 0.
                    // Always show as £ — £0 means total loss.
                    var totalLoss = r.post_damage_value === 0 && r.combined_damage > 0;
                    tr.appendChild(cell(
                        fmtGBP(r.post_damage_value || 0), 'right',
                        totalLoss ? '#bf360c' : null, totalLoss
                    ));
                    // LTV: Loan O/S / Residual × 100. When residual = 0 with
                    // outstanding debt it's a wipe-out — say so instead of
                    // 999%.
                    var ltvText, ltvColor = null, ltvBold = false;
                    if (totalLoss && r.outstanding_balance > 0) {
                        ltvText = 'Total loss';
                        ltvColor = '#d32f2f';
                        ltvBold = true;
                    } else if (r.combined_ltv != null) {
                        ltvText = fmtPct(r.combined_ltv);
                        if (r.combined_ltv > 100) { ltvColor = '#d32f2f'; ltvBold = true; }
                    } else {
                        ltvText = '\\u2014';
                    }
                    tr.appendChild(cell(ltvText, 'right', ltvColor, ltvBold));
                    tr.appendChild(cell(fmtMonths(r.remaining_term_months), 'right'));
                    tbody.appendChild(tr);
                });
                table.appendChild(tbody);

                container.innerHTML = '';
                container.appendChild(table);
            }
"""
