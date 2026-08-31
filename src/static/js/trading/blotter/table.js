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

            function renderBlotterTable() {
                var wrap = document.getElementById('td-blotter-table-wrap');
                if (!wrap || !tdBlotterData) return;

                var filtered = getFilteredTrades();

                var cols = [
                    {key: 'swap_id', label: 'Swap ID', w: '100px'},
                    {key: 'direction', label: 'Dir', w: '36px'},
                    {key: 'gauge_id', label: 'Gauge', w: 'auto'},
                    {key: 'counterparty', label: 'Ctpy', w: 'auto'},
                    {key: 'notional', label: 'Notional', w: '85px', fmt: 'gbp', agg: 'sum'},
                    {key: 'maturity', label: 'Maturity', w: '60px', fmt: 'mat'},
                    {key: 'trade_spread_bps', label: 'Trade Spd', w: '65px', fmt: 'bps', agg: 'avg'},
                    {key: 'current_hazard_rate', label: 'Hazard', w: '60px', fmt: 'hazard', agg: 'wavg'},
                    {key: 'gauge_fs01', label: 'FS01', w: '80px', fmt: 'dv01', agg: 'sum'},
                    {key: 'new_trade_pnl', label: 'Nwt P&L', w: '80px', fmt: 'pnl', agg: 'sum'},
                    {key: 'market_pnl', label: 'Mkt P&L', w: '80px', fmt: 'pnl', agg: 'sum'},
                    {key: 'mtm', label: 'MTM', w: '80px', fmt: 'pnl', agg: 'sum'},
                    {key: '_contract', label: '', w: '30px'},
                    {key: '_close', label: '', w: '50px'}
                ];

                // Sort: newest first by default
                var sortOrder = window._tdSortOrder || 'newest';
                filtered.sort(function(a, b) {
                    var da = a.trade_date || a.swap_id || '';
                    var db = b.trade_date || b.swap_id || '';
                    return sortOrder === 'newest' ? (db > da ? 1 : db < da ? -1 : 0)
                                                  : (da > db ? 1 : da < db ? -1 : 0);
                });

                var todayStr = new Date().toISOString().slice(0, 10);

                var html = '<table style="width:100%;border-collapse:collapse;font-size:var(--size-xs);">';

                // Header
                html += '<thead><tr style="background:var(--accent-mid);color:var(--inverse);position:sticky;top:0;z-index:1;">';
                for (var c = 0; c < cols.length; c++) {
                    var sortIcon = '';
                    if (cols[c].key === 'swap_id') {
                        sortIcon = ' <span onclick="event.stopPropagation();tdToggleSort()" style="cursor:pointer;font-size:var(--size-xxs);opacity:0.8;">' +
                            (sortOrder === 'newest' ? '\u25bc' : '\u25b2') + '</span>';
                    }
                    html += '<th style="padding:var(--space-3) var(--space-4);text-align:' + (c > 3 ? 'right' : 'left') + ';font-weight:600;white-space:nowrap;">' + cols[c].label + sortIcon + '</th>';
                }
                html += '</tr></thead><tbody>';

                // Rows (filtered)
                for (var i = 0; i < filtered.length; i++) {
                    var t = filtered[i];
                    // Find original index for click handlers
                    var origIdx = tdBlotterData.indexOf(t);
                    var isToday = (t.trade_date || '').slice(0, 10) === todayStr;
                    var isClosed = (t.trade_status || 'Open').toLowerCase() === 'closed';
                    var bg = isClosed ? 'var(--raised)' : (isToday ? 'var(--ok-bg)' : (i % 2 === 0 ? 'var(--panel)' : 'var(--wash)'));
                    var leftBorder = isToday && !isClosed ? 'border-left:3px solid var(--green-dark);' : '';
                    var rowOpacity = isClosed ? 'opacity:0.6;' : '';

                    html += '<tr style="background:' + bg + ';border-bottom:1px solid var(--line-soft);cursor:pointer;' + leftBorder + rowOpacity + '" ' +
                        'onmouseenter="this.style.background=\'var(--accent-soft)\';this.style.opacity=\'1\'" ' +
                        'onmouseleave="this.style.background=\'' + bg + '\';this.style.opacity=\'' + (isClosed ? '0.6' : '1') + '\'" ' +
                        'onclick="tdViewTrade(' + origIdx + ')">';

                    for (var c = 0; c < cols.length; c++) {
                        var col = cols[c];
                        var val = t[col.key];
                        var align = c > 3 ? 'right' : 'left';
                        var display = '';
                        var color = 'var(--text)';

                        if (col.key === '_contract') {
                            display = '<button onclick="event.stopPropagation();tdViewContract(\'' + (t.swap_id || '') + '\')" ' +
                                'style="padding:var(--space-hair) var(--space-3);font-size:var(--size-xxs);background:none;border:1px solid var(--blue-grey-pale);border-radius:var(--radius-sm);cursor:pointer;color:var(--blue-grey-dark);" ' +
                                'title="View trade contract PDF">\u2709</button>';
                        } else if (col.key === '_close') {
                            if (isClosed) {
                                display = '';
                            } else {
                                display = '<button onclick="event.stopPropagation();tdCloseOutTrade(' + origIdx + ')" ' +
                                    'style="padding:var(--space-1) var(--space-3);font-size:var(--size-xxs);background:var(--accent-mid);color:var(--inverse);border:none;border-radius:var(--radius-sm);cursor:pointer;font-weight:600;" ' +
                                    'title="Close out this trade">Close</button>';
                            }
                        } else if (col.key === 'direction') {
                            var isPayer = t.is_payer;
                            var dirLabel = isPayer ? 'Pay' : 'Rcv';
                            var dirColor = isPayer ? 'var(--red-dark)' : 'var(--green-dark)';
                            display = '<span style="font-weight:bold;color:' + dirColor + ';">' + dirLabel + '</span>';
                        } else if (col.fmt === 'gbp') {
                            // Sign notional: negative for Pay, positive for Rcv
                            if (col.key === 'notional') {
                                val = t.is_payer ? -Math.abs(val) : Math.abs(val);
                            }
                            display = fmtGBP(val);
                        } else if (col.fmt === 'hazard') {
                            display = val != null ? (val * 10000).toFixed(0) + 'bp' : '\u2014';
                            // Bloomberg-style: green bg if curve up, red bg if curve down
                            var curFair = t.fair_spread_bps || 0;
                            var prevFair = t.prev_fair_spread_bps || 0;
                            if (curFair > prevFair + 0.1) {
                                color = 'var(--panel)'; display = '<span style="background:var(--green-deep);color:var(--panel);padding:var(--space-hair) var(--space-2);border-radius:var(--radius-sm);">' + display + ' \u25b2</span>';
                            } else if (curFair < prevFair - 0.1) {
                                color = 'var(--panel)'; display = '<span style="background:var(--red-deep);color:var(--panel);padding:var(--space-hair) var(--space-2);border-radius:var(--radius-sm);">' + display + ' \u25bc</span>';
                            }
                        } else if (col.fmt === 'bps') {
                            display = val != null ? val.toFixed(1) : '\u2014';
                        } else if (col.fmt === 'mat') {
                            display = fmtMaturity(val);
                        } else if (col.fmt === 'pnl') {
                            color = val >= 0 ? 'var(--green-dark)' : 'var(--red-dark)';
                            display = fmtGBP(val);
                        } else if (col.fmt === 'dv01') {
                            color = val > 0 ? 'var(--accent-mid)' : (val < 0 ? 'var(--red-dark)' : 'var(--text)');
                            display = fmtGBP(val);
                        } else {
                            display = val != null ? String(val) : '\u2014';
                        }

                        // Show gauge short name instead of ID
                        if (col.key === 'gauge_id') {
                            display = extractAreaName(t.gauge_name || val || '');
                        }

                        // Swap ID: add CLOSED badge for closed trades
                        if (col.key === 'swap_id' && isClosed) {
                            display += ' <span style="font-size:var(--size-8);background:var(--amber-deep);color:var(--inverse);padding:var(--space-hair) var(--space-2);border-radius:var(--radius-sm);font-weight:700;vertical-align:middle;">CLOSED</span>';
                        }

                        // Notional: show original struck through + 0 for closed trades
                        if (col.key === 'notional' && isClosed) {
                            var origNot = t.original_notional || 0;
                            var signedOrig = t.is_payer ? -Math.abs(origNot) : Math.abs(origNot);
                            display = '<span style="text-decoration:line-through;color:var(--muted-2);font-size:var(--size-xxs);">' + fmtGBP(signedOrig) + '</span> <span style="font-weight:700;">0</span>';
                        }

                        // MTM: show final P&L for closed trades
                        if (col.key === 'mtm' && isClosed) {
                            var finalPnl = t.final_pnl || 0;
                            color = finalPnl >= 0 ? 'var(--green-dark)' : 'var(--red-dark)';
                            display = fmtGBP(finalPnl);
                        }

                        html += '<td style="padding:var(--space-3) var(--space-4);text-align:' + align + ';color:' + color + ';white-space:nowrap;">' + display + '</td>';
                    }
                    html += '</tr>';
                }

                if (filtered.length === 0) {
                    html += '<tr><td colspan="' + cols.length + '" style="padding:var(--space-wide);text-align:center;color:var(--muted-2);">No trades match current filters</td></tr>';
                }

                // Summary / totals row
                if (filtered.length > 0) {
                    html += '</tbody><tfoot><tr style="background:var(--info-bg);border-top:2px solid var(--accent-mid);font-weight:700;position:sticky;bottom:0;z-index:1;">';
                    var totNotional = 0, totSpread = 0, totHaz = 0, totHazWeight = 0;
                    var totFs01 = 0, totNwtPnl = 0, totMktPnl = 0, totMtm = 0;
                    for (var si = 0; si < filtered.length; si++) {
                        var st = filtered[si];
                        totNotional += st.is_payer ? -(st.notional || 0) : (st.notional || 0);
                        totSpread += (st.trade_spread_bps || 0);
                        var hr = st.current_hazard_rate || 0;
                        var w = Math.abs(st.notional || 0);
                        totHaz += hr * w;
                        totHazWeight += w;
                        totFs01 += (st.gauge_fs01 || 0);
                        totNwtPnl += (st.new_trade_pnl || 0);
                        totMktPnl += (st.market_pnl || 0);
                        totMtm += (st.mtm || 0);
                    }
                    var avgSpread = filtered.length > 0 ? totSpread / filtered.length : 0;
                    var wavgHaz = totHazWeight > 0 ? totHaz / totHazWeight : 0;
                    for (var fc = 0; fc < cols.length; fc++) {
                        var fcol = cols[fc];
                        var fAlign = fc > 3 ? 'right' : 'left';
                        var fVal = '';
                        var fColor = 'var(--text)';
                        if (fcol.key === 'swap_id') { fVal = 'Total'; }
                        else if (fcol.key === 'notional') { fVal = fmtGBP(totNotional); }
                        else if (fcol.key === 'trade_spread_bps') { fVal = avgSpread.toFixed(1); fColor = 'var(--text-3)'; }
                        else if (fcol.key === 'current_hazard_rate') { fVal = (wavgHaz * 10000).toFixed(0) + 'bp'; fColor = 'var(--text-3)'; }
                        else if (fcol.key === 'gauge_fs01') { fColor = totFs01 > 0 ? 'var(--accent-mid)' : (totFs01 < 0 ? 'var(--red-dark)' : 'var(--text)'); fVal = fmtGBP(totFs01); }
                        else if (fcol.key === 'new_trade_pnl') { fColor = totNwtPnl >= 0 ? 'var(--green-dark)' : 'var(--red-dark)'; fVal = fmtGBP(totNwtPnl); }
                        else if (fcol.key === 'market_pnl') { fColor = totMktPnl >= 0 ? 'var(--green-dark)' : 'var(--red-dark)'; fVal = fmtGBP(totMktPnl); }
                        else if (fcol.key === 'mtm') { fColor = totMtm >= 0 ? 'var(--green-dark)' : 'var(--red-dark)'; fVal = fmtGBP(totMtm); }
                        html += '<td style="padding:var(--space-3) var(--space-4);text-align:' + fAlign + ';color:' + fColor + ';white-space:nowrap;font-size:var(--size-xs);">' + fVal + '</td>';
                    }
                    html += '</tr></tfoot>';
                }

                html += '</table>';
                wrap.innerHTML = html;
            }

            // Toggle sort order (newest/oldest)
            window.tdToggleSort = function() {
                window._tdSortOrder = (window._tdSortOrder || 'newest') === 'newest' ? 'oldest' : 'newest';
                renderBlotterTable();
            };
