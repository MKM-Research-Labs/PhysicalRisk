# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial 
# research and educational use only. Any commercial use, including 
# but not limited to use in or for products or services offered for sale, 
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
EOD (End of Day) — render sub-module.

P&L summary cards, history table, daily P&L chart, and attribution panel.
"""


def get_js() -> str:
    """Return JavaScript fragment for EOD rendering functions."""
    return """
            function renderEodCards() {
                var cards = document.getElementById('td-eod-cards');
                if (!cards) return;

                // Use most recent EOD or show empty
                var latest = tdEodHistory && tdEodHistory.length > 0 ? tdEodHistory[0] : null;

                if (!latest) {
                    cards.innerHTML = '<span style="font-size:12px;color:#aaa;">No EOD snapshots yet. Click EOD Submit to generate.</span>';
                    return;
                }

                function card(label, value, color) {
                    return '<div style="background:#f5f5f5;border-radius:6px;padding:8px 16px;min-width:120px;text-align:center;">' +
                        '<div style="font-size:9px;color:#888;text-transform:uppercase;">' + label + '</div>' +
                        '<div style="font-size:16px;font-weight:700;color:' + (color || '#333') + ';">' + value + '</div>' +
                    '</div>';
                }

                // Use live blotter summary for current P&L (reflects curve changes)
                var live = tdLiveSummary || {};
                var dailyPnl = live.total_daily_pnl != null ? live.total_daily_pnl : latest.total_daily_pnl;
                var runPnl = live.total_running_pnl != null ? live.total_running_pnl : latest.total_running_pnl;
                var dailyColor = dailyPnl >= 0 ? '#2e7d32' : '#c62828';
                var runColor = runPnl >= 0 ? '#2e7d32' : '#c62828';

                cards.innerHTML =
                    card('Last EOD', latest.date || '\\u2014') +
                    card('Trades', live.num_trades || latest.num_open_trades || 0) +
                    card('Notional', fmtGBP(live.total_notional || latest.total_notional)) +
                    card('Daily P&L', fmtGBP(dailyPnl), dailyColor) +
                    card('Running P&L', fmtGBP(runPnl), runColor);
            }

            function renderEodHistory() {
                var wrap = document.getElementById('td-eod-history-wrap');
                if (!wrap) return;

                var html = '<div style="font-size:11px;font-weight:600;color:#555;padding:4px 8px;margin-bottom:4px;">EOD History (' + (tdEodHistory ? tdEodHistory.length : 0) + ' days)</div>';

                if (!tdEodHistory || tdEodHistory.length === 0) {
                    html += '<div style="color:#aaa;font-size:11px;padding:8px;">No snapshots yet.</div>';
                    wrap.innerHTML = html;
                    return;
                }

                html += '<table style="width:100%;border-collapse:collapse;font-size:10px;">';
                html += '<tr style="background:#eceff1;">' +
                    '<th style="padding:4px 6px;text-align:left;">Date</th>' +
                    '<th style="padding:4px 6px;text-align:right;">Trades</th>' +
                    '<th style="padding:4px 6px;text-align:right;">Daily P&L</th>' +
                    '<th style="padding:4px 6px;text-align:right;">Running</th>' +
                    '<th style="padding:4px 4px;text-align:center;">PDF</th></tr>';

                for (var i = 0; i < tdEodHistory.length; i++) {
                    var e = tdEodHistory[i];
                    var dColor = e.total_daily_pnl >= 0 ? '#2e7d32' : '#c62828';
                    var rColor = e.total_running_pnl >= 0 ? '#2e7d32' : '#c62828';
                    var bg = i % 2 === 0 ? '#fff' : '#f8f9fa';

                    var pdfBtn = '';
                    if (e.has_pdf) {
                        pdfBtn = '<button onclick="event.stopPropagation();tdDownloadEodPdf(\\'' + e.date + '\\')" ' +
                            'style="padding:1px 4px;font-size:9px;background:none;border:1px solid #90a4ae;border-radius:3px;cursor:pointer;color:#546e7a;" ' +
                            'title="Download EOD PDF">\\u2193</button>';
                    }

                    html += '<tr style="background:' + bg + ';border-bottom:1px solid #eee;">' +
                        '<td style="padding:4px 6px;">' + e.date + '</td>' +
                        '<td style="padding:4px 6px;text-align:right;">' + e.num_open_trades + '</td>' +
                        '<td style="padding:4px 6px;text-align:right;color:' + dColor + ';">' + fmtGBP(e.total_daily_pnl) + '</td>' +
                        '<td style="padding:4px 6px;text-align:right;color:' + rColor + ';">' + fmtGBP(e.total_running_pnl) + '</td>' +
                        '<td style="padding:4px 4px;text-align:center;">' + pdfBtn + '</td>' +
                    '</tr>';
                }

                html += '</table>';
                wrap.innerHTML = html;
            }

            function renderEodChart() {
                var wrap = document.getElementById('td-eod-chart-wrap');
                if (!wrap) return;

                if (!tdEodPnlSeries || tdEodPnlSeries.length === 0) {
                    wrap.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:100%;color:#aaa;font-size:12px;">P&L chart will appear after EOD submissions.</div>';
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
                var dailyColors = dailyPnl.map(function(v) { return v >= 0 ? 'rgba(46,125,50,0.8)' : 'rgba(198,40,40,0.8)'; });

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
                                grid: {color: '#eee'},
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
                var html = '<div style="display:flex;gap:16px;font-size:10px;">';

                // P&L Attribution breakdown
                html += '<div style="flex:1;">';
                html += '<div style="font-weight:700;color:#555;margin-bottom:6px;font-size:11px;">P&L Attribution</div>';
                html += '<table style="width:100%;border-collapse:collapse;">';

                var fromTrades = live.daily_pnl_from_trades || 0;
                var fromMarket = live.daily_pnl_from_market || 0;
                var totalDaily = live.total_daily_pnl || 0;

                function attrRow(label, val) {
                    var c = val >= 0 ? '#2e7d32' : '#c62828';
                    return '<tr style="border-bottom:1px solid #f0f0f0;">' +
                        '<td style="padding:3px 6px;color:#666;">' + label + '</td>' +
                        '<td style="padding:3px 6px;text-align:right;font-weight:600;color:' + c + ';">' + fmtGBP(val) + '</td></tr>';
                }

                html += attrRow('New Trades', fromTrades);
                html += attrRow('Market Moves', fromMarket);
                html += '<tr style="border-top:2px solid #1565c0;font-weight:700;">' +
                    '<td style="padding:3px 6px;">Total Daily</td>' +
                    '<td style="padding:3px 6px;text-align:right;color:' + (totalDaily >= 0 ? '#2e7d32' : '#c62828') + ';">' + fmtGBP(totalDaily) + '</td></tr>';
                html += '</table></div>';

                // Top trades by running P&L (use blotter-loaded data if available)
                html += '<div style="flex:1;">';
                html += '<div style="font-weight:700;color:#555;margin-bottom:6px;font-size:11px;">Top Trades (Running P&L)</div>';

                if (tdBlotterData && tdBlotterData.length > 0) {
                    var sorted = tdBlotterData.slice().sort(function(a, b) {
                        return Math.abs(b.running_pnl || b.mtm || 0) - Math.abs(a.running_pnl || a.mtm || 0);
                    });
                    var top5 = sorted.slice(0, 5);
                    html += '<table style="width:100%;border-collapse:collapse;">';
                    html += '<tr style="color:#999;"><td style="padding:2px 4px;">Trade</td><td style="padding:2px 4px;">Gauge</td><td style="padding:2px 4px;text-align:right;">P&L</td></tr>';
                    for (var ti = 0; ti < top5.length; ti++) {
                        var tt = top5[ti];
                        var pnl = tt.running_pnl || tt.mtm || 0;
                        var tc = pnl >= 0 ? '#2e7d32' : '#c62828';
                        var shortId = (tt.swap_id || '').slice(-8);
                        var gName = tt.gauge_name || tt.gauge_id || '';
                        html += '<tr style="border-bottom:1px solid #f0f0f0;">' +
                            '<td style="padding:2px 4px;color:#1565c0;font-family:monospace;">' + shortId + '</td>' +
                            '<td style="padding:2px 4px;color:#666;">' + gName + '</td>' +
                            '<td style="padding:2px 4px;text-align:right;font-weight:600;color:' + tc + ';">' + fmtGBP(pnl) + '</td></tr>';
                    }
                    html += '</table>';
                } else {
                    html += '<span style="color:#aaa;">Load blotter tab for trade data</span>';
                }
                html += '</div>';
                html += '</div>';

                wrap.innerHTML = html;
            }
"""
