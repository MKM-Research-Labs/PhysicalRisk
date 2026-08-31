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

            function _renderStressTable(data) {
                var wrap = document.getElementById('stress-table-wrap');
                if (!wrap) return;

                var trades = data.trades || [];
                var hourly = data.hourly || [];
                var summary = data.summary || {};
                var peakHour = summary.peak_p_flood_hour || 0;
                var peakData = hourly[peakHour] || {};
                var perTrade = peakData.per_trade || [];

                var ptMap = {};
                perTrade.forEach(function(pt) { ptMap[pt.swap_id] = pt; });

                var fmtGBP = function(v) {
                    var abs = Math.abs(v);
                    var s = abs >= 1e6 ? (abs/1e6).toFixed(1) + 'M' :
                            abs >= 1e3 ? (abs/1e3).toFixed(1) + 'K' :
                            abs.toFixed(0);
                    var cc = (window.__BACKEND_CONFIG || {}).currency || 'GBP';
                    var sym = {GBP: '\u00A3', USD: '$', EUR: '\u20AC'}[cc] || (cc + ' ');
                    return (v < 0 ? '-' : '') + sym + s;
                };
                var pnlColor = function(v) { return v >= 0 ? 'var(--green-dark)' : 'var(--red-dark)'; };

                var html = '<table style="width:100%;border-collapse:collapse;font-size:var(--size-xxs);">' +
                    '<thead><tr style="background:var(--sunken);border-bottom:2px solid var(--line-strong);">' +
                    '<th style="padding:var(--space-2) var(--space-3);text-align:left;">Swap</th>' +
                    '<th style="padding:var(--space-2) var(--space-2);text-align:center;">Dir</th>' +
                    '<th style="padding:var(--space-2) var(--space-3);text-align:right;">Notional</th>' +
                    '<th style="padding:var(--space-2) var(--space-3);text-align:right;">MTM</th>' +
                    '<th style="padding:var(--space-2) var(--space-3);text-align:right;">Cash Price</th>' +
                    '<th style="padding:var(--space-2) var(--space-3);text-align:right;">Stress P&L</th>' +
                    '<th style="padding:var(--space-2) var(--space-2);text-align:center;">Status</th>' +
                    '</tr></thead><tbody>';

                var totalNotional = 0, totalMtm = 0, totalCash = 0, totalStress = 0;
                var numTriggered = 0;

                trades.forEach(function(t) {
                    var pt = ptMap[t.swap_id] || {};
                    var cashPrice = pt.cash_price || 0;
                    var stressPnl = pt.stress_pnl || 0;
                    var dir = t.is_payer ? 'Pay' : 'Rcv';
                    var dirColor = t.is_payer ? 'var(--red-dark)' : 'var(--green-dark)';
                    var isTriggered = t.triggered_hour != null;
                    if (isTriggered) numTriggered++;
                    var statusLabel = isTriggered ?
                        '<span style="background:var(--red-dark);color:var(--panel);padding:var(--space-hair) var(--space-2);border-radius:var(--radius-sm);font-size:var(--size-8);font-weight:700;">KO H' + t.triggered_hour + '</span>' :
                        '<span style="color:var(--muted-2);font-size:var(--size-8);">Live</span>';

                    totalNotional += t.notional;
                    totalMtm += t.mtm;
                    totalCash += cashPrice;
                    totalStress += stressPnl;

                    html += '<tr style="border-bottom:1px solid var(--code);' +
                            (isTriggered ? 'background:var(--rv-bad-bg);' : '') + '">' +
                        '<td style="padding:var(--space-2) var(--space-3);font-family:monospace;font-size:var(--size-xxs);">' +
                            t.swap_id.substring(0, 12) + '</td>' +
                        '<td style="padding:var(--space-2) var(--space-2);text-align:center;color:' + dirColor + ';font-weight:600;">' +
                            dir + '</td>' +
                        '<td style="padding:var(--space-2) var(--space-3);text-align:right;">' + fmtGBP(t.notional) + '</td>' +
                        '<td style="padding:var(--space-2) var(--space-3);text-align:right;color:' + pnlColor(t.mtm) + ';">' +
                            fmtGBP(t.mtm) + '</td>' +
                        '<td style="padding:var(--space-2) var(--space-3);text-align:right;color:' + pnlColor(cashPrice) + ';">' +
                            fmtGBP(cashPrice) + '</td>' +
                        '<td style="padding:var(--space-2) var(--space-3);text-align:right;font-weight:700;color:' +
                            pnlColor(stressPnl) + ';">' + fmtGBP(stressPnl) + '</td>' +
                        '<td style="padding:var(--space-2) var(--space-2);text-align:center;">' + statusLabel + '</td>' +
                        '</tr>';
                });

                html += '<tr style="border-top:2px solid var(--text);background:var(--wash);font-weight:700;">' +
                    '<td style="padding:var(--space-2) var(--space-3);" colspan="2">TOTAL</td>' +
                    '<td style="padding:var(--space-2) var(--space-3);text-align:right;">' + fmtGBP(totalNotional) + '</td>' +
                    '<td style="padding:var(--space-2) var(--space-3);text-align:right;color:' + pnlColor(totalMtm) + ';">' +
                        fmtGBP(totalMtm) + '</td>' +
                    '<td style="padding:var(--space-2) var(--space-3);text-align:right;color:' + pnlColor(totalCash) + ';">' +
                        fmtGBP(totalCash) + '</td>' +
                    '<td style="padding:var(--space-2) var(--space-3);text-align:right;color:' + pnlColor(totalStress) + ';">' +
                        fmtGBP(totalStress) + '</td>' +
                    '<td style="padding:var(--space-2) var(--space-2);text-align:center;font-size:var(--size-xxs);color:var(--red-dark);">' +
                        (numTriggered > 0 ? numTriggered + '/' + trades.length : '') + '</td>' +
                    '</tr>';

                html += '</tbody></table>';

                var headerHtml = '<div style="padding:var(--space-2) 0 var(--space-4) 0;font-size:var(--size-xxs);color:var(--text-3);">' +
                    '<b>Values at peak P(flood) \u2014 Hour ' + peakHour + '</b>' +
                    ' | Water: ' + (peakData.water_level || 0).toFixed(2) + 'm' +
                    ' | P(flood): ' + ((peakData.p_flood || 0) * 100).toFixed(1) + '%' +
                    '</div>';

                wrap.innerHTML = headerHtml + html;
            }

            function _renderStressStats(data) {
                var bar = document.getElementById('hazard-stats-bar');
                if (!bar) return;

                var s = data.summary || {};
                var fmtGBP = function(v) {
                    var abs = Math.abs(v);
                    var str = abs >= 1e6 ? (abs/1e6).toFixed(1) + 'M' :
                              abs >= 1e3 ? (abs/1e3).toFixed(1) + 'K' :
                              abs.toFixed(0);
                    var cc = (window.__BACKEND_CONFIG || {}).currency || 'GBP';
                    var sym = {GBP: '\u00A3', USD: '$', EUR: '\u20AC'}[cc] || (cc + ' ');
                    return (v < 0 ? '-' : '+') + sym + str;
                };
                var pnlColor = function(v) { return v >= 0 ? 'var(--green-dark)' : 'var(--red-dark)'; };

                var koText = s.num_triggered > 0 ?
                    '<span style="font-weight:700;color:var(--red-dark);"><b>Knocked Out:</b> ' +
                        s.num_triggered + '/' + s.num_trades + ' @ hr ' + s.first_trigger_hour + '</span>' :
                    '<span style="color:var(--green-dark);"><b>No knock-outs</b></span>';

                bar.innerHTML = [
                    '<span><b>MTM:</b> <span style="color:' + pnlColor(s.total_mtm) + ';">' +
                        fmtGBP(s.total_mtm) + '</span></span>',
                    '<span style="color:var(--amber-deep);"><b>Peak P:</b> ' +
                        (s.peak_p_flood * 100).toFixed(1) + '% @ hr ' + s.peak_p_flood_hour + '</span>',
                    koText,
                    '<span style="font-weight:700;color:' + pnlColor(s.max_stress_pnl) + ';">' +
                        '<b>Max Stress P&L:</b> ' + fmtGBP(s.max_stress_pnl) +
                        ' @ hr ' + s.max_stress_hour + '</span>'
                ].join('');
            }

            function _cleanupStressCharts() {
                if (_stressChart) { _stressChart.destroy(); _stressChart = null; }
            }
