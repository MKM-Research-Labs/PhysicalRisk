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

            var basisSHDChart = null;

            function renderBasisSHD() {
                var container = document.getElementById('phc-chart-container');
                if (basisSHDChart) { basisSHDChart.destroy(); basisSHDChart = null; }

                var storms = phcData.storm_details || [];
                var nearestGauges = phcData.nearest_gauges || [];
                var propElev = phcData.elevation_m || 0;

                var primaryGauge = nearestGauges.find(function(ng) {
                    return ng.gauge_id.indexOf('SYNTH') !== 0;
                }) || nearestGauges[0] || {};

                var distanceKm = primaryGauge.distance_km || 0;
                var gaugeElev = primaryGauge.gauge_elevation_m || 0;
                var thresholds = primaryGauge.gauge_thresholds || {};
                var severeLevel = thresholds.severe_level || 0;

                // Sort by flood depth descending
                var sorted = storms.slice().sort(function(a, b) {
                    return b.flood_depth_m - a.flood_depth_m;
                });

                var withDepthCount = 0;
                var data = sorted.map(function(s, i) {
                    if (s.flood_depth_m > 0) withDepthCount++;
                    return {
                        x: i,
                        y: s.flood_depth_m,
                        stormId: s.storm_id,
                        gaugePeak: s.gauge_peak_m,
                        retention: s.retention_factor,
                        flooded: s.flooded,
                    };
                });

                // Summary
                var avgRetention = 0;
                storms.forEach(function(s) { avgRetention += s.retention_factor; });
                avgRetention = storms.length > 0 ? avgRetention / storms.length : 0;

                var summaryHtml =
                    '<div style="padding:8px 0 4px 0;font-size:12px;color:var(--text-2);">' +
                    '<b>Distance Effect:</b> Gauge ' + distanceKm.toFixed(1) + 'km from property' +
                    ' &nbsp;|&nbsp; Avg retention: ' + (avgRetention * 100).toFixed(0) + '%' +
                    ' &nbsp;|&nbsp; <b>' + withDepthCount + '</b> of <b>' + storms.length +
                    '</b> storms produce flood depth > 0 after decay' +
                    '</div>';

                container.innerHTML = summaryHtml +
                    '<div style="display:flex;flex:1;gap:8px;min-height:0;">' +
                    '<canvas id="basis-shd-decay" style="width:35%;min-width:250px;"></canvas>' +
                    '<canvas id="basis-shd-waterfall" style="flex:1;"></canvas>' +
                    '</div>';

                // --- Distance decay diagram ---
                _drawDistanceDecay(
                    document.getElementById('basis-shd-decay'),
                    distanceKm, avgRetention,
                    basisSelectedStorm ? storms.find(function(s) { return s.storm_id === basisSelectedStorm; }) : null
                );

                // --- Spread waterfall (right panel) ---
                _renderSpreadWaterfall('basis-shd-waterfall', 2);

                var bar = document.getElementById('phc-stats-bar');
                if (bar) {
                    var sd = phcData.spread_decomposition || {};
                    var shdSpread = sd.shd_spread_bps || 0;
                    bar.innerHTML =
                        '<span><b>Distance:</b> ' + distanceKm.toFixed(1) + 'km</span>' +
                        '<span><b>Avg Retention:</b> ' + (avgRetention * 100).toFixed(0) + '%</span>' +
                        '<span><b>Storms with depth:</b> ' + withDepthCount + '</span>' +
                        '<span><b>SHD Spread:</b> ' + shdSpread.toFixed(1) + ' bps</span>';
                }
            }

            // --- Distance decay canvas diagram ---
            function _drawDistanceDecay(canvas, distanceKm, avgRetention, selectedStorm) {
                var ctx = canvas.getContext('2d');
                var W = canvas.width = canvas.offsetWidth * (window.devicePixelRatio || 1);
                var H = canvas.height = canvas.offsetHeight * (window.devicePixelRatio || 1);
                ctx.scale(window.devicePixelRatio || 1, window.devicePixelRatio || 1);
                var w = canvas.offsetWidth;
                var h = canvas.offsetHeight;

                ctx.clearRect(0, 0, w, h);

                var pad = { top: 30, bottom: 40, left: 50, right: 20 };
                var plotW = w - pad.left - pad.right;
                var plotH = h - pad.top - pad.bottom;

                // X-axis: 0 to max(distanceKm * 1.5, 1) km
                var maxDist = Math.max(distanceKm * 1.5, 1);
                // Y-axis: retention 0 to 1
                function xPos(d) { return pad.left + plotW * (d / maxDist); }
                function yPos(r) { return pad.top + plotH * (1 - r); }

                // Draw decay curve (exponential-like: retention = 1 - d/25 for d<25km)
                ctx.beginPath();
                ctx.strokeStyle = Theme.value('accent');
                ctx.lineWidth = 2;
                for (var i = 0; i <= 100; i++) {
                    var d = maxDist * i / 100;
                    var ret = Math.max(0, 1 - d / 25);  // simplified decay model
                    var px = xPos(d);
                    var py = yPos(ret);
                    if (i === 0) ctx.moveTo(px, py);
                    else ctx.lineTo(px, py);
                }
                ctx.stroke();

                // Fill under curve
                ctx.lineTo(xPos(maxDist), yPos(0));
                ctx.lineTo(xPos(0), yPos(0));
                ctx.closePath();
                ctx.fillStyle = Theme.value('chart-fill-accent');
                ctx.fill();

                // Mark property distance
                var propRet = Math.max(0, 1 - distanceKm / 25);
                ctx.setLineDash([4, 3]);
                ctx.strokeStyle = Theme.value('red-bright');
                ctx.lineWidth = 1.5;
                ctx.beginPath();
                ctx.moveTo(xPos(distanceKm), yPos(0));
                ctx.lineTo(xPos(distanceKm), yPos(propRet));
                ctx.lineTo(xPos(0), yPos(propRet));
                ctx.stroke();
                ctx.setLineDash([]);

                // Property marker
                ctx.beginPath();
                ctx.arc(xPos(distanceKm), yPos(propRet), 5, 0, Math.PI * 2);
                ctx.fillStyle = Theme.value('red-bright');
                ctx.fill();

                // Gauge marker at origin
                ctx.beginPath();
                ctx.arc(xPos(0), yPos(1), 5, 0, Math.PI * 2);
                ctx.fillStyle = Theme.value('green-bright');
                ctx.fill();

                // Selected storm highlight
                if (selectedStorm) {
                    var stormRet = selectedStorm.retention_factor;
                    ctx.beginPath();
                    ctx.arc(xPos(distanceKm), yPos(stormRet), 8, 0, Math.PI * 2);
                    ctx.strokeStyle = Theme.value('amber-bright');
                    ctx.lineWidth = 2;
                    ctx.stroke();
                    ctx.fillStyle = Theme.value('amber-bright');
                    ctx.font = 'bold 9px Arial';
                    ctx.fillText('Storm ' + selectedStorm.storm_id, xPos(distanceKm) + 12, yPos(stormRet) + 3);
                }

                // Labels
                ctx.fillStyle = Theme.value('green-bright');
                ctx.font = 'bold 10px Arial';
                ctx.textAlign = 'center';
                ctx.fillText('Gauge', xPos(0), yPos(1) - 10);

                ctx.fillStyle = Theme.value('red-bright');
                ctx.fillText('Property', xPos(distanceKm), yPos(propRet) - 10);
                ctx.fillText(distanceKm.toFixed(1) + 'km', xPos(distanceKm), yPos(0) + 14);

                // Retention label
                ctx.fillStyle = Theme.value('accent-mid');
                ctx.font = '10px Arial';
                ctx.textAlign = 'left';
                ctx.fillText((propRet * 100).toFixed(0) + '%', xPos(0) + 4, yPos(propRet) - 4);

                // Axes
                ctx.strokeStyle = Theme.value('muted-2');
                ctx.lineWidth = 1;
                ctx.beginPath();
                ctx.moveTo(pad.left, pad.top);
                ctx.lineTo(pad.left, pad.top + plotH);
                ctx.lineTo(pad.left + plotW, pad.top + plotH);
                ctx.stroke();

                // Axis labels
                ctx.fillStyle = Theme.value('text-3');
                ctx.font = '10px Arial';
                ctx.textAlign = 'center';
                ctx.fillText('Distance (km)', pad.left + plotW / 2, h - 5);

                ctx.save();
                ctx.translate(12, pad.top + plotH / 2);
                ctx.rotate(-Math.PI / 2);
                ctx.fillText('Retention Factor', 0, 0);
                ctx.restore();

                // Title
                ctx.fillStyle = Theme.value('text');
                ctx.font = 'bold 11px Arial';
                ctx.textAlign = 'center';
                ctx.fillText('Distance Decay', w / 2, 14);
                ctx.textAlign = 'left';
            }
