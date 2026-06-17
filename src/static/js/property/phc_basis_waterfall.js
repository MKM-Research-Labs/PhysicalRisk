
            // ================================================================
            // Basis Explorer — Spread Waterfall (shared)
            // ================================================================
            var _basisWaterfallChart = null;

            function _renderSpreadWaterfall(canvasId, activeStep) {
                if (_basisWaterfallChart) { _basisWaterfallChart.destroy(); _basisWaterfallChart = null; }

                // Stages are pre-built server-side (models.prs.waterfall) — the
                // single source shared with the CDM Asset Review tool — so the
                // labels, spreads, colours and the BRI 5th stage are not rebuilt
                // here. The property_hazard route always attaches them.
                var stages = phcData.waterfall_stages || [];
                if (!stages.length) return;

                var labels = stages.map(function(s) { return s.label; });
                var values = stages.map(function(s) { return s.bps; });
                var baseColors = stages.map(function(s) { return s.colour; });
                var mutedColors = stages.map(function(s) { return s.muted; });

                // Colours: muted for inactive, bold for active step
                var bgColors = values.map(function(_, i) {
                    return i === activeStep ? baseColors[i] : mutedColors[i];
                });
                var borderColors = baseColors.slice();
                var borderWidths = values.map(function(_, i) {
                    return i === activeStep ? 3 : 1;
                });

                // Effect annotations — only meaningful once the gauge spread > 0.
                var suffix = { she: ' (elevation)', shd: ' (distance)',
                               property: ' (total)', bri: ' (resilience)' };
                var gaugePositive = stages.length && stages[0].bps > 0;
                var effects = stages.map(function(s) {
                    if (!gaugePositive || s.effect === null || s.effect === undefined) return '';
                    return (s.effect >= 0 ? '+' : '') + s.effect.toFixed(1)
                        + ' bps' + (suffix[s.key] || '');
                });

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
