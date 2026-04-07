# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""
Client tab — table rendering sub-module.

Property PRS trade table with columns for property details and pricing.
"""


def get_js() -> str:
    """Return JavaScript fragment for client table rendering."""
    return """
            function renderClientTable() {
                var wrap = document.getElementById('td-client-table-wrap');
                if (!wrap || !tdClientData) return;

                var cols = [
                    {key: 'swap_id', label: 'Swap ID', w: '110px'},
                    {key: 'direction', label: 'Dir', w: '36px'},
                    {key: 'property_address', label: 'Property', w: 'auto'},
                    {key: 'postcode', label: 'Postcode', w: '70px'},
                    {key: 'counterparty', label: 'Ctpy', w: 'auto'},
                    {key: 'notional', label: 'Notional', w: '95px', fmt: 'gbp'},
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
                    var align = c > 4 ? 'right' : 'left';
                    html += '<th style="padding:6px 8px;text-align:' + align + ';font-weight:600;white-space:nowrap;">' + cols[c].label + '</th>';
                }
                html += '</tr></thead><tbody>';

                // Rows
                for (var i = 0; i < trades.length; i++) {
                    var t = trades[i];
                    var bg = i % 2 === 0 ? '#fff' : '#f8f9fa';

                    html += '<tr style="background:' + bg + ';border-bottom:1px solid #eee;" ' +
                        'onmouseenter="this.style.background=\\'#e3f2fd\\'" ' +
                        'onmouseleave="this.style.background=\\'' + bg + '\\'">';

                    for (var c = 0; c < cols.length; c++) {
                        var col = cols[c];
                        var val = t[col.key];
                        var align = c > 4 ? 'right' : 'left';
                        var display = '';
                        var color = '#333';

                        if (col.key === 'direction') {
                            var isPayer = t.is_payer;
                            var dirLabel = isPayer ? 'Pay' : 'Rcv';
                            var dirColor = isPayer ? '#c62828' : '#2e7d32';
                            display = '<span style="font-weight:bold;color:' + dirColor + ';">' + dirLabel + '</span>';
                        } else if (col.fmt === 'gbp') {
                            if (col.key === 'notional') {
                                val = t.is_payer ? -Math.abs(val) : Math.abs(val);
                            }
                            display = fmtGBP(val);
                        } else if (col.fmt === 'bps') {
                            display = val != null ? val.toFixed(1) : '\\u2014';
                        } else if (col.fmt === 'mat') {
                            display = fmtMaturity(val);
                        } else if (col.fmt === 'dv01') {
                            color = val > 0 ? '#1565c0' : (val < 0 ? '#c62828' : '#333');
                            display = fmtGBP(val);
                        } else if (col.fmt === 'pnl') {
                            color = val >= 0 ? '#2e7d32' : '#c62828';
                            display = fmtGBP(val);
                        } else {
                            display = val != null ? String(val) : '\\u2014';
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
                    var totNotional = 0, totNpv = 0, totFs01 = 0, totSpread = 0;
                    for (var si = 0; si < trades.length; si++) {
                        var st = trades[si];
                        totNotional += st.is_payer ? -(st.notional || 0) : (st.notional || 0);
                        totNpv += (st.npv || 0);
                        totFs01 += (st.gauge_fs01 || 0);
                        totSpread += (st.spread_bps || 0);
                    }
                    var avgSpread = trades.length > 0 ? totSpread / trades.length : 0;

                    for (var fc = 0; fc < cols.length; fc++) {
                        var fcol = cols[fc];
                        var fAlign = fc > 4 ? 'right' : 'left';
                        var fVal = '';
                        var fColor = '#333';
                        if (fcol.key === 'swap_id') { fVal = 'Total'; }
                        else if (fcol.key === 'notional') { fVal = fmtGBP(totNotional); }
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
"""
