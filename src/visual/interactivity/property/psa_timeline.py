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
Property storm analysis — Flood Timeline tab.

Tab 1: Hydrograph with water level, property elevation,
floor threshold, gauge elevations, and flood fill shading.
"""


def get_js() -> str:
    """Return JS fragment for flood timeline tab."""
    return """
            // ================================================================
            // Tab 1: Flood Timeline (hydrograph for selected storm)
            // ================================================================
            function renderTimeline(selectedStormId) {
                var content = document.getElementById('prop-storm-content');
                if (currentChart) { currentChart.destroy(); currentChart = null; }
                if (!propStormData || !propStormData.flood_events || propStormData.flood_events.length === 0) {
                    content.innerHTML = '<p style="color:#999;text-align:center;margin-top:40px;">No flood events</p>';
                    return;
                }

                var events = propStormData.flood_events.filter(function(e) { return e.flooded; });
                if (events.length === 0) {
                    content.innerHTML = '<p style="color:#999;text-align:center;margin-top:40px;">No flooded events with hydrograph data</p>';
                    return;
                }
                var info = propStormData.property_info || {};
                var elevation = info.elevation_m || 0;
                var floorLevel = info.floor_level_m || 0;
                var threshold = elevation + floorLevel;
                var nearestGauges = propStormData.nearest_gauges || [];

                // Storm selector
                var selectorHtml = '<div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">' +
                    '<span style="font-size:11px;font-weight:600;color:#555;">Storm:</span>' +
                    '<select id="prop-timeline-select" style="flex:1;padding:3px 6px;font-size:11px;border:1px solid #ddd;border-radius:3px;">';
                events.forEach(function(e, i) {
                    var sel = (selectedStormId && e.storm_id === selectedStormId) || (!selectedStormId && i === 0) ? ' selected' : '';
                    selectorHtml += '<option value="' + e.storm_id + '"' + sel + '>' +
                        e.storm_id + ' (depth: ' + e.flood_depth_m.toFixed(2) + 'm, damage: ' + (e.damage_ratio * 100).toFixed(0) + '%)</option>';
                });
                selectorHtml += '</select></div>';

                content.innerHTML = selectorHtml +
                    '<canvas id="prop-timeline-chart" height="300"></canvas>' +
                    '<div id="prop-timeline-stats" style="display:flex;gap:16px;flex-wrap:wrap;font-size:11px;color:#555;padding:8px 0;border-top:1px solid #eee;"></div>';

                document.getElementById('prop-timeline-select').onchange = function() {
                    renderTimeline(this.value);
                };

                // Get selected event
                var event = events[0];
                if (selectedStormId) {
                    var found = events.find(function(e) { return e.storm_id === selectedStormId; });
                    if (found) event = found;
                }

                var readings = event.readings || [];
                if (readings.length === 0) {
                    document.getElementById('prop-timeline-stats').innerHTML =
                        '<span style="color:#999;">No hydrograph readings for this storm</span>';
                    return;
                }

                var hours = readings.map(function(r) { return r.hour; });
                var wseData = readings.map(function(r) { return r.wse_m; });

                // Build datasets: reference lines on left axis, flood depth on right axis
                var datasets = [];

                // Gauge elevations (river level — local minima, lowest lines)
                var gaugeColors = ['#B71C1C', '#E65100', '#4A148C'];
                var gaugeStyles = [[4, 3], [6, 3], [8, 4]];
                nearestGauges.forEach(function(g, gi) {
                    var gaugeElev = g.gauge_elevation_m;
                    var isSynth = (g.gauge_id || '').indexOf('SYNTH') === 0;
                    var prefix = isSynth ? '\u2605 ' : '';
                    if (typeof gaugeElev === 'number' && gaugeElev > 0) {
                        datasets.push({
                            label: prefix + g.gauge_id + ' Elev (' + gaugeElev.toFixed(1) + 'm)',
                            data: new Array(readings.length).fill(gaugeElev),
                            borderColor: gaugeColors[gi % 3],
                            borderDash: gaugeStyles[gi % 3],
                            pointRadius: 0,
                            borderWidth: isSynth ? 2 : 1.5,
                            fill: false
                        });
                    }
                    // Show flood stages for the synthetic gauge
                    if (isSynth && g.flood_stages) {
                        var fs = g.flood_stages;
                        if (fs.severe) {
                            datasets.push({
                                label: '\u2605 Severe (' + fs.severe.toFixed(1) + 'm)',
                                data: new Array(readings.length).fill(fs.severe),
                                borderColor: '#d32f2f',
                                borderDash: [8, 4],
                                pointRadius: 0,
                                borderWidth: 1.5,
                                fill: false
                            });
                        }
                        if (fs.warning) {
                            datasets.push({
                                label: '\u2605 Warning (' + fs.warning.toFixed(1) + 'm)',
                                data: new Array(readings.length).fill(fs.warning),
                                borderColor: '#ff9800',
                                borderDash: [6, 3],
                                pointRadius: 0,
                                borderWidth: 1,
                                fill: false
                            });
                        }
                        if (fs.alert) {
                            datasets.push({
                                label: '\u2605 Alert (' + fs.alert.toFixed(1) + 'm)',
                                data: new Array(readings.length).fill(fs.alert),
                                borderColor: '#ffc107',
                                borderDash: [4, 3],
                                pointRadius: 0,
                                borderWidth: 1,
                                fill: false
                            });
                        }
                    }
                });

                // Property ground elevation (above gauge elevations)
                datasets.push({
                    label: 'Property Ground (' + elevation.toFixed(1) + 'm)',
                    data: new Array(readings.length).fill(elevation),
                    borderColor: '#1565C0',
                    borderDash: [2, 2],
                    pointRadius: 0,
                    borderWidth: 1.5,
                    fill: false
                });

                // Property flood threshold (elevation + floor level — highest reference)
                var floorIdx = datasets.length;
                datasets.push({
                    label: 'Property Floor (' + threshold.toFixed(2) + 'm)',
                    data: new Array(readings.length).fill(threshold),
                    borderColor: '#f44336',
                    borderDash: [6, 3],
                    pointRadius: 0,
                    borderWidth: 2,
                    fill: false
                });

                // Water surface elevation line (absolute elevation on left axis)
                datasets.push({
                    label: 'Water Level (m AOD)',
                    data: wseData,
                    borderColor: '#ff9800',
                    backgroundColor: 'rgba(255,152,0,0.1)',
                    fill: true,
                    tension: 0.3,
                    pointRadius: 0,
                    borderWidth: 2,
                    spanGaps: true
                });

                // Red shading where water exceeds property floor
                datasets.push({
                    label: '_flood_fill',
                    data: wseData.slice(),
                    borderWidth: 0,
                    pointRadius: 0,
                    fill: { target: floorIdx, above: 'rgba(244,67,54,0.25)', below: 'rgba(0,0,0,0)' },
                    tension: 0.3
                });

                var ctx = document.getElementById('prop-timeline-chart').getContext('2d');
                currentChart = new Chart(ctx, {
                    type: 'line',
                    data: { labels: hours, datasets: datasets },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        interaction: { mode: 'index', intersect: false },
                        plugins: {
                            legend: {
                                position: 'top',
                                labels: {
                                    font: { size: 9 }, boxWidth: 12,
                                    filter: function(item) { return item.text.charAt(0) !== '_'; }
                                }
                            },
                            title: { display: true, text: 'Flood Timeline: ' + event.storm_id, font: { size: 13 } },
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
                            x: { title: { display: true, text: 'Hour' } },
                            y: { title: { display: true, text: 'Elevation (m AOD)' }, position: 'left' }
                        }
                    }
                });

                // Stats
                var floodedHours = wseData.filter(function(w) { return w !== null && w > threshold; }).length;
                var waterHours = wseData.filter(function(w) { return w !== null && w > elevation; }).length;
                var peakWse = wseData.filter(function(w) { return w !== null; });
                var maxWse = peakWse.length > 0 ? Math.max.apply(null, peakWse) : 0;
                var maxAboveFloor = maxWse > threshold ? (maxWse - threshold) : 0;
                document.getElementById('prop-timeline-stats').innerHTML = [
                    '<span>Peak above floor: <b>' + maxAboveFloor.toFixed(2) + 'm</b></span>',
                    '<span>Peak depth: <b>' + event.flood_depth_m.toFixed(2) + 'm</b></span>',
                    '<span>Damage: <b>' + (event.damage_ratio * 100).toFixed(1) + '%</b></span>',
                    '<span>Arrival: <b>Hr ' + (event.arrival_time_hrs !== null ? event.arrival_time_hrs : '-') + '</b></span>',
                    '<span>Peak: <b>Hr ' + (event.peak_time_hrs !== null ? event.peak_time_hrs : '-') + '</b></span>',
                    '<span>Flooded: <b>' + floodedHours + '/' + readings.length + ' hrs</b></span>',
                    '<span>Water above ground: <b>' + waterHours + ' hrs</b></span>',
                    '<span>Floor: <b>' + threshold.toFixed(2) + 'm</b> (' + elevation.toFixed(1) + ' + ' + floorLevel.toFixed(2) + ')</span>',
                ].join('');
            }
"""
