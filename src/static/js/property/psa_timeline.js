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

            function renderTimeline(selectedStormId) {
                var content = document.getElementById('prop-storm-content');
                if (currentChart) { currentChart.destroy(); currentChart = null; }
                if (!propStormData || !propStormData.flood_events || propStormData.flood_events.length === 0) {
                    content.innerHTML = '<p style="color:var(--muted-2);text-align:center;margin-top:var(--space-inset);">No flood events</p>';
                    return;
                }

                var events = propStormData.flood_events.filter(function(e) { return e.flooded; });
                if (events.length === 0) {
                    content.innerHTML = '<p style="color:var(--muted-2);text-align:center;margin-top:var(--space-inset);">No flooded events with hydrograph data</p>';
                    return;
                }
                var info = propStormData.property_info || {};
                var elevation = info.elevation_m || 0;
                var floorLevel = info.floor_level_m || 0;
                var threshold = elevation + floorLevel;
                var nearestGauges = propStormData.nearest_gauges || [];

                // Storm selector
                var selectorHtml = '<div style="display:flex;align-items:center;gap:var(--space-4);margin-bottom:var(--space-4);">' +
                    '<span style="font-size:var(--size-xs);font-weight:600;color:var(--text-2);">Storm:</span>' +
                    '<select id="prop-timeline-select" style="flex:1;padding:var(--space-2) var(--space-3);font-size:var(--size-xs);border:1px solid var(--line-strong);border-radius:var(--radius-sm);">';
                events.forEach(function(e, i) {
                    var sel = (selectedStormId && e.storm_id === selectedStormId) || (!selectedStormId && i === 0) ? ' selected' : '';
                    selectorHtml += '<option value="' + e.storm_id + '"' + sel + '>' +
                        __STORM_OPT__ + '</option>';
                });
                selectorHtml += '</select></div>';

                content.innerHTML = selectorHtml +
                    '<div id="prop-timeline-typhoon-banner"></div>' +
                    '<canvas id="prop-timeline-chart" height="300"></canvas>' +
                    '<div id="prop-timeline-stats" style="display:flex;gap:var(--space-8);flex-wrap:wrap;font-size:var(--size-xs);color:var(--text-2);padding:var(--space-4) 0;border-top:1px solid var(--line-soft);"></div>';

                document.getElementById('prop-timeline-select').onchange = function() {
                    renderTimeline(this.value);
                };

                // Get selected event
                var event = events[0];
                if (selectedStormId) {
                    var found = events.find(function(e) { return e.storm_id === selectedStormId; });
                    if (found) event = found;
                }

                // Typhoon banner — visible only when the selected storm was
                // paired with a typhoon by the severity-bucket linkage.
                var banner = document.getElementById('prop-timeline-typhoon-banner');
                if (banner) {
                    if (event.typhoon && event.typhoon.event_id) {
                        var t = event.typhoon;
                        var peak = (t.peak_wind_ms != null) ? t.peak_wind_ms.toFixed(1) : '?';
                        var wd = (t.wind_damage_ratio != null) ? (t.wind_damage_ratio * 100).toFixed(1) + '%' : '—';
                        var wdColor = (t.wind_damage_ratio || 0) >= 0.5 ? Theme.value('red')
                                    : (t.wind_damage_ratio || 0) >= 0.1 ? Theme.value('amber')
                                    : Theme.value('text');
                        banner.innerHTML =
                            '<div style="background:linear-gradient(90deg,var(--warn-bg-warm) 0%,var(--warn-line-pale) 100%);' +
                            'border:1px solid var(--amber-dark);border-left:5px solid var(--orange-deep);' +
                            'border-radius:var(--radius-4);padding:var(--space-3) var(--space-6);margin:var(--space-2) 0 var(--space-4);' +
                            'display:flex;align-items:center;gap:var(--space-6);font-size:var(--size-sm);">' +
                              '<span style="font-size:var(--size-18);">⚡</span>' +
                              '<span style="font-weight:700;color:var(--orange-deep);letter-spacing:0.5px;">TYPHOON</span>' +
                              '<span style="color:var(--text);">' + (t.event_id || '?') + ' &nbsp;·&nbsp; ' +
                                  '<b>' + (t.scenario_family || '?') + '</b> family</span>' +
                              '<span style="color:var(--text);">peak <b>' + peak + ' m/s</b></span>' +
                              '<span style="color:' + wdColor + ';">wind damage <b>' + wd + '</b></span>' +
                            '</div>';
                    } else {
                        banner.innerHTML = '';
                    }
                }

                var readings = event.readings || [];
                if (readings.length === 0) {
                    document.getElementById('prop-timeline-stats').innerHTML =
                        '<span style="color:var(--muted-2);">No hydrograph readings for this storm</span>';
                    return;
                }

                var hours = readings.map(function(r) { return r.hour; });
                var wseData = readings.map(function(r) { return r.wse_m; });

                // Build datasets: reference lines on left axis, flood depth on right axis
                var datasets = [];

                // Gauge elevations (river level — local minima, lowest lines)
                var gaugeColors = [Theme.value('red-deep'), Theme.value('amber-deep'), Theme.value('purple-dark')];
                var gaugeStyles = [[4, 3], [6, 3], [8, 4]];
                nearestGauges.forEach(function(g, gi) {
                    var gaugeElev = g.gauge_elevation_m;
                    var isSynth = (g.gauge_id || '').indexOf('SYNTH') === 0;
                    var prefix = isSynth ? '★ ' : '';
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
                                label: '★ Severe (' + fs.severe.toFixed(1) + 'm)',
                                data: new Array(readings.length).fill(fs.severe),
                                borderColor: Theme.value('red'),
                                borderDash: [8, 4],
                                pointRadius: 0,
                                borderWidth: 1.5,
                                fill: false
                            });
                        }
                        if (fs.warning) {
                            datasets.push({
                                label: '★ Warning (' + fs.warning.toFixed(1) + 'm)',
                                data: new Array(readings.length).fill(fs.warning),
                                borderColor: Theme.value('amber-bright'),
                                borderDash: [6, 3],
                                pointRadius: 0,
                                borderWidth: 1,
                                fill: false
                            });
                        }
                        if (fs.alert) {
                            datasets.push({
                                label: '★ Alert (' + fs.alert.toFixed(1) + 'm)',
                                data: new Array(readings.length).fill(fs.alert),
                                borderColor: Theme.value('amber-yellow'),
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
                    borderColor: Theme.value('accent-mid'),
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
                    borderColor: Theme.value('red-bright'),
                    borderDash: [6, 3],
                    pointRadius: 0,
                    borderWidth: 2,
                    fill: false
                });

                // Water surface elevation line (absolute elevation on left axis)
                datasets.push({
                    label: 'Water Level (m AOD)',
                    data: wseData,
                    borderColor: Theme.value('amber-bright'),
                    backgroundColor: Theme.value('chart-wash-amber'),
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
                    fill: { target: floorIdx, above: Theme.value('chart-fill-danger'), below: Theme.value('chart-transparent') },
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
                            title: { display: true, text: 'Flood Timeline: ' + __STORM_TITLE__, font: { size: 13 } },
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
