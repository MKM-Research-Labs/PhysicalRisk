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

"""Gauge Storm Analysis — storm selector, flood timeline (Tab 1), worst storms (Tab 2)."""

from config.format import storm_option_js as _storm_opt


def get_js():
    """Return JS fragment for storm selector, timeline chart, and worst storms chart."""
    return """
            // ================================================================
            // Storm selector (for Timeline tab)
            // ================================================================
            function buildStormSelector() {
                var controls = document.getElementById('storm-controls');
                var responses = stormData.storm_responses.responses || [];
                var fs = stormData.flood_stages || {};

                // Sort by peak level descending
                var sorted = responses.slice().sort(function(a, b) {
                    return b.peak_level_m - a.peak_level_m;
                });

                var html = '<label style="margin-right:8px;font-weight:600;">Storm:</label>';
                html += '<select id="storm-selector" style="padding:4px 8px;border:1px solid #ccc;border-radius:4px;max-width:400px;">';
                html += '<option value="sim">Flood Simulation (default)</option>';

                sorted.forEach(function(r, i) {
                    var icon = '';
                    if (r.exceeded_severe) icon = ' \\uD83D\\uDD34';
                    else if (r.exceeded_warning) icon = ' \\uD83D\\uDFE0';
                    else if (r.exceeded_alert) icon = ' \\uD83D\\uDFE1';
                    html += '<option value="' + r.storm_id + '">' +
                        __STORM_OPT__ + icon +
                        '</option>';
                });

                html += '</select>';
                controls.innerHTML = html;

                document.getElementById('storm-selector').onchange = function() {
                    renderTimeline();
                };
            }

            // ================================================================
            // Tab 1: Flood Timeline
            // ================================================================
            function renderTimeline() {
                var ctx = document.getElementById('storm-chart').getContext('2d');
                if (currentChart) currentChart.destroy();

                var fs = stormData.flood_stages || {};
                var selector = document.getElementById('storm-selector');
                var selectedStorm = selector ? selector.value : 'sim';

                var labels, levels, chartTitle;

                if (selectedStorm === 'sim') {
                    // Show flood simulation readings
                    var readings = stormData.flood_simulation.readings || [];
                    labels = readings.map(function(r, i) { return r.timestamp ? r.timestamp.split('T')[1].substring(0,5) : 'H' + i; });
                    levels = readings.map(function(r) { return r.waterLevel || r.level || 0; });
                    chartTitle = 'Flood Simulation';
                } else {
                    // Scale the flood simulation hydrograph so its peak matches the storm's peak
                    var readings = stormData.flood_simulation.readings || [];
                    var storm = stormData.storm_responses.responses.find(function(r) { return r.storm_id === selectedStorm; });

                    labels = readings.map(function(r, i) { return r.timestamp ? r.timestamp.split('T')[1].substring(0,5) : 'H' + i; });
                    var rawLevels = readings.map(function(r) { return r.waterLevel || r.level || 0; });

                    if (storm) {
                        // Scale: keep base level, stretch the rise to match storm peak
                        var simBase = Math.min.apply(null, rawLevels);
                        var simPeak = Math.max.apply(null, rawLevels);
                        var simRise = simPeak - simBase;
                        var stormRise = storm.peak_level_m - simBase;
                        var scaleFactor = simRise > 0 ? stormRise / simRise : 1;

                        levels = rawLevels.map(function(v) {
                            return simBase + (v - simBase) * scaleFactor;
                        });
                        chartTitle = selectedStorm + ' (peak: ' + storm.peak_level_m.toFixed(2) + 'm)';
                    } else {
                        levels = rawLevels;
                        chartTitle = selectedStorm;
                    }
                }

                var n = labels.length;
                var datasets = [
                    {
                        label: chartTitle,
                        data: levels,
                        borderColor: '#2196F3',
                        backgroundColor: 'rgba(33,150,243,0.1)',
                        fill: true,
                        tension: 0.3,
                        pointRadius: 1,
                        borderWidth: 2
                    }
                ];

                if (fs.FloodAlert) datasets.push({
                    label: 'Alert (' + fs.FloodAlert.toFixed(1) + 'm)',
                    data: Array(n).fill(fs.FloodAlert),
                    borderColor: '#FFC107', borderDash: [5,5], borderWidth: 1, pointRadius: 0, fill: false
                });
                if (fs.FloodWarning) datasets.push({
                    label: 'Warning (' + fs.FloodWarning.toFixed(1) + 'm)',
                    data: Array(n).fill(fs.FloodWarning),
                    borderColor: '#FF9800', borderDash: [5,5], borderWidth: 1, pointRadius: 0, fill: false
                });
                if (fs.SevereFloodWarning) {
                    var severeIdx = datasets.length;
                    datasets.push({
                        label: 'Severe (' + fs.SevereFloodWarning.toFixed(1) + 'm)',
                        data: Array(n).fill(fs.SevereFloodWarning),
                        borderColor: '#F44336', borderDash: [5,5], borderWidth: 1, pointRadius: 0, fill: false
                    });
                    // Red shading: invisible copy of main line, fills down to the severe line
                    datasets.push({
                        label: '_severe_fill',
                        data: levels.slice(),
                        borderWidth: 0,
                        pointRadius: 0,
                        fill: { target: severeIdx, above: 'rgba(244,67,54,0.25)', below: 'rgba(0,0,0,0)' },
                        tension: 0.3
                    });
                }

                currentChart = new Chart(ctx, {
                    type: 'line',
                    data: { labels: labels, datasets: datasets },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        interaction: { intersect: false, mode: 'index' },
                        plugins: {
                            legend: {
                                position: 'top',
                                labels: {
                                    usePointStyle: true, boxWidth: 8, font: { size: 11 },
                                    filter: function(item) { return item.text.charAt(0) !== '_'; }
                                }
                            },
                            tooltip: {
                                filter: function(item) { return item.dataset.label.charAt(0) !== '_'; },
                                callbacks: {
                                    label: function(ctx) {
                                        return ctx.dataset.label + ': ' + ctx.parsed.y.toFixed(2) + 'm';
                                    }
                                }
                            }
                        },
                        scales: {
                            x: { title: { display: true, text: 'Time' }, ticks: { maxTicksLimit: 12, font: { size: 10 } } },
                            y: { title: { display: true, text: 'Water Level (m)' }, min: 0 }
                        }
                    }
                });

                // Stats for timeline
                var bar = document.getElementById('storm-stats-bar');
                var simMax = Math.max.apply(null, levels);
                var minLevel = Math.min.apply(null, levels);

                // Show storm peak if a storm is selected, otherwise flood sim max
                var peakLabel, peakValue;
                if (selectedStorm !== 'sim') {
                    var storm = stormData.storm_responses.responses.find(function(r) { return r.storm_id === selectedStorm; });
                    if (storm) {
                        peakLabel = 'Storm Peak';
                        peakValue = storm.peak_level_m;
                    } else {
                        peakLabel = 'Peak';
                        peakValue = simMax;
                    }
                } else {
                    peakLabel = 'Peak';
                    peakValue = simMax;
                }

                bar.innerHTML = [
                    '<span><b>' + peakLabel + ':</b> ' + peakValue.toFixed(2) + 'm</span>',
                    '<span><b>Base:</b> ' + minLevel.toFixed(2) + 'm</span>',
                    '<span><b>Rise:</b> ' + (peakValue - minLevel).toFixed(2) + 'm</span>',
                    '<span><b>Duration:</b> ' + n + ' hours</span>',
                ].join('');
            }

            // ================================================================
            // Tab 2: Worst Storms
            // ================================================================
            function renderWorstStorms() {
                var ctx = document.getElementById('storm-chart').getContext('2d');
                if (currentChart) currentChart.destroy();

                var responses = stormData.storm_responses.responses || [];
                var fs = stormData.flood_stages || {};

                // Top 20 by peak level
                var sorted = responses.slice().sort(function(a, b) {
                    return b.peak_level_m - a.peak_level_m;
                }).slice(0, 20);

                var labels = sorted.map(function(r) { return r.name ? r.name + ' (' + r.storm_id + ')' : r.storm_id; });
                var values = sorted.map(function(r) { return r.peak_level_m; });

                var alertVal = fs.FloodAlert || Infinity;
                var warnVal = fs.FloodWarning || Infinity;
                var severeVal = fs.SevereFloodWarning || Infinity;

                var colors = values.map(function(v) {
                    if (v >= severeVal) return 'rgba(244,67,54,0.8)';
                    if (v >= warnVal) return 'rgba(255,152,0,0.8)';
                    if (v >= alertVal) return 'rgba(255,193,7,0.8)';
                    return 'rgba(76,175,80,0.8)';
                });

                currentChart = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: labels,
                        datasets: [{
                            label: 'Peak Level (m)',
                            data: values,
                            backgroundColor: colors,
                            borderColor: colors.map(function(c) { return c.replace('0.8', '1'); }),
                            borderWidth: 1
                        }]
                    },
                    options: {
                        indexAxis: 'y',
                        responsive: true,
                        maintainAspectRatio: false,
                        onClick: function(evt, elements) {
                            if (elements.length > 0) {
                                var idx = elements[0].index;
                                var stormId = sorted[idx].storm_id;
                                // Switch to timeline tab with this storm selected
                                var selector = document.getElementById('storm-selector');
                                if (selector) {
                                    selector.value = stormId;
                                }
                                switchTab(1);
                            }
                        },
                        plugins: {
                            legend: { display: false },
                            tooltip: {
                                callbacks: {
                                    label: function(ctx) {
                                        var r = sorted[ctx.dataIndex];
                                        var status = '';
                                        if (r.exceeded_severe) status = ' (Severe)';
                                        else if (r.exceeded_warning) status = ' (Warning)';
                                        else if (r.exceeded_alert) status = ' (Alert)';
                                        return ctx.parsed.x.toFixed(2) + 'm' + status;
                                    }
                                }
                            }
                        },
                        scales: {
                            x: { title: { display: true, text: 'Peak Water Level (m)' }, min: 0 },
                            y: { ticks: { font: { size: 9 } } }
                        }
                    }
                });

                // Stats
                var bar = document.getElementById('storm-stats-bar');
                bar.innerHTML = [
                    '<span><b>Top 20 events shown</b></span>',
                    '<span style="color:#F44336;">Click a bar to view timeline</span>',
                ].join('');
            }
""".replace('__STORM_OPT__', _storm_opt('r'))
