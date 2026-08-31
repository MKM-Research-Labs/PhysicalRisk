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

            function renderBasisAnalysis() {
                var ctx = document.getElementById('phc-chart').getContext('2d');
                if (currentChart) currentChart.destroy();

                var nearestGauges = phcData.nearest_gauges || [];
                var ts = phcData.term_structure || {};
                var tenors = ts.tenors || [];
                var idx5 = tenors.indexOf(5);
                if (idx5 < 0) idx5 = 3;

                var gaugeLabels = nearestGauges.map(function(ng) {
                    return ng.gauge_id.substring(0, 14) + '\n(' + ng.distance_km + 'km)';
                });

                var thresholdInfo = [
                    { key: 'any_flood', color: Theme.value('green-bright'), label: 'Any Flood' },
                    { key: 'moderate', color: Theme.value('amber-bright'), label: 'Moderate' },
                    { key: 'severe', color: Theme.value('red-bright'), label: 'Severe' }
                ];

                var datasets = thresholdInfo.map(function(ti) {
                    return {
                        label: ti.label + ' Basis (5yr)',
                        data: nearestGauges.map(function(ng) {
                            var basisData = (ng.basis_bps || {})[ti.key] || {};
                            var vals = basisData.values || [];
                            return vals[idx5] || 0;
                        }),
                        backgroundColor: ti.color + 'BB',
                        borderColor: ti.color,
                        borderWidth: 1
                    };
                });

                currentChart = new Chart(ctx, {
                    type: 'bar',
                    data: { labels: gaugeLabels, datasets: datasets },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                position: 'top',
                                labels: { usePointStyle: true, boxWidth: 8, font: { size: 11 } }
                            },
                            tooltip: {
                                callbacks: {
                                    label: function(ctx) {
                                        return ctx.dataset.label + ': ' + ctx.parsed.y.toFixed(1) + ' bps';
                                    }
                                }
                            }
                        },
                        scales: {
                            x: { title: { display: true, text: 'Nearest Gauge' } },
                            y: { title: { display: true, text: 'Basis (bps)' } }
                        }
                    }
                });

                var bar = document.getElementById('phc-stats-bar');
                var parts = ['<span><b>Event Counts:</b></span>'];

                nearestGauges.forEach(function(ng) {
                    parts.push(
                        '<span>' + ng.gauge_id.substring(0, 12) + ': ' +
                        ng.property_flood_count + '/' + ng.gauge_flood_count +
                        ' (' + (ng.flood_transmission_rate * 100).toFixed(0) + '%) ' +
                        'basis=' + ng.event_basis + '</span>'
                    );
                });

                bar.innerHTML = parts.join('');
            }
