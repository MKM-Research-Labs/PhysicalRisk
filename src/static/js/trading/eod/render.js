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

            function renderEodCards() {
                var cards = document.getElementById('td-eod-cards');
                if (!cards) return;

                // Use most recent EOD or show empty
                var latest = tdEodHistory && tdEodHistory.length > 0 ? tdEodHistory[0] : null;

                if (!latest) {
                    cards.innerHTML = '<span style="font-size:var(--size-sm);color:var(--disabled);">No EOD snapshots yet. Click EOD Submit to generate.</span>';
                    return;
                }

                function card(label, value, color) {
                    return '<div style="background:var(--sunken);border-radius:var(--radius-md);padding:var(--space-4) var(--space-8);min-width:120px;text-align:center;">' +
                        '<div style="font-size:var(--size-xxs);color:var(--muted);text-transform:uppercase;">' + label + '</div>' +
                        '<div style="font-size:var(--size-lg);font-weight:700;color:' + (color || 'var(--text)') + ';">' + value + '</div>' +
                    '</div>';
                }

                // Use live blotter summary for current P&L (reflects curve changes)
                var live = tdLiveSummary || {};
                var dailyPnl = live.total_daily_pnl != null ? live.total_daily_pnl : latest.total_daily_pnl;
                var runPnl = live.total_running_pnl != null ? live.total_running_pnl : latest.total_running_pnl;
                var dailyColor = dailyPnl >= 0 ? Theme.value('gain') : Theme.value('loss');
                var runColor = runPnl >= 0 ? Theme.value('gain') : Theme.value('loss');

                cards.innerHTML =
                    card('Last EOD', latest.date || '\u2014') +
                    card('Trades', live.num_trades || latest.num_open_trades || 0) +
                    card('Notional', fmtGBP(live.total_notional || latest.total_notional)) +
                    card('Daily P&L', fmtGBP(dailyPnl), dailyColor) +
                    card('Running P&L', fmtGBP(runPnl), runColor);
            }

            function renderEodHistory() {
                var wrap = document.getElementById('td-eod-history-wrap');
                if (!wrap) return;

                var html = '<div style="font-size:var(--size-xs);font-weight:600;color:var(--text-2);padding:var(--space-2) var(--space-4);margin-bottom:var(--space-2);">EOD History (' + (tdEodHistory ? tdEodHistory.length : 0) + ' days)</div>';

                if (!tdEodHistory || tdEodHistory.length === 0) {
                    html += '<div style="color:var(--disabled);font-size:var(--size-xs);padding:var(--space-4);">No snapshots yet.</div>';
                    wrap.innerHTML = html;
                    return;
                }

                html += '<table style="width:100%;border-collapse:collapse;font-size:var(--size-xxs);">';
                html += '<tr style="background:var(--blue-grey-bg);">' +
                    '<th style="padding:var(--space-2) var(--space-3);text-align:left;">Date</th>' +
                    '<th style="padding:var(--space-2) var(--space-3);text-align:right;">Trades</th>' +
                    '<th style="padding:var(--space-2) var(--space-3);text-align:right;">Daily P&L</th>' +
                    '<th style="padding:var(--space-2) var(--space-3);text-align:right;">Running</th>' +
                    '<th style="padding:var(--space-2) var(--space-2);text-align:center;">PDF</th></tr>';

                for (var i = 0; i < tdEodHistory.length; i++) {
                    var e = tdEodHistory[i];
                    var dColor = e.total_daily_pnl >= 0 ? Theme.value('gain') : Theme.value('loss');
                    var rColor = e.total_running_pnl >= 0 ? Theme.value('gain') : Theme.value('loss');
                    var bg = i % 2 === 0 ? Theme.value('panel') : Theme.value('wash');

                    var pdfBtn = '';
                    if (e.has_pdf) {
                        pdfBtn = '<button onclick="event.stopPropagation();tdDownloadEodPdf(\'' + e.date + '\')" ' +
                            'style="padding:var(--space-hair) var(--space-2);font-size:var(--size-xxs);background:none;border:1px solid var(--blue-grey-pale);border-radius:var(--radius-sm);cursor:pointer;color:var(--blue-grey-dark);" ' +
                            'title="Download EOD PDF">\u2193</button>';
                    }

                    html += '<tr style="background:' + bg + ';border-bottom:1px solid var(--line-soft);">' +
                        '<td style="padding:var(--space-2) var(--space-3);">' + e.date + '</td>' +
                        '<td style="padding:var(--space-2) var(--space-3);text-align:right;">' + e.num_open_trades + '</td>' +
                        '<td style="padding:var(--space-2) var(--space-3);text-align:right;color:' + dColor + ';">' + fmtGBP(e.total_daily_pnl) + '</td>' +
                        '<td style="padding:var(--space-2) var(--space-3);text-align:right;color:' + rColor + ';">' + fmtGBP(e.total_running_pnl) + '</td>' +
                        '<td style="padding:var(--space-2) var(--space-2);text-align:center;">' + pdfBtn + '</td>' +
                    '</tr>';
                }

                html += '</table>';
                wrap.innerHTML = html;
            }

            function renderEodChart() {
                var wrap = document.getElementById('td-eod-chart-wrap');
                if (!wrap) return;

                if (!tdEodPnlSeries || tdEodPnlSeries.length === 0) {
                    wrap.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:100%;color:var(--disabled);font-size:var(--size-sm);">P&L chart will appear after EOD submissions.</div>';
                    return;
                }

                wrap.innerHTML = '';
                var canvas = document.createElement('canvas');
                canvas.id = 'td-eod-chart';
                canvas.style.cssText = 'width:100%;height:100%;';
                wrap.appendChild(canvas);

                if (tdEodChart) {
                    tdEodChart.destroy();
                    tdEodChart = null;
                }

                var labels = tdEodPnlSeries.map(function(d) { return d.date; });
                var dailyPnl = tdEodPnlSeries.map(function(d) { return d.daily_pnl; });
                var dailyColors = dailyPnl.map(function(v) { return v >= 0 ? Theme.value('gain-fill') : Theme.value('loss-fill'); });

                tdEodChart = new Chart(canvas.getContext('2d'), {
                    type: 'bar',
                    data: {
                        labels: labels,
                        datasets: [{
                            label: 'Daily P&L',
                            data: dailyPnl,
                            backgroundColor: dailyColors,
                            borderWidth: 0,
                            borderRadius: 2
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            title: {display: true, text: 'Daily P&L', font: {size: 13}},
                            legend: {display: false},
                            tooltip: {
                                callbacks: {
                                    label: function(ctx) {
                                        var v = ctx.parsed.y;
                                        var sign = v >= 0 ? '+' : '';
                                        return sign + fmtGBP(v);
                                    }
                                }
                            }
                        },
                        scales: {
                            y: {
                                title: {display: true, text: 'GBP'},
                                grid: {color: Theme.value('line-soft')},
                                ticks: {
                                    callback: function(val) { return fmtGBP(val); }
                                }
                            },
                            x: {
                                grid: {display: false},
                                ticks: {maxTicksLimit: 15, font: {size: 9}}
                            }
                        }
                    }
                });
            }

            function renderEodAttribution() {
                var wrap = document.getElementById('td-eod-attribution');
                if (!wrap) return;

                var live = tdLiveSummary || {};
                var trades = (tdBlotterData || tdLiveSummary && tdLiveSummary._trades) || [];

                // If we have the blotter data from the parallel fetch, use it for top trades
                // The blotter data is loaded into tdBlotterData by the blotter tab; in EOD we use
                // the separate fetch result stored in tdLiveSummary
                var html = '<div style="display:flex;gap:var(--space-8);font-size:var(--size-xxs);">';

                // P&L Attribution breakdown
                html += '<div style="flex:1;">';
                html += '<div style="font-weight:700;color:var(--text-2);margin-bottom:var(--space-3);font-size:var(--size-xs);">P&L Attribution</div>';
                html += '<table style="width:100%;border-collapse:collapse;">';

                var fromTrades = live.daily_pnl_from_trades || 0;
                var fromMarket = live.daily_pnl_from_market || 0;
                var totalDaily = live.total_daily_pnl || 0;

                function attrRow(label, val) {
                    var c = val >= 0 ? Theme.value('gain') : Theme.value('loss');
                    return '<tr style="border-bottom:1px solid var(--code);">' +
                        '<td style="padding:var(--space-2) var(--space-3);color:var(--text-3);">' + label + '</td>' +
                        '<td style="padding:var(--space-2) var(--space-3);text-align:right;font-weight:600;color:' + c + ';">' + fmtGBP(val) + '</td></tr>';
                }

                html += attrRow('New Trades', fromTrades);
                html += attrRow('Market Moves', fromMarket);
                html += '<tr style="border-top:2px solid var(--accent-mid);font-weight:700;">' +
                    '<td style="padding:var(--space-2) var(--space-3);">Total Daily</td>' +
                    '<td style="padding:var(--space-2) var(--space-3);text-align:right;color:' + (totalDaily >= 0 ? 'var(--green-dark)' : 'var(--red-dark)') + ';">' + fmtGBP(totalDaily) + '</td></tr>';
                html += '</table></div>';

                // Top trades by running P&L (use blotter-loaded data if available)
                html += '<div style="flex:1;">';
                html += '<div style="font-weight:700;color:var(--text-2);margin-bottom:var(--space-3);font-size:var(--size-xs);">Top Trades (Running P&L)</div>';

                if (tdBlotterData && tdBlotterData.length > 0) {
                    var sorted = tdBlotterData.slice().sort(function(a, b) {
                        return Math.abs(b.running_pnl || b.mtm || 0) - Math.abs(a.running_pnl || a.mtm || 0);
                    });
                    var top5 = sorted.slice(0, 5);
                    html += '<table style="width:100%;border-collapse:collapse;">';
                    html += '<tr style="color:var(--muted-2);"><td style="padding:var(--space-1) var(--space-2);">Trade</td><td style="padding:var(--space-1) var(--space-2);">Gauge</td><td style="padding:var(--space-1) var(--space-2);text-align:right;">P&L</td></tr>';
                    for (var ti = 0; ti < top5.length; ti++) {
                        var tt = top5[ti];
                        var pnl = tt.running_pnl || tt.mtm || 0;
                        var tc = pnl >= 0 ? Theme.value('gain') : Theme.value('loss');
                        var shortId = (tt.swap_id || '').slice(-8);
                        var gName = tt.gauge_name || tt.gauge_id || '';
                        html += '<tr style="border-bottom:1px solid var(--code);">' +
                            '<td style="padding:var(--space-1) var(--space-2);color:var(--accent-mid);font-family:monospace;">' + shortId + '</td>' +
                            '<td style="padding:var(--space-1) var(--space-2);color:var(--text-3);">' + gName + '</td>' +
                            '<td style="padding:var(--space-1) var(--space-2);text-align:right;font-weight:600;color:' + tc + ';">' + fmtGBP(pnl) + '</td></tr>';
                    }
                    html += '</table>';
                } else {
                    html += '<span style="color:var(--disabled);">Load blotter tab for trade data</span>';
                }
                html += '</div>';
                html += '</div>';

                wrap.innerHTML = html;
            }
