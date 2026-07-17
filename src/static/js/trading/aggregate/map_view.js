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

            var tdTradeMap = null;
            var tdMapData = null;

            function createMapView() {
                var view = document.createElement('div');
                view.id = 'td-map-view';
                view.style.cssText = 'flex:1;display:none;flex-direction:column;overflow:hidden;';

                // Map container
                var mapContainer = document.createElement('div');
                mapContainer.id = 'td-map-container';
                mapContainer.style.cssText = 'flex:1;min-height:300px;background:#e8eaf6;';
                view.appendChild(mapContainer);

                // Legend bar
                var legend = document.createElement('div');
                legend.id = 'td-map-legend';
                legend.style.cssText = 'padding:6px 16px;border-top:1px solid #eee;font-size:10px;color:#666;background:#f9f9f9;display:flex;gap:16px;align-items:center;';
                legend.innerHTML =
                    '<span>\u25cf <span style="color:#1565c0;">Long FS01</span></span>' +
                    '<span>\u25cf <span style="color:#c62828;">Short FS01</span></span>' +
                    '<span>Solid = Gauge</span>' +
                    '<span>Dashed = Property</span>' +
                    '<span>Circle size = |FS01|</span>';
                view.appendChild(legend);

                return view;
            }

            function loadMapData() {
                var url = getBaseUrl() + '/api/v1/trading/trade-map';
                fetch(url, {mode: 'cors'})
                    .then(function(r) { return r.json(); })
                    .then(function(result) {
                        if (result.status === 'success') {
                            tdMapData = result;
                            setTimeout(renderTradeMap, 100);
                        }
                    })
                    .catch(function(err) {
                        console.error('[Aggregate] Fetch error:', err);
                    });
            }

            function extractAreaName(gaugeName) {
                if (!gaugeName) return '';
                return gaugeName;
            }

            function renderTradeMap() {
                var container = document.getElementById('td-map-container');
                if (!container || !tdMapData) return;

                // Cleanup previous map
                if (tdTradeMap) {
                    tdTradeMap.remove();
                    tdTradeMap = null;
                }

                // Create map
                tdTradeMap = L.map(container, {zoomControl: true}).setView([__MAP_LAT__, __MAP_LON__], 13);
                L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                    attribution: '\u00a9 OpenStreetMap',
                    maxZoom: 18
                }).addTo(tdTradeMap);

                var bounds = [];
                var gauges = tdMapData.gauges || [];

                // First pass: find max |FS01| for area-proportional scaling
                var maxAbsFs01 = 0;
                for (var mi = 0; mi < gauges.length; mi++) {
                    var av = Math.abs(gauges[mi].net_fs01 || 0);
                    if (av > maxAbsFs01) maxAbsFs01 = av;
                }

                // Gauge circles — area proportional to |net FS01|
                for (var i = 0; i < gauges.length; i++) {
                    var g = gauges[i];
                    if (!g.lat || !g.lon) continue;

                    var fs01 = g.net_fs01 || 0;
                    var color = fs01 >= 0 ? '#1565c0' : '#c62828';

                    // Area-proportional: r = sqrt(|FS01| / max) * maxRadius
                    var absFs01 = Math.abs(fs01);
                    var radius = maxAbsFs01 > 0
                        ? Math.max(6, Math.sqrt(absFs01 / maxAbsFs01) * 30)
                        : 6;

                    var areaName = extractAreaName(g.gauge_name || g.gauge_id);
                    var fs01Label = fs01 >= 0 ? '+' : '';

                    // Build FS01-by-tenor breakdown with hazard rate levels
                    var tenorRows = '';
                    if (g.fs01_by_tenor) {
                        var tenorKeys = Object.keys(g.fs01_by_tenor);
                        var hzByTenor = g.hazard_by_tenor || {};
                        tenorRows += '<tr style="border-bottom:1px solid #eee;"><td style="padding:1px 4px;color:#999;font-size:9px;"></td>' +
                            '<td style="padding:1px 4px;text-align:right;color:#999;font-size:9px;">FS01</td>' +
                            '<td style="padding:1px 4px;text-align:right;color:#999;font-size:9px;">Rate</td></tr>';
                        for (var ti = 0; ti < tenorKeys.length; ti++) {
                            var tv = g.fs01_by_tenor[tenorKeys[ti]];
                            var tc = tv >= 0 ? '#1565c0' : '#c62828';
                            var hzRate = hzByTenor[tenorKeys[ti]];
                            var hzDisplay = (hzRate !== undefined && hzRate !== null) ? hzRate.toFixed(0) + 'bp' : '';
                            tenorRows += '<tr><td style="padding:1px 4px;color:#666;">' + tenorKeys[ti] + '</td>' +
                                '<td style="padding:1px 4px;text-align:right;color:' + tc + ';font-weight:600;">' + fmtGBP(tv) + '</td>' +
                                '<td style="padding:1px 4px;text-align:right;color:#555;">' + hzDisplay + '</td></tr>';
                        }
                    }

                    var dailyPnl = g.daily_pnl || 0;
                    var runPnl = g.running_pnl || 0;
                    var dColor = dailyPnl >= 0 ? '#2e7d32' : '#c62828';
                    var rColor = runPnl >= 0 ? '#2e7d32' : '#c62828';

                    var netNotional = g.net_notional || 0;
                    var nnColor = netNotional >= 0 ? '#1565c0' : '#c62828';

                    var popup =
                        '<div style="font-size:11px;min-width:180px;">' +
                            '<b style="font-size:12px;">' + areaName + '</b><br>' +
                            '<span style="color:#888;">' + g.gauge_id + '</span><br>' +
                            '<hr style="margin:4px 0;border:0;border-top:1px solid #eee;">' +
                            '<div style="display:flex;justify-content:space-between;"><span>Trades:</span><b>' + g.num_trades + '</b></div>' +
                            '<div style="display:flex;justify-content:space-between;"><span>Gross Notional:</span><b>' + fmtGBP(g.total_notional) + '</b></div>' +
                            '<div style="display:flex;justify-content:space-between;"><span>Net Notional:</span><span style="color:' + nnColor + ';font-weight:bold;">' + fmtGBP(netNotional) + '</span></div>' +
                            '<div style="display:flex;justify-content:space-between;"><span>Net FS01:</span><span style="color:' + color + ';font-weight:bold;">' + fmtGBP(fs01) + '</span></div>' +
                            (tenorRows ? '<hr style="margin:4px 0;border:0;border-top:1px solid #eee;"><div style="font-size:10px;font-weight:600;color:#555;margin-bottom:2px;">FS01 by Tenor</div><table style="width:100%;font-size:10px;">' + tenorRows + '</table>' : '') +
                            '<hr style="margin:4px 0;border:0;border-top:1px solid #eee;">' +
                            '<div style="display:flex;justify-content:space-between;"><span>Daily P&amp;L:</span><span style="color:' + dColor + ';font-weight:600;">' + fmtGBP(dailyPnl) + '</span></div>' +
                            '<div style="display:flex;justify-content:space-between;"><span>Running P&amp;L:</span><span style="color:' + rColor + ';font-weight:600;">' + fmtGBP(runPnl) + '</span></div>' +
                            '<hr style="margin:4px 0;border:0;border-top:1px solid #eee;">' +
                            '<a href="#" onclick="event.preventDefault();window.showGaugeBlotter&&window.showGaugeBlotter(\'' + g.gauge_id + '\',\'' + (g.gauge_name || '').replace(/\'/g, "\\\'") + '\')" ' +
                                'style="color:#1565c0;font-size:10px;">View Gauge Blotter \u2192</a><br>' +
                            '<a href="#" onclick="event.preventDefault();window.tdViewHazardCurve&&window.tdViewHazardCurve(\'' + g.gauge_id + '\')" ' +
                                'style="color:#1565c0;font-size:10px;">View Hazard Curve \u2192</a><br>' +
                            '<a href="#" onclick="event.preventDefault();window.tdNewTrade&&window.tdNewTrade(\'' + g.gauge_id + '\')" ' +
                                'style="color:#1565c0;font-size:10px;">New Trade \u2192</a>' +
                        '</div>';

                    var circle = L.circleMarker([g.lat, g.lon], {
                        radius: radius,
                        fillColor: color,
                        color: '#fff',
                        weight: 2,
                        fillOpacity: 0.7
                    }).bindPopup(popup).addTo(tdTradeMap);

                    // Permanent area label
                    circle.bindTooltip(areaName, {
                        permanent: true,
                        direction: 'top',
                        offset: [0, -radius - 2],
                        className: 'td-gauge-label'
                    });

                    bounds.push([g.lat, g.lon]);
                }

                // Property PRS markers (diamond-shaped)
                var properties = tdMapData.properties || [];
                for (var pi = 0; pi < properties.length; pi++) {
                    var p = properties[pi];
                    if (!p.lat || !p.lon) continue;

                    var pFs01 = p.fs01 || 0;
                    var pColor = pFs01 >= 0 ? '#1565c0' : '#c62828';
                    var pAbsFs01 = Math.abs(pFs01);
                    var pRadius = maxAbsFs01 > 0
                        ? Math.max(5, Math.sqrt(pAbsFs01 / maxAbsFs01) * 25)
                        : 5;

                    var pNotional = p.net_notional || 0;
                    var pnColor = pNotional >= 0 ? '#1565c0' : '#c62828';
                    var npvColor = (p.npv || 0) >= 0 ? '#2e7d32' : '#c62828';

                    var pDisplayName = window.propertyDisplayName(p.property_id, p.address);
                    var pPopup =
                        '<div style="font-size:11px;min-width:180px;">' +
                            '<b style="font-size:12px;">' + pDisplayName + '</b><br>' +
                            '<span style="color:#888;">' + (p.postcode || '') + ' \u2014 ' + (p.ea_flood_zone || '') + '</span><br>' +
                            '<hr style="margin:4px 0;border:0;border-top:1px solid #eee;">' +
                            '<div style="display:flex;justify-content:space-between;"><span>Swap:</span><b>' + (p.swap_id || '') + '</b></div>' +
                            '<div style="display:flex;justify-content:space-between;"><span>Ctpy:</span><b>' + (p.counterparty || '') + '</b></div>' +
                            '<div style="display:flex;justify-content:space-between;"><span>Direction:</span><b>' + (p.is_payer ? 'Payer' : 'Receiver') + '</b></div>' +
                            '<div style="display:flex;justify-content:space-between;"><span>Notional:</span><span style="color:' + pnColor + ';font-weight:bold;">' + fmtGBP(pNotional) + '</span></div>' +
                            '<div style="display:flex;justify-content:space-between;"><span>Spread:</span><b>' + (p.spread_bps || 0).toFixed(1) + ' bps</b></div>' +
                            '<div style="display:flex;justify-content:space-between;"><span>FS01:</span><span style="color:' + pColor + ';font-weight:bold;">' + fmtGBP(pFs01) + '</span></div>' +
                            '<div style="display:flex;justify-content:space-between;"><span>NPV:</span><span style="color:' + npvColor + ';font-weight:bold;">' + fmtGBP(p.npv || 0) + '</span></div>' +
                        '</div>';

                    L.circleMarker([p.lat, p.lon], {
                        radius: pRadius,
                        fillColor: pColor,
                        color: '#fff',
                        weight: 1.5,
                        fillOpacity: 0.55,
                        dashArray: '3 3'
                    }).bindPopup(pPopup).bindTooltip(pDisplayName, {
                        permanent: true,
                        direction: 'bottom',
                        offset: [0, pRadius + 2],
                        className: 'td-prop-label'
                    }).addTo(tdTradeMap);

                    bounds.push([p.lat, p.lon]);
                }

                // Add label styling
                var style = document.createElement('style');
                style.textContent =
                    '.td-gauge-label { ' +
                    'background: transparent !important; ' +
                    'border: none !important; ' +
                    'box-shadow: none !important; ' +
                    'font-size: 10px !important; ' +
                    'font-weight: 600 !important; ' +
                    'color: #333 !important; ' +
                    'padding: 0 !important; ' +
                    '}' +
                    '.td-gauge-label::before { display: none !important; }' +
                    '.td-prop-label { ' +
                    'background: white !important; ' +
                    'border: 1px solid #ccc !important; ' +
                    'box-shadow: 0 1px 3px rgba(0,0,0,0.2) !important; ' +
                    'font-size: 10px !important; ' +
                    'font-weight: 600 !important; ' +
                    'color: #000 !important; ' +
                    'padding: 2px 6px !important; ' +
                    'border-radius: 3px !important; ' +
                    '}' +
                    '.td-prop-label::before { display: none !important; }';
                document.head.appendChild(style);

                // Fit bounds
                if (bounds.length > 0) {
                    tdTradeMap.fitBounds(bounds, {padding: [40, 40]});
                }

                // Force size recalculation
                setTimeout(function() {
                    if (tdTradeMap) tdTradeMap.invalidateSize();
                }, 200);
            }

            // Navigate to gauge hazard curve panel (PRS pricing screen)
            window.tdViewHazardCurve = function(gaugeId) {
                // Hide the trading desk panel
                if (window.TradingDesk && window.TradingDesk.hide) {
                    window.TradingDesk.hide();
                }
                // Open the gauge hazard curve / PRS pricing panel
                if (window.GaugeHazardCurve && window.GaugeHazardCurve.show) {
                    window.GaugeHazardCurve.show(gaugeId);
                } else if (window.viewHazardCurve) {
                    window.viewHazardCurve(gaugeId);
                }
            };

            // Navigate to PRS pricing screen for a new trade on this gauge
            window.tdNewTrade = function(gaugeId) {
                // Hide the trading desk panel
                if (window.TradingDesk && window.TradingDesk.hide) {
                    window.TradingDesk.hide();
                }
                // Open the gauge hazard curve / PRS pricing panel
                if (window.GaugeHazardCurve && window.GaugeHazardCurve.show) {
                    window.GaugeHazardCurve.show(gaugeId);
                } else if (window.viewHazardCurve) {
                    window.viewHazardCurve(gaugeId);
                }
            };

            function tdCleanupMap() {
                if (tdTradeMap) {
                    tdTradeMap.remove();
                    tdTradeMap = null;
                }
            }
