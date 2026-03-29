# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""Stress P&L chart — bar chart with water level overlay."""


def get_pnl_chart_js() -> str:
    """Return JS for _tdRenderStressPnlChart."""
    return """
            // ---- Chart 2: Stress P&L ----
            function _tdRenderStressPnlChart(data) {
                var ctx = document.getElementById('td-stress-chart-canvas');
                if (!ctx) return;
                if (tdStressChart) { tdStressChart.destroy(); tdStressChart = null; }

                var hourly = data.hourly || [];
                var labels = hourly.map(function(h) { return 'H' + h.hour; });

                var waterLevels = hourly.map(function(h) { return h.water_level; });
                var stressPnls = hourly.map(function(h) { return h.portfolio_stress_pnl; });

                var barColors = stressPnls.map(function(v) {
                    return v >= 0 ? 'rgba(46,125,50,0.6)' : 'rgba(198,40,40,0.6)';
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
                                borderColor: '#c62828',
                                borderWidth: 2,
                                borderDash: [4, 3],
                                label: {
                                    display: true,
                                    content: 'KO H' + summary2.first_trigger_hour,
                                    position: 'start',
                                    backgroundColor: 'rgba(198,40,40,0.85)',
                                    color: '#fff',
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
                                label: 'Stress P&L (\\u00A3)',
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
                                borderColor: '#1565c0',
                                backgroundColor: 'rgba(21,101,192,0.08)',
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
                                        if (ds.indexOf('P&L') >= 0) return ds + ': \\u00A3' + ctx.parsed.y.toLocaleString();
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
                                title: { display: true, text: 'Water Level (m)', font: { size: 10 }, color: '#1565c0' },
                                ticks: { font: { size: 9 }, color: '#1565c0' },
                                grid: { drawOnChartArea: false }
                            },
                            yPnl: {
                                position: 'right',
                                title: { display: true, text: 'Stress P&L (\\u00A3)', font: { size: 10 }, color: '#555' },
                                ticks: {
                                    font: { size: 9 },
                                    callback: function(v) {
                                        var abs = Math.abs(v);
                                        var s = abs >= 1e6 ? (abs/1e6).toFixed(1) + 'M' :
                                                abs >= 1e3 ? (abs/1e3).toFixed(0) + 'K' :
                                                abs.toFixed(0);
                                        return (v < 0 ? '-' : '') + '\\u00A3' + s;
                                    }
                                },
                                grid: { color: 'rgba(0,0,0,0.04)' }
                            }
                        }
                    }
                });
            }
"""
