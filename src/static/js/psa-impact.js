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

            function renderFloodHistory() {
                var content = document.getElementById('prop-storm-content');
                if (currentChart) { currentChart.destroy(); currentChart = null; }
                if (!propStormData || !propStormData.flood_events || propStormData.flood_events.length === 0) {
                    content.innerHTML = '<p style="color:var(--muted-2);text-align:center;margin-top:var(--space-inset);">No flood history available</p>';
                    return;
                }

                // Show every event that EITHER flooded OR was a typhoon — so
                // a typhoon that didn't flood this property still appears in
                // the history with its wind impact.
                var events = propStormData.flood_events.filter(function(e) {
                    return e.flooded || (e.typhoon && e.typhoon.event_id);
                });
                var totalStorms = propStormData.flood_events.length;
                var floodedCount = 0;
                var maxDepth = 0, sumDepth = 0, sumDmg = 0;
                var typhoonCount = 0, maxWind = 0, sumWindDmg = 0;
                events.forEach(function(e) {
                    if (e.flooded) floodedCount += 1;
                    maxDepth = Math.max(maxDepth, e.flood_depth_m || 0);
                    sumDepth += e.flood_depth_m || 0;
                    sumDmg += e.damage_ratio || 0;
                    if (e.typhoon && e.typhoon.event_id) {
                        typhoonCount += 1;
                        maxWind = Math.max(maxWind, e.typhoon.peak_wind_ms || 0);
                        sumWindDmg += e.typhoon.wind_damage_ratio || 0;
                    }
                });
                var meanDepth = events.length > 0 ? sumDepth / events.length : 0;
                var meanDmg = events.length > 0 ? sumDmg / events.length : 0;

                // Sequence type badge styling
                var seqBadge = function(seqType) {
                    var seqBg = Theme.ramp('sequence_bg');
                    var seqInk = Theme.ramp('sequence_ink');
                    var labels = {isolated:'Isolated', doublet:'Doublet',
                                  cluster:'Cluster', persistent:'Persistent'};
                    var c = {
                        bg: seqBg[seqType] || Theme.value('sunken'),
                        color: seqInk[seqType] || Theme.value('text-2'),
                        label: labels[seqType] || seqType || '?'
                    };
                    return '<span style="background:' + c.bg + ';color:' + c.color + ';font-size:var(--size-xxs);' +
                           'padding:var(--space-hair) var(--space-3);border-radius:var(--radius-sm);font-weight:600;">' + c.label + '</span>';
                };

                // Typhoon badge — emitted for any event whose storm was
                // paired with a typhoon by the severity-bucket linkage.
                var typhoonBadge = function(typhoon) {
                    if (!typhoon || !typhoon.event_id) return '';
                    var fam = typhoon.scenario_family || '?';
                    var peak = typhoon.peak_wind_ms;
                    var title = 'Typhoon ' + typhoon.event_id + ' (' + fam +
                                ', peak ' + (peak != null ? peak.toFixed(1) : '?') + ' m/s)';
                    return '<span title="' + title + '" style="background:var(--warn-bg-warm);color:var(--orange-deep);' +
                           'font-size:var(--size-xxs);padding:var(--space-hair) var(--space-3);border-radius:var(--radius-sm);font-weight:700;' +
                           'margin-left:var(--space-2);">⚡ ' + fam.toUpperCase() + '</span>';
                };

                // Table + chart layout
                var html =
                    '<div style="display:flex;gap:var(--space-6);height:100%;">' +
                    '<div style="flex:1;overflow-y:auto;max-height:360px;">' +
                    '<table style="width:100%;border-collapse:collapse;font-size:var(--size-xs);">' +
                    '<thead><tr style="background:var(--sunken);position:sticky;top:0;">' +
                    '<th style="padding:var(--space-2) var(--space-4);text-align:left;">Storm</th>' +
                    '<th style="padding:var(--space-2) var(--space-3);text-align:left;">Sequence</th>' +
                    '<th style="padding:var(--space-2) var(--space-4);text-align:right;">Depth (m)</th>' +
                    '<th style="padding:var(--space-2) var(--space-4);text-align:right;">Flood Dmg %</th>' +
                    '<th style="padding:var(--space-2) var(--space-4);text-align:right;">Wind (m/s)</th>' +
                    '<th style="padding:var(--space-2) var(--space-4);text-align:right;">Wind Dmg %</th>' +
                    '</tr></thead><tbody>';

                events.forEach(function(e, i) {
                    var bg = i % 2 === 0 ? Theme.value('panel') : Theme.value('raised');
                    var depthColor = e.flood_depth_m >= 1.0 ? Theme.value('red') : e.flood_depth_m >= 0.5 ? Theme.value('amber') : Theme.value('text');
                    var sid = (e.storm_id || '').replace(/'/g, "\\'");
                    var ty = e.typhoon;
                    var windCell = '—', windDmgCell = '—', windColor = Theme.value('muted-2');
                    if (ty && ty.event_id) {
                        if (ty.peak_wind_ms != null) windCell = ty.peak_wind_ms.toFixed(1);
                        if (ty.wind_damage_ratio != null) {
                            var wd = ty.wind_damage_ratio;
                            windDmgCell = (wd * 100).toFixed(1) + '%';
                            windColor = wd >= 0.5 ? Theme.value('red') : wd >= 0.1 ? Theme.value('amber') : Theme.value('text');
                        }
                    }
                    // Inline onclick runs in global scope; switchTab is local
                    // to the panel IIFE, so use the window-exposed alias.
                    html +=
                        '<tr style="background:' + bg + ';cursor:pointer;" ' +
                        'onclick="window.propStormSwitchTab(1, \'' + sid + '\')" ' +
                        'title="Click to view flood timeline">' +
                        '<td style="padding:var(--space-2) var(--space-4);font-family:monospace;color:var(--accent-mid);">' +
                          (e.storm_id || '-').substring(0, 16) + typhoonBadge(ty) + '</td>' +
                        '<td style="padding:var(--space-2) var(--space-3);">' + seqBadge(e.sequence_type) + '</td>' +
                        '<td style="padding:var(--space-2) var(--space-4);text-align:right;color:' + depthColor + ';font-weight:600;">' + (e.flood_depth_m || 0).toFixed(2) + '</td>' +
                        '<td style="padding:var(--space-2) var(--space-4);text-align:right;">' + ((e.damage_ratio || 0) * 100).toFixed(1) + '%</td>' +
                        '<td style="padding:var(--space-2) var(--space-4);text-align:right;">' + windCell + '</td>' +
                        '<td style="padding:var(--space-2) var(--space-4);text-align:right;color:' + windColor + ';font-weight:600;">' + windDmgCell + '</td>' +
                        '</tr>';
                });
                html += '</tbody></table></div>';
                html +=
                    '<div style="flex:1;"><canvas id="prop-history-chart" height="320"></canvas></div>' +
                    '</div>' +
                    '<div id="prop-history-stats" style="display:flex;gap:var(--space-8);font-size:var(--size-xs);color:var(--text-2);padding:var(--space-4) 0;border-top:1px solid var(--line-soft);"></div>';

                content.innerHTML = html;

                // Bar chart of flood depths
                var labels = events.map(function(e) { return (e.storm_id || '').substring(0, 10); });
                var depths = events.map(function(e) { return e.flood_depth_m || 0; });
                var seqTypeColors = Theme.ramp('sequence');
                var barColors = events.map(function(e) {
                    return seqTypeColors[e.sequence_type] || Theme.value('accent-light');
                });

                var ctx = document.getElementById('prop-history-chart').getContext('2d');
                currentChart = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: labels,
                        datasets: [{
                            label: 'Flood Depth (m)',
                            data: depths,
                            backgroundColor: barColors,
                            borderWidth: 0
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { display: false },
                            title: { display: true, text: 'Flood Depths by Storm (colour = sequence type)', font: { size: 12 } },
                            tooltip: {
                                callbacks: {
                                    label: function(ctx) {
                                        var e = events[ctx.dataIndex];
                                        return [
                                            'Depth: ' + ctx.parsed.y.toFixed(2) + 'm',
                                            'Type: ' + (e.sequence_type || 'isolated'),
                                            'Damage: ' + ((e.damage_ratio || 0) * 100).toFixed(1) + '%'
                                        ];
                                    }
                                }
                            }
                        },
                        scales: {
                            x: { ticks: { font: { size: 9 }, maxRotation: 45 } },
                            y: { title: { display: true, text: 'Depth (m)' }, beginAtZero: true }
                        },
                        onClick: function(evt, elems) {
                            if (elems && elems.length > 0) {
                                var idx = elems[0].index;
                                var ev = events[idx];
                                if (ev && ev.storm_id) {
                                    switchTab(1, ev.storm_id);
                                }
                            }
                        }
                    }
                });

                // Sequence type counts for stats bar
                var seqCounts = {};
                events.forEach(function(e) {
                    var t = e.sequence_type || 'isolated';
                    seqCounts[t] = (seqCounts[t] || 0) + 1;
                });
                var seqSummary = Object.keys(seqCounts).map(function(t) {
                    return seqCounts[t] + ' ' + t;
                }).join(', ');

                var meanWindDmg = typhoonCount > 0 ? sumWindDmg / typhoonCount : 0;
                document.getElementById('prop-history-stats').innerHTML = [
                    '<span><b>Total storms:</b> ' + totalStorms + '</span>',
                    '<span><b>Floods:</b> ' + floodedCount + ' (' + (totalStorms > 0 ? (floodedCount / totalStorms * 100).toFixed(0) : '0') + '%)</span>',
                    '<span><b>Typhoons:</b> ' + typhoonCount +
                        (typhoonCount > 0 ? ' (max wind ' + maxWind.toFixed(1) + ' m/s, mean dmg ' + (meanWindDmg * 100).toFixed(1) + '%)' : '') + '</span>',
                    '<span><b>Max depth:</b> ' + maxDepth.toFixed(2) + 'm</span>',
                    '<span><b>Mean depth:</b> ' + meanDepth.toFixed(2) + 'm</span>',
                    '<span><b>Sequences:</b> ' + seqSummary + '</span>'
                ].join('');
            }

            // ================================================================
            // Tab 4: Mortgage Impact (damage cost + LTV impact per storm)
            // ================================================================
            function renderMortgageImpact() {
                var content = document.getElementById('prop-storm-content');
                if (currentChart) { currentChart.destroy(); currentChart = null; }

                if (!propMortgageData) {
                    content.innerHTML = '<p style="color:var(--muted-2);text-align:center;margin-top:var(--space-inset);">No mortgage linked to this property</p>';
                    return;
                }
                if (!propStormData || !propStormData.flood_events || propStormData.flood_events.length === 0) {
                    content.innerHTML = '<p style="color:var(--muted-2);text-align:center;margin-top:var(--space-inset);">No flood events for this property</p>';
                    return;
                }

                var fin = propMortgageData.FinancialTerms || {};
                var cur = propMortgageData.CurrentStatus || {};
                var propertyValue = fin.PurchaseValue || 0;
                var outstanding = cur.OutstandingBalance || 0;
                var currentLtv = cur.CurrentLTV || 0;

                if (propertyValue <= 0) {
                    content.innerHTML = '<p style="color:var(--muted-2);text-align:center;margin-top:var(--space-inset);">No property value available</p>';
                    return;
                }

                // Compute per-storm impact
                var events = propStormData.flood_events.filter(function(e) { return e.flooded && e.damage_ratio > 0; });
                var impacts = events.map(function(e) {
                    var damageAmt = propertyValue * e.damage_ratio;
                    var postValue = propertyValue * (1 - e.damage_ratio);
                    var postLtv = postValue > 0 ? (outstanding / postValue) * 100 : 999;
                    return {
                        storm_id: e.storm_id,
                        damage_ratio: e.damage_ratio,
                        flood_depth_m: e.flood_depth_m,
                        damage_amount: damageAmt,
                        post_value: postValue,
                        post_ltv: postLtv,
                        negative_equity: postValue < outstanding
                    };
                });
                impacts.sort(function(a, b) { return b.damage_amount - a.damage_amount; });
                var top = impacts.slice(0, 20);

                // Chart + stats layout
                content.innerHTML =
                    '<canvas id="prop-mortgage-chart" height="280"></canvas>' +
                    '<div id="prop-mortgage-stats" style="display:flex;gap:var(--space-8);flex-wrap:wrap;font-size:var(--size-xs);color:var(--text-2);padding:var(--space-4) 0;border-top:1px solid var(--line-soft);"></div>';

                var labels = top.map(function(e) { return e.storm_id.substring(0, 16); });
                var retained = top.map(function(e) { return e.post_value; });
                var losses = top.map(function(e) { return e.damage_amount; });

                var ctx = document.getElementById('prop-mortgage-chart').getContext('2d');
                currentChart = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: labels,
                        datasets: [
                            {
                                label: 'Retained Value',
                                data: retained,
                                backgroundColor: Theme.value('chart-fill-bright'),
                                borderWidth: 0
                            },
                            {
                                label: 'Damage Loss',
                                data: losses,
                                backgroundColor: Theme.value('chart-fill-red'),
                                borderWidth: 0
                            }
                        ]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { position: 'top', labels: { font: { size: 10 }, boxWidth: 12 } },
                            title: { display: true, text: 'Storm Damage vs Property Value', font: { size: 13 } },
                            annotation: {
                                annotations: {
                                    outstandingLine: {
                                        type: 'line',
                                        yMin: outstanding,
                                        yMax: outstanding,
                                        borderColor: Theme.value('amber-deep'),
                                        borderWidth: 2,
                                        borderDash: [6, 3],
                                        label: {
                                            display: true,
                                            content: 'Outstanding: ' + outstanding.toLocaleString('en-GB', {style:'currency',currency:'GBP',maximumFractionDigits:0}),
                                            position: 'start',
                                            font: { size: 10 },
                                            backgroundColor: Theme.value('chart-fill-amber')
                                        }
                                    }
                                }
                            },
                            tooltip: {
                                callbacks: {
                                    label: function(ctx) {
                                        return ctx.dataset.label + ': ' + ctx.parsed.y.toLocaleString('en-GB', {style:'currency',currency:'GBP',maximumFractionDigits:0});
                                    }
                                }
                            }
                        },
                        scales: {
                            x: { stacked: true, ticks: { font: { size: 9 }, maxRotation: 45 } },
                            y: {
                                stacked: true,
                                title: { display: true, text: 'Value (\u00a3)' },
                                beginAtZero: true,
                                ticks: {
                                    callback: function(v) { return '\u00a3' + (v / 1000).toFixed(0) + 'k'; }
                                }
                            }
                        }
                    }
                });

                // Summary stats
                var negEquityCount = impacts.filter(function(e) { return e.negative_equity; }).length;
                var worstDmg = impacts.length > 0 ? impacts[0] : null;
                var fmtGbp = function(v) { return '\u00a3' + Math.round(v).toLocaleString('en-GB'); };

                var statsHtml = [
                    '<span>Property: <b>' + fmtGbp(propertyValue) + '</b></span>',
                    '<span>Outstanding: <b>' + fmtGbp(outstanding) + '</b></span>',
                    '<span>Current LTV: <b>' + currentLtv.toFixed(1) + '%</b></span>',
                ];
                if (worstDmg) {
                    statsHtml.push('<span>Worst loss: <b>' + fmtGbp(worstDmg.damage_amount) + ' (' + (worstDmg.damage_ratio * 100).toFixed(1) + '%)</b></span>');
                    statsHtml.push('<span>Worst LTV: <b>' + Math.min(worstDmg.post_ltv, 999).toFixed(1) + '%</b></span>');
                }
                if (negEquityCount > 0) {
                    statsHtml.push('<span style="color:var(--red);">Negative equity: <b>' + negEquityCount + '/' + impacts.length + ' storms</b></span>');
                } else {
                    statsHtml.push('<span style="color:var(--green-dark);">No negative equity scenarios</span>');
                }

                document.getElementById('prop-mortgage-stats').innerHTML = statsHtml.join('');
            }
