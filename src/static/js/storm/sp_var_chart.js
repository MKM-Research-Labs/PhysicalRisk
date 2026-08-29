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

            function renderVarChart(data, mode) {
                if (!mode) mode = spVarMode;
                var wrap = document.getElementById('sp-var-chart-wrap');
                wrap.innerHTML = '<canvas id="sp-var-canvas"></canvas>';

                if (spVarChart) {
                    spVarChart.destroy();
                    spVarChart = null;
                }

                var isProp = mode === 'property';
                var bins = isProp ? data.prop_histogram : data.mort_histogram;
                var pd = isProp ? data.property_damage : data.mortgage_impairment;
                var chartColor = isProp ? Theme.value('chart-fill-accent-half')
                                        : Theme.value('chart-fill-purple-half');
                var lineColor = isProp ? Theme.value('accent') : Theme.value('purple');
                var distLabel = isProp ? 'Property Damage' : 'Mortgage Impairment';
                var labels = [];
                var propCounts = [];
                bins.forEach(function(b) {
                    if (b.count === 0) return;
                    var mid = (b.lo + b.hi) / 2;
                    labels.push(mid);
                    propCounts.push(b.count);
                });

                var ctx = document.getElementById('sp-var-canvas').getContext('2d');
                spVarChart = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: labels,
                        datasets: [{
                            label: distLabel,
                            data: propCounts,
                            backgroundColor: labels.map(function(v) {
                                if (v >= pd.cond_var_999) return Theme.value('severe-fill');
                                if (v >= pd.cond_var_95) return Theme.value('warning-fill');
                                return chartColor;
                            }),
                            borderColor: labels.map(function(v) {
                                if (v >= pd.cond_var_999) return Theme.value('red');
                                if (v >= pd.cond_var_95) return Theme.value('amber');
                                return lineColor;
                            }),
                            borderWidth: 1,
                            barPercentage: 1.0,
                            categoryPercentage: 1.0,
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        interaction: {
                            mode: 'index',
                            intersect: false,
                        },
                        plugins: {
                            legend: { display: false },
                            title: {
                                display: true,
                                text: distLabel + ' Distribution (' + data.storm_count.toLocaleString() + ' storms, ' + data.storms_with_damage + ' with damage)',
                                font: { size: 13, weight: 'bold' },
                                color: Theme.value('text'),
                            },
                            tooltip: {
                                callbacks: {
                                    title: function(items) {
                                        var b = bins[items[0].dataIndex];
                                        return fmtGBP(b.lo) + ' – ' + fmtGBP(b.hi);
                                    },
                                    label: function(item) {
                                        return item.parsed.y + ' storms';
                                    }
                                }
                            },
                            annotation: {
                                annotations: {
                                    var95Line: {
                                        type: 'line',
                                        xMin: pd.cond_var_95,
                                        xMax: pd.cond_var_95,
                                        borderColor: Theme.value('amber'),
                                        borderWidth: 2,
                                        borderDash: [6, 4],
                                        label: {
                                            display: true,
                                            content: 'VaR 95%: ' + fmtGBP(pd.cond_var_95),
                                            position: 'start',
                                            backgroundColor: Theme.value('warning-fill'),
                                            color: 'white',
                                            font: { size: 10, weight: 'bold' },
                                            padding: 4,
                                        }
                                    },
                                    var999Line: {
                                        type: 'line',
                                        xMin: pd.cond_var_999,
                                        xMax: pd.cond_var_999,
                                        borderColor: Theme.value('red'),
                                        borderWidth: 2,
                                        borderDash: [6, 4],
                                        label: {
                                            display: true,
                                            content: 'VaR 99.9%: ' + fmtGBP(pd.cond_var_999),
                                            position: 'start',
                                            backgroundColor: Theme.value('severe-fill'),
                                            color: 'white',
                                            font: { size: 10, weight: 'bold' },
                                            padding: 4,
                                            yAdjust: 20,
                                        }
                                    }
                                }
                            }
                        },
                        scales: {
                            x: {
                                type: 'linear',
                                title: {
                                    display: true,
                                    text: distLabel + ' (£)',
                                    font: { size: 11 },
                                },
                                ticks: {
                                    callback: function(v) {
                                        if (v >= 1000000) return '£' + (v / 1000000).toFixed(1) + 'M';
                                        if (v >= 1000) return '£' + (v / 1000).toFixed(0) + 'K';
                                        return '£' + v;
                                    },
                                    font: { size: 10 },
                                },
                                min: 0,
                            },
                            y: {
                                title: {
                                    display: true,
                                    text: 'Number of Storms',
                                    font: { size: 11 },
                                },
                                beginAtZero: true,
                                ticks: { font: { size: 10 } },
                            }
                        }
                    }
                });
            }
