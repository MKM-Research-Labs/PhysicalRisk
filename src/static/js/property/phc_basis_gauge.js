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

            var basisGaugeChart = null;

            function renderBasisGauge() {
                var container = document.getElementById('phc-chart-container');
                if (basisGaugeChart) { basisGaugeChart.destroy(); basisGaugeChart = null; }

                var storms = phcData.storm_details || [];
                var nearestGauges = phcData.nearest_gauges || [];

                // Use first non-synthetic gauge, or first gauge
                var primaryGauge = nearestGauges.find(function(ng) {
                    return ng.gauge_id.indexOf('SYNTH') !== 0;
                }) || nearestGauges[0] || {};

                var thresholds = primaryGauge.gauge_thresholds || {};
                var alertLevel = thresholds.alert_level || 0;
                var warningLevel = thresholds.warning_level || 0;
                var severeLevel = thresholds.severe_level || 0;

                // Sort storms by gauge peak level descending
                var sorted = storms.slice().sort(function(a, b) {
                    return b.gauge_peak_m - a.gauge_peak_m;
                });

                var severeCount = 0;
                var data = sorted.map(function(s, i) {
                    var isSevere = s.exceeded_severe || false;
                    if (isSevere) severeCount++;
                    return {
                        x: i,
                        y: s.gauge_peak_m,
                        stormId: s.storm_id,
                        flooded: s.flooded,
                        isSevere: isSevere,
                    };
                });

                var colors = data.map(function(d) {
                    return d.isSevere ? '#F44336' : '#BDBDBD';
                });

                // Summary
                var summaryHtml =
                    '<div style="padding:8px 0 4px 0;font-size:12px;color:#555;">' +
                    '<b>Gauge:</b> ' + (primaryGauge.gauge_id || 'Unknown').substring(0, 20) +
                    ' &nbsp;|&nbsp; <b>' + severeCount + '</b> of <b>' + storms.length +
                    '</b> storms exceed severe (' + (severeLevel > 0 ? severeLevel.toFixed(2) + 'm' : 'n/a') + ')' +
                    '</div>';

                container.innerHTML = summaryHtml +
                    '<div style="display:flex;flex:1;gap:8px;min-height:0;">' +
                    '<canvas id="basis-gauge-canvas" style="flex:1;"></canvas>' +
                    '<canvas id="basis-gauge-waterfall" style="width:35%;min-width:220px;"></canvas>' +
                    '</div>';

                var ctx = document.getElementById('basis-gauge-canvas').getContext('2d');

                // Threshold annotation lines
                var annotations = {};
                if (severeLevel > 0) {
                    annotations.severeLine = {
                        type: 'line', yMin: severeLevel, yMax: severeLevel,
                        borderColor: '#F44336', borderWidth: 2, borderDash: [6, 3],
                        label: { display: true, content: 'Severe ' + severeLevel.toFixed(2) + 'm',
                                 position: 'end', backgroundColor: '#F44336', color: '#fff',
                                 font: { size: 10 }, padding: 3 }
                    };
                }
                if (warningLevel > 0) {
                    annotations.warningLine = {
                        type: 'line', yMin: warningLevel, yMax: warningLevel,
                        borderColor: '#FF9800', borderWidth: 1.5, borderDash: [4, 4],
                        label: { display: true, content: 'Warning ' + warningLevel.toFixed(2) + 'm',
                                 position: 'end', backgroundColor: '#FF9800', color: '#fff',
                                 font: { size: 9 }, padding: 2 }
                    };
                }
                if (alertLevel > 0) {
                    annotations.alertLine = {
                        type: 'line', yMin: alertLevel, yMax: alertLevel,
                        borderColor: '#FFC107', borderWidth: 1, borderDash: [3, 3],
                        label: { display: true, content: 'Alert ' + alertLevel.toFixed(2) + 'm',
                                 position: 'end', backgroundColor: '#FFC107', color: '#333',
                                 font: { size: 9 }, padding: 2 }
                    };
                }

                basisGaugeChart = new Chart(ctx, {
                    type: 'scatter',
                    data: {
                        datasets: [{
                            label: 'Storm Peak at Gauge',
                            data: data,
                            backgroundColor: colors,
                            borderColor: colors,
                            pointRadius: 3,
                            pointHoverRadius: 6,
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        onClick: function(evt, elements) {
                            if (elements.length > 0) {
                                var idx = elements[0].index;
                                var sid = data[idx].stormId;
                                basisSelectedStorm = sid;
                                renderBasisSubTab(basisActiveSubTab);
                            }
                        },
                        plugins: {
                            legend: { display: false },
                            annotation: { annotations: annotations },
                            tooltip: {
                                callbacks: {
                                    title: function(items) {
                                        var d = data[items[0].dataIndex];
                                        return 'Storm ' + d.stormId;
                                    },
                                    label: function(ctx) {
                                        var d = data[ctx.dataIndex];
                                        var lines = ['Peak: ' + d.y.toFixed(3) + 'm'];
                                        if (d.isSevere) lines.push('\u26A0 Exceeds severe');
                                        if (d.flooded) lines.push('\u2192 Property flooded');
                                        return lines;
                                    }
                                }
                            }
                        },
                        scales: {
                            x: {
                                title: { display: true, text: 'Storm (sorted by peak level)', font: { size: 11 } },
                                ticks: { display: false },
                            },
                            y: {
                                title: { display: true, text: 'Gauge Peak Water Level (m)', font: { size: 11 } },
                                beginAtZero: false,
                            }
                        }
                    }
                });

                // Highlight selected storm
                if (basisSelectedStorm) {
                    var selIdx = data.findIndex(function(d) { return d.stormId === basisSelectedStorm; });
                    if (selIdx >= 0) {
                        basisGaugeChart.setActiveElements([{datasetIndex: 0, index: selIdx}]);
                        basisGaugeChart.update();
                    }
                }

                // Spread waterfall (right panel)
                _renderSpreadWaterfall('basis-gauge-waterfall', 0);

                // Stats bar
                var bar = document.getElementById('phc-stats-bar');
                if (bar) {
                    bar.innerHTML =
                        '<span><b>Storms:</b> ' + storms.length + '</span>' +
                        '<span><b>Exceed Severe:</b> ' + severeCount + '</span>' +
                        '<span><b>Flood Property:</b> ' + phcData.flood_count + '</span>' +
                        '<span><b>Basis:</b> ' + (severeCount - phcData.flood_count) + ' storms</span>';
                }
            }
