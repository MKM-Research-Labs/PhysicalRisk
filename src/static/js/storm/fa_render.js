
            // ================================================================
            // Leaflet mini-map
            // ================================================================
            var miniMap = null;
            var gaugeMarkers = {};
            var propMarkers = {};
            var floodCircles = [];

            function initMiniMap() {
                var container = document.getElementById('anim-map-container');
                if (miniMap) {
                    miniMap.remove();
                    miniMap = null;
                }
                container.style.height = '400px';

                miniMap = L.map(container, {
                    zoomControl: true,
                    attributionControl: false,
                }).setView([__MAP_LAT__, __MAP_LON__], 11);

                L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
                    maxZoom: 18,
                }).addTo(miniMap);

                setTimeout(function() { miniMap.invalidateSize(); }, 100);
            }

            function clearMapLayers() {
                Object.values(gaugeMarkers).forEach(function(m) { miniMap.removeLayer(m); });
                Object.values(propMarkers).forEach(function(m) { miniMap.removeLayer(m); });
                floodCircles.forEach(function(c) { miniMap.removeLayer(c); });
                gaugeMarkers = {};
                propMarkers = {};
                floodCircles = [];
            }

            // Fit the viewport to the loaded catchment's gauges + properties.
            // The initial setView() is only a placeholder until data arrives —
            // fitting to real coordinates keeps the map catchment-agnostic.
            function fitMiniMapBounds() {
                if (!miniMap || !animData || !animData.frames || !animData.frames.length) return;
                var frame = animData.frames[0];
                var coords = [];
                (frame.gauges || []).forEach(function(g) {
                    if (g.lat || g.lon) coords.push([g.lat, g.lon]);
                });
                (frame.properties || []).forEach(function(p) {
                    if (p.lat || p.lon) coords.push([p.lat, p.lon]);
                });
                if (!coords.length) return;
                miniMap.fitBounds(L.latLngBounds(coords), {padding: [40, 40], maxZoom: 13});
            }

            // ================================================================
            // Data loading
            // ================================================================
            function loadStormList() {
                var select = document.getElementById('anim-storm-select');
                select.innerHTML = '<option value="">Loading storms...</option>';
                var baseUrl = getBaseUrl();
                fetch(baseUrl + '/api/v1/propertyts/storms', {mode: 'cors'})
                    .then(function(r) { return r.json(); })
                    .then(function(data) {
                        select.innerHTML = '';
                        if (data.status !== 'success' || !data.storms || data.storms.length === 0) {
                            select.innerHTML = '<option value="">No flooding storms found</option>';
                            return;
                        }
                        // Add composite "All Storms" option first
                        var compOpt = document.createElement('option');
                        compOpt.value = 'COMPOSITE';
                        compOpt.textContent = 'All Storms (Worst Case Portfolio)';
                        select.appendChild(compOpt);

                        data.storms.forEach(function(s, i) {
                            var opt = document.createElement('option');
                            opt.value = s.storm_id;
                            opt.textContent = __STORM_OPT__;
                            select.appendChild(opt);
                        });
                        // Default to composite
                        loadStorm('COMPOSITE');
                    })
                    .catch(function(err) {
                        select.innerHTML = '<option value="">Error loading storms</option>';
                        console.error('Storm list error:', err);
                    });
            }

            function loadStorm(stormId) {
                if (!stormId) return;
                stopAnim();
                animFrame = 0;

                var statsBar = document.getElementById('anim-stats-bar');
                statsBar.innerHTML = '<span>Loading storm data...</span>';
                var baseUrl = getBaseUrl();

                var animUrl = stormId === 'COMPOSITE'
                    ? baseUrl + '/api/v1/propertyts/animate/composite'
                    : baseUrl + '/api/v1/propertyts/animate/' + stormId;
                fetch(animUrl, {mode: 'cors'})
                    .then(function(r) { return r.json(); })
                    .then(function(data) {
                        if (data.status !== 'success') {
                            statsBar.innerHTML = '<span style="color:red;">Error: ' + (data.message || 'Unknown') + '</span>';
                            return;
                        }
                        animData = data;
                        document.getElementById('anim-panel-title').textContent =
                            'Flood Animation — ' + stormId + ' (' + data.n_properties_affected + ' properties)';
                        renderFrame(0);
                        fitMiniMapBounds();
                    })
                    .catch(function(err) {
                        statsBar.innerHTML = '<span style="color:red;">Failed to load storm data</span>';
                        console.error('Animate error:', err);
                    });
            }

            // ================================================================
            // Rendering
            // ================================================================
            function renderFrame(hour) {
                if (!animData || !animData.frames || hour >= animData.frames.length) return;
                animFrame = hour;

                var frame = animData.frames[hour];
                clearMapLayers();

                // Gauge markers + flood circles
                frame.gauges.forEach(function(g) {
                    var color = gaugeColor(g.status);
                    var marker = L.circleMarker([g.lat, g.lon], {
                        radius: 6,
                        color: color,
                        fillColor: color,
                        fillOpacity: 0.9,
                        weight: 2,
                    }).addTo(miniMap);
                    marker.bindTooltip((g.name || g.gauge_id) + '<br>Level: ' + g.water_level_m.toFixed(2) + 'm<br>Status: ' + g.status,
                        {direction: 'top', offset: [0, -8]});
                    gaugeMarkers[g.gauge_id] = marker;

                    if (g.status !== 'normal') {
                        var radius = Math.min(hour * 80, 3000);
                        var opacity = g.status === 'severe' ? 0.2 : g.status === 'warning' ? 0.15 : 0.1;
                        var circle = L.circle([g.lat, g.lon], {
                            radius: radius,
                            color: color,
                            fillColor: color,
                            fillOpacity: opacity,
                            weight: 0,
                        }).addTo(miniMap);
                        floodCircles.push(circle);
                    }
                });

                // Property markers with wavefront coloring
                frame.properties.forEach(function(p) {
                    if (!p.arrived && !p.flooded) return;
                    var wfColor = wavefrontColor(p);
                    var radius = p.flooded ? Math.max(4, Math.min(8, 4 + p.depth_m * 2)) : 3;
                    var marker = L.circleMarker([p.lat, p.lon], {
                        radius: radius,
                        color: wfColor,
                        fillColor: wfColor,
                        fillOpacity: p.flooded ? 0.85 : 0.4,
                        weight: 1,
                    }).addTo(miniMap);
                    marker.bindTooltip(p.property_id + '<br>Depth: ' + p.depth_m.toFixed(2) + 'm' +
                        (p.flooded ? '<br><b>FLOODED</b><br><i>Click to view</i>' : ''),
                        {direction: 'top', offset: [0, -6]});
                    marker.on('click', (function(pid) {
                        return function() {
                            hidePanel();
                            if (window.viewPropertyDetails) {
                                window.viewPropertyDetails(pid);
                            } else if (window.PropertyStormAnalysis && window.PropertyStormAnalysis.show) {
                                window.PropertyStormAnalysis.show(pid);
                            } else {
                                document.dispatchEvent(new CustomEvent('propertyStormRequested', {
                                    detail: { propertyId: pid }, bubbles: true
                                }));
                            }
                        };
                    })(p.property_id));
                    propMarkers[p.property_id] = marker;
                });

                // Update stats bar
                var statsBar = document.getElementById('anim-stats-bar');
                statsBar.innerHTML =
                    '<span><b>Hour ' + hour + '</b> / 59</span>' +
                    '<span>Gauges flooded: <b>' + frame.stats.gauges_flooded + '</b></span>' +
                    '<span>Properties flooded: <b>' + frame.stats.properties_flooded + '</b></span>' +
                    '<span>Total depth: <b>' + frame.stats.total_depth_m.toFixed(1) + 'm</b></span>';

                document.getElementById('anim-scrubber').value = hour;
                document.getElementById('anim-hour-label').textContent = 'Hour ' + hour;
            }
