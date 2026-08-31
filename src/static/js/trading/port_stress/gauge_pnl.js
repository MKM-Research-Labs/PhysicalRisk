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

            function _psRenderGaugePnlTab(result) {
                var content = document.getElementById('ps-content');
                if (!content) return;

                var gaugesWithTrades = (result.gauges || []).filter(function(g) {
                    return g.num_trades > 0;
                });

                if (gaugesWithTrades.length === 0) {
                    content.innerHTML =
                        '<div style="padding:var(--space-inset);text-align:center;color:var(--muted-2);">No open trades in portfolio for this storm.</div>';
                    return;
                }

                // Build dropdown
                var dropdownHtml =
                    '<div style="padding:var(--space-4) var(--space-6);border-bottom:1px solid var(--line-soft);display:flex;align-items:center;gap:var(--space-5);background:var(--header-from);flex-shrink:0;">' +
                    '<span style="font-size:var(--size-xs);font-weight:600;color:var(--text);">Gauge:</span>' +
                    '<select id="ps-gaugepnl-sel" style="padding:var(--space-2) var(--space-4);font-size:var(--size-xs);border:1px solid var(--divider);border-radius:var(--radius-sm);min-width:300px;">';

                gaugesWithTrades.forEach(function(g) {
                    var thresholdBadge = g.threshold !== 'clean' ? ' [' + g.threshold.toUpperCase() + ']' : '';
                    var selected = (g.gauge_id === psSelectedGaugeId) ? ' selected' : '';
                    dropdownHtml += '<option value="' + g.gauge_id + '"' + selected + '>' +
                        g.gauge_name + thresholdBadge +
                        ' — P=' + g.p_flood_pct.toFixed(1) + '%' +
                        ' | ' + g.num_trades + ' trade' + (g.num_trades !== 1 ? 's' : '') +
                        '</option>';
                });
                dropdownHtml +=
                    '</select>' +
                    '</div>';

                content.innerHTML = dropdownHtml;

                var sel = document.getElementById('ps-gaugepnl-sel');
                var tableArea = document.createElement('div');
                tableArea.id = 'ps-gauge-table-area';
                tableArea.style.cssText = 'flex:1;overflow-y:auto;padding:0;';
                content.appendChild(tableArea);

                function renderForGauge(gaugeId) {
                    var g = gaugesWithTrades.find(function(x) { return x.gauge_id === gaugeId; });
                    if (g) _psRenderGaugeTable(g, tableArea);
                }

                if (sel) {
                    sel.onchange = function() {
                        psSelectedGaugeId = this.value;
                        renderForGauge(this.value);
                    };
                    // Initial render: pre-selected or first
                    var initialId = psSelectedGaugeId && gaugesWithTrades.find(function(g) {
                        return g.gauge_id === psSelectedGaugeId;
                    }) ? psSelectedGaugeId : gaugesWithTrades[0].gauge_id;
                    sel.value = initialId;
                    renderForGauge(initialId);
                }
            }

            function _psRenderGaugeTable(gaugeData, container) {
                if (!container) container = document.getElementById('ps-gauge-table-area');
                if (!container) return;

                var thresholdColor = gaugeData.threshold === 'severe' ? Theme.value('red-dark') :
                                     gaugeData.threshold === 'warning' ? Theme.value('amber-deep') :
                                     gaugeData.threshold === 'alert' ? Theme.value('gold-deep') : Theme.value('text-4');
                var thresholdBg = gaugeData.threshold === 'severe' ? Theme.value('danger-bg-soft') :
                                  gaugeData.threshold === 'warning' ? Theme.value('warn-bg-warm') :
                                  gaugeData.threshold === 'alert' ? 'var(--warn-bg)' : Theme.value('sunken');
                var pnlColor = gaugeData.stress_pnl >= 0 ? Theme.value('gain') : Theme.value('loss');

                var headerHtml =
                    '<div style="padding:var(--space-5) var(--space-8);border-bottom:1px solid var(--line-soft);display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:var(--space-4);">' +
                    '<div style="display:flex;align-items:center;gap:var(--space-5);">' +
                    '<span style="font-size:var(--size-md);font-weight:700;color:var(--text);">' + gaugeData.gauge_name + '</span>' +
                    '<span style="background:' + thresholdBg + ';color:' + thresholdColor + ';border:1px solid ' + thresholdColor + ';' +
                    'padding:var(--space-hair) var(--space-4);border-radius:var(--radius-xl);font-size:var(--size-xxs);font-weight:700;">' + gaugeData.threshold.toUpperCase() + '</span>' +
                    '</div>' +
                    '<div style="display:flex;align-items:center;gap:var(--space-8);">' +
                    '<span style="font-size:var(--size-xs);color:var(--text-3);">P(flood): <b>' + gaugeData.p_flood_pct.toFixed(1) + '%</b></span>' +
                    '<span style="font-size:var(--size-xs);color:var(--text-3);">Peak: <b>' + gaugeData.peak_water_level_m.toFixed(2) + 'm</b></span>' +
                    '<span style="font-size:var(--size-md);font-weight:700;color:' + pnlColor + ';">Total Stress P&amp;L: ' + fmtGBP(gaugeData.stress_pnl) + '</span>' +
                    '<button data-gaugeid="' + gaugeData.gauge_id + '" class="ps-detail-btn" style="padding:var(--space-2) var(--space-5);font-size:var(--size-xxs);background:var(--accent);color:var(--inverse);border:none;border-radius:var(--radius-sm);cursor:pointer;">' +
                    '→ Full Detail ↗' +
                    '</button>' +
                    '</div>' +
                    '</div>';

                // Hourly P&L chart (top half)
                var chartHtml = '';
                if (gaugeData.hydrograph && gaugeData.hydrograph.length > 0 && gaugeData.severe_level > 0) {
                    chartHtml = '<div style="padding:var(--space-2) var(--space-8) 0 var(--space-8);height:200px;">' +
                        '<canvas id="ps-hourly-pnl-canvas"></canvas></div>';
                }

                var tradesHtml = '';
                if (gaugeData.trades && gaugeData.trades.length > 0) {
                    tradesHtml =
                        '<table style="width:100%;border-collapse:collapse;font-size:var(--size-xxs);">' +
                        '<thead><tr style="background:var(--sunken);border-bottom:2px solid var(--line-strong);">' +
                        '<th style="padding:var(--space-3) var(--space-4);text-align:left;">Trade</th>' +
                        '<th style="padding:var(--space-3) var(--space-2);text-align:center;">Dir</th>' +
                        '<th style="padding:var(--space-3) var(--space-2);text-align:center;">Trigger</th>' +
                        '<th style="padding:var(--space-3) var(--space-2);text-align:center;">Tenor</th>' +
                        '<th style="padding:var(--space-3) var(--space-4);text-align:right;">Notional</th>' +
                        '<th style="padding:var(--space-3) var(--space-4);text-align:right;">P(flood)</th>' +
                        '<th style="padding:var(--space-3) var(--space-4);text-align:right;">MTM</th>' +
                        '<th style="padding:var(--space-3) var(--space-4);text-align:right;">Stress P&amp;L</th>' +
                        '</tr></thead><tbody>';

                    var totalNotional = 0, totalMtm = 0, totalStress = 0;
                    gaugeData.trades.forEach(function(t) {
                        var dirColor = t.is_payer ? Theme.value('red-dark') : Theme.value('green-dark');
                        var spnlColor = t.stress_pnl >= 0 ? Theme.value('gain') : Theme.value('loss');
                        totalNotional += t.notional;
                        totalMtm += t.mtm;
                        totalStress += t.stress_pnl;
                        tradesHtml +=
                            '<tr style="border-bottom:1px solid var(--code);">' +
                            '<td style="padding:var(--space-2) var(--space-4);font-family:monospace;font-size:var(--size-xxs);">' + t.swap_id.substring(0, 14) + '</td>' +
                            '<td style="padding:var(--space-2) var(--space-2);text-align:center;color:' + dirColor + ';font-weight:600;">' + (t.is_payer ? 'Pay' : 'Rcv') + '</td>' +
                            '<td style="padding:var(--space-2) var(--space-2);text-align:center;font-size:var(--size-xxs);text-transform:capitalize;">' + (t.trigger || '—') + '</td>' +
                            '<td style="padding:var(--space-2) var(--space-2);text-align:center;font-size:var(--size-xxs);">' + (t.tenor ? t.tenor + 'Y' : '—') + '</td>' +
                            '<td style="padding:var(--space-2) var(--space-4);text-align:right;">' + fmtGBP(t.notional) + '</td>' +
                            '<td style="padding:var(--space-2) var(--space-4);text-align:right;">' + gaugeData.p_flood_pct.toFixed(1) + '%</td>' +
                            '<td style="padding:var(--space-2) var(--space-4);text-align:right;">' + fmtGBP(t.mtm) + '</td>' +
                            '<td style="padding:var(--space-2) var(--space-4);text-align:right;font-weight:700;color:' + spnlColor + ';">' + fmtGBP(t.stress_pnl) + '</td>' +
                            '</tr>';
                    });

                    tradesHtml +=
                        '<tr style="border-top:2px solid var(--text);background:var(--wash);font-weight:700;">' +
                        '<td style="padding:var(--space-3) var(--space-4);" colspan="4">TOTAL</td>' +
                        '<td style="padding:var(--space-3) var(--space-4);text-align:right;">' + fmtGBP(totalNotional) + '</td>' +
                        '<td style="padding:var(--space-3) var(--space-4);text-align:right;">' + gaugeData.p_flood_pct.toFixed(1) + '%</td>' +
                        '<td style="padding:var(--space-3) var(--space-4);text-align:right;color:' + (totalMtm >= 0 ? 'var(--green-dark)' : 'var(--red-dark)') + ';">' + fmtGBP(totalMtm) + '</td>' +
                        '<td style="padding:var(--space-3) var(--space-4);text-align:right;color:' + (totalStress >= 0 ? 'var(--green-dark)' : 'var(--red-dark)') + ';">' + fmtGBP(totalStress) + '</td>' +
                        '</tr></tbody></table>';
                } else {
                    tradesHtml = '<div style="padding:var(--space-10);color:var(--muted-2);text-align:center;">No open trades at this gauge.</div>';
                }

                container.innerHTML = headerHtml + chartHtml + tradesHtml;

                // Render hourly P&L chart
                if (gaugeData.hydrograph && gaugeData.hydrograph.length > 0 && gaugeData.severe_level > 0) {
                    _psRenderHourlyPnlChart(gaugeData);
                }

                // Bind "Full Detail" button
                var detailBtn = container.querySelector('.ps-detail-btn');
                if (detailBtn) {
                    detailBtn.addEventListener('click', function() {
                        var gid = this.getAttribute('data-gaugeid');
                        if (psResult) window._stressStormHint = psResult.storm_id;
                        tdStressGaugeHint = gid;
                        switchTab('stress');
                    });
                }
            }

            function _psRenderHourlyPnlChart(gaugeData) {
                var canvas = document.getElementById('ps-hourly-pnl-canvas');
                if (!canvas) return;
                if (psGaugeHourlyChart) { psGaugeHourlyChart.destroy(); psGaugeHourlyChart = null; }

                var hydro = gaugeData.hydrograph;
                var sev = gaugeData.severe_level;
                var nHours = hydro.length;

                // Compute hourly P(flood) and aggregate stress P&L
                var hourLabels = [];
                var pFloodSeries = [];
                var stressPnlSeries = [];

                // Net signed notional across all trades
                var netSignedNotional = 0;
                var totalMtm = 0;
                (gaugeData.trades || []).forEach(function(t) {
                    netSignedNotional += t.notional;  // already signed
                    totalMtm += t.mtm;
                });

                for (var hr = 0; hr < nHours; hr++) {
                    hourLabels.push(hr);
                    var pf = _fpPFlood(hydro[hr], hr, sev);
                    pFloodSeries.push(Math.round(pf * 10000) / 100);  // percentage
                    var cashPrice = netSignedNotional * pf;
                    stressPnlSeries.push(Math.round(cashPrice - totalMtm));
                }

                var ctx = canvas.getContext('2d');
                psGaugeHourlyChart = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: hourLabels,
                        datasets: [
                            {
                                label: 'Stress P&L',
                                data: stressPnlSeries,
                                borderColor: Theme.value('accent'),
                                backgroundColor: Theme.value('chart-fill-accent'),
                                fill: true,
                                yAxisID: 'yPnl',
                                pointRadius: 0,
                                borderWidth: 1.5,
                                tension: 0.3
                            },
                            {
                                label: 'P(flood) %',
                                data: pFloodSeries,
                                borderColor: Theme.value('red-dark'),
                                backgroundColor: 'transparent',
                                borderDash: [4, 2],
                                yAxisID: 'yPflood',
                                pointRadius: 0,
                                borderWidth: 1.5,
                                tension: 0.3
                            }
                        ]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        interaction: { mode: 'index', intersect: false },
                        plugins: {
                            legend: { position: 'top', labels: { font: { size: 9 }, boxWidth: 12, padding: 8 } },
                            tooltip: {
                                callbacks: {
                                    title: function(items) { return 'Hour ' + items[0].label; },
                                    label: function(ctx) {
                                        if (ctx.dataset.yAxisID === 'yPnl') return 'Stress P&L: ' + fmtGBP(ctx.raw);
                                        return 'P(flood): ' + ctx.raw.toFixed(1) + '%';
                                    }
                                }
                            }
                        },
                        scales: {
                            x: {
                                title: { display: true, text: 'Storm Hour', font: { size: 9 } },
                                ticks: { font: { size: 8 }, maxTicksLimit: 12 }
                            },
                            yPnl: {
                                type: 'linear',
                                position: 'left',
                                title: { display: true, text: 'Stress P&L', font: { size: 9 } },
                                ticks: {
                                    font: { size: 8 },
                                    callback: function(v) { return fmtGBP(v); }
                                },
                                grid: { color: Theme.value('grid-line') }
                            },
                            yPflood: {
                                type: 'linear',
                                position: 'right',
                                min: 0,
                                max: 100,
                                title: { display: true, text: 'P(flood) %', font: { size: 9 } },
                                ticks: { font: { size: 8 }, callback: function(v) { return v + '%'; } },
                                grid: { drawOnChartArea: false }
                            }
                        }
                    }
                });
            }
