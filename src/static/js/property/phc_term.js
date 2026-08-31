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

            function renderTermStructure() {
                var ctx = document.getElementById('phc-chart').getContext('2d');
                if (currentChart) currentChart.destroy();

                var ts = phcData.term_structure || {};
                var tenors = ts.tenors || [1, 2, 3, 4, 5];
                var labels = tenors.map(function(t) { return t + 'yr'; });

                // Annual probability from event count
                var severeData = ts.severe || {};
                var spreadBps = (severeData.prs_spread_bps || [])[0] || 0;
                var annualProb = spreadBps / 10000;

                // Survival: S(t) = (1 - p)^t
                var survivalPct = tenors.map(function(t) {
                    return Math.pow(1 - annualProb, t) * 100;
                });

                // Spread is flat across tenors
                var spreadLine = tenors.map(function() { return spreadBps; });

                var datasets = [
                    {
                        label: 'Survival Probability (%)',
                        data: survivalPct,
                        borderColor: Theme.value('accent'),
                        backgroundColor: Theme.value('chart-wash-accent-hex'),
                        fill: true, tension: 0.3, pointRadius: 5,
                        pointBackgroundColor: Theme.value('accent'), borderWidth: 2,
                        yAxisID: 'y'
                    },
                    {
                        label: 'Flood Spread (bp)',
                        data: spreadLine,
                        borderColor: Theme.value('red-bright'),
                        borderDash: [6, 3],
                        borderWidth: 2,
                        pointRadius: 3,
                        pointBackgroundColor: Theme.value('red-bright'),
                        fill: false,
                        yAxisID: 'y1'
                    }
                ];

                // Stage 7 — when the catchment has wind data the flat spread
                // fans into the four peril outcomes. Overlay the union (headline
                // PRS), wind-only and joint flat lines on the spread axis. Absent
                // for flood-only catchments → identical chart as before.
                var perilTs = ts.perils || null;
                var perilSpreads = {};
                if (perilTs) {
                    [
                        ['flood_or_wind', 'Flood \u222A Wind (union)', Theme.value('product-edge'), [2, 2]],
                        ['wind_only',     'Wind only',                  Theme.value('teal-mid'), [4, 4]],
                        ['flood_and_wind','Flood \u2229 Wind (joint)', Theme.value('product'), [1, 3]],
                    ].forEach(function(spec) {
                        var k = spec[0];
                        var leg = (perilTs[k] && perilTs[k].prs_spread_bps) || [];
                        var v = leg[0] || 0;
                        perilSpreads[k] = v;
                        datasets.push({
                            label: spec[1],
                            data: tenors.map(function() { return v; }),
                            borderColor: spec[2],
                            borderDash: spec[3],
                            borderWidth: 2,
                            pointRadius: 2,
                            pointBackgroundColor: spec[2],
                            fill: false,
                            yAxisID: 'y1'
                        });
                    });
                }

                // BRI-anchored combined perils (bow/baw). These are not in
                // term_structure.perils (which carries only the raw-flood fan);
                // they live as flat scalars in spread_decomposition. Overlay them
                // as flat lines, only when the bow/baw scenario files were run.
                var sd = phcData.spread_decomposition || {};
                [
                    ['bow_spread_bps', 'BRI \u222A Wind (union)', Theme.value('purple-deep'), [8, 4]],
                    ['baw_spread_bps', 'BRI \u2229 Wind (joint)', Theme.value('purple-dark'), [2, 4]],
                ].forEach(function(spec) {
                    var v = sd[spec[0]];
                    if (v == null) return;
                    datasets.push({
                        label: spec[1],
                        data: tenors.map(function() { return v; }),
                        borderColor: spec[2],
                        borderDash: spec[3],
                        borderWidth: 2,
                        pointRadius: 2,
                        pointBackgroundColor: spec[2],
                        fill: false,
                        yAxisID: 'y1'
                    });
                });

                currentChart = new Chart(ctx, {
                    type: 'line',
                    data: { labels: labels, datasets: datasets },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        interaction: { intersect: false, mode: 'index' },
                        plugins: {
                            legend: {
                                position: 'top',
                                labels: { usePointStyle: true, boxWidth: 8, font: { size: 11 } }
                            },
                            tooltip: {
                                callbacks: {
                                    label: function(ctx) {
                                        if (ctx.datasetIndex === 0)
                                            return 'Survival: ' + ctx.parsed.y.toFixed(2) + '%';
                                        return 'Spread: ' + ctx.parsed.y.toFixed(1) + ' bp';
                                    }
                                }
                            }
                        },
                        scales: {
                            x: { title: { display: true, text: 'Tenor (years)', font: { size: 11 } } },
                            y: {
                                title: { display: true, text: 'Survival Probability (%)', font: { size: 11 } },
                                min: Math.max(0, Math.min.apply(null, survivalPct) - 5),
                                max: 100,
                                position: 'left'
                            },
                            y1: {
                                title: { display: true, text: 'Spread (bp)', font: { size: 11 } },
                                position: 'right',
                                grid: { drawOnChartArea: false },
                                min: 0
                            }
                        }
                    }
                });

                // Stats bar
                var bar = document.getElementById('phc-stats-bar');
                var summary = phcData.summary || {};
                var zone = phcData.flood_zone || '';

                var barItems = [
                    '<span style="color:var(--accent);font-weight:bold;">Event Count</span>',
                    '<span><b>Zone:</b> ' + zone + '</span>',
                    '<span><b>Floods:</b> ' + phcData.flood_count + '</span>',
                    '<span><b>Flood Spread:</b> <span style="color:var(--red-bright);">' + spreadBps.toFixed(1) + ' bp</span></span>',
                ];
                if (perilTs) {
                    barItems.push(
                        '<span><b>Flood\u222AWind:</b> <span style="color:var(--product-edge);">' +
                        (perilSpreads.flood_or_wind || 0).toFixed(1) + ' bp</span></span>',
                        '<span><b>Wind only:</b> <span style="color:var(--teal-mid);">' +
                        (perilSpreads.wind_only || 0).toFixed(1) + ' bp</span></span>');
                }
                barItems.push(
                    '<span><b>P(annual):</b> ' + (annualProb * 100).toFixed(3) + '%</span>',
                    '<span><b>S(5yr):</b> ' + survivalPct[survivalPct.length - 1].toFixed(2) + '%</span>',
                    '<span><b>Max Depth:</b> ' + (summary.max_depth_m || 0).toFixed(2) + 'm</span>',
                    '<span><b>Transmission:</b> ' + ((summary.flood_transmission_rate || 0) * 100).toFixed(1) + '%</span>');
                bar.innerHTML = barItems.join('');
            }
