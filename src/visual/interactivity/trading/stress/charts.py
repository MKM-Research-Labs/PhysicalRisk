# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial 
# research and educational use only. Any commercial use, including 
# but not limited to use in or for products or services offered for sale, 
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Stress Test — charts sub-module.

Flood Probability chart and Stress P&L chart.
"""


def get_js() -> str:
    """Return JavaScript fragment for stress test charts."""
    return """
            // ---- Chart 1: Flood Probability ----
            function _tdRenderProbabilityChart(data) {
                var ctx = document.getElementById('td-stress-chart-canvas');
                if (!ctx) return;
                if (tdStressChart) { tdStressChart.destroy(); tdStressChart = null; }

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
                        borderColor: '#1565c0',
                        backgroundColor: 'rgba(21,101,192,0.08)',
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
                        borderColor: '#e65100',
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

                if (alertLevel > 0) {
                    datasets.push({
                        label: 'Alert',
                        type: 'line',
                        data: Array(labels.length).fill(alertLevel),
                        borderColor: '#FFC107',
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
                        borderColor: '#FF9800',
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
                        borderColor: '#D32F2F',
                        borderDash: [6, 3],
                        borderWidth: 1.5,
                        pointRadius: 0,
                        fill: false,
                        yAxisID: 'yLevel',
                        order: 0
                    });
                    datasets.push({
                        label: '_severe_fill',
                        type: 'line',
                        data: waterLevels.slice(),
                        borderWidth: 0,
                        pointRadius: 0,
                        fill: { target: severeIdx, above: 'rgba(244,67,54,0.25)', below: 'rgba(0,0,0,0)' },
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
                                borderColor: '#c62828',
                                borderWidth: 2,
                                borderDash: [4, 3],
                                label: {
                                    display: true,
                                    content: 'KO H' + summary.first_trigger_hour,
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
                                title: { display: true, text: 'Water Level (m)', font: { size: 10 }, color: '#1565c0' },
                                ticks: { font: { size: 9 }, color: '#1565c0' },
                                grid: { color: 'rgba(0,0,0,0.04)' }
                            },
                            yProb: {
                                position: 'right',
                                title: { display: true, text: 'P(flood) %', font: { size: 10 }, color: '#e65100' },
                                ticks: { font: { size: 9 }, color: '#e65100' },
                                min: 0, max: 100,
                                grid: { drawOnChartArea: false }
                            }
                        }
                    }
                });
            }

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

            // ---- Tab 3: P(flood) Surface Table ----
            function _tdRenderSurfaceTable(data) {
                var wrap = document.getElementById('td-stress-surface-wrap');
                if (!wrap) return;

                var surface = data.probability_surface;
                if (!surface || !surface.water_levels || !surface.hours) {
                    wrap.innerHTML = '<div style="color:#999;text-align:center;padding:40px 0;">No surface data available</div>';
                    return;
                }

                var levels = surface.water_levels;
                var hours = surface.hours;
                var probs = surface.probabilities;
                var alertLv = data.alert_level || 0;
                var warningLv = data.warning_level || 0;
                var severeLv = data.severe_level || 0;
                var koHour = (data.summary || {}).first_trigger_hour;

                // Build HTML table
                var html = '<table style="border-collapse:collapse;font-size:10px;font-family:monospace;">';
                // Header row: hours
                html += '<tr><th style="padding:3px 6px;border:1px solid #ddd;background:#f5f5f5;font-size:9px;position:sticky;left:0;z-index:1;">m \\\\ H</th>';
                for (var hi = 0; hi < hours.length; hi++) {
                    html += '<th style="padding:3px 5px;border:1px solid #ddd;background:#f5f5f5;font-size:9px;min-width:38px;text-align:center;">H' + hours[hi] + '</th>';
                }
                html += '</tr>';

                // Data rows: one per water level (descending)
                for (var li = 0; li < levels.length; li++) {
                    var lv = levels[li];
                    // Row background based on trigger band
                    var rowBg = '#fff';
                    if (severeLv > 0 && lv >= severeLv) rowBg = '#FFEBEE';
                    else if (warningLv > 0 && lv >= warningLv) rowBg = '#FFF3E0';
                    else if (alertLv > 0 && lv >= alertLv) rowBg = '#FFF8E1';

                    // Level label with trigger band colour indicator
                    var lvColor = '#333';
                    if (severeLv > 0 && lv >= severeLv) lvColor = '#c62828';
                    else if (warningLv > 0 && lv >= warningLv) lvColor = '#e65100';
                    else if (alertLv > 0 && lv >= alertLv) lvColor = '#f57f17';

                    html += '<tr>';
                    html += '<td style="padding:3px 6px;border:1px solid #ddd;background:#f5f5f5;font-weight:bold;color:' + lvColor + ';position:sticky;left:0;z-index:1;white-space:nowrap;">' + lv.toFixed(1) + '</td>';

                    for (var hi = 0; hi < hours.length; hi++) {
                        var p = probs[li][hi];
                        var cellBg = rowBg;
                        var cellText = '';
                        if (p == null) {
                            // After KO: blank
                            cellBg = '#f0f0f0';
                            cellText = '';
                        } else {
                            cellText = p.toFixed(1);
                            // Intensity shading within band
                            var alpha = Math.min(p / 100, 1.0) * 0.3;
                            if (severeLv > 0 && lv >= severeLv) cellBg = 'rgba(211,47,47,' + (0.08 + alpha) + ')';
                            else if (warningLv > 0 && lv >= warningLv) cellBg = 'rgba(230,81,0,' + (0.06 + alpha * 0.8) + ')';
                            else if (alertLv > 0 && lv >= alertLv) cellBg = 'rgba(255,193,7,' + (0.06 + alpha * 0.6) + ')';
                            else cellBg = 'rgba(200,200,200,' + (alpha * 0.3) + ')';
                        }

                        html += '<td style="padding:2px 4px;border:1px solid #eee;text-align:right;background:' + cellBg + ';font-size:9px;">' + cellText + '</td>';
                    }
                    html += '</tr>';
                }
                html += '</table>';
                html += '<div style="padding:6px 8px;font-size:9px;color:#888;">P(flood) % at each water level (rows) and hour (columns). Capped at severe level. Shading: ' +
                    '<span style="background:#FFF8E1;padding:1px 6px;border:1px solid #ddd;">Alert</span> ' +
                    '<span style="background:#FFF3E0;padding:1px 6px;border:1px solid #ddd;">Warning</span> ' +
                    '<span style="background:#FFEBEE;padding:1px 6px;border:1px solid #ddd;">Severe</span>' +
                    (koHour != null ? ' | Columns trimmed at KO H' + koHour : '') +
                    '</div>';
                wrap.innerHTML = html;
            }
"""
