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

            function _buildPRSComponentTableHTML(result, gauges, propElev) {
                var compRows = '';
                var gaugeColors = ['var(--purple-bright)', Theme.value('cyan-bright'), 'var(--brown)'];

                gauges.forEach(function(g, i) {
                    var isSynth = g.gauge_id.indexOf('SYNTH') === 0;
                    var color = isSynth ? 'var(--grey)' : (gaugeColors[i] || 'var(--muted-2)');
                    var label = isSynth
                        ? '\u2605 ' + g.gauge_id.substring(0, 14)
                        : g.gauge_id.substring(0, 16);
                    var clickAttr = '';
                    var rowStyle = isSynth ? ' style="background:var(--sunken);"' : '';
                    if (!isSynth && window.GaugeHazardCurve && window.GaugeHazardCurve.show) {
                        clickAttr = ' onclick="window.GaugeHazardCurve.show(\'' + g.gauge_id + '\')" ' +
                            'title="Open gauge PRS pricer"';
                        rowStyle = ' style="cursor:pointer;" onmouseover="this.style.background=\'var(--accent-soft)\'" onmouseout="this.style.background=\'\'"';
                    }
                    compRows +=
                        '<tr' + rowStyle + clickAttr + '>' +
                        '<td style="padding:var(--space-2) var(--space-4);"><span style="color:' + color + ';">\u25CF</span> ' +
                        label + '</td>' +
                        '<td style="padding:var(--space-2) var(--space-4);text-align:right;">' + g.distance_km.toFixed(1) + 'km</td>' +
                        '<td style="padding:var(--space-2) var(--space-4);text-align:right;">' + g.gauge_elevation_m.toFixed(1) + 'm</td>' +
                        '<td style="padding:var(--space-2) var(--space-4);text-align:right;font-weight:600;">' + g.gauge_spread.toFixed(1) + '</td>' +
                        '<td style="padding:var(--space-2) var(--space-4);text-align:right;color:var(--text-3);">+' + g.basis.toFixed(1) + '</td>' +
                        '</tr>';
                });

                // Property row
                compRows +=
                    '<tr style="border-top:2px solid var(--accent);background:var(--accent-soft);">' +
                    '<td style="padding:var(--space-2) var(--space-4);font-weight:bold;"><span style="color:var(--accent);">\u25CF</span> Property PRS</td>' +
                    '<td style="padding:var(--space-2) var(--space-4);text-align:right;">\u2014</td>' +
                    '<td style="padding:var(--space-2) var(--space-4);text-align:right;">' + propElev.toFixed(1) + 'm</td>' +
                    '<td style="padding:var(--space-2) var(--space-4);text-align:right;font-weight:bold;color:var(--accent);">' + result.propSpreadAtTenor.toFixed(1) + '</td>' +
                    '<td style="padding:var(--space-2) var(--space-4);text-align:right;">\u2014</td>' +
                    '</tr>';

                // Avg basis row
                compRows +=
                    '<tr style="background:var(--warn-bg-warm);">' +
                    '<td style="padding:var(--space-2) var(--space-4);font-weight:bold;">Avg Basis</td>' +
                    '<td style="padding:var(--space-2) var(--space-4);text-align:right;">\u2014</td>' +
                    '<td style="padding:var(--space-2) var(--space-4);text-align:right;">\u2014</td>' +
                    '<td style="padding:var(--space-2) var(--space-4);text-align:right;">\u2014</td>' +
                    '<td style="padding:var(--space-2) var(--space-4);text-align:right;font-weight:bold;color:var(--amber-deep);">+' + result.avgBasis.toFixed(1) + '</td>' +
                    '</tr>';

                return '<table style="width:100%;border-collapse:collapse;font-size:var(--size-xs);font-family:monospace;">' +
                    '<thead><tr style="background:var(--sunken);border-bottom:2px solid var(--line-strong);">' +
                    '<th style="padding:var(--space-2) var(--space-4);text-align:left;">Component</th>' +
                    '<th style="padding:var(--space-2) var(--space-4);text-align:right;">Distance</th>' +
                    '<th style="padding:var(--space-2) var(--space-4);text-align:right;">Elevation</th>' +
                    '<th style="padding:var(--space-2) var(--space-4);text-align:right;">Fair Spread</th>' +
                    '<th style="padding:var(--space-2) var(--space-4);text-align:right;">Basis (bps)</th>' +
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
                    var tColor = terrainDelta < 0 ? 'var(--green-dark)' : 'var(--amber-deep)';
                    terrainRow =
                        '<tr style="background:var(--purple-bg);"><td style="padding:var(--space-1) var(--space-3);font-size:var(--size-xxs);">Terrain Effect</td>' +
                        '<td style="padding:var(--space-1) var(--space-3);text-align:right;font-weight:600;color:' + tColor + ';">' + (terrainDelta >= 0 ? '+' : '') + terrainDelta.toFixed(1) + '</td>' +
                        '<td style="padding:var(--space-1) var(--space-3);text-align:right;color:var(--muted);font-size:var(--size-xxs);">' + selectedZone + '</td></tr>';
                }

                var sdRows = '';
                // Path 1: Distance first
                sdRows +=
                    '<tr style="background:var(--accent-soft);">' +
                    '<td colspan="3" style="padding:var(--space-2) var(--space-3);font-weight:bold;font-size:var(--size-xxs);color:var(--accent-mid);">Path 1: Distance First</td></tr>';
                sdRows +=
                    '<tr><td style="padding:var(--space-1) var(--space-3);font-size:var(--size-xxs);">Gauge Spread</td>' +
                    '<td style="padding:var(--space-1) var(--space-3);text-align:right;font-weight:600;">' + gaugeSpread.toFixed(1) + '</td>' +
                    '<td style="padding:var(--space-1) var(--space-3);text-align:right;color:var(--muted);font-size:var(--size-xxs);">baseline</td></tr>';
                sdRows += terrainRow;
                var distEff1 = df.distance_effect_bps || 0;
                sdRows +=
                    '<tr><td style="padding:var(--space-1) var(--space-3);font-size:var(--size-xxs);">Distance Effect</td>' +
                    '<td style="padding:var(--space-1) var(--space-3);text-align:right;font-weight:600;color:' + (distEff1 < 0 ? 'var(--green-dark)' : 'var(--amber-deep)') + ';">' + (distEff1 >= 0 ? '+' : '') + distEff1.toFixed(1) + '</td>' +
                    '<td style="padding:var(--space-1) var(--space-3);text-align:right;color:var(--muted);font-size:var(--size-xxs);">SHE=' + sheSpread.toFixed(1) + 'bp</td></tr>';
                var elevEff1 = df.elevation_effect_bps || 0;
                sdRows +=
                    '<tr><td style="padding:var(--space-1) var(--space-3);font-size:var(--size-xxs);">Elevation Effect</td>' +
                    '<td style="padding:var(--space-1) var(--space-3);text-align:right;font-weight:600;color:' + (elevEff1 < 0 ? 'var(--green-dark)' : 'var(--amber-deep)') + ';">' + (elevEff1 >= 0 ? '+' : '') + elevEff1.toFixed(1) + '</td>' +
                    '<td style="padding:var(--space-1) var(--space-3);text-align:right;color:var(--muted);font-size:var(--size-xxs);">\u2192 property</td></tr>';
                // Path 2: Elevation first
                sdRows +=
                    '<tr style="background:var(--warn-bg-warm);">' +
                    '<td colspan="3" style="padding:var(--space-2) var(--space-3);font-weight:bold;font-size:var(--size-xxs);color:var(--amber-deep);">Path 2: Elevation First</td></tr>';
                sdRows += terrainRow;
                var elevEff2 = ef.elevation_effect_bps || 0;
                sdRows +=
                    '<tr><td style="padding:var(--space-1) var(--space-3);font-size:var(--size-xxs);">Elevation Effect</td>' +
                    '<td style="padding:var(--space-1) var(--space-3);text-align:right;font-weight:600;color:' + (elevEff2 < 0 ? 'var(--green-dark)' : 'var(--amber-deep)') + ';">' + (elevEff2 >= 0 ? '+' : '') + elevEff2.toFixed(1) + '</td>' +
                    '<td style="padding:var(--space-1) var(--space-3);text-align:right;color:var(--muted);font-size:var(--size-xxs);">SHD=' + shdSpread.toFixed(1) + 'bp</td></tr>';
                var distEff2 = ef.distance_effect_bps || 0;
                sdRows +=
                    '<tr><td style="padding:var(--space-1) var(--space-3);font-size:var(--size-xxs);">Distance Effect</td>' +
                    '<td style="padding:var(--space-1) var(--space-3);text-align:right;font-weight:600;color:' + (distEff2 < 0 ? 'var(--green-dark)' : 'var(--amber-deep)') + ';">' + (distEff2 >= 0 ? '+' : '') + distEff2.toFixed(1) + '</td>' +
                    '<td style="padding:var(--space-1) var(--space-3);text-align:right;color:var(--muted);font-size:var(--size-xxs);">\u2192 property</td></tr>';
                // Property row (adjusted for terrain)
                sdRows +=
                    '<tr style="border-top:2px solid var(--text);font-weight:bold;background:var(--ok-bg);">' +
                    '<td style="padding:var(--space-2) var(--space-3);">Property Spread</td>' +
                    '<td style="padding:var(--space-2) var(--space-3);text-align:right;color:var(--accent);">' + adjustedPropSpread.toFixed(1) + ' bp</td>' +
                    '<td></td></tr>';

                // ---- Independent perils (fire / seismic) ----------------------
                // Mirrors the Hazard Curve tab's "Independent perils" block
                // (phc-hazard.js). Rendered only when the commercial hazard
                // route's read-time joins have folded fire_spread_bps /
                // seismic_spread_bps into the decomposition — a no-op for
                // residential / pre-peril assets, so the table is unchanged for
                // them. Fire and seismic are independent hazards: they don't
                // combine linearly with the flood/wind basis, so the all-in PRS
                // is a root-sum-of-squares of the basis and each peril leg.
                var fireBps = (sd.fire_spread_bps != null && !isNaN(sd.fire_spread_bps))
                    ? parseFloat(sd.fire_spread_bps) : null;
                var seisBps = (sd.seismic_spread_bps != null && !isNaN(sd.seismic_spread_bps))
                    ? parseFloat(sd.seismic_spread_bps) : null;
                if (fireBps !== null || seisBps !== null) {
                    var po = sd.peril_outcomes || {};
                    function _perilCount(o) {
                        return (o && typeof o.count === 'number') ? o.count : 0;
                    }
                    // Flood/wind basis the all-in lands on: prefer the widest
                    // union scenario (BRI-OR-wind, then flood-OR-wind), else the
                    // terrain-adjusted property spread heading this table. This
                    // is usually NOT the Property Spread row directly above, so
                    // it is rendered as its own row below — without it the
                    // all-in looks like it fails to reconcile.
                    var fwBase, fwBaseLabel;
                    if (sd.bow_spread_bps != null) {
                        fwBase = parseFloat(sd.bow_spread_bps);
                        fwBaseLabel = 'BOW (BRI OR wind)';
                    } else if (sd.fow_spread_bps != null) {
                        fwBase = parseFloat(sd.fow_spread_bps);
                        fwBaseLabel = 'FOW (flood OR wind)';
                    } else {
                        fwBase = adjustedPropSpread;
                        fwBaseLabel = 'property spread';
                    }
                    var sumSq = fwBase * fwBase;
                    if (fireBps !== null) sumSq += fireBps * fireBps;
                    if (seisBps !== null) sumSq += seisBps * seisBps;
                    var allIn = Math.sqrt(sumSq);

                    sdRows +=
                        '<tr style="background:var(--blue-grey-bg);">' +
                        '<td colspan="3" style="padding:var(--space-2) var(--space-3);font-weight:bold;font-size:var(--size-xxs);color:var(--peril-seismic-row);">' +
                        'Independent Perils — all-in (√Σ sq)</td></tr>';
                    // Basis row: which flood/wind leg the all-in is built on.
                    sdRows +=
                        '<tr><td style="padding:var(--space-1) var(--space-3);font-size:var(--size-xxs);color:var(--blue-grey-dark);">Flood/wind basis</td>' +
                        '<td style="padding:var(--space-1) var(--space-3);text-align:right;font-weight:600;color:var(--blue-grey-dark);">' + fwBase.toFixed(1) + '</td>' +
                        '<td style="padding:var(--space-1) var(--space-3);text-align:right;color:var(--muted);font-size:var(--size-xxs);">' + fwBaseLabel + '</td></tr>';
                    if (fireBps !== null) {
                        sdRows +=
                            '<tr><td style="padding:var(--space-1) var(--space-3);font-size:var(--size-xxs);color:var(--orange-deep);font-weight:600;">FIRE (full conflagration)</td>' +
                            '<td style="padding:var(--space-1) var(--space-3);text-align:right;font-weight:600;color:var(--orange-deep);">' + fireBps.toFixed(1) + '</td>' +
                            '<td style="padding:var(--space-1) var(--space-3);text-align:right;color:var(--muted);font-size:var(--size-xxs);">' + _perilCount(po.fire_conflagration).toLocaleString() + ' PNR</td></tr>';
                    }
                    if (seisBps !== null) {
                        sdRows +=
                            '<tr><td style="padding:var(--space-1) var(--space-3);font-size:var(--size-xxs);color:var(--peril-seismic-row);font-weight:600;">SEISMIC (collapse)</td>' +
                            '<td style="padding:var(--space-1) var(--space-3);text-align:right;font-weight:600;color:var(--peril-seismic-row);">' + seisBps.toFixed(1) + '</td>' +
                            '<td style="padding:var(--space-1) var(--space-3);text-align:right;color:var(--muted);font-size:var(--size-xxs);">' + _perilCount(po.seismic).toLocaleString() + ' DS3</td></tr>';
                    }
                    sdRows +=
                        '<tr style="border-top:2px solid var(--text);font-weight:bold;background:var(--blue-grey-bg);">' +
                        '<td style="padding:var(--space-2) var(--space-3);">All-in PRS</td>' +
                        '<td style="padding:var(--space-2) var(--space-3);text-align:right;color:var(--text);">' + allIn.toFixed(1) + ' bp</td>' +
                        '<td></td></tr>';
                }

                return '<table style="width:100%;border-collapse:collapse;font-size:var(--size-xs);font-family:monospace;margin-top:var(--space-2);">' +
                    '<thead><tr style="background:var(--warn-bg);border-bottom:1px solid var(--warn-line-soft);">' +
                    '<th style="padding:var(--space-1) var(--space-3);text-align:left;font-size:var(--size-xxs);">Spread Decomposition</th>' +
                    '<th style="padding:var(--space-1) var(--space-3);text-align:right;font-size:var(--size-xxs);">bps</th>' +
                    '<th style="padding:var(--space-1) var(--space-3);text-align:right;font-size:var(--size-xxs);">Detail</th>' +
                    '</tr></thead>' +
                    '<tbody>' + sdRows + '</tbody></table>';
            }
