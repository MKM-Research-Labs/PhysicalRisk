
            // ================================================================
            // Basis Explorer — SHE sub-tab
            // ================================================================
            var basisSHEChart = null;

            function renderBasisSHE() {
                var container = document.getElementById('phc-chart-container');
                if (basisSHEChart) { basisSHEChart.destroy(); basisSHEChart = null; }

                var storms = phcData.storm_details || [];
                var nearestGauges = phcData.nearest_gauges || [];
                var propElev = phcData.elevation_m || 0;
                var floorLevel = phcData.floor_level_m || 0;

                var primaryGauge = nearestGauges.find(function(ng) {
                    return ng.gauge_id.indexOf('SYNTH') !== 0;
                }) || nearestGauges[0] || {};

                var gaugeElev = primaryGauge.gauge_elevation_m || 0;
                var thresholds = primaryGauge.gauge_thresholds || {};
                var severeLevel = thresholds.severe_level || 0;

                // Height difference: water must exceed this to reach property
                var heightDiff = Math.max(0, propElev - gaugeElev);
                var floodThreshold = heightDiff + floorLevel;

                // Classify storms: does gauge peak produce water above property elevation?
                // Water above gauge = peak - bankfull (bankfull ~ severe - 0.5m)
                var bankfull = Math.max(0, severeLevel - 0.5);
                var reachCount = 0;
                var severeCount = 0;

                var sorted = storms.slice().sort(function(a, b) {
                    return b.gauge_peak_m - a.gauge_peak_m;
                });

                var data = sorted.map(function(s, i) {
                    var isSevere = s.exceeded_severe || false;
                    if (isSevere) severeCount++;
                    var waterAboveGauge = Math.max(0, s.gauge_peak_m - bankfull);
                    var reachesProperty = waterAboveGauge > floodThreshold;
                    if (reachesProperty) reachCount++;
                    return {
                        x: i,
                        y: s.gauge_peak_m,
                        stormId: s.storm_id,
                        isSevere: isSevere,
                        reachesProperty: reachesProperty,
                        waterAboveGauge: waterAboveGauge,
                    };
                });

                // Summary
                var summaryHtml =
                    '<div style="padding:8px 0 4px 0;font-size:12px;color:#555;">' +
                    '<b>Elevation Effect:</b> Gauge at ' + gaugeElev.toFixed(1) + 'm, ' +
                    'Property at ' + propElev.toFixed(1) + 'm ' +
                    '(+' + heightDiff.toFixed(1) + 'm, floor +' + floorLevel.toFixed(1) + 'm)' +
                    ' &nbsp;|&nbsp; <b>' + reachCount + '</b> of <b>' + severeCount +
                    '</b> severe storms produce water above property level' +
                    '</div>';

                // Cross-section diagram (canvas) + spread waterfall
                container.innerHTML = summaryHtml +
                    '<div style="display:flex;flex:1;gap:8px;min-height:0;">' +
                    '<canvas id="basis-she-section" style="width:35%;min-width:250px;"></canvas>' +
                    '<canvas id="basis-she-waterfall" style="flex:1;"></canvas>' +
                    '</div>';

                // --- Cross-section diagram ---
                _drawElevationSection(
                    document.getElementById('basis-she-section'),
                    gaugeElev, propElev, floorLevel, severeLevel, bankfull,
                    basisSelectedStorm ? sorted.find(function(s) { return s.storm_id === basisSelectedStorm; }) : null
                );

                // --- Spread waterfall (right panel) ---
                _renderSpreadWaterfall('basis-she-waterfall', 1);

                var bar = document.getElementById('phc-stats-bar');
                if (bar) {
                    var sd = phcData.spread_decomposition || {};
                    var sheSpread = sd.she_spread_bps || 0;
                    bar.innerHTML =
                        '<span><b>Severe storms:</b> ' + severeCount + '</span>' +
                        '<span><b>Reach property level:</b> ' + reachCount + '</span>' +
                        '<span><b>Filtered by elevation:</b> ' + (severeCount - reachCount) + '</span>' +
                        '<span><b>SHE Spread:</b> ' + sheSpread.toFixed(1) + ' bps</span>';
                }
            }

            // --- Elevation cross-section canvas drawing ---
            function _drawElevationSection(canvas, gaugeElev, propElev, floorLevel,
                                            severeLevel, bankfull, selectedStorm) {
                var ctx = canvas.getContext('2d');
                var W = canvas.width = canvas.offsetWidth * (window.devicePixelRatio || 1);
                var H = canvas.height = canvas.offsetHeight * (window.devicePixelRatio || 1);
                ctx.scale(window.devicePixelRatio || 1, window.devicePixelRatio || 1);
                var w = canvas.offsetWidth;
                var h = canvas.offsetHeight;

                ctx.clearRect(0, 0, w, h);

                var pad = { top: 30, bottom: 30, left: 50, right: 20 };
                var plotW = w - pad.left - pad.right;
                var plotH = h - pad.top - pad.bottom;

                // Y-axis: elevation range
                var allElev = [0, gaugeElev, propElev, propElev + floorLevel, severeLevel + gaugeElev];
                if (selectedStorm) allElev.push(selectedStorm.gauge_peak_m + gaugeElev);
                var minE = Math.min.apply(null, allElev) - 0.5;
                var maxE = Math.max.apply(null, allElev) + 1;

                function yPos(elev) {
                    return pad.top + plotH * (1 - (elev - minE) / (maxE - minE));
                }

                // Ground profile
                var gaugeX = pad.left + plotW * 0.2;
                var propX = pad.left + plotW * 0.75;

                // Draw ground
                ctx.beginPath();
                ctx.moveTo(pad.left, yPos(gaugeElev));
                ctx.lineTo(gaugeX, yPos(gaugeElev));
                ctx.lineTo(propX, yPos(propElev));
                ctx.lineTo(w - pad.right, yPos(propElev));
                ctx.lineTo(w - pad.right, yPos(minE));
                ctx.lineTo(pad.left, yPos(minE));
                ctx.closePath();
                ctx.fillStyle = '#E8D5B7';
                ctx.fill();
                ctx.strokeStyle = '#8D6E63';
                ctx.lineWidth = 2;
                ctx.stroke();

                // Property floor level
                if (floorLevel > 0) {
                    var floorY = yPos(propElev + floorLevel);
                    ctx.setLineDash([3, 3]);
                    ctx.strokeStyle = '#1976D2';
                    ctx.lineWidth = 1;
                    ctx.beginPath();
                    ctx.moveTo(propX - 20, floorY);
                    ctx.lineTo(propX + 40, floorY);
                    ctx.stroke();
                    ctx.setLineDash([]);
                    ctx.fillStyle = '#1976D2';
                    ctx.font = '9px Arial';
                    ctx.fillText('Floor +' + floorLevel.toFixed(1) + 'm', propX + 42, floorY + 3);
                }

                // Water level for selected storm
                if (selectedStorm) {
                    var waterAbove = Math.max(0, selectedStorm.gauge_peak_m - bankfull);
                    var waterWSE = gaugeElev + waterAbove;
                    var waterY = yPos(waterWSE);

                    ctx.fillStyle = 'rgba(33, 150, 243, 0.25)';
                    ctx.beginPath();
                    ctx.moveTo(pad.left, waterY);
                    ctx.lineTo(gaugeX, waterY);
                    // Water slopes down to property (simplified)
                    var propWaterWSE = Math.min(waterWSE, propElev + waterAbove);
                    ctx.lineTo(propX, yPos(propWaterWSE));
                    ctx.lineTo(propX, yPos(propElev));
                    ctx.lineTo(gaugeX, yPos(gaugeElev));
                    ctx.lineTo(pad.left, yPos(gaugeElev));
                    ctx.closePath();
                    ctx.fill();

                    ctx.strokeStyle = '#2196F3';
                    ctx.lineWidth = 2;
                    ctx.beginPath();
                    ctx.moveTo(pad.left, waterY);
                    ctx.lineTo(gaugeX, waterY);
                    ctx.lineTo(propX, yPos(propWaterWSE));
                    ctx.stroke();

                    ctx.fillStyle = '#1565C0';
                    ctx.font = 'bold 10px Arial';
                    ctx.fillText('Storm ' + selectedStorm.storm_id, pad.left + 5, waterY - 5);
                }

                // Severe threshold at gauge
                if (severeLevel > 0) {
                    var sevY = yPos(gaugeElev + severeLevel);
                    ctx.setLineDash([5, 3]);
                    ctx.strokeStyle = '#F44336';
                    ctx.lineWidth = 1;
                    ctx.beginPath();
                    ctx.moveTo(pad.left, sevY);
                    ctx.lineTo(gaugeX + 30, sevY);
                    ctx.stroke();
                    ctx.setLineDash([]);
                    ctx.fillStyle = '#F44336';
                    ctx.font = '9px Arial';
                    ctx.fillText('Severe', gaugeX + 32, sevY + 3);
                }

                // Labels
                ctx.fillStyle = '#333';
                ctx.font = 'bold 11px Arial';
                ctx.textAlign = 'center';
                ctx.fillText('Gauge', gaugeX, yPos(gaugeElev) + 15);
                ctx.fillText(gaugeElev.toFixed(1) + 'm', gaugeX, yPos(gaugeElev) + 27);
                ctx.fillText('Property', propX, yPos(propElev) + 15);
                ctx.fillText(propElev.toFixed(1) + 'm', propX, yPos(propElev) + 27);
                ctx.textAlign = 'left';

                // Y-axis label
                ctx.save();
                ctx.translate(12, h / 2);
                ctx.rotate(-Math.PI / 2);
                ctx.font = '10px Arial';
                ctx.fillStyle = '#666';
                ctx.textAlign = 'center';
                ctx.fillText('Elevation (m AOD)', 0, 0);
                ctx.restore();

                // Title
                ctx.fillStyle = '#333';
                ctx.font = 'bold 11px Arial';
                ctx.textAlign = 'center';
                ctx.fillText('Elevation Cross-Section', w / 2, 14);
                ctx.textAlign = 'left';
            }
