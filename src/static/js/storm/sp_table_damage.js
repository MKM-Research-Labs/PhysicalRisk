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

            function _residentialRowsFromImpact(impact) {
                var details = (window._propDetailsByPid = window._propDetailsByPid || {});
                return (impact.properties || []).map(function(p) {
                    return {
                        asset_id: p.property_id,
                        asset_class: 'residential',
                        address: (details[p.property_id] || {}).address || '',
                        type: 'Residential',
                        value: p.property_value,
                        damage_amount: p.damage_amount,
                        damage_ratio: p.damage_ratio,
                        flood_depth_m: p.flood_depth_m,
                        outstanding_balance: p.outstanding_balance,
                        current_ltv: p.current_ltv,
                        post_damage_ltv: p.post_damage_ltv,
                        remaining_term_months: p.remaining_term_months,
                        negative_equity: p.negative_equity,
                    };
                });
            }

            function _commercialRowsFromImpact(impact) {
                return (impact.assets || []).map(function(a) {
                    return {
                        asset_id: a.property_id,
                        asset_class: 'commercial',
                        address: a.property_address,
                        type: a.commercial_type || 'Commercial',
                        value: a.property_value,
                        damage_amount: a.damage_amount,
                        damage_ratio: a.damage_ratio,
                        flood_depth_m: a.flood_depth_m,
                        outstanding_balance: a.outstanding_balance,
                        current_ltv: a.current_ltv,
                        post_damage_ltv: a.post_damage_ltv,
                        remaining_term_months: a.remaining_term_months,
                        negative_equity: a.negative_equity,
                    };
                });
            }

            // Cache addresses from the residential blotter so flood-impact
            // rows (which only carry property_id) can show a proper address.
            function _seedResidentialAddresses() {
                if (!spBlotterData || !spBlotterData.properties) return;
                var map = (window._propDetailsByPid = window._propDetailsByPid || {});
                spBlotterData.properties.forEach(function(p) {
                    map[p.property_id] = { address: p.property_address };
                });
            }

            function loadFloodDamage(stormId) {
                var summary = document.getElementById('sp-summary');
                var container = document.getElementById('sp-table-container');
                if (!stormId) {
                    summary.innerHTML = '';
                    container.innerHTML = '<div style="padding:var(--space-10);text-align:center;color:var(--muted-2);">Select a storm above</div>';
                    return;
                }

                // Residential impact already loaded by onStormChanged; commercial
                // is fetched lazily (cache invalidated on storm change).
                _seedResidentialAddresses();

                if (spCommercialImpact && spCommercialImpact._storm_id === stormId) {
                    _renderFloodDamage(stormId);
                    return;
                }

                container.innerHTML = '<div style="padding:var(--space-10);text-align:center;color:var(--muted-2);">Loading commercial impact...</div>';
                fetch(getBaseUrl() + '/api/v1/commercial/' + stormId + '/portfolio-impact', {mode:'cors'})
                    .then(function(r) { return r.json(); })
                    .then(function(data) {
                        if (data.status === 'success') {
                            data._storm_id = stormId;
                            spCommercialImpact = data;
                        } else {
                            // No commercial flooding — keep an empty record so
                            // the combined table still renders residential rows.
                            spCommercialImpact = {
                                _storm_id: stormId, assets: [],
                                portfolio: { assets_affected: 0, total_damage: 0,
                                             total_affected_loans: 0,
                                             loans_in_negative_equity: 0 },
                            };
                        }
                        _renderFloodDamage(stormId);
                    })
                    .catch(function(err) {
                        console.error('[StormPortfolio] commercial impact error:', err);
                        spCommercialImpact = {
                            _storm_id: stormId, assets: [],
                            portfolio: { assets_affected: 0, total_damage: 0,
                                         total_affected_loans: 0,
                                         loans_in_negative_equity: 0 },
                        };
                        _renderFloodDamage(stormId);
                    });
            }

            function _renderFloodDamage(stormId) {
                var rows = [];
                if (spData && spData.portfolio) rows = rows.concat(_residentialRowsFromImpact(spData));
                if (spCommercialImpact) rows = rows.concat(_commercialRowsFromImpact(spCommercialImpact));

                _renderFloodSummary();
                _renderDamageTable(rows, 'flood');
            }

            function _renderFloodSummary() {
                var summary = document.getElementById('sp-summary');
                var p = (spData && spData.portfolio) || {};
                var c = (spCommercialImpact && spCommercialImpact.portfolio) || {};
                var totalDamage = (p.total_damage || 0) + (c.total_damage || 0);
                var totalAffectedDebt = (p.total_affected_mortgages || 0) + (c.total_affected_loans || 0);
                var negEquity = (p.mortgages_in_negative_equity || 0) + (c.loans_in_negative_equity || 0);
                var cards = [
                    { label: 'Properties Affected', value: (p.properties_affected || 0) + ' / ' + (p.total_properties || 0), color: 'var(--accent)' },
                    { label: 'Commercials Affected', value: (c.assets_affected || 0) + ' / ' + (c.total_assets || 0), color: 'var(--accent)' },
                    { label: 'Total Flood Damage', value: fmtGBP(totalDamage), color: 'var(--red)' },
                    { label: 'Debt Exposure', value: fmtGBP(totalAffectedDebt), color: 'var(--purple)' },
                    { label: 'Negative Equity', value: negEquity, color: negEquity > 0 ? 'var(--red)' : 'var(--green)' },
                ];
                summary.innerHTML = '';
                cards.forEach(function(card) {
                    var div = document.createElement('div');
                    div.style.cssText = 'flex:1;min-width:120px;padding:var(--space-4) var(--space-6);border-radius:var(--radius-md);background:var(--sunken);border-left:3px solid ' + card.color + ';';
                    div.innerHTML = '<div style="font-size:var(--size-xxs);color:var(--muted);text-transform:uppercase;letter-spacing:0.5px;">' + card.label + '</div>' +
                        '<div style="font-size:var(--size-lg);font-weight:700;color:' + card.color + ';margin-top:var(--space-1);">' + card.value + '</div>';
                    summary.appendChild(div);
                });
            }

            // Shared damage-table renderer — used by Flood and Wind tabs.
            // `kind` is 'flood' or 'wind'; only affects the column label.
            function _renderDamageTable(rows, kind) {
                var container = document.getElementById('sp-table-container');
                var cols = [
                    { key: 'asset_id', label: 'Asset', fmt: function(v) { return v; }, align: 'left' },
                    { key: 'address', label: 'Address', fmt: function(v) { return v || '\u2014'; }, align: 'left' },
                    { key: 'type', label: 'Type', fmt: function(v) { return v || '\u2014'; }, align: 'left' },
                    { key: 'value', label: 'Value', fmt: fmtGBP, align: 'right' },
                    { key: 'damage_amount', label: (kind === 'wind' ? 'Wind Damage £' : 'Flood Damage £'), fmt: function(v) { return (v == null) ? '\u2014' : fmtGBP(v); }, align: 'right' },
                    { key: 'damage_ratio', label: (kind === 'wind' ? 'Wind %' : 'Flood %'), fmt: function(v) { return (v == null) ? '\u2014' : (v * 100).toFixed(1) + '%'; }, align: 'right' },
                ];

                if (!rows || rows.length === 0) {
                    container.innerHTML =
                        '<table style="width:100%;border-collapse:collapse;font-size:var(--size-xs);">' +
                          '<tbody><tr><td style="padding:var(--space-inset);text-align:center;color:var(--muted-2);font-size:var(--size-md);">' +
                            (kind === 'wind' ? 'Wind damage model not yet wired — no rows to show.'
                                             : 'This storm does not cause any flooding to the combined portfolio.') +
                          '</td></tr></tbody></table>';
                    return;
                }

                var table = document.createElement('table');
                table.style.cssText = 'width:100%;border-collapse:collapse;font-size:var(--size-xs);';

                var thead = document.createElement('thead');
                var tr = document.createElement('tr');
                cols.forEach(function(col) {
                    var th = document.createElement('th');
                    th.textContent = col.label + (spSortCol === col.key ? (spSortAsc ? ' \u25b2' : ' \u25bc') : '');
                    th.style.cssText = 'padding:var(--space-3) var(--space-4);text-align:' + col.align + ';border-bottom:2px solid var(--line-strong);background:var(--raised);cursor:pointer;white-space:nowrap;font-size:var(--size-xxs);color:var(--text-2);position:sticky;top:0;';
                    th.onclick = (function(k) {
                        return function() {
                            if (spSortCol === k) spSortAsc = !spSortAsc;
                            else { spSortCol = k; spSortAsc = false; }
                            _renderDamageTable(rows, kind);
                        };
                    })(col.key);
                    tr.appendChild(th);
                });
                thead.appendChild(tr);
                table.appendChild(thead);

                var sorted = rows.slice().sort(function(a, b) {
                    var va = a[spSortCol], vb = b[spSortCol];
                    if (va == null && vb == null) return 0;
                    if (va == null) return 1;
                    if (vb == null) return -1;
                    if (typeof va === 'string') return spSortAsc ? va.localeCompare(vb) : vb.localeCompare(va);
                    return spSortAsc ? va - vb : vb - va;
                });

                var tbody = document.createElement('tbody');
                sorted.forEach(function(r, idx) {
                    var row = document.createElement('tr');
                    if (r.asset_class === 'commercial') row.style.background = Theme.value('rv-wash-4');
                    else if (idx % 2 === 1) row.style.background = Theme.value('raised');
                    row.style.cursor = 'pointer';
                    row.onmouseenter = function() { this.style.opacity = '0.8'; };
                    row.onmouseleave = function() { this.style.opacity = '1'; };
                    row.onclick = (function(aid) {
                        return function() {
                            hidePanel();
                            if (window.PropertyStormAnalysis && window.PropertyStormAnalysis.show) {
                                window.PropertyStormAnalysis.show(aid);
                            } else {
                                document.dispatchEvent(new CustomEvent('propertyStormRequested', {
                                    detail: { propertyId: aid }, bubbles: true
                                }));
                            }
                        };
                    })(r.asset_id);

                    cols.forEach(function(col) {
                        var td = document.createElement('td');
                        td.textContent = col.fmt(r[col.key]);
                        td.style.cssText = 'padding:var(--space-3) var(--space-4);border-bottom:1px solid var(--code);text-align:' + col.align + ';white-space:nowrap;';
                        if (col.key === 'damage_amount' && r[col.key]) td.style.color = Theme.value('red');
                        row.appendChild(td);
                    });
                    tbody.appendChild(row);
                });
                table.appendChild(tbody);

                container.innerHTML = '';
                container.appendChild(table);
            }

            // Legacy entry point kept so the storm-change loader in
            // sp_table.py (renderSummary + renderTable) still works:
            // renderSummary now delegates to the flood summary,
            // renderTable to the combined damage table.
            function renderSummary(portfolio, derivatives) {
                _renderFloodSummary();
            }
            function renderTable(properties) {
                var stormSel = document.getElementById('sp-storm-select');
                var sid = stormSel ? stormSel.value : '';
                loadFloodDamage(sid);
            }
