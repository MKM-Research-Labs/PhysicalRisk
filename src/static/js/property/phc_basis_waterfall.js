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

            var _basisWaterfallChart = null;

            function _renderSpreadWaterfall(canvasId, activeStep) {
                if (_basisWaterfallChart) { _basisWaterfallChart.destroy(); _basisWaterfallChart = null; }

                var sd = phcData.spread_decomposition || {};
                var gaugeSpread = sd.gauge_spread_bps || 0;
                var sheSpread = sd.she_spread_bps || 0;
                var shdSpread = sd.shd_spread_bps || 0;
                var propSpread = sd.property_spread_bps || 0;

                var labels = ['Gauge', 'SHE (elevation)', 'SHD (distance)', 'Property'];
                var values = [gaugeSpread, sheSpread, shdSpread, propSpread];
                var baseColors = [Theme.value('red-soft'), Theme.value('amber-bright'), Theme.value('green-soft'), Theme.value('accent-light')];
                var mutedColors = [Theme.value('danger-line-alt'), Theme.value('warn-line-pale'), Theme.value('ok-line'), Theme.value('accent-border')];

                // 5th stage — BRI-adjusted (resilient) spread. Only present once
                // the propertybri stage has run; raising the effective flood
                // floor removes severe floods so the resilient spread <= pure.
                var hasBri = (sd.bri_spread_bps !== undefined && sd.bri_spread_bps !== null);
                if (hasBri) {
                    labels.push('BRI (resilient)');
                    values.push(sd.bri_spread_bps || 0);
                    baseColors.push(Theme.value('product-edge'));
                    mutedColors.push(Theme.value('purple-pale'));
                }

                // Colours: muted for inactive, bold for active step
                var bgColors = values.map(function(_, i) {
                    return i === activeStep ? baseColors[i] : mutedColors[i];
                });
                var borderColors = values.map(function(_, i) {
                    return baseColors[i];
                });
                var borderWidths = values.map(function(_, i) {
                    return i === activeStep ? 3 : 1;
                });

                // Effect annotations between bars
                var effects = [];
                if (gaugeSpread > 0) {
                    var sheEffect = sheSpread - gaugeSpread;
                    var shdEffect = shdSpread - gaugeSpread;
                    var propEffect = propSpread - gaugeSpread;
                    effects = [
                        '',
                        (sheEffect >= 0 ? '+' : '') + sheEffect.toFixed(1) + ' bps (elevation)',
                        (shdEffect >= 0 ? '+' : '') + shdEffect.toFixed(1) + ' bps (distance)',
                        (propEffect >= 0 ? '+' : '') + propEffect.toFixed(1) + ' bps (total)',
                    ];
                    if (hasBri) {
                        // Resilience credit: pure spread - resilient spread >= 0,
                        // shown as a negative delta off the property bar.
                        var resilienceEffect = (sd.bri_spread_bps || 0) - propSpread;
                        effects.push(
                            (resilienceEffect >= 0 ? '+' : '') +
                            resilienceEffect.toFixed(1) + ' bps (resilience)');
                    }
                }

                // Optional "before" overlay — set by the CDM Asset Review tool to
                // show a before/after recompute. Absent in the main app (single
                // series, unchanged). Ghost bars behind the current ("after") ones.
                var hasBefore = !!(phcData && phcData.before_decomposition);
                var beforeValues = [];
                if (hasBefore) {
                    var bd = phcData.before_decomposition;
                    beforeValues = [bd.gauge_spread_bps || 0, bd.she_spread_bps || 0,
                                    bd.shd_spread_bps || 0, bd.property_spread_bps || 0];
                    if (hasBri) beforeValues.push(bd.bri_spread_bps || 0);
                }

                var datasets = [{
                    label: hasBefore ? 'After' : 'Spread (bps)',
                    data: values,
                    backgroundColor: bgColors,
                    borderColor: borderColors,
                    borderWidth: borderWidths,
                    barPercentage: 0.7,
                    categoryPercentage: 0.8,
                }];
                if (hasBefore) {
                    datasets.push({
                        label: 'Before',
                        data: beforeValues,
                        backgroundColor: Theme.value('chart-wash-neutral'),
                        borderColor: Theme.value('chart-fill-neutral'),
                        borderWidth: 1,
                        barPercentage: 0.7,
                        categoryPercentage: 0.8,
                    });
                }

                var ctx = document.getElementById(canvasId).getContext('2d');

                _basisWaterfallChart = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: labels,
                        datasets: datasets
                    },
                    options: {
                        indexAxis: 'y',
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { display: hasBefore, position: 'bottom',
                                      labels: { boxWidth: 12, font: { size: 10 } } },
                            tooltip: {
                                callbacks: {
                                    label: function(ctx) {
                                        var v = ctx.raw;
                                        var lines = [v.toFixed(1) + ' bps'];
                                        if (effects[ctx.dataIndex]) lines.push(effects[ctx.dataIndex]);
                                        return lines;
                                    }
                                }
                            }
                        },
                        layout: {
                            padding: { right: 70 }
                        },
                        scales: {
                            x: {
                                beginAtZero: true,
                                suggestedMax: Math.max.apply(null, values.concat(beforeValues)) * 1.15,
                                title: { display: true, text: 'Spread (bps)', font: { size: 11 } },
                                grid: { color: Theme.value('code') },
                            },
                            y: {
                                grid: { display: false },
                                ticks: {
                                    font: function(context) {
                                        return { size: 11, weight: context.index === activeStep ? 'bold' : 'normal' };
                                    },
                                    color: function(context) {
                                        return context.index === activeStep ? baseColors[activeStep] : Theme.value('text-3');
                                    },
                                },
                            }
                        },
                        animation: {
                            onComplete: function() {
                                // Draw effect labels at end of each bar
                                var chart = _basisWaterfallChart;
                                if (!chart) return;
                                var cCtx = chart.ctx;
                                cCtx.font = '10px Arial';
                                cCtx.textBaseline = 'middle';
                                chart.data.datasets[0].data.forEach(function(val, i) {
                                    var meta = chart.getDatasetMeta(0);
                                    var bar = meta.data[i];
                                    var x = bar.x + 6;
                                    var y = bar.y;
                                    cCtx.fillStyle = borderColors[i];
                                    cCtx.textAlign = 'left';
                                    cCtx.fillText(val.toFixed(1) + ' bps', x, y);
                                });
                            }
                        }
                    }
                });
            }
