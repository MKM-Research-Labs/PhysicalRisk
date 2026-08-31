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

            function _renderProbabilityChart(data) {
                var ctx = document.getElementById('stress-chart-canvas');
                if (!ctx) return;
                if (_stressChart) { _stressChart.destroy(); _stressChart = null; }

                var hourly = data.hourly || [];
                var alertLevel = data.alert_level || 0;
                var warningLevel = data.warning_level || 0;
                var severeLevel = data.severe_level || 0;
                var labels = hourly.map(function(h) { return 'H' + h.hour; });

                var waterLevels = hourly.map(function(h) { return h.water_level; });
                var pFloods = hourly.map(function(h) { return h.p_flood != null ? h.p_flood * 100 : null; });

                var datasets = [
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
                    },
                    {
                        label: 'P(flood) %',
                        type: 'line',
                        data: pFloods,
                        borderColor: Theme.value('amber-deep'),
                        borderDash: [4, 2],
                        borderWidth: 2,
                        pointRadius: 0,
                        tension: 0.3,
                        fill: false,
                        spanGaps: false,
                        yAxisID: 'yProb',
                        order: 2
                    }
                ];

                // Add trigger level lines
                if (alertLevel > 0) {
                    datasets.push({
                        label: 'Alert',
                        type: 'line',
                        data: Array(labels.length).fill(alertLevel),
                        borderColor: Theme.value('amber-yellow'),
                        borderDash: [6, 3],
                        borderWidth: 1.5,
                        pointRadius: 0,
                        fill: false,
                        yAxisID: 'yLevel',
                        order: 0
                    });
                }
                if (warningLevel > 0) {
                    datasets.push({
                        label: 'Warning',
                        type: 'line',
                        data: Array(labels.length).fill(warningLevel),
                        borderColor: Theme.value('amber-bright'),
                        borderDash: [6, 3],
                        borderWidth: 1.5,
                        pointRadius: 0,
                        fill: false,
                        yAxisID: 'yLevel',
                        order: 0
                    });
                }
                var severeIdx = -1;
                if (severeLevel > 0) {
                    severeIdx = datasets.length;
                    datasets.push({
                        label: 'Severe',
                        type: 'line',
                        data: Array(labels.length).fill(severeLevel),
                        borderColor: Theme.value('red'),
                        borderDash: [6, 3],
                        borderWidth: 1.5,
                        pointRadius: 0,
                        fill: false,
                        yAxisID: 'yLevel',
                        order: 0
                    });
                    // Red shading: invisible copy of water line, fills down to severe
                    datasets.push({
                        label: '_severe_fill',
                        type: 'line',
                        data: waterLevels.slice(),
                        borderWidth: 0,
                        pointRadius: 0,
                        fill: { target: severeIdx, above: Theme.value('chart-fill-danger'), below: Theme.value('chart-transparent') },
                        tension: 0.3,
                        yAxisID: 'yLevel',
                        order: 1
                    });
                }

                // Knock-out annotation
                var koPlugins = {};
                var summary = data.summary || {};
                if (summary.first_trigger_hour != null) {
                    koPlugins.annotation = {
                        annotations: {
                            koLine: {
                                type: 'line',
                                xMin: summary.first_trigger_hour,
                                xMax: summary.first_trigger_hour,
                                borderColor: Theme.value('red-dark'),
                                borderWidth: 2,
                                borderDash: [4, 3],
                                label: {
                                    display: true,
                                    content: 'KO H' + summary.first_trigger_hour,
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

                _stressChart = new Chart(ctx.getContext('2d'), {
                    type: 'line',
                    data: { labels: labels, datasets: datasets },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        interaction: { intersect: false, mode: 'index' },
                        plugins: Object.assign({
                            legend: {
                                position: 'top',
                                labels: {
                                    usePointStyle: true, boxWidth: 8, font: { size: 9 },
                                    filter: function(item) { return item.text.charAt(0) !== '_'; }
                                }
                            },
                            tooltip: {
                                filter: function(item) { return item.dataset.label.charAt(0) !== '_'; },
                                callbacks: {
                                    label: function(ctx) {
                                        var ds = ctx.dataset.label;
                                        if (ds.indexOf('P(flood)') >= 0) return ds + ': ' + ctx.parsed.y.toFixed(1) + '%';
                                        return ds + ': ' + ctx.parsed.y.toFixed(2) + 'm';
                                    }
                                }
                            }
                        }, koPlugins),
                        scales: {
                            x: {
                                ticks: { maxTicksLimit: 15, font: { size: 8 } },
                                title: { display: true, text: 'Hour', font: { size: 10 } }
                            },
                            yLevel: {
                                position: 'left',
                                title: { display: true, text: 'Water Level (m)', font: { size: 10 }, color: Theme.value('accent-mid') },
                                ticks: { font: { size: 9 }, color: Theme.value('accent-mid') },
                                grid: { color: Theme.value('grid-line') }
                            },
                            yProb: {
                                position: 'right',
                                title: { display: true, text: 'P(flood) %', font: { size: 10 }, color: Theme.value('amber-deep') },
                                ticks: { font: { size: 9 }, color: Theme.value('amber-deep') },
                                min: 0, max: 100,
                                grid: { drawOnChartArea: false }
                            }
                        }
                    }
                });
            }
