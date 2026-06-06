
            // ================================================================
            // REIT Blotter — property PRS trades (REIT perspective)
            // ================================================================
            function loadTradesData() {
                var summary = document.getElementById('sp-summary');
                var container = document.getElementById('sp-table-container');
                summary.innerHTML = '<div style="padding:4px;color:#888;font-size:11px;">Loading REIT trades...</div>';
                container.innerHTML = '';

                if (spTradesData) {
                    renderTradesSummary(spTradesData);
                    renderTradesTable(spTradesData.trades);
                    return;
                }

                var baseUrl = getBaseUrl();
                fetch(baseUrl + '/api/v1/trading/client', {mode: 'cors'})
                    .then(function(r) { return r.json(); })
                    .then(function(data) {
                        if (data.status === 'success') {
                            spTradesData = data;
                            renderTradesSummary(data);
                            renderTradesTable(data.trades);
                        } else {
                            summary.innerHTML = '<div style="color:red;">Error loading trades</div>';
                        }
                    })
                    .catch(function(err) {
                        summary.innerHTML = '<div style="color:red;">Failed to load trades</div>';
                        console.error('[StormPortfolio] Trades error:', err);
                    });
            }

            function renderTradesSummary(data) {
                var summary = document.getElementById('sp-summary');
                var ts = data.trader_summary || {};
                var trades = data.trades || [];
                var totalNpv = 0;
                trades.forEach(function(t) { totalNpv += (t.npv || 0); });
                // Stored NPV is already from payer (REIT) perspective
                var npvColor = totalNpv >= 0 ? '#388e3c' : '#d32f2f';
                var totalPropValue = 0;
                trades.forEach(function(t) { totalPropValue += (t.property_value || 0); });
                var cards = [
                    { label: 'Protection Bought', value: ts.num_trades || trades.length, color: '#1976d2' },
                    { label: 'Total Notional', value: fmtGBP(ts.total_notional_sold || 0), color: '#7b1fa2' },
                    { label: 'Avg Spread Paid', value: (ts.avg_spread_collected || 0).toFixed(1) + ' bps', color: '#e65100' },
                    { label: 'Property Value Covered', value: fmtGBP(ts.total_property_value_covered || totalPropValue), color: '#388e3c' },
                    { label: 'Total NPV', value: fmtGBP(totalNpv), color: npvColor },
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

            function renderTradesTable(trades) {
                var container = document.getElementById('sp-table-container');
                var tradeCols = [
                    { key: 'swap_id', label: 'Swap ID', align: 'left', fmt: function(v) { return v || '\u2014'; } },
                    { key: '_dir', label: 'Dir', align: 'left', fmt: function(v) { return 'Pay'; } },
                    { key: 'property_address', label: 'Property', align: 'left', fmt: function(v) { return v || '\u2014'; } },
                    { key: 'postcode', label: 'Postcode', align: 'left', fmt: function(v) { return v || '\u2014'; } },
                    { key: 'counterparty', label: 'Ctpty', align: 'left', fmt: function(v) { return v || '\u2014'; } },
                    { key: 'property_value', label: 'Prop Value', align: 'right', fmt: fmtGBP },
                    { key: 'notional', label: 'Notional', align: 'right', fmt: fmtGBP },
                    { key: 'hedge_ratio', label: 'Hedge %', align: 'right', fmt: function(v) { return v ? v.toFixed(1) + '%' : '\u2014'; } },
                    { key: 'end_date', label: 'Maturity', align: 'right', fmt: function(v) { return v ? v.substring(0, 7) : '\u2014'; } },
                    { key: 'spread_bps', label: 'Trade Spd', align: 'right', fmt: function(v) { return v ? v.toFixed(1) : '\u2014'; } },
                    { key: 'fair_spread_bps', label: 'Fair Spd', align: 'right', fmt: function(v) { return v ? v.toFixed(1) : '\u2014'; } },
                    { key: 'gauge_fs01', label: 'FS01', align: 'right', fmt: fmtGBP },
                    { key: 'ea_flood_zone', label: 'Flood Zone', align: 'left', fmt: function(v) { return v || '\u2014'; } },
                    { key: 'npv', label: 'NPV', align: 'right', fmt: fmtGBP },
                ];

                var table = document.createElement('table');
                table.style.cssText = 'width:100%;border-collapse:collapse;font-size:11px;';

                var thead = document.createElement('thead');
                var tr = document.createElement('tr');
                tradeCols.forEach(function(col) {
                    var th = document.createElement('th');
                    th.textContent = col.label;
                    th.style.cssText = 'padding:6px 8px;text-align:' + col.align + ';border-bottom:2px solid #ddd;background:#fafafa;white-space:nowrap;font-size:10px;color:#555;position:sticky;top:0;';
                    tr.appendChild(th);
                });
                thead.appendChild(tr);
                table.appendChild(thead);

                var tbody = document.createElement('tbody');
                var totalNotional = 0, totalPropValue = 0, totalNpv = 0;
                (trades || []).forEach(function(t, idx) {
                    // Stored NPV and FS01 are already from payer (REIT) perspective
                    totalNotional += (t.notional || 0);
                    totalPropValue += (t.property_value || 0);
                    totalNpv += (t.npv || 0);

                    var row = document.createElement('tr');
                    if (idx % 2 === 1) row.style.background = '#fafafa';
                    row.style.cursor = 'pointer';
                    row.onmouseenter = function() { this.style.opacity = '0.8'; };
                    row.onmouseleave = function() { this.style.opacity = '1'; };

                    tradeCols.forEach(function(col) {
                        var td = document.createElement('td');
                        var val = t[col.key];
                        td.textContent = col.fmt(val);
                        td.style.cssText = 'padding:5px 8px;border-bottom:1px solid #f0f0f0;text-align:' + col.align + ';white-space:nowrap;';
                        if (col.key === '_dir') {
                            td.style.color = '#1565c0';
                            td.style.fontWeight = 'bold';
                        }
                        if (col.key === 'npv' || col.key === 'gauge_fs01') {
                            td.style.color = val >= 0 ? '#2e7d32' : '#c62828';
                            td.style.fontWeight = 'bold';
                        }
                        if (col.key === 'hedge_ratio') {
                            var hv = t.hedge_ratio || 0;
                            td.style.color = hv > 200 ? '#c62828' : hv > 100 ? '#e65100' : '#2e7d32';
                        }
                        row.appendChild(td);
                    });
                    tbody.appendChild(row);
                });

                // Footer totals row
                var footRow = document.createElement('tr');
                footRow.style.cssText = 'font-weight:bold;background:#f5f5f5;border-top:2px solid #ccc;';
                tradeCols.forEach(function(col) {
                    var td = document.createElement('td');
                    td.style.cssText = 'padding:6px 8px;text-align:' + col.align + ';white-space:nowrap;';
                    if (col.key === 'swap_id') { td.textContent = 'Total'; }
                    else if (col.key === 'property_value') { td.textContent = fmtGBP(totalPropValue); }
                    else if (col.key === 'notional') { td.textContent = fmtGBP(totalNotional); }
                    else if (col.key === 'npv') {
                        td.textContent = fmtGBP(totalNpv);
                        td.style.color = totalNpv >= 0 ? '#2e7d32' : '#c62828';
                    }
                    footRow.appendChild(td);
                });
                tbody.appendChild(footRow);

                table.appendChild(tbody);

                container.innerHTML = '';
                container.appendChild(table);
            }
