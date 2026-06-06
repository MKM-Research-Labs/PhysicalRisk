
            // ================================================================
            // Basis Explorer — Property sub-tab
            // ================================================================
            var basisPropertyChart = null;

            function renderBasisProperty() {
                var container = document.getElementById('phc-chart-container');
                if (basisPropertyChart) { basisPropertyChart.destroy(); basisPropertyChart = null; }

                var storms = phcData.storm_details || [];
                var nearestGauges = phcData.nearest_gauges || [];

                var primaryGauge = nearestGauges.find(function(ng) {
                    return ng.gauge_id.indexOf('SYNTH') !== 0;
                }) || nearestGauges[0] || {};

                var thresholds = primaryGauge.gauge_thresholds || {};
                var severeLevel = thresholds.severe_level || 0;

                // Spread data
                var sd = phcData.spread_decomposition || {};
                var gaugeSpread = sd.gauge_spread_bps || 0;
                var propSpread = sd.property_spread_bps || 0;
                var basis = propSpread - gaugeSpread;

                // Quadrant counts
                var qTopRight = 0;    // gauge triggers + property floods (hedged)
                var qBottomRight = 0; // gauge triggers + property dry (basis risk)
                var qTopLeft = 0;     // gauge silent + property floods (unhedged)
                var qBottomLeft = 0;  // gauge silent + property dry (no event)

                var data = storms.map(function(s) {
                    var gaugeTriggers = s.exceeded_severe || false;
                    var propFloods = s.flooded;

                    if (gaugeTriggers && propFloods) qTopRight++;
                    else if (gaugeTriggers && !propFloods) qBottomRight++;
                    else if (!gaugeTriggers && propFloods) qTopLeft++;
                    else qBottomLeft++;

                    return {
                        x: s.gauge_peak_m,
                        y: s.flood_depth_m,
                        stormId: s.storm_id,
                        damageRatio: s.damage_ratio,
                        gaugeTriggers: gaugeTriggers,
                        propFloods: propFloods,
                    };
                });

                // Colour by damage ratio (grey -> orange -> red)
                var colors = data.map(function(d) {
                    if (d.damageRatio <= 0) return '#BDBDBD';
                    if (d.damageRatio < 0.1) return '#FFB74D';
                    if (d.damageRatio < 0.3) return '#FF9800';
                    if (d.damageRatio < 0.6) return '#F44336';
                    return '#B71C1C';
                });

                // Summary cards
                var summaryHtml =
                    '<div style="padding:8px 0 4px 0;display:flex;gap:12px;flex-wrap:wrap;font-size:11px;">' +
                    '<div style="padding:4px 10px;background:#E8F5E9;border-radius:4px;border-left:3px solid #4CAF50;">' +
                    '<b>Hedged</b><br>' + qTopRight + ' storms</div>' +
                    '<div style="padding:4px 10px;background:#FFF3E0;border-radius:4px;border-left:3px solid #FF9800;">' +
                    '<b>Basis Risk</b> (gauge triggers, property dry)<br>' + qBottomRight + ' storms</div>' +
                    '<div style="padding:4px 10px;background:#FFEBEE;border-radius:4px;border-left:3px solid #F44336;">' +
                    '<b>Unhedged</b> (property floods, no trigger)<br>' + qTopLeft + ' storms</div>' +
                    '<div style="padding:4px 10px;background:#F5F5F5;border-radius:4px;border-left:3px solid #9E9E9E;">' +
                    '<b>No Event</b><br>' + qBottomLeft + ' storms</div>' +
                    '</div>';

                // When the catchment has wind data the spread fans into the
                // four peril outcomes at the property node — stack the peril
                // fan beneath the waterfall in the right column. Flood-only
                // catchments keep the full-height waterfall (unchanged layout).
                var hasPerils = (typeof _perilOutcomesData === 'function')
                    && _perilOutcomesData();
                var rightCol = hasPerils
                    ? ('<div style="display:flex;flex-direction:column;width:38%;min-width:240px;gap:6px;">' +
                       '<canvas id="basis-prop-waterfall" style="flex:1.4;min-height:0;"></canvas>' +
                       '<canvas id="basis-prop-perils" style="flex:1;min-height:0;"></canvas>' +
                       '</div>')
                    : '<canvas id="basis-prop-waterfall" style="width:35%;min-width:220px;"></canvas>';

                container.innerHTML = summaryHtml +
                    '<div style="display:flex;flex:1;gap:8px;min-height:0;">' +
                    '<canvas id="basis-prop-canvas" style="flex:1;"></canvas>' +
                    rightCol +
                    '</div>';

                var ctx = document.getElementById('basis-prop-canvas').getContext('2d');

                // Annotations: vertical line at severe, horizontal at depth=0
                var annotations = {};
                if (severeLevel > 0) {
                    annotations.severeLine = {
                        type: 'line', xMin: severeLevel, xMax: severeLevel,
                        borderColor: '#F44336', borderWidth: 2, borderDash: [6, 3],
                        label: { display: true, content: 'Gauge Severe Trigger',
                                 position: 'start', backgroundColor: '#F44336', color: '#fff',
                                 font: { size: 10 }, padding: 3, rotation: 270 }
                    };
                    annotations.qBR = {
                        type: 'label',
                        xValue: severeLevel + (severeLevel * 0.15),
                        yValue: 0.001,
                        content: ['Basis Risk'],
                        font: { size: 10, style: 'italic' },
                        color: '#FF9800',
                    };
                    annotations.qTR = {
                        type: 'label',
                        xValue: severeLevel + (severeLevel * 0.15),
                        yValue: (Math.max.apply(null, data.map(function(d) { return d.y; }).concat([0.1]))) * 0.85,
                        content: ['Hedged'],
                        font: { size: 10, style: 'italic' },
                        color: '#4CAF50',
                    };
                }

                basisPropertyChart = new Chart(ctx, {
                    type: 'scatter',
                    data: {
                        datasets: [{
                            label: 'Storm Impact',
                            data: data,
                            backgroundColor: colors,
                            borderColor: colors.map(function(c) { return c === '#BDBDBD' ? '#BDBDBD' : c; }),
                            pointRadius: 4,
                            pointHoverRadius: 7,
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        onClick: function(evt, elements) {
                            if (elements.length > 0) {
                                var idx = elements[0].index;
                                basisSelectedStorm = data[idx].stormId;
                                renderBasisSubTab(basisActiveSubTab);
                            }
                        },
                        plugins: {
                            legend: { display: false },
                            annotation: { annotations: annotations },
                            tooltip: {
                                callbacks: {
                                    title: function(items) { return 'Storm ' + data[items[0].dataIndex].stormId; },
                                    label: function(ctx) {
                                        var d = data[ctx.dataIndex];
                                        var lines = [
                                            'Gauge peak: ' + d.x.toFixed(3) + 'm',
                                            'Flood depth: ' + d.y.toFixed(4) + 'm',
                                            'Damage: ' + (d.damageRatio * 100).toFixed(1) + '%',
                                        ];
                                        if (d.gaugeTriggers && d.propFloods)
                                            lines.push('\u2705 Hedged');
                                        else if (d.gaugeTriggers && !d.propFloods)
                                            lines.push('\u26A0 Basis risk: gauge triggers but property dry');
                                        else if (!d.gaugeTriggers && d.propFloods)
                                            lines.push('\u274C Unhedged: property floods without trigger');
                                        return lines;
                                    }
                                }
                            }
                        },
                        scales: {
                            x: {
                                title: { display: true, text: 'Gauge Peak Water Level (m)', font: { size: 11 } },
                            },
                            y: {
                                title: { display: true, text: 'Asset Flood Depth (m)', font: { size: 11 } },
                                beginAtZero: true,
                            }
                        }
                    }
                });

                if (basisSelectedStorm) {
                    var selIdx = data.findIndex(function(d) { return d.stormId === basisSelectedStorm; });
                    if (selIdx >= 0) {
                        basisPropertyChart.setActiveElements([{datasetIndex: 0, index: selIdx}]);
                        basisPropertyChart.update();
                    }
                }

                // Spread waterfall (right panel) + peril fan when wind present
                _renderSpreadWaterfall('basis-prop-waterfall', 3);
                if (hasPerils) _renderPerilOutcomes('basis-prop-perils');

                var bar = document.getElementById('phc-stats-bar');
                if (bar) {
                    var statsHtml =
                        '<span><b>Gauge Spread:</b> ' + gaugeSpread.toFixed(1) + ' bps</span>' +
                        '<span><b>Asset Spread:</b> ' + propSpread.toFixed(1) + ' bps</span>' +
                        '<span><b>Basis:</b> ' + (basis >= 0 ? '+' : '') + basis.toFixed(1) + ' bps</span>' +
                        '<span><b>Hedged:</b> ' + qTopRight + '</span>' +
                        '<span><b>Basis Risk:</b> ' + qBottomRight + '</span>' +
                        '<span><b>Unhedged:</b> ' + qTopLeft + '</span>';
                    if (hasPerils) {
                        var po = _perilOutcomesData();
                        var uw = (po.flood_or_wind && po.flood_or_wind.spread_bps) || 0;
                        var ww = (po.wind_only && po.wind_only.spread_bps) || 0;
                        statsHtml +=
                            '<span style="color:#7E57C2;"><b>Flood\u222AWind:</b> ' + uw.toFixed(1) + ' bps</span>' +
                            '<span style="color:#26A69A;"><b>Wind only:</b> ' + ww.toFixed(1) + ' bps</span>';
                    }
                    bar.innerHTML = statsHtml;
                }
            }
