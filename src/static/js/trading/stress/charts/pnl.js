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

            function _tdRenderStressPnlChart(data) {
                var ctx = document.getElementById('td-stress-chart-canvas');
                if (!ctx) return;
                if (tdStressChart) { tdStressChart.destroy(); tdStressChart = null; }

                var hourly = data.hourly || [];
                var labels = hourly.map(function(h) { return 'H' + h.hour; });

                var waterLevels = hourly.map(function(h) { return h.water_level; });
                var stressPnls = hourly.map(function(h) { return h.portfolio_stress_pnl; });

                var barColors = stressPnls.map(function(v) {
                    return v >= 0 ? Theme.value('gain-fill') : Theme.value('loss-fill');
                });

                var koPlugins2 = {};
                var summary2 = data.summary || {};
                if (summary2.first_trigger_hour != null) {
                    koPlugins2.annotation = {
                        annotations: {
                            koLine: {
                                type: 'line',
                                xMin: summary2.first_trigger_hour,
                                xMax: summary2.first_trigger_hour,
                                borderColor: Theme.value('red-dark'),
                                borderWidth: 2,
                                borderDash: [4, 3],
                                label: {
                                    display: true,
                                    content: 'KO H' + summary2.first_trigger_hour,
                                    position: 'start',
                                    backgroundColor: Theme.value('loss-fill'),
                                    color: Theme.value('panel'),
                                    font: { size: 9, weight: 'bold' },
                                    padding: 3
                                }
                            }
                        }
                    };
                }

                tdStressChart = new Chart(ctx.getContext('2d'), {
                    type: 'bar',
                    data: {
                        labels: labels,
                        datasets: [
                            {
                                label: 'Stress P&L (\u00A3)',
                                data: stressPnls,
                                backgroundColor: barColors,
                                borderWidth: 0,
                                yAxisID: 'yPnl',
                                order: 2
                            },
                            {
                                label: 'Water Level (m)',
                                type: 'line',
                                data: waterLevels,
                                borderColor: Theme.value('accent-mid'),
                                backgroundColor: Theme.value('chart-fill-accent'),
                                fill: true,
                                borderWidth: 2.5,
                                pointRadius: 0,
                                tension: 0.3,
                                yAxisID: 'yLevel',
                                order: 1
                            }
                        ]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        interaction: { intersect: false, mode: 'index' },
                        plugins: Object.assign({
                            legend: {
                                position: 'top',
                                labels: { usePointStyle: true, boxWidth: 8, font: { size: 9 } }
                            },
                            tooltip: {
                                callbacks: {
                                    label: function(ctx) {
                                        var ds = ctx.dataset.label;
                                        if (ds.indexOf('P&L') >= 0) return ds + ': \u00A3' + ctx.parsed.y.toLocaleString();
                                        return ds + ': ' + ctx.parsed.y.toFixed(2) + 'm';
                                    }
                                }
                            }
                        }, koPlugins2),
                        scales: {
                            x: {
                                ticks: { maxTicksLimit: 15, font: { size: 8 } },
                                title: { display: true, text: 'Hour', font: { size: 10 } }
                            },
                            yLevel: {
                                position: 'left',
                                title: { display: true, text: 'Water Level (m)', font: { size: 10 }, color: Theme.value('accent-mid') },
                                ticks: { font: { size: 9 }, color: Theme.value('accent-mid') },
                                grid: { drawOnChartArea: false }
                            },
                            yPnl: {
                                position: 'right',
                                title: { display: true, text: 'Stress P&L (\u00A3)', font: { size: 10 }, color: Theme.value('text-2') },
                                ticks: {
                                    font: { size: 9 },
                                    callback: function(v) {
                                        var abs = Math.abs(v);
                                        var s = abs >= 1e6 ? (abs/1e6).toFixed(1) + 'M' :
                                                abs >= 1e3 ? (abs/1e3).toFixed(0) + 'K' :
                                                abs.toFixed(0);
                                        return (v < 0 ? '-' : '') + '\u00A3' + s;
                                    }
                                },
                                grid: { color: Theme.value('grid-line') }
                            }
                        }
                    }
                });
            }
