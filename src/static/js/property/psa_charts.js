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

            function renderDistribution() {
                var content = document.getElementById('prop-storm-content');
                if (currentChart) { currentChart.destroy(); currentChart = null; }
                if (!propStormData || !propStormData.flood_events || propStormData.flood_events.length === 0) {
                    content.innerHTML = '<p style="color:#999;text-align:center;margin-top:40px;">No flood events for this property</p>';
                    return;
                }

                var events = propStormData.flood_events.filter(function(e) { return e.flooded; });
                var depths = events.map(function(e) { return e.flood_depth_m; }).filter(function(d) { return typeof d === 'number' && isFinite(d) && d > 0; });
                var summary = propStormData.summary || {};
                var info = propStormData.property_info || {};

                if (depths.length === 0) {
                    content.innerHTML = '<p style="color:#999;text-align:center;margin-top:40px;">No valid flood depth data</p>';
                    return;
                }

                // Build histogram bins (0.2m intervals)
                var maxDepth = Math.max.apply(null, depths);
                var binSize = 0.2;
                var nBins = Math.ceil(maxDepth / binSize) + 1;
                if (!isFinite(nBins) || nBins < 1) nBins = 1;
                if (nBins > 500) nBins = 500;
                var bins = new Array(nBins).fill(0);
                var labels = [];
                for (var b = 0; b < nBins; b++) {
                    labels.push((b * binSize).toFixed(1));
                    depths.forEach(function(d) {
                        if (d >= b * binSize && d < (b + 1) * binSize) bins[b]++;
                    });
                }

                content.innerHTML =
                    '<div style="display:flex;gap:12px;margin-bottom:8px;">' +
                    '<div style="flex:1;">' +
                    '<canvas id="prop-dist-chart" height="260"></canvas>' +
                    '</div></div>' +
                    '<div id="prop-dist-stats" style="display:flex;gap:16px;flex-wrap:wrap;font-size:11px;color:#555;padding:8px 0;border-top:1px solid #eee;"></div>';

                var ctx = document.getElementById('prop-dist-chart').getContext('2d');
                currentChart = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: labels,
                        datasets: [{
                            label: 'Flood Events',
                            data: bins,
                            backgroundColor: 'rgba(33,150,243,0.6)',
                            borderColor: 'rgba(33,150,243,1)',
                            borderWidth: 1
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { display: false },
                            title: { display: true, text: 'Flood Depth Distribution', font: { size: 13 } }
                        },
                        scales: {
                            x: { title: { display: true, text: 'Flood Depth (m)' } },
                            y: { title: { display: true, text: 'Number of Events' }, beginAtZero: true, ticks: { stepSize: 1 } }
                        }
                    }
                });

                // Stats
                var meanDepth = depths.reduce(function(a, b) { return a + b; }, 0) / depths.length;
                var gaugeFloods = summary.severe_at_nearest_gauge || summary.floods_at_nearest_gauge || 0;
                var propFloods = summary.floods_at_property || 0;
                var ratio = gaugeFloods > 0 ? (propFloods / gaugeFloods * 100).toFixed(1) : '0.0';

                document.getElementById('prop-dist-stats').innerHTML = [
                    '<span>Events: <b>' + depths.length + '</b></span>',
                    '<span>Mean depth: <b>' + meanDepth.toFixed(2) + 'm</b></span>',
                    '<span>Max depth: <b>' + maxDepth.toFixed(2) + 'm</b></span>',
                    '<span>Max damage: <b>' + ((summary.max_damage_ratio || 0) * 100).toFixed(1) + '%</b></span>',
                    '<span>Gauge severe: <b>' + gaugeFloods + '</b></span>',
                    '<span>Gauge&rarr;Property: <b>' + ratio + '%</b></span>',
                    '<span>Elevation: <b>' + (info.elevation_m || 0).toFixed(1) + 'm</b></span>',
                    '<span>Floor level: <b>' + (info.floor_level_m || 0).toFixed(2) + 'm</b></span>',
                ].join('');
            }

            // ================================================================
            // Tab 2: Worst Storms (horizontal bar chart)
            // ================================================================
            function renderWorstStorms() {
                var content = document.getElementById('prop-storm-content');
                if (currentChart) { currentChart.destroy(); currentChart = null; }
                if (!propStormData || !propStormData.flood_events || propStormData.flood_events.length === 0) {
                    content.innerHTML = '<p style="color:#999;text-align:center;margin-top:40px;">No flood events</p>';
                    return;
                }

                var events = propStormData.flood_events.filter(function(e) { return e.flooded; }).sort(function(a, b) {
                    return b.flood_depth_m - a.flood_depth_m;
                });
                var top = events.slice(0, 20);

                var labels = top.map(function(e) { return e.storm_id.substring(0, 16); });
                var depths = top.map(function(e) { return e.flood_depth_m; });
                var colors = depths.map(function(d) {
                    if (d >= 2.0) return '#d32f2f';
                    if (d >= 1.0) return '#f57c00';
                    if (d >= 0.5) return '#fbc02d';
                    return '#42a5f5';
                });

                content.innerHTML =
                    '<canvas id="prop-worst-chart" height="350"></canvas>' +
                    '<div id="prop-worst-stats" style="display:flex;gap:16px;font-size:11px;color:#555;padding:8px 0;border-top:1px solid #eee;"></div>';

                var ctx = document.getElementById('prop-worst-chart').getContext('2d');
                currentChart = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: labels,
                        datasets: [{
                            label: 'Flood Depth (m)',
                            data: depths,
                            backgroundColor: colors,
                            borderWidth: 0
                        }]
                    },
                    options: {
                        indexAxis: 'y',
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { display: false },
                            title: { display: true, text: 'Worst Storms by Flood Depth', font: { size: 13 } }
                        },
                        scales: {
                            x: { title: { display: true, text: 'Flood Depth (m)' }, beginAtZero: true },
                            y: { ticks: { font: { size: 10 } } }
                        },
                        onClick: function(evt, elems) {
                            if (elems && elems.length > 0) {
                                var idx = elems[0].index;
                                var ev = top[idx];
                                if (ev && ev.storm_id) {
                                    switchTab(1, ev.storm_id);
                                }
                            }
                        }
                    }
                });

                document.getElementById('prop-worst-stats').innerHTML = [
                    '<span><b>Top ' + top.length + ' storms shown</b></span>',
                    '<span style="color:#1976d2;">Click a bar to view depth vs time</span>',
                ].join('');
            }
