
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
                var pnlColor = function(v) { return v >= 0 ? '#2e7d32' : '#c62828'; };

                var html = '<table style="width:100%;border-collapse:collapse;font-size:10px;">' +
                    '<thead><tr style="background:#f5f5f5;border-bottom:2px solid #ddd;">' +
                    '<th style="padding:4px 6px;text-align:left;">Swap</th>' +
                    '<th style="padding:4px 4px;text-align:center;">Dir</th>' +
                    '<th style="padding:4px 6px;text-align:right;">Notional</th>' +
                    '<th style="padding:4px 6px;text-align:right;">MTM</th>' +
                    '<th style="padding:4px 6px;text-align:right;">Cash Price</th>' +
                    '<th style="padding:4px 6px;text-align:right;">Stress P&L</th>' +
                    '<th style="padding:4px 4px;text-align:center;">Status</th>' +
                    '</tr></thead><tbody>';

                var totalNotional = 0, totalMtm = 0, totalCash = 0, totalStress = 0;
                var numTriggered = 0;

                trades.forEach(function(t) {
                    var pt = ptMap[t.swap_id] || {};
                    var cashPrice = pt.cash_price || 0;
                    var stressPnl = pt.stress_pnl || 0;
                    var dir = t.is_payer ? 'Pay' : 'Rcv';
                    var dirColor = t.is_payer ? '#c62828' : '#2e7d32';
                    var isTriggered = t.triggered_hour != null;
                    if (isTriggered) numTriggered++;
                    var statusLabel = isTriggered ?
                        '<span style="background:#c62828;color:#fff;padding:1px 4px;border-radius:2px;font-size:8px;font-weight:700;">KO H' + t.triggered_hour + '</span>' :
                        '<span style="color:#999;font-size:8px;">Live</span>';

                    totalNotional += t.notional;
                    totalMtm += t.mtm;
                    totalCash += cashPrice;
                    totalStress += stressPnl;

                    html += '<tr style="border-bottom:1px solid #f0f0f0;' +
                            (isTriggered ? 'background:#fff5f5;' : '') + '">' +
                        '<td style="padding:3px 6px;font-family:monospace;font-size:9px;">' +
                            t.swap_id.substring(0, 12) + '</td>' +
                        '<td style="padding:3px 4px;text-align:center;color:' + dirColor + ';font-weight:600;">' +
                            dir + '</td>' +
                        '<td style="padding:3px 6px;text-align:right;">' + fmtGBP(t.notional) + '</td>' +
                        '<td style="padding:3px 6px;text-align:right;color:' + pnlColor(t.mtm) + ';">' +
                            fmtGBP(t.mtm) + '</td>' +
                        '<td style="padding:3px 6px;text-align:right;color:' + pnlColor(cashPrice) + ';">' +
                            fmtGBP(cashPrice) + '</td>' +
                        '<td style="padding:3px 6px;text-align:right;font-weight:700;color:' +
                            pnlColor(stressPnl) + ';">' + fmtGBP(stressPnl) + '</td>' +
                        '<td style="padding:3px 4px;text-align:center;">' + statusLabel + '</td>' +
                        '</tr>';
                });

                html += '<tr style="border-top:2px solid #333;background:#f8f9fa;font-weight:700;">' +
                    '<td style="padding:4px 6px;" colspan="2">TOTAL</td>' +
                    '<td style="padding:4px 6px;text-align:right;">' + fmtGBP(totalNotional) + '</td>' +
                    '<td style="padding:4px 6px;text-align:right;color:' + pnlColor(totalMtm) + ';">' +
                        fmtGBP(totalMtm) + '</td>' +
                    '<td style="padding:4px 6px;text-align:right;color:' + pnlColor(totalCash) + ';">' +
                        fmtGBP(totalCash) + '</td>' +
                    '<td style="padding:4px 6px;text-align:right;color:' + pnlColor(totalStress) + ';">' +
                        fmtGBP(totalStress) + '</td>' +
                    '<td style="padding:4px 4px;text-align:center;font-size:9px;color:#c62828;">' +
                        (numTriggered > 0 ? numTriggered + '/' + trades.length : '') + '</td>' +
                    '</tr>';

                html += '</tbody></table>';

                var headerHtml = '<div style="padding:4px 0 8px 0;font-size:10px;color:#666;">' +
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
                var pnlColor = function(v) { return v >= 0 ? '#2e7d32' : '#c62828'; };

                var koText = s.num_triggered > 0 ?
                    '<span style="font-weight:700;color:#c62828;"><b>Knocked Out:</b> ' +
                        s.num_triggered + '/' + s.num_trades + ' @ hr ' + s.first_trigger_hour + '</span>' :
                    '<span style="color:#2e7d32;"><b>No knock-outs</b></span>';

                bar.innerHTML = [
                    '<span><b>MTM:</b> <span style="color:' + pnlColor(s.total_mtm) + ';">' +
                        fmtGBP(s.total_mtm) + '</span></span>',
                    '<span style="color:#e65100;"><b>Peak P:</b> ' +
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
