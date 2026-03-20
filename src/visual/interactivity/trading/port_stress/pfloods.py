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

"""Port Stress — P(flood) sub-tab."""


def get_js() -> str:
    """Return JavaScript fragment for the P(flood) sub-tab."""
    return """
            // ---- Port Stress: P(flood) Sub-Tab ----
            function _psRenderPFloodTab(result) {
                var content = document.getElementById('ps-content');
                if (!content) return;

                var gauges = result.gauges || [];

                // Build gauge dropdown options (all gauges; "impacted" ones marked)
                var impactedGauges = gauges.filter(function(g) {
                    return g.p_flood_pct > 0 || g.impacted;
                });

                var dropdownHtml =
                    '<div style="padding:8px 12px;border-bottom:1px solid #eee;display:flex;align-items:center;gap:10px;background:#f5f7fa;flex-shrink:0;">' +
                    '<span style="font-size:11px;font-weight:600;color:#333;">View:</span>' +
                    '<select id="ps-pflood-gauge-sel" style="padding:4px 8px;font-size:11px;border:1px solid #ccc;border-radius:3px;min-width:260px;">' +
                    '<option value="">All Gauges (Portfolio Chart)</option>';

                impactedGauges.forEach(function(g) {
                    var badge = g.threshold === 'severe' ? ' [SEVERE]' :
                                g.threshold === 'warning' ? ' [WARN]' :
                                g.threshold === 'alert' ? ' [ALERT]' : '';
                    dropdownHtml += '<option value="' + g.gauge_id + '">' +
                        g.gauge_name + badge + ' \u2014 P=' + g.p_flood_pct.toFixed(1) + '%' +
                        '</option>';
                });
                dropdownHtml += '</select></div>';

                var chartAreaHtml =
                    '<div id="ps-pflood-chart-area" style="flex:1;display:flex;flex-direction:column;overflow:hidden;padding:8px;">' +
                    '<div style="flex:1;position:relative;min-height:0;">' +
                    '<canvas id="ps-pflood-canvas" style="width:100%;height:100%;"></canvas>' +
                    '</div></div>';

                content.innerHTML = dropdownHtml + chartAreaHtml;

                // Bind dropdown change
                var sel = document.getElementById('ps-pflood-gauge-sel');
                if (sel) {
                    sel.onchange = function() {
                        if (this.value) {
                            _psRenderSingleGaugeCard(result, this.value);
                        } else {
                            _psDrawPFloodChart(result);
                        }
                    };
                }

                // Default: show portfolio bar chart
                _psDrawPFloodChart(result);
            }

            function _psDrawPFloodChart(result) {
                var chartArea = document.getElementById('ps-pflood-chart-area');
                if (chartArea) {
                    chartArea.innerHTML =
                        '<div style="flex:1;position:relative;min-height:0;">' +
                        '<canvas id="ps-pflood-canvas" style="width:100%;height:100%;"></canvas>' +
                        '</div>';
                }

                var ctx = document.getElementById('ps-pflood-canvas');
                if (!ctx) return;
                if (psPFloodChart) { psPFloodChart.destroy(); psPFloodChart = null; }

                var gauges = (result.gauges || []).slice();
                // Sort west to east by longitude for geographic ordering
                gauges.sort(function(a, b) { return a.lon - b.lon; });

                var labels = gauges.map(function(g) {
                    var name = g.gauge_name || g.gauge_id;
                    // Shorten long names
                    return name.length > 16 ? name.substring(0, 14) + '\u2026' : name;
                });

                var data = gauges.map(function(g) { return g.p_flood_pct; });

                var bgColors = gauges.map(function(g) {
                    if (g.threshold === 'severe') return '#c62828';
                    if (g.threshold === 'warning') return '#e65100';
                    if (g.threshold === 'alert') return '#f9a825';
                    return '#bdbdbd';
                });

                psPFloodChart = new Chart(ctx.getContext('2d'), {
                    type: 'bar',
                    data: {
                        labels: labels,
                        datasets: [{
                            label: 'P(flood) %',
                            data: data,
                            backgroundColor: bgColors,
                            borderWidth: 0,
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { display: false },
                            tooltip: {
                                callbacks: {
                                    label: function(ctx) {
                                        var g = gauges[ctx.dataIndex];
                                        return [
                                            'P(flood): ' + ctx.parsed.y.toFixed(1) + '%',
                                            'Threshold: ' + g.threshold.toUpperCase(),
                                            'Peak level: ' + g.peak_water_level_m.toFixed(2) + 'm'
                                        ];
                                    }
                                }
                            }
                        },
                        scales: {
                            x: {
                                ticks: { font: { size: 9 }, maxRotation: 45 },
                                title: { display: true, text: 'Gauge (west \u2192 east)', font: { size: 10 } }
                            },
                            y: {
                                min: 0, max: 100,
                                title: { display: true, text: 'P(flood) %', font: { size: 10 } },
                                ticks: {
                                    font: { size: 9 },
                                    callback: function(v) { return v + '%'; }
                                }
                            }
                        }
                    }
                });
            }

            function _psRenderSingleGaugeCard(result, gaugeId) {
                var chartArea = document.getElementById('ps-pflood-chart-area');
                if (!chartArea) return;

                if (psPFloodChart) { psPFloodChart.destroy(); psPFloodChart = null; }

                var g = (result.gauges || []).find(function(x) { return x.gauge_id === gaugeId; });
                if (!g) {
                    chartArea.innerHTML = '<div style="padding:40px;color:#999;text-align:center;">Gauge not found</div>';
                    return;
                }

                var thresholdColor = g.threshold === 'severe' ? '#c62828' :
                                     g.threshold === 'warning' ? '#e65100' :
                                     g.threshold === 'alert' ? '#f9a825' : '#757575';
                var thresholdBg = g.threshold === 'severe' ? '#ffebee' :
                                  g.threshold === 'warning' ? '#fff3e0' :
                                  g.threshold === 'alert' ? '#fffde7' : '#f5f5f5';

                var tradesHtml = '';
                if (g.trades && g.trades.length > 0) {
                    tradesHtml =
                        '<table style="width:100%;border-collapse:collapse;font-size:10px;margin-top:12px;">' +
                        '<thead><tr style="background:#f5f5f5;border-bottom:2px solid #ddd;">' +
                        '<th style="padding:4px 6px;text-align:left;">Swap</th>' +
                        '<th style="padding:4px 4px;text-align:center;">Dir</th>' +
                        '<th style="padding:4px 6px;text-align:right;">Notional</th>' +
                        '<th style="padding:4px 6px;text-align:right;">MTM</th>' +
                        '<th style="padding:4px 6px;text-align:right;">Cash Price</th>' +
                        '<th style="padding:4px 6px;text-align:right;">Stress P&amp;L</th>' +
                        '</tr></thead><tbody>';
                    g.trades.forEach(function(t) {
                        var dirColor = t.is_payer ? '#c62828' : '#2e7d32';
                        var pnlColor = t.stress_pnl >= 0 ? '#2e7d32' : '#c62828';
                        tradesHtml +=
                            '<tr style="border-bottom:1px solid #f0f0f0;">' +
                            '<td style="padding:3px 6px;font-family:monospace;font-size:9px;">' + t.swap_id.substring(0, 12) + '</td>' +
                            '<td style="padding:3px 4px;text-align:center;color:' + dirColor + ';font-weight:600;">' + (t.is_payer ? 'Pay' : 'Rcv') + '</td>' +
                            '<td style="padding:3px 6px;text-align:right;">' + fmtGBP(t.notional) + '</td>' +
                            '<td style="padding:3px 6px;text-align:right;">' + fmtGBP(t.mtm) + '</td>' +
                            '<td style="padding:3px 6px;text-align:right;">' + fmtGBP(t.cash_price) + '</td>' +
                            '<td style="padding:3px 6px;text-align:right;font-weight:700;color:' + pnlColor + ';">' + fmtGBP(t.stress_pnl) + '</td>' +
                            '</tr>';
                    });
                    tradesHtml += '</tbody></table>';
                } else {
                    tradesHtml = '<div style="padding:16px 0;color:#999;font-size:11px;">No open trades at this gauge.</div>';
                }

                chartArea.innerHTML =
                    '<div style="padding:16px;overflow-y:auto;height:100%;">' +
                    '<div style="display:flex;align-items:center;gap:16px;margin-bottom:16px;">' +
                    '<div style="font-size:16px;font-weight:700;color:#333;">' + g.gauge_name + '</div>' +
                    '<span style="background:' + thresholdBg + ';color:' + thresholdColor + ';border:1px solid ' + thresholdColor + ';' +
                    'padding:2px 10px;border-radius:10px;font-size:11px;font-weight:700;">' + g.threshold.toUpperCase() + '</span>' +
                    '</div>' +
                    '<div style="display:flex;gap:24px;flex-wrap:wrap;margin-bottom:12px;">' +
                    '<div style="text-align:center;">' +
                    '<div style="font-size:28px;font-weight:700;color:' + thresholdColor + ';">' + g.p_flood_pct.toFixed(1) + '%</div>' +
                    '<div style="font-size:10px;color:#666;">P(flood)</div>' +
                    '</div>' +
                    '<div style="text-align:center;">' +
                    '<div style="font-size:22px;font-weight:700;color:#333;">' + g.peak_water_level_m.toFixed(2) + 'm</div>' +
                    '<div style="font-size:10px;color:#666;">Peak Water Level</div>' +
                    '</div>' +
                    '<div style="text-align:center;">' +
                    '<div style="font-size:22px;font-weight:700;color:' + (g.stress_pnl < 0 ? '#c62828' : '#2e7d32') + ';">' + fmtGBP(g.stress_pnl) + '</div>' +
                    '<div style="font-size:10px;color:#666;">Stress P&amp;L</div>' +
                    '</div>' +
                    '<div style="text-align:center;">' +
                    '<div style="font-size:22px;font-weight:700;color:#333;">' + g.num_trades + '</div>' +
                    '<div style="font-size:10px;color:#666;">Open Trades</div>' +
                    '</div>' +
                    '</div>' +
                    '<div style="font-size:10px;color:#666;margin-bottom:8px;">' +
                    'Alert: ' + g.alert_level.toFixed(2) + 'm &nbsp;|&nbsp; ' +
                    'Warning: ' + g.warning_level.toFixed(2) + 'm &nbsp;|&nbsp; ' +
                    'Severe: ' + g.severe_level.toFixed(2) + 'm' +
                    '</div>' +
                    tradesHtml +
                    '</div>';
            }
"""
