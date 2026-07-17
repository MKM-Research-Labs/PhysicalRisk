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

            function renderClientTable() {
                var wrap = document.getElementById('td-client-table-wrap');
                if (!wrap || !tdClientData) return;

                var cols = [
                    {key: 'swap_id', label: 'Swap ID', w: '110px'},
                    {key: 'direction', label: 'Dir', w: '36px'},
                    {key: 'prs_variant', label: 'Variant', w: '70px', fmt: 'variant'},
                    {key: '_property_label', label: 'Property', w: 'auto'},
                    {key: 'postcode', label: 'Postcode', w: '70px'},
                    {key: 'counterparty', label: 'Ctpy', w: 'auto'},
                    {key: 'property_value', label: 'Prop Value', w: '95px', fmt: 'gbp'},
                    {key: 'notional', label: 'Notional', w: '95px', fmt: 'gbp'},
                    {key: 'hedge_ratio', label: 'Hedge %', w: '55px', fmt: 'hedge'},
                    {key: 'end_date', label: 'Maturity', w: '60px', fmt: 'mat'},
                    {key: 'spread_bps', label: 'Trade Spd', w: '65px', fmt: 'bps'},
                    {key: 'fair_spread_bps', label: 'Fair Spd', w: '65px', fmt: 'bps'},
                    {key: 'gauge_fs01', label: 'FS01', w: '80px', fmt: 'dv01'},
                    {key: 'ea_flood_zone', label: 'Flood Zone', w: '70px'},
                    {key: 'npv', label: 'NPV', w: '80px', fmt: 'pnl'}
                ];

                var trades = tdClientData;

                var html = '<table style="width:100%;border-collapse:collapse;font-size:11px;">';

                // Header
                html += '<thead><tr style="background:#0d47a1;color:white;position:sticky;top:0;z-index:1;">';
                for (var c = 0; c < cols.length; c++) {
                    var align = c > 5 ? 'right' : 'left';
                    html += '<th style="padding:6px 8px;text-align:' + align + ';font-weight:600;white-space:nowrap;">' + cols[c].label + '</th>';
                }
                html += '</tr></thead><tbody>';

                // Rows
                for (var i = 0; i < trades.length; i++) {
                    var t = trades[i];
                    var bg = i % 2 === 0 ? '#fff' : '#f8f9fa';

                    html += '<tr style="background:' + bg + ';border-bottom:1px solid #eee;" ' +
                        'onmouseenter="this.style.background=\'#e3f2fd\'" ' +
                        'onmouseleave="this.style.background=\'' + bg + '\'">';

                    for (var c = 0; c < cols.length; c++) {
                        var col = cols[c];
                        var val = t[col.key];
                        var align = c > 5 ? 'right' : 'left';
                        var display = '';
                        var color = '#333';

                        if (col.key === '_property_label') {
                            display = window.propertyDisplayName(t.property_id, t.property_address);
                        } else if (col.key === 'direction') {
                            // Trader is always receiver on PropertyPRS
                            display = '<span style="font-weight:bold;color:#2e7d32;">Rcv</span>';
                        } else if (col.fmt === 'variant') {
                            // Pure (surveyed floor) vs resilient (BRI-adjusted).
                            var isResilient = (val === 'resilient');
                            var vBg = isResilient ? '#EDE7F6' : '#E3F2FD';
                            var vFg = isResilient ? '#4527A0' : '#1565C0';
                            var vLbl = isResilient ? 'Resilient' : 'Pure';
                            display = '<span style="background:' + vBg + ';color:' + vFg +
                                ';padding:1px 6px;border-radius:8px;font-size:10px;font-weight:600;">' +
                                vLbl + '</span>';
                        } else if (col.fmt === 'hedge') {
                            display = val != null ? val.toFixed(1) + '%' : '\u2014';
                            color = val >= 100 ? '#2e7d32' : (val > 0 ? '#f57c00' : '#999');
                        } else if (col.fmt === 'gbp') {
                            display = fmtGBP(val);
                        } else if (col.fmt === 'bps') {
                            display = val != null ? val.toFixed(1) : '\u2014';
                        } else if (col.fmt === 'mat') {
                            display = fmtMaturity(val);
                        } else if (col.fmt === 'dv01') {
                            color = val > 0 ? '#1565c0' : (val < 0 ? '#c62828' : '#333');
                            display = fmtGBP(val);
                        } else if (col.fmt === 'pnl') {
                            color = val >= 0 ? '#2e7d32' : '#c62828';
                            display = fmtGBP(val);
                        } else {
                            display = val != null ? String(val) : '\u2014';
                        }

                        html += '<td style="padding:5px 8px;text-align:' + align + ';color:' + color + ';white-space:nowrap;">' + display + '</td>';
                    }
                    html += '</tr>';
                }

                if (trades.length === 0) {
                    html += '<tr><td colspan="' + cols.length + '" style="padding:20px;text-align:center;color:#999;">No property PRS trades found</td></tr>';
                }

                // Totals row
                if (trades.length > 0) {
                    html += '</tbody><tfoot><tr style="background:#e8eaf6;border-top:2px solid #0d47a1;font-weight:700;position:sticky;bottom:0;z-index:1;">';
                    var totNotional = 0, totNpv = 0, totFs01 = 0, totSpread = 0, totPropVal = 0, spreadCnt = 0;
                    for (var si = 0; si < trades.length; si++) {
                        var st = trades[si];
                        totNotional += (st.notional || 0);
                        totNpv += (st.npv || 0);
                        totFs01 += (st.gauge_fs01 || 0);
                        if (st.spread_bps > 0) { totSpread += st.spread_bps; spreadCnt++; }
                        totPropVal += (st.property_value || 0);
                    }
                    var avgSpread = spreadCnt > 0 ? totSpread / spreadCnt : 0;
                    var totHedge = totPropVal > 0 ? (totNotional / totPropVal * 100) : 0;

                    for (var fc = 0; fc < cols.length; fc++) {
                        var fcol = cols[fc];
                        var fAlign = fc > 5 ? 'right' : 'left';
                        var fVal = '';
                        var fColor = '#333';
                        if (fcol.key === 'swap_id') { fVal = 'Total'; }
                        else if (fcol.key === 'property_value') { fVal = fmtGBP(totPropVal); }
                        else if (fcol.key === 'notional') { fVal = fmtGBP(totNotional); }
                        else if (fcol.key === 'hedge_ratio') { fVal = totHedge.toFixed(1) + '%'; fColor = totHedge >= 100 ? '#2e7d32' : '#f57c00'; }
                        else if (fcol.key === 'spread_bps') { fVal = avgSpread.toFixed(1); fColor = '#666'; }
                        else if (fcol.key === 'gauge_fs01') { fColor = totFs01 > 0 ? '#1565c0' : (totFs01 < 0 ? '#c62828' : '#333'); fVal = fmtGBP(totFs01); }
                        else if (fcol.key === 'npv') { fColor = totNpv >= 0 ? '#2e7d32' : '#c62828'; fVal = fmtGBP(totNpv); }
                        html += '<td style="padding:6px 8px;text-align:' + fAlign + ';color:' + fColor + ';white-space:nowrap;font-size:11px;">' + fVal + '</td>';
                    }
                    html += '</tr></tfoot>';
                }

                html += '</table>';
                wrap.innerHTML = html;
            }
