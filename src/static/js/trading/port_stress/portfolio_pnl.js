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

            function _psRenderPortPnlTab(result) {
                var content = document.getElementById('ps-content');
                if (!content) return;

                var totalPnl = result.portfolio_stress_pnl || 0;
                var totalMtm = result.portfolio_mtm || 0;
                var pnlColor = totalPnl >= 0 ? Theme.value('gain') : Theme.value('loss');
                var mtmColor = totalMtm >= 0 ? Theme.value('gain') : Theme.value('loss');

                var headerHtml =
                    '<div style="padding:var(--space-6) var(--space-8);border-bottom:1px solid var(--line-soft);background:var(--header-from);flex-shrink:0;">' +
                    '<div style="display:flex;align-items:baseline;gap:var(--space-10);flex-wrap:wrap;">' +
                    '<div>' +
                    '<span style="font-size:var(--size-xs);color:var(--text-3);">Portfolio Stress P&amp;L</span><br>' +
                    '<span style="font-size:22px;font-weight:700;color:' + pnlColor + ';">' + fmtGBP(totalPnl) + '</span>' +
                    '</div>' +
                    '<div>' +
                    '<span style="font-size:var(--size-xs);color:var(--text-3);">vs MTM</span><br>' +
                    '<span style="font-size:var(--size-lg);font-weight:600;color:' + mtmColor + ';">' + fmtGBP(totalMtm) + '</span>' +
                    '</div>' +
                    '<div>' +
                    '<span style="font-size:var(--size-xs);color:var(--text-3);">Move vs MTM</span><br>' +
                    '<span style="font-size:var(--size-lg);font-weight:600;color:' + (totalPnl - totalMtm >= 0 ? 'var(--green-dark)' : 'var(--red-dark)') + ';">' +
                    fmtGBP(totalPnl - totalMtm) + '</span>' +
                    '</div>' +
                    '</div>' +
                    '</div>';

                var chartAreaHtml =
                    '<div style="flex:1;padding:var(--space-4);overflow:hidden;display:flex;flex-direction:column;">' +
                    '<div style="flex:1;position:relative;min-height:0;">' +
                    '<canvas id="ps-portpnl-canvas" style="width:100%;height:100%;"></canvas>' +
                    '</div></div>';

                content.innerHTML = headerHtml + chartAreaHtml;

                var ctx = document.getElementById('ps-portpnl-canvas');
                if (!ctx) return;
                if (psPortPnlChart) { psPortPnlChart.destroy(); psPortPnlChart = null; }

                // Only gauges with trades, sorted by stress_pnl ascending (most negative first)
                var gaugesWithTrades = (result.gauges || []).filter(function(g) {
                    return g.num_trades > 0;
                });
                gaugesWithTrades.sort(function(a, b) { return a.stress_pnl - b.stress_pnl; });

                var labels = gaugesWithTrades.map(function(g) {
                    var name = g.gauge_name || g.gauge_id;
                    return name.length > 20 ? name.substring(0, 18) + '…' : name;
                });
                var data = gaugesWithTrades.map(function(g) { return g.stress_pnl; });
                var bgColors = gaugesWithTrades.map(function(g) {
                    return g.stress_pnl >= 0 ? Theme.value('gain') : Theme.value('loss');
                });
                var bgAlpha = gaugesWithTrades.map(function(g) {
                    return g.stress_pnl >= 0 ? Theme.value('gain-fill') : Theme.value('loss-fill');
                });

                psPortPnlChart = new Chart(ctx.getContext('2d'), {
                    type: 'bar',
                    data: {
                        labels: labels,
                        datasets: [{
                            label: 'Stress P&L (£)',
                            data: data,
                            backgroundColor: bgAlpha,
                            borderColor: bgColors,
                            borderWidth: 1,
                        }]
                    },
                    options: {
                        indexAxis: 'y',
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { display: false },
                            tooltip: {
                                callbacks: {
                                    label: function(ctx) {
                                        var g = gaugesWithTrades[ctx.dataIndex];
                                        return [
                                            'Stress P&L: ' + fmtGBP(ctx.parsed.x),
                                            'MTM: ' + fmtGBP(g.mtm),
                                            'Trades: ' + g.num_trades,
                                            'Threshold: ' + g.threshold.toUpperCase()
                                        ];
                                    }
                                }
                            }
                        },
                        scales: {
                            x: {
                                title: { display: true, text: 'Stress P&L (£)', font: { size: 10 } },
                                ticks: {
                                    font: { size: 9 },
                                    callback: function(v) {
                                        var abs = Math.abs(v);
                                        var s = abs >= 1e6 ? (abs / 1e6).toFixed(1) + 'M' :
                                                abs >= 1e3 ? (abs / 1e3).toFixed(0) + 'K' :
                                                abs.toFixed(0);
                                        return (v < 0 ? '-' : '') + '£' + s;
                                    }
                                }
                            },
                            y: {
                                ticks: { font: { size: 9 } }
                            }
                        }
                    }
                });
            }
