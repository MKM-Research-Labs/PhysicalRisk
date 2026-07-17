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

            var phcYieldCurve = {'1': 0.035, '2': 0.04, '3': 0.043, '4': 0.045, '5': 0.04, '6': 0.04};

            function interpolateYieldRate(curve, t) {
                if (!curve || Object.keys(curve).length === 0) return 0.04;
                var keys = Object.keys(curve).map(Number).sort(function(a,b){return a-b;});
                if (t <= keys[0]) return curve[String(keys[0])];
                if (t >= keys[keys.length-1]) return curve[String(keys[keys.length-1])];
                for (var i = 0; i < keys.length - 1; i++) {
                    if (t >= keys[i] && t <= keys[i+1]) {
                        var frac = (t - keys[i]) / (keys[i+1] - keys[i]);
                        return curve[String(keys[i])] * (1-frac) + curve[String(keys[i+1])] * frac;
                    }
                }
                return curve[String(keys[keys.length-1])];
            }

            (function() {
                var cfg = window.__BACKEND_CONFIG || {};
                var baseUrl = cfg.url || '';
                fetch(baseUrl + '/api/v1/trading/yield-curve', {mode: 'cors'})
                    .then(function(r) { return r.json(); })
                    .then(function(data) {
                        if (data.yield_curve) phcYieldCurve = data.yield_curve;
                    })
                    .catch(function() {});
            })();

            // ================================================================
            // PRS Pricer — event count model
            // S(t) = (1 - p)^t, semi-annual cashflows
            // ================================================================
            function computePropertyPRSCashflows() {
                var triggerKey = 'severe';
                var notionalStr = document.getElementById('phc-notional').value.replace(/,/g, '');
                var notional = parseFloat(notionalStr) || 10000000;
                var tenor = parseInt(document.getElementById('phc-tenor').value) || 5;
                var spreadBps = parseFloat(document.getElementById('phc-spread').value) || 100;
                var spread = spreadBps / 10000;
                var recovery = 0.0;

                // Direction: payer (buy protection) or receiver (sell protection)
                var dirEl = document.getElementById('phc-direction');
                var isPayer = dirEl ? (dirEl.value === 'payer') : true;

                // Fair spread from event count
                var ts = phcData.term_structure || {};
                var tsData = ts[triggerKey] || {};
                var tenors = ts.tenors || [1, 2, 3, 4, 5];
                var propSpreadArr = tsData.prs_spread_bps || [];
                var fairSpreadBps = propSpreadArr[0] || 0;
                var annualProb = fairSpreadBps / 10000;

                // Survival: S(t) = (1 - p)^t
                function survivalAt(t) {
                    return Math.pow(1 - annualProb, t);
                }

                // Build semi-annual cashflow schedule
                var nPeriods = tenor * 2;
                var dt = 0.5;
                var periods = [];
                var totalPremPV = 0, totalProtPV = 0, riskyAnnuity = 0;

                for (var i = 1; i <= nPeriods; i++) {
                    var t = i * dt;
                    var tPrev = (i - 1) * dt;
                    var S_t = survivalAt(t);
                    var S_prev = survivalAt(tPrev);
                    var rf = interpolateYieldRate(phcYieldCurve, t);
                    var df = Math.exp(-rf * t);

                    var premCF = spread * dt * notional * S_t;
                    var premPV = premCF * df;
                    var protCF = (1 - recovery) * notional * (S_prev - S_t);
                    var protPV = protCF * df;

                    totalPremPV += premPV;
                    totalProtPV += protPV;
                    riskyAnnuity += dt * S_t * df;

                    periods.push({
                        period: i,
                        t: t,
                        label: t.toFixed(1) + 'y',
                        S_t: S_t,
                        df: df,
                        premCF: premCF,
                        premPV: premPV,
                        protCF: protCF,
                        protPV: protPV
                    });
                }

                var fairSpread = riskyAnnuity > 0 ? totalProtPV / (riskyAnnuity * notional) : 0;
                // NPV from perspective of direction
                var npv = isPayer ? (totalProtPV - totalPremPV) : (totalPremPV - totalProtPV);

                // Compute gauge spreads and basis at selected tenor
                var nearestGauges = phcData.nearest_gauges || [];
                var tenorIdx = tenors.indexOf(tenor);
                if (tenorIdx < 0) {
                    tenorIdx = 0;
                    for (var j = 1; j < tenors.length; j++) {
                        if (Math.abs(tenors[j] - tenor) < Math.abs(tenors[tenorIdx] - tenor)) tenorIdx = j;
                    }
                }

                var propSpreadAtTenor = propSpreadArr[tenorIdx] || 0;

                var gaugeComponents = nearestGauges.slice(0, 3).map(function(ng) {
                    var basisData = (ng.basis_bps || {})[triggerKey] || {};
                    var basisVals = basisData.values || [];
                    var basisAtTenor = basisVals[tenorIdx] || 0;
                    var gaugeSpreadAtTenor = propSpreadAtTenor + basisAtTenor;
                    return {
                        gauge_id: ng.gauge_id,
                        distance_km: ng.distance_km || 0,
                        gauge_elevation_m: ng.gauge_elevation_m || 0,
                        gauge_spread: gaugeSpreadAtTenor,
                        basis: basisAtTenor,
                        property_flood_count: ng.property_flood_count || 0,
                        gauge_flood_count: ng.gauge_flood_count || 0,
                        flood_transmission_rate: ng.flood_transmission_rate || 0
                    };
                });

                var avgBasis = 0;
                if (gaugeComponents.length > 0) {
                    var sumBasis = gaugeComponents.reduce(function(s, g) { return s + g.basis; }, 0);
                    avgBasis = sumBasis / gaugeComponents.length;
                }

                // ---- Terrain delta via grid interpolation ----
                var zoneEl = document.getElementById('phc-ea-zone');
                var selectedZone = zoneEl ? zoneEl.value : '';
                var actualZone = phcData.flood_zone || 'Zone 1';
                var terrainDelta = 0;

                var terrainGrid = (phcData._metadata || {}).terrain_grid || null;
                if (!terrainGrid && window._phcMetadata) {
                    terrainGrid = window._phcMetadata.terrain_grid || null;
                }

                if (terrainGrid && selectedZone && selectedZone !== actualZone) {
                    var avgDistM = 0, avgElevDiff = 0;
                    var propElev = phcData.elevation_m || 0;
                    if (nearestGauges.length > 0) {
                        var totalDist = 0, totalElevDiff = 0;
                        nearestGauges.forEach(function(ng) {
                            totalDist += (ng.distance_km || 0) * 1000;
                            totalElevDiff += Math.max(0, propElev - (ng.gauge_elevation_m || 0));
                        });
                        avgDistM = totalDist / nearestGauges.length;
                        avgElevDiff = totalElevDiff / nearestGauges.length;
                    }
                    terrainDelta = interpolateTerrainSpread(terrainGrid, selectedZone, avgDistM, avgElevDiff)
                                 - interpolateTerrainSpread(terrainGrid, actualZone, avgDistM, avgElevDiff);
                }

                return {
                    periods: periods,
                    totalPremPV: totalPremPV,
                    totalProtPV: totalProtPV,
                    riskyAnnuity: riskyAnnuity,
                    fairSpread: fairSpread,
                    fairSpreadBps: fairSpread * 10000,
                    npv: npv,
                    isPayer: isPayer,
                    notional: notional,
                    tenor: tenor,
                    spread: spread,
                    spreadBps: spreadBps,
                    yieldCurve: phcYieldCurve,
                    recovery: recovery,
                    triggerKey: triggerKey,
                    propSpreadAtTenor: propSpreadAtTenor,
                    gaugeComponents: gaugeComponents,
                    avgBasis: avgBasis,
                    terrainDelta: terrainDelta,
                    selectedZone: selectedZone,
                    actualZone: actualZone
                };
            }

            // ================================================================
            // Terrain grid bilinear interpolation (for zone what-if)
            // ================================================================
            function interpolateTerrainSpread(terrainGrid, zone, distance_m, elevation_m) {
                if (!terrainGrid || !terrainGrid.zones || !terrainGrid.zones[zone]) return 0;
                var distances = terrainGrid.distances;
                var elevations = terrainGrid.elevations;
                var grid = terrainGrid.zones[zone].grid;

                var d = Math.max(distances[0], Math.min(distance_m, distances[distances.length - 1]));
                var h = Math.max(elevations[0], Math.min(elevation_m, elevations[elevations.length - 1]));

                var di = 0;
                for (var i = 0; i < distances.length - 1; i++) {
                    if (distances[i + 1] >= d) { di = i; break; }
                    if (i === distances.length - 2) di = i;
                }
                var ei = 0;
                for (var i = 0; i < elevations.length - 1; i++) {
                    if (elevations[i + 1] >= h) { ei = i; break; }
                    if (i === elevations.length - 2) ei = i;
                }

                var dSpan = distances[di + 1] - distances[di];
                var eSpan = elevations[ei + 1] - elevations[ei];
                var td = dSpan > 0 ? (d - distances[di]) / dSpan : 0;
                var te = eSpan > 0 ? (h - elevations[ei]) / eSpan : 0;

                var v00 = grid[di][ei], v01 = grid[di][ei + 1];
                var v10 = grid[di + 1][ei], v11 = grid[di + 1][ei + 1];
                return v00 * (1 - td) * (1 - te) + v10 * td * (1 - te) +
                       v01 * (1 - td) * te + v11 * td * te;
            }
