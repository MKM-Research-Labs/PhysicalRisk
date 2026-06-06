
            // ================================================================
            // Tab 3: Basis Analysis (Bar chart by gauge)
            // ================================================================
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
                    { key: 'any_flood', color: '#4CAF50', label: 'Any Flood' },
                    { key: 'moderate', color: '#FF9800', label: 'Moderate' },
                    { key: 'severe', color: '#F44336', label: 'Severe' }
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
