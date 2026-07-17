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

            var spSimMap = null;
            var spSimGaugeMarkers = {};
            var spSimPropMarkers = {};
            var spSimFloodCircles = [];
            var spSimFrame = 0;
            var spSimPlaying = false;
            var spSimTimer = null;
            var spSimSpeed = 1;
            var spSimMapData = null;

            // ================================================================
            // Sim tab — DOM creation
            // ================================================================
            function createSimView() {
                var view = document.createElement('div');
                view.id = 'sp-sim-view';
                view.style.cssText = 'display:none;flex-direction:column;flex:1;overflow:hidden;';

                // Controls row
                var controls = document.createElement('div');
                controls.id = 'sp-sim-controls';
                controls.style.cssText = 'padding:8px 16px;border-bottom:1px solid #eee;display:flex;align-items:center;gap:10px;';

                var playBtn = document.createElement('button');
                playBtn.id = 'sp-sim-play-btn';
                playBtn.innerHTML = '&#9654;';
                playBtn.style.cssText = 'width:32px;height:32px;border:1px solid #ddd;border-radius:4px;background:#fff;cursor:pointer;font-size:14px;';
                playBtn.onclick = spTogglePlay;

                var speedBtns = document.createElement('div');
                speedBtns.style.cssText = 'display:flex;gap:4px;';
                [1,2,5].forEach(function(s) {
                    var btn = document.createElement('button');
                    btn.textContent = s + 'x';
                    btn.className = 'sp-sim-speed-btn';
                    btn.dataset.speed = s;
                    btn.style.cssText = 'padding:2px 8px;font-size:11px;border:1px solid #ddd;border-radius:3px;background:' + (s === 1 ? '#e3f2fd' : '#fff') + ';cursor:pointer;';
                    btn.onclick = function() { spSetSpeed(s); };
                    speedBtns.appendChild(btn);
                });

                var scrubber = document.createElement('input');
                scrubber.id = 'sp-sim-scrubber';
                scrubber.type = 'range';
                scrubber.min = '0';
                scrubber.max = '__SCRUBBER_MAX__';
                scrubber.value = '0';
                scrubber.style.cssText = 'flex:1;';
                scrubber.oninput = function() { spSeekTo(parseInt(this.value)); };

                var hourLabel = document.createElement('span');
                hourLabel.id = 'sp-sim-hour-label';
                hourLabel.style.cssText = 'font-size:12px;font-weight:600;min-width:55px;text-align:right;';
                hourLabel.textContent = 'Hour 0';

                controls.appendChild(playBtn);
                controls.appendChild(speedBtns);
                controls.appendChild(scrubber);
                controls.appendChild(hourLabel);

                // Stats bar
                var statsBar = document.createElement('div');
                statsBar.id = 'sp-sim-stats-bar';
                statsBar.style.cssText = 'padding:6px 16px;border-bottom:1px solid #eee;display:flex;gap:20px;font-size:11px;color:#666;background:#f9f9f9;';

                // Legend
                var legend = document.createElement('div');
                legend.style.cssText = 'padding:4px 16px;border-bottom:1px solid #eee;display:flex;gap:16px;font-size:10px;color:#666;background:#fff;align-items:center;';
                legend.innerHTML =
                    '<span style="font-weight:600;">Legend:</span>' +
                    '<span><span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#2196f3;margin-right:3px;vertical-align:middle;"></span>Approaching</span>' +
                    '<span><span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#ff9800;margin-right:3px;vertical-align:middle;"></span>Flooded</span>' +
                    '<span><span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#d32f2f;margin-right:3px;vertical-align:middle;"></span>Peak/Severe</span>' +
                    '<span style="margin-left:12px;"><span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#4caf50;margin-right:3px;vertical-align:middle;"></span>Gauge Normal</span>' +
                    '<span><span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#fbc02d;margin-right:3px;vertical-align:middle;"></span>Alert</span>' +
                    '<span><span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#f57c00;margin-right:3px;vertical-align:middle;"></span>Warning</span>' +
                    '<span><span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#d32f2f;margin-right:3px;vertical-align:middle;"></span>Severe</span>';

                // Map container
                var mapContainer = document.createElement('div');
                mapContainer.id = 'sp-sim-map-container';
                mapContainer.style.cssText = 'flex:1;position:relative;overflow:hidden;';

                view.appendChild(controls);
                view.appendChild(statsBar);
                view.appendChild(legend);
                view.appendChild(mapContainer);
                return view;
            }

            // ================================================================
            // Leaflet map init / cleanup
            // ================================================================
            function initSimMap() {
                var container = document.getElementById('sp-sim-map-container');
                if (!container) return;
                if (spSimMap) {
                    spSimMap.remove();
                    spSimMap = null;
                }
                spSimGaugeMarkers = {};
                spSimPropMarkers = {};
                spSimFloodCircles = [];
                spSimFrame = 0;

                spSimMap = L.map(container, {
                    zoomControl: true,
                    attributionControl: false,
                }).setView([__MAP_LAT__, __MAP_LON__], 11);

                L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
                    maxZoom: 18,
                }).addTo(spSimMap);

                setTimeout(function() { if (spSimMap) spSimMap.invalidateSize(); }, 100);
            }

            function clearSimMapLayers() {
                if (!spSimMap) return;
                Object.values(spSimGaugeMarkers).forEach(function(m) { spSimMap.removeLayer(m); });
                Object.values(spSimPropMarkers).forEach(function(m) { spSimMap.removeLayer(m); });
                spSimFloodCircles.forEach(function(c) { spSimMap.removeLayer(c); });
                spSimGaugeMarkers = {};
                spSimPropMarkers = {};
                spSimFloodCircles = [];
            }

            // Fit the viewport to the loaded catchment's gauges + properties.
            // The initial setView() is only a placeholder until data arrives —
            // fitting to real coordinates keeps the map catchment-agnostic.
            function spFitSimBounds() {
                if (!spSimMap || !spSimMapData || !spSimMapData.frames || !spSimMapData.frames.length) return;
                var frame = spSimMapData.frames[0];
                var coords = [];
                (frame.gauges || []).forEach(function(g) {
                    if (g.lat || g.lon) coords.push([g.lat, g.lon]);
                });
                (frame.properties || []).forEach(function(p) {
                    if (p.lat || p.lon) coords.push([p.lat, p.lon]);
                });
                if (!coords.length) return;
                spSimMap.fitBounds(L.latLngBounds(coords), {padding: [40, 40], maxZoom: 13});
            }

            // ================================================================
            // Sim map data loading
            // ================================================================
            function loadSimMapData(stormId) {
                if (!stormId) return;
                spStopAnim();
                spSimFrame = 0;
                var statsBar = document.getElementById('sp-sim-stats-bar');
                if (statsBar) statsBar.innerHTML = '<span>Loading storm data...</span>';

                var baseUrl = getBaseUrl();
                fetch(baseUrl + '/api/v1/propertyts/animate/' + stormId, {mode: 'cors'})
                    .then(function(r) { return r.json(); })
                    .then(function(data) {
                        if (data.status !== 'success') {
                            if (statsBar) statsBar.innerHTML = '<span style="color:red;">Error: ' + (data.message || 'Unknown') + '</span>';
                            return;
                        }
                        spSimMapData = data;
                        console.log('[StormPortfolio] Sim map loaded:', data.n_frames, 'frames');
                        renderSimFrame(0);
                        spFitSimBounds();
                    })
                    .catch(function(err) {
                        if (statsBar) statsBar.innerHTML = '<span style="color:red;">Failed to load storm</span>';
                        console.error('Sim map error:', err);
                    });
            }

            // ================================================================
            // Frame rendering
            // ================================================================
            function renderSimFrame(hour) {
                if (!spSimMapData || !spSimMapData.frames || hour >= spSimMapData.frames.length) return;
                if (!spSimMap) return;
                spSimFrame = hour;
                var frame = spSimMapData.frames[hour];
                clearSimMapLayers();

                // Gauge markers + flood circles
                frame.gauges.forEach(function(g) {
                    var color = spGaugeColor(g.status);
                    var marker = L.circleMarker([g.lat, g.lon], {
                        radius: 6,
                        color: color,
                        fillColor: color,
                        fillOpacity: 0.9,
                        weight: 2,
                    }).addTo(spSimMap);
                    marker.bindTooltip(g.gauge_id + '<br>Level: ' + g.water_level_m.toFixed(2) + 'm<br>Status: ' + g.status,
                        {direction: 'top', offset: [0, -8]});
                    spSimGaugeMarkers[g.gauge_id] = marker;

                    if (g.status !== 'normal') {
                        var radius = Math.min(hour * 80, 3000);
                        var opacity = g.status === 'severe' ? 0.2 : g.status === 'warning' ? 0.15 : 0.1;
                        var circle = L.circle([g.lat, g.lon], {
                            radius: radius,
                            color: color,
                            fillColor: color,
                            fillOpacity: opacity,
                            weight: 0,
                        }).addTo(spSimMap);
                        spSimFloodCircles.push(circle);
                    }
                });

                // Property markers with wavefront coloring
                frame.properties.forEach(function(p) {
                    if (!p.arrived && !p.flooded) return;
                    var wfColor = spWavefrontColor(p);
                    var pRadius = p.flooded ? Math.max(4, Math.min(8, 4 + p.depth_m * 2)) : 3;
                    var marker = L.circleMarker([p.lat, p.lon], {
                        radius: pRadius,
                        color: wfColor,
                        fillColor: wfColor,
                        fillOpacity: p.flooded ? 0.85 : 0.4,
                        weight: 1,
                    }).addTo(spSimMap);
                    marker.bindTooltip(p.property_id + '<br>Depth: ' + p.depth_m.toFixed(2) + 'm' +
                        (p.flooded ? '<br><b>FLOODED</b>' : ''),
                        {direction: 'top', offset: [0, -6]});
                    spSimPropMarkers[p.property_id] = marker;
                });

                // Update stats bar
                var statsBar = document.getElementById('sp-sim-stats-bar');
                if (statsBar) {
                    statsBar.innerHTML =
                        '<span><b>Hour ' + hour + '</b> / 59</span>' +
                        '<span>Gauges flooded: <b>' + frame.stats.gauges_flooded + '</b></span>' +
                        '<span>Properties flooded: <b>' + frame.stats.properties_flooded + '</b></span>' +
                        '<span>Total depth: <b>' + frame.stats.total_depth_m.toFixed(1) + 'm</b></span>';
                }
                var scrubber = document.getElementById('sp-sim-scrubber');
                if (scrubber) scrubber.value = hour;
                var hourLbl = document.getElementById('sp-sim-hour-label');
                if (hourLbl) hourLbl.textContent = 'Hour ' + hour;
            }

            // ================================================================
            // Playback controls
            // ================================================================
            function spTogglePlay() {
                if (spSimPlaying) spStopAnim(); else spStartAnim();
            }

            function spStartAnim() {
                spSimPlaying = true;
                var btn = document.getElementById('sp-sim-play-btn');
                if (btn) btn.innerHTML = '&#9646;&#9646;';
                spSimTimer = setInterval(function() {
                    if (spSimFrame >= __ANIM_MAX__) { spStopAnim(); return; }
                    renderSimFrame(spSimFrame + 1);
                }, 1000 / spSimSpeed);
            }

            function spStopAnim() {
                spSimPlaying = false;
                if (spSimTimer) clearInterval(spSimTimer);
                spSimTimer = null;
                var btn = document.getElementById('sp-sim-play-btn');
                if (btn) btn.innerHTML = '&#9654;';
            }

            function spSetSpeed(s) {
                spSimSpeed = s;
                document.querySelectorAll('.sp-sim-speed-btn').forEach(function(btn) {
                    btn.style.background = parseInt(btn.dataset.speed) === s ? '#e3f2fd' : '#fff';
                });
                if (spSimPlaying) { spStopAnim(); spStartAnim(); }
            }

            function spSeekTo(hour) {
                spStopAnim();
                renderSimFrame(hour);
            }
