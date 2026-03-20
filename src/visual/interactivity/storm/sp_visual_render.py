# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""sp_visual — Chart.js multi-line chart rendering (renderSimChart)."""


def get_render_js() -> str:
    """Return JS for the renderSimChart function."""
    return """
            // ================================================================
            // Simulation chart rendering
            // ================================================================
            function renderSimChart(data) {
                var wrap = document.getElementById('sp-sim-chart-wrap');
                wrap.innerHTML = '<canvas id="sp-sim-canvas"></canvas>';

                if (spSimChart) {
                    spSimChart.destroy();
                    spSimChart = null;
                }

                var frames = data.frames || [];
                var hours = frames.map(function(f) { return f.hour; });

                var gaugeIds = [];
                var gaugeNames = {};
                if (frames.length > 0 && frames[0].gauges) {
                    frames[0].gauges.forEach(function(g) {
                        gaugeIds.push(g.gauge_id);
                        gaugeNames[g.gauge_id] = g.name || g.gauge_id;
                    });
                }

                // Populate gauge dropdown
                var dd = document.getElementById('sp-vis-gauge-dropdown');
                if (dd) {
                    dd.innerHTML = '';
                    gaugeIds.forEach(function(gid, idx) {
                        var row = document.createElement('label');
                        row.style.cssText = 'display:flex;align-items:center;gap:6px;padding:3px 10px;cursor:pointer;font-size:11px;white-space:nowrap;';
                        row.onmouseenter = function() { this.style.background = '#f5f5f5'; };
                        row.onmouseleave = function() { this.style.background = ''; };
                        var cb = document.createElement('input');
                        cb.type = 'checkbox';
                        cb.checked = true;
                        cb.dataset.gaugeIdx = idx;
                        cb.style.cssText = 'margin:0;';
                        cb.onchange = function() { toggleGaugeVisibility(idx, this.checked); };
                        var swatch = document.createElement('span');
                        swatch.style.cssText = 'display:inline-block;width:10px;height:3px;border-radius:1px;background:' + simGaugeColors[idx % simGaugeColors.length] + ';';
                        var lbl = document.createElement('span');
                        lbl.textContent = gaugeNames[gid] || gid;
                        row.appendChild(cb);
                        row.appendChild(swatch);
                        row.appendChild(lbl);
                        dd.appendChild(row);
                    });
                    var btn = document.getElementById('sp-vis-gauge-btn');
                    if (btn) btn.textContent = gaugeIds.length + ' Gauges';
                }

                // Build gauge water level datasets
                var datasets = [];
                gaugeIds.forEach(function(gid, idx) {
                    var levels = frames.map(function(f) {
                        var g = f.gauges.find(function(gg) { return gg.gauge_id === gid; });
                        return g ? g.water_level_m : 0;
                    });
                    datasets.push({
                        label: gaugeNames[gid] || gid,
                        data: levels,
                        borderColor: simGaugeColors[idx % simGaugeColors.length],
                        backgroundColor: 'transparent',
                        borderWidth: 1.5,
                        pointRadius: 0,
                        tension: 0.3,
                        yAxisID: 'y',
                    });
                });

                // Properties flooded per hour
                var propsFlooded = frames.map(function(f) {
                    return f.stats ? f.stats.properties_flooded : 0;
                });
                datasets.push({
                    label: 'Properties Flooded',
                    data: propsFlooded,
                    borderColor: '#d32f2f',
                    backgroundColor: 'rgba(211,47,47,0.1)',
                    borderWidth: 2.5,
                    pointRadius: 0,
                    tension: 0.3,
                    fill: true,
                    yAxisID: 'y1',
                });

                // Alert/warning threshold annotations
                var annotations = {};
                if (frames.length > 0 && frames[0].gauges && frames[0].gauges.length > 0) {
                    var refGauge = frames[0].gauges[0];
                    if (refGauge.alert_level) {
                        annotations.alertLine = {
                            type: 'line',
                            yMin: refGauge.alert_level,
                            yMax: refGauge.alert_level,
                            borderColor: '#fbc02d',
                            borderWidth: 1,
                            borderDash: [6, 4],
                            yScaleID: 'y',
                            label: {
                                display: true,
                                content: 'Alert',
                                position: 'start',
                                backgroundColor: 'rgba(251,192,45,0.8)',
                                color: 'white',
                                font: { size: 9 },
                                padding: 2,
                            }
                        };
                    }
                    if (refGauge.warning_level) {
                        annotations.warningLine = {
                            type: 'line',
                            yMin: refGauge.warning_level,
                            yMax: refGauge.warning_level,
                            borderColor: '#f57c00',
                            borderWidth: 1,
                            borderDash: [6, 4],
                            yScaleID: 'y',
                            label: {
                                display: true,
                                content: 'Warning',
                                position: 'start',
                                backgroundColor: 'rgba(245,124,0,0.8)',
                                color: 'white',
                                font: { size: 9 },
                                padding: 2,
                            }
                        };
                    }
                }

                var ctx = document.getElementById('sp-sim-canvas').getContext('2d');
                spSimChart = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: hours,
                        datasets: datasets,
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        interaction: {
                            mode: 'index',
                            intersect: false,
                        },
                        plugins: {
                            legend: {
                                display: true,
                                labels: {
                                    usePointStyle: true, boxWidth: 8, font: { size: 10 },
                                    filter: function(item) {
                                        // Only show legend when 3 or fewer gauges are visible
                                        var chart = item.chart || (spSimChart);
                                        if (!chart) return false;
                                        var visCount = 0;
                                        var nGauges = chart.data.datasets.length - 1;
                                        for (var i = 0; i < nGauges; i++) {
                                            if (chart.isDatasetVisible(i)) visCount++;
                                        }
                                        if (visCount > 3) return false;
                                        if (item.text === 'Properties Flooded') return true;
                                        return chart.isDatasetVisible(item.datasetIndex);
                                    }
                                }
                            },
                            title: {
                                display: true,
                                text: (data._stormLabel || data.storm_id) + ' (' + data.n_frames + ' hours)',
                                font: { size: 13, weight: 'bold' },
                                color: '#333',
                            },
                            annotation: {
                                annotations: annotations,
                            },
                        },
                        scales: {
                            x: {
                                title: {
                                    display: true,
                                    text: 'Hour',
                                    font: { size: 11 },
                                },
                                ticks: { font: { size: 10 } },
                            },
                            y: {
                                type: 'linear',
                                position: 'left',
                                title: {
                                    display: true,
                                    text: 'Water Level (m)',
                                    font: { size: 11 },
                                },
                                beginAtZero: true,
                                ticks: { font: { size: 10 } },
                            },
                            y1: {
                                type: 'linear',
                                position: 'right',
                                title: {
                                    display: true,
                                    text: 'Properties Flooded',
                                    font: { size: 11 },
                                    color: '#d32f2f',
                                },
                                beginAtZero: true,
                                ticks: {
                                    font: { size: 10 },
                                    color: '#d32f2f',
                                    stepSize: 1,
                                },
                                grid: { drawOnChartArea: false },
                            },
                        },
                    }
                });
            }
"""
