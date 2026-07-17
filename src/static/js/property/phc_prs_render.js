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

            function renderPRSPricing() {
                if (currentChart) { currentChart.destroy(); currentChart = null; }

                var result = computePropertyPRSCashflows();
                var periods = result.periods;
                var container = document.getElementById('phc-chart-container');
                var gauges = result.gaugeComponents;

                function fmtMoney(v) {
                    var abs = Math.abs(v);
                    if (abs >= 1e6) return (v < 0 ? '-' : '') + '$' + (abs/1e6).toFixed(2) + 'M';
                    if (abs >= 1e3) return (v < 0 ? '-' : '') + '$' + (abs/1e3).toFixed(1) + 'K';
                    return (v < 0 ? '-' : '') + '$' + abs.toFixed(0);
                }

                function fmtK(v) {
                    return (v/1000).toFixed(1) + 'K';
                }

                // Component table HTML (left side of top row)
                var propElev = phcData.elevation_m || 0;
                var componentTable = _buildPRSComponentTableHTML(result, gauges, propElev);

                // Spread decomposition + waterfall (right side of top row)
                var sd = phcData.spread_decomposition || {};
                var gaugeSpread = sd.gauge_spread_bps || 0;
                var propSpread = sd.property_spread_bps || 0;
                var terrainDelta = result.terrainDelta || 0;
                var selectedZone = result.selectedZone || '';
                var actualZone = result.actualZone || '';
                var adjustedPropSpread = propSpread + terrainDelta;
                var waterfallTable = _buildPRSWaterfallTableHTML(
                    sd, terrainDelta, selectedZone, actualZone, adjustedPropSpread);

                // ---- Cashflow table ----
                var cfRows = '';
                periods.forEach(function(p) {
                    cfRows +=
                        '<tr>' +
                        '<td style="padding:2px 6px;font-weight:600;">' + p.label + '</td>' +
                        '<td style="padding:2px 6px;text-align:right;">' + (p.S_t * 100).toFixed(2) + '%</td>' +
                        '<td style="padding:2px 6px;text-align:right;">' + p.df.toFixed(4) + '</td>' +
                        '<td style="padding:2px 6px;text-align:right;color:#1976D2;">' + fmtK(p.premPV) + '</td>' +
                        '<td style="padding:2px 6px;text-align:right;color:#F44336;">' + fmtK(p.protPV) + '</td>' +
                        '</tr>';
                });

                cfRows +=
                    '<tr style="border-top:2px solid #333;font-weight:bold;background:#f0f0f0;">' +
                    '<td style="padding:3px 6px;">TOTAL</td>' +
                    '<td></td><td></td>' +
                    '<td style="padding:3px 6px;text-align:right;color:#1976D2;font-weight:bold;">' + fmtMoney(result.totalPremPV) + '</td>' +
                    '<td style="padding:3px 6px;text-align:right;color:#F44336;font-weight:bold;">' + fmtMoney(result.totalProtPV) + '</td>' +
                    '</tr>';

                var cashflowTable =
                    '<table style="width:100%;border-collapse:collapse;font-size:10px;font-family:monospace;">' +
                    '<thead><tr style="background:#f5f5f5;border-bottom:2px solid #ddd;">' +
                    '<th style="padding:3px 6px;text-align:left;">Period</th>' +
                    '<th style="padding:3px 6px;text-align:right;">S(t)</th>' +
                    '<th style="padding:3px 6px;text-align:right;">DF(t)</th>' +
                    '<th style="padding:3px 6px;text-align:right;color:#1976D2;">PV Prem</th>' +
                    '<th style="padding:3px 6px;text-align:right;color:#F44336;">PV Prot</th>' +
                    '</tr></thead>' +
                    '<tbody>' + cfRows + '</tbody></table>';

                // Selected counterparty info for deal ticket
                var ctpyEl = document.getElementById('phc-counterparty');
                var ctpySelected = ctpyEl && ctpyEl.value;
                var ctpyDisplayName = '';
                if (ctpySelected && ctpyEl.selectedIndex > 0) {
                    ctpyDisplayName = ctpyEl.options[ctpyEl.selectedIndex].text;
                }

                // Build layout: top = components + waterfall side by side, bottom = cashflow + chart
                var ctpyHeader = ctpyDisplayName ?
                    '<span style="color:#1565C0;font-weight:bold;">' + ctpyDisplayName + '</span> \u2014 ' : '';

                container.innerHTML =
                    '<div style="display:flex;flex-direction:column;height:100%;gap:6px;">' +
                    '<div style="font-weight:bold;font-size:12px;color:#333;">' +
                    ctpyHeader + 'Severe Trigger \u2014 ' + result.tenor + 'yr Tenor</div>' +
                    '<div style="flex:0 0 auto;display:flex;gap:10px;overflow-y:auto;max-height:42%;">' +
                    '<div style="flex:1;min-width:0;">' + componentTable + '</div>' +
                    '<div style="flex:1;min-width:0;">' + waterfallTable + '</div>' +
                    '</div>' +
                    '<div style="flex:1;display:flex;gap:12px;min-height:0;">' +
                    '<div style="flex:1;overflow-y:auto;min-width:0;">' + cashflowTable + '</div>' +
                    '<div style="flex:1;min-width:0;display:flex;align-items:center;">' +
                    '<canvas id="phc-chart" style="width:100%;height:100%;"></canvas>' +
                    '</div></div></div>';

                // Render bar chart
                var ctx = document.getElementById('phc-chart').getContext('2d');
                var labels = periods.map(function(p) { return p.label; });
                var premPVs = periods.map(function(p) { return p.premPV / 1000; });
                var protPVs = periods.map(function(p) { return p.protPV / 1000; });

                currentChart = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: labels,
                        datasets: [
                            {
                                label: 'PV Premium ($K)',
                                data: premPVs,
                                backgroundColor: 'rgba(25,118,210,0.6)',
                                borderColor: '#1976D2',
                                borderWidth: 1
                            },
                            {
                                label: 'PV Protection ($K)',
                                data: protPVs,
                                backgroundColor: 'rgba(244,67,54,0.6)',
                                borderColor: '#F44336',
                                borderWidth: 1
                            }
                        ]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                position: 'top',
                                labels: { usePointStyle: true, boxWidth: 8, font: { size: 10 } }
                            },
                            tooltip: {
                                callbacks: {
                                    label: function(ctx) {
                                        return ctx.dataset.label + ': $' + ctx.parsed.y.toFixed(1) + 'K';
                                    }
                                }
                            }
                        },
                        scales: {
                            x: { title: { display: true, text: 'Semi-Annual Period', font: { size: 10 } } },
                            y: { title: { display: true, text: 'PV ($K)', font: { size: 10 } }, min: 0 }
                        }
                    }
                });

                // Stats bar
                var bar = document.getElementById('phc-stats-bar');
                var npvColor = result.npv >= 0 ? '#4CAF50' : '#F44336';
                var dirLabel = result.isPayer ? 'Payer' : 'Receiver';
                var npvLabel = (result.npv >= 0 ? '+ve' : '-ve') + ' (' + dirLabel + ')';

                var commitBtn = ctpySelected ?
                    '<button id="phc-commit-btn" onclick="commitPropertyPRSTrade()" ' +
                    'style="padding:4px 14px;background:#4CAF50;color:white;border:none;border-radius:3px;' +
                    'cursor:pointer;font-weight:bold;font-size:11px;margin-left:8px;">Commit</button>' :
                    '<span style="color:#aaa;font-size:10px;margin-left:8px;">(select ctpy to commit)</span>';

                var ctpyTag = ctpyDisplayName ?
                    '<span><b>Ctpy:</b> <span style="color:#1565C0;">' + ctpyDisplayName + '</span></span>' :
                    '<span style="color:#aaa;"><b>Ctpy:</b> none</span>';

                var zoneTag = '';
                if (selectedZone && selectedZone !== actualZone) {
                    zoneTag = '<span><b>Zone:</b> ' + selectedZone + ' <span style="color:#888;">(vs ' + actualZone + ')</span></span>';
                }

                bar.innerHTML = [
                    ctpyTag,
                    zoneTag,
                    '<span><b>Fair Spread:</b> <span style="font-size:13px;color:#1976D2;">' + result.fairSpreadBps.toFixed(1) + ' bps</span></span>',
                    '<span><b>Running:</b> ' + result.spreadBps.toFixed(0) + ' bps</span>',
                    '<span style="color:' + npvColor + ';"><b>NPV:</b> ' + fmtMoney(result.npv) + ' (' + npvLabel + ')</span>',
                    '<span><b>Premium:</b> ' + fmtMoney(result.totalPremPV) + '</span>',
                    '<span><b>Protection:</b> ' + fmtMoney(result.totalProtPV) + '</span>',
                    '<span><b>Spread:</b> <span style="color:#1976D2;">' + adjustedPropSpread.toFixed(1) + 'bp</span> / Gauge: ' + gaugeSpread.toFixed(1) + 'bp</span>',
                    commitBtn
                ].join('');

                document.getElementById('phc-status').textContent =
                    'Severe trigger | ' + result.tenor + 'yr | Fair=' +
                    result.fairSpreadBps.toFixed(1) + 'bps | Prop=' + propSpread.toFixed(1) + 'bp | Gauge=' + gaugeSpread.toFixed(1) + 'bp';
            }
