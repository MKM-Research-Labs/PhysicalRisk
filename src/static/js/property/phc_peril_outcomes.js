
            // ================================================================
            // Basis Explorer — Peril Outcomes fan (Stage 7)
            // ================================================================
            var _perilOutcomesChart = null;

            // Peril data for the active property, or null for flood-only
            // catchments (no typhoon stage). Prefer the decomposition mirror
            // (BRI-adjusted node) and fall back to the top-level prs_perils.
            function _perilOutcomesData() {
                var sd = phcData.spread_decomposition || {};
                return sd.peril_outcomes || phcData.prs_perils || null;
            }

            function _renderPerilOutcomes(canvasId) {
                if (_perilOutcomesChart) { _perilOutcomesChart.destroy(); _perilOutcomesChart = null; }

                var perils = _perilOutcomesData();
                if (!perils) return false;  // flood-only fallback: nothing to draw

                var order = ['flood_only', 'wind_only', 'flood_or_wind', 'flood_and_wind'];
                var labels = ['Flood only', 'Wind only', 'Flood \u222A Wind', 'Flood \u2229 Wind'];
                var colors = ['#42A5F5', '#26A69A', '#7E57C2', '#5E35B1'];
                // BRI-anchored combined perils (bow/baw) — same union/intersection
                // but on the BRI-resilient flood leg. Appended only when present
                // (catchments/runs that produced the bow/baw scenario files), so
                // raw-flood-only payloads keep the four-bar layout unchanged.
                if (perils.bri_or_wind) {
                    order.push('bri_or_wind');
                    labels.push('BRI \u222A Wind');
                    colors.push('#6A1B9A');
                }
                if (perils.bri_and_wind) {
                    order.push('bri_and_wind');
                    labels.push('BRI \u2229 Wind');
                    colors.push('#4A148C');
                }

                var spreads = order.map(function(k) {
                    return (perils[k] && perils[k].spread_bps) || 0;
                });
                var counts = order.map(function(k) {
                    return (perils[k] && perils[k].count) || 0;
                });

                var ctx = document.getElementById(canvasId).getContext('2d');
                _perilOutcomesChart = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: labels,
                        datasets: [{
                            label: 'Spread (bps)',
                            data: spreads,
                            backgroundColor: colors,
                            borderColor: colors,
                            borderWidth: 1,
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
                            title: {
                                display: true,
                                text: 'Peril outcomes (property node)',
                                font: { size: 11, weight: 'bold' },
                                color: '#444',
                            },
                            tooltip: {
                                callbacks: {
                                    label: function(c) {
                                        return [c.raw.toFixed(1) + ' bps',
                                                counts[c.dataIndex] + ' events'];
                                    }
                                }
                            }
                        },
                        layout: { padding: { right: 60 } },
                        scales: {
                            x: {
                                beginAtZero: true,
                                suggestedMax: Math.max.apply(null, spreads) * 1.15 || 1,
                                title: { display: true, text: 'Spread (bps)', font: { size: 10 } },
                                grid: { color: '#f0f0f0' },
                            },
                            y: { grid: { display: false }, ticks: { font: { size: 10 } } }
                        },
                        animation: {
                            onComplete: function() {
                                var chart = _perilOutcomesChart;
                                if (!chart) return;
                                var cCtx = chart.ctx;
                                cCtx.font = '10px Arial';
                                cCtx.textBaseline = 'middle';
                                cCtx.textAlign = 'left';
                                chart.data.datasets[0].data.forEach(function(val, i) {
                                    var bar = chart.getDatasetMeta(0).data[i];
                                    cCtx.fillStyle = colors[i];
                                    cCtx.fillText(val.toFixed(1) + ' bps', bar.x + 6, bar.y);
                                });
                            }
                        }
                    }
                });
                return true;
            }
