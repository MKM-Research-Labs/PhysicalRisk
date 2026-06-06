
            // ================================================================
            // VaR chart rendering
            // ================================================================
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
                var chartColor = isProp ? 'rgba(25,118,210' : 'rgba(123,31,162';
                var lineColor = isProp ? '#1976d2' : '#7b1fa2';
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
                                if (v >= pd.cond_var_999) return 'rgba(211,47,47,0.7)';
                                if (v >= pd.cond_var_95) return 'rgba(245,124,0,0.6)';
                                return chartColor + ',0.5)';
                            }),
                            borderColor: labels.map(function(v) {
                                if (v >= pd.cond_var_999) return '#d32f2f';
                                if (v >= pd.cond_var_95) return '#f57c00';
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
                                color: '#333',
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
                                        borderColor: '#f57c00',
                                        borderWidth: 2,
                                        borderDash: [6, 4],
                                        label: {
                                            display: true,
                                            content: 'VaR 95%: ' + fmtGBP(pd.cond_var_95),
                                            position: 'start',
                                            backgroundColor: 'rgba(245,124,0,0.9)',
                                            color: 'white',
                                            font: { size: 10, weight: 'bold' },
                                            padding: 4,
                                        }
                                    },
                                    var999Line: {
                                        type: 'line',
                                        xMin: pd.cond_var_999,
                                        xMax: pd.cond_var_999,
                                        borderColor: '#d32f2f',
                                        borderWidth: 2,
                                        borderDash: [6, 4],
                                        label: {
                                            display: true,
                                            content: 'VaR 99.9%: ' + fmtGBP(pd.cond_var_999),
                                            position: 'start',
                                            backgroundColor: 'rgba(211,47,47,0.9)',
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
