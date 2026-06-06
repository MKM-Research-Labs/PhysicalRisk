
            // ---- Component summary table ----
            function _buildPRSComponentTableHTML(result, gauges, propElev) {
                var compRows = '';
                var gaugeColors = ['#9C27B0', '#00BCD4', '#795548'];

                gauges.forEach(function(g, i) {
                    var isSynth = g.gauge_id.indexOf('SYNTH') === 0;
                    var color = isSynth ? '#9E9E9E' : (gaugeColors[i] || '#999');
                    var label = isSynth
                        ? '\u2605 ' + g.gauge_id.substring(0, 14)
                        : g.gauge_id.substring(0, 16);
                    var clickAttr = '';
                    var rowStyle = isSynth ? ' style="background:#F5F5F5;"' : '';
                    if (!isSynth && window.GaugeHazardCurve && window.GaugeHazardCurve.show) {
                        clickAttr = ' onclick="window.GaugeHazardCurve.show(\'' + g.gauge_id + '\')" ' +
                            'title="Open gauge PRS pricer"';
                        rowStyle = ' style="cursor:pointer;" onmouseover="this.style.background=\'#E3F2FD\'" onmouseout="this.style.background=\'\'"';
                    }
                    compRows +=
                        '<tr' + rowStyle + clickAttr + '>' +
                        '<td style="padding:4px 8px;"><span style="color:' + color + ';">\u25CF</span> ' +
                        label + '</td>' +
                        '<td style="padding:4px 8px;text-align:right;">' + g.distance_km.toFixed(1) + 'km</td>' +
                        '<td style="padding:4px 8px;text-align:right;">' + g.gauge_elevation_m.toFixed(1) + 'm</td>' +
                        '<td style="padding:4px 8px;text-align:right;font-weight:600;">' + g.gauge_spread.toFixed(1) + '</td>' +
                        '<td style="padding:4px 8px;text-align:right;color:#666;">+' + g.basis.toFixed(1) + '</td>' +
                        '</tr>';
                });

                // Property row
                compRows +=
                    '<tr style="border-top:2px solid #1976D2;background:#E3F2FD;">' +
                    '<td style="padding:4px 8px;font-weight:bold;"><span style="color:#1976D2;">\u25CF</span> Property PRS</td>' +
                    '<td style="padding:4px 8px;text-align:right;">\u2014</td>' +
                    '<td style="padding:4px 8px;text-align:right;">' + propElev.toFixed(1) + 'm</td>' +
                    '<td style="padding:4px 8px;text-align:right;font-weight:bold;color:#1976D2;">' + result.propSpreadAtTenor.toFixed(1) + '</td>' +
                    '<td style="padding:4px 8px;text-align:right;">\u2014</td>' +
                    '</tr>';

                // Avg basis row
                compRows +=
                    '<tr style="background:#FFF3E0;">' +
                    '<td style="padding:4px 8px;font-weight:bold;">Avg Basis</td>' +
                    '<td style="padding:4px 8px;text-align:right;">\u2014</td>' +
                    '<td style="padding:4px 8px;text-align:right;">\u2014</td>' +
                    '<td style="padding:4px 8px;text-align:right;">\u2014</td>' +
                    '<td style="padding:4px 8px;text-align:right;font-weight:bold;color:#E65100;">+' + result.avgBasis.toFixed(1) + '</td>' +
                    '</tr>';

                return '<table style="width:100%;border-collapse:collapse;font-size:11px;font-family:monospace;">' +
                    '<thead><tr style="background:#f5f5f5;border-bottom:2px solid #ddd;">' +
                    '<th style="padding:4px 8px;text-align:left;">Component</th>' +
                    '<th style="padding:4px 8px;text-align:right;">Distance</th>' +
                    '<th style="padding:4px 8px;text-align:right;">Elevation</th>' +
                    '<th style="padding:4px 8px;text-align:right;">Fair Spread</th>' +
                    '<th style="padding:4px 8px;text-align:right;">Basis (bps)</th>' +
                    '</tr></thead>' +
                    '<tbody>' + compRows + '</tbody></table>';
            }

            // ---- Spread-decomposition waterfall (severe trigger, both paths) ----
            function _buildPRSWaterfallTableHTML(sd, terrainDelta, selectedZone, actualZone, adjustedPropSpread) {
                var gaugeSpread = sd.gauge_spread_bps || 0;
                var shdSpread = sd.shd_spread_bps || 0;
                var sheSpread = sd.she_spread_bps || 0;
                var df = sd.distance_first || {};
                var ef = sd.elevation_first || {};

                // Terrain effect row (shared between both paths).
                // Hide when the user-selected zone matches the property's actual
                // zone — any residual numerical delta from the pricer is not a
                // counterfactual adjustment and should not be displayed.
                var zoneMatches = selectedZone && actualZone && selectedZone === actualZone;
                var terrainRow = '';
                if (!zoneMatches && Math.abs(terrainDelta) >= 0.05) {
                    var tColor = terrainDelta < 0 ? '#2E7D32' : '#E65100';
                    terrainRow =
                        '<tr style="background:#F3E5F5;"><td style="padding:2px 6px;font-size:10px;">Terrain Effect</td>' +
                        '<td style="padding:2px 6px;text-align:right;font-weight:600;color:' + tColor + ';">' + (terrainDelta >= 0 ? '+' : '') + terrainDelta.toFixed(1) + '</td>' +
                        '<td style="padding:2px 6px;text-align:right;color:#888;font-size:9px;">' + selectedZone + '</td></tr>';
                }

                var sdRows = '';
                // Path 1: Distance first
                sdRows +=
                    '<tr style="background:#E3F2FD;">' +
                    '<td colspan="3" style="padding:3px 6px;font-weight:bold;font-size:10px;color:#1565C0;">Path 1: Distance First</td></tr>';
                sdRows +=
                    '<tr><td style="padding:2px 6px;font-size:10px;">Gauge Spread</td>' +
                    '<td style="padding:2px 6px;text-align:right;font-weight:600;">' + gaugeSpread.toFixed(1) + '</td>' +
                    '<td style="padding:2px 6px;text-align:right;color:#888;font-size:9px;">baseline</td></tr>';
                sdRows += terrainRow;
                var distEff1 = df.distance_effect_bps || 0;
                sdRows +=
                    '<tr><td style="padding:2px 6px;font-size:10px;">Distance Effect</td>' +
                    '<td style="padding:2px 6px;text-align:right;font-weight:600;color:' + (distEff1 < 0 ? '#2E7D32' : '#E65100') + ';">' + (distEff1 >= 0 ? '+' : '') + distEff1.toFixed(1) + '</td>' +
                    '<td style="padding:2px 6px;text-align:right;color:#888;font-size:9px;">SHE=' + sheSpread.toFixed(1) + 'bp</td></tr>';
                var elevEff1 = df.elevation_effect_bps || 0;
                sdRows +=
                    '<tr><td style="padding:2px 6px;font-size:10px;">Elevation Effect</td>' +
                    '<td style="padding:2px 6px;text-align:right;font-weight:600;color:' + (elevEff1 < 0 ? '#2E7D32' : '#E65100') + ';">' + (elevEff1 >= 0 ? '+' : '') + elevEff1.toFixed(1) + '</td>' +
                    '<td style="padding:2px 6px;text-align:right;color:#888;font-size:9px;">\u2192 property</td></tr>';
                // Path 2: Elevation first
                sdRows +=
                    '<tr style="background:#FFF3E0;">' +
                    '<td colspan="3" style="padding:3px 6px;font-weight:bold;font-size:10px;color:#E65100;">Path 2: Elevation First</td></tr>';
                sdRows += terrainRow;
                var elevEff2 = ef.elevation_effect_bps || 0;
                sdRows +=
                    '<tr><td style="padding:2px 6px;font-size:10px;">Elevation Effect</td>' +
                    '<td style="padding:2px 6px;text-align:right;font-weight:600;color:' + (elevEff2 < 0 ? '#2E7D32' : '#E65100') + ';">' + (elevEff2 >= 0 ? '+' : '') + elevEff2.toFixed(1) + '</td>' +
                    '<td style="padding:2px 6px;text-align:right;color:#888;font-size:9px;">SHD=' + shdSpread.toFixed(1) + 'bp</td></tr>';
                var distEff2 = ef.distance_effect_bps || 0;
                sdRows +=
                    '<tr><td style="padding:2px 6px;font-size:10px;">Distance Effect</td>' +
                    '<td style="padding:2px 6px;text-align:right;font-weight:600;color:' + (distEff2 < 0 ? '#2E7D32' : '#E65100') + ';">' + (distEff2 >= 0 ? '+' : '') + distEff2.toFixed(1) + '</td>' +
                    '<td style="padding:2px 6px;text-align:right;color:#888;font-size:9px;">\u2192 property</td></tr>';
                // Property row (adjusted for terrain)
                sdRows +=
                    '<tr style="border-top:2px solid #333;font-weight:bold;background:#E8F5E9;">' +
                    '<td style="padding:3px 6px;">Property Spread</td>' +
                    '<td style="padding:3px 6px;text-align:right;color:#1976D2;">' + adjustedPropSpread.toFixed(1) + ' bp</td>' +
                    '<td></td></tr>';

                return '<table style="width:100%;border-collapse:collapse;font-size:11px;font-family:monospace;margin-top:4px;">' +
                    '<thead><tr style="background:#FFF8E1;border-bottom:1px solid #FFE082;">' +
                    '<th style="padding:2px 6px;text-align:left;font-size:10px;">Spread Decomposition</th>' +
                    '<th style="padding:2px 6px;text-align:right;font-size:10px;">bps</th>' +
                    '<th style="padding:2px 6px;text-align:right;font-size:10px;">Detail</th>' +
                    '</tr></thead>' +
                    '<tbody>' + sdRows + '</tbody></table>';
            }
