
            // ================================================================
            // Basis Explorer — Spread Waterfall (shared)
            // ================================================================
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
                var baseColors = ['#EF5350', '#FF9800', '#66BB6A', '#42A5F5'];
                var mutedColors = ['#FFCDD2', '#FFE0B2', '#C8E6C9', '#BBDEFB'];

                // 5th stage — BRI-adjusted (resilient) spread. Only present once
                // the propertybri stage has run; raising the effective flood
                // floor removes severe floods so the resilient spread <= pure.
                var hasBri = (sd.bri_spread_bps !== undefined && sd.bri_spread_bps !== null);
                if (hasBri) {
                    labels.push('BRI (resilient)');
                    values.push(sd.bri_spread_bps || 0);
                    baseColors.push('#7E57C2');
                    mutedColors.push('#D1C4E9');
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

                var ctx = document.getElementById(canvasId).getContext('2d');

                _basisWaterfallChart = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: labels,
                        datasets: [{
                            label: 'Spread (bps)',
                            data: values,
                            backgroundColor: bgColors,
                            borderColor: borderColors,
                            borderWidth: borderWidths,
                            barPercentage: 0.7,
                            categoryPercentage: 0.8,
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
                                suggestedMax: Math.max.apply(null, values) * 1.15,
                                title: { display: true, text: 'Spread (bps)', font: { size: 11 } },
                                grid: { color: '#f0f0f0' },
                            },
                            y: {
                                grid: { display: false },
                                ticks: {
                                    font: function(context) {
                                        return { size: 11, weight: context.index === activeStep ? 'bold' : 'normal' };
                                    },
                                    color: function(context) {
                                        return context.index === activeStep ? baseColors[activeStep] : '#666';
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
