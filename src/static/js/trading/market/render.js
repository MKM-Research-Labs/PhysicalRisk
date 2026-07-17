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

            function renderYieldCurve(chartArea, inputRow, label, info) {
                if (label) label.textContent = 'Risk-Free Yield Curve';

                var tenors = ['1', '2', '3', '4', '5', '6'];
                var rates = tenors.map(function(t) { return (tdYieldCurve[t] || 0) * 100; });

                tdRenderLineChart(chartArea, tenors.map(function(t) { return t + 'Y'; }), rates, {
                    title: 'Yield Curve (Continuous Rate)',
                    yLabel: 'Rate (%)',
                    lineColor: '#1565c0',
                    pointColor: '#0d47a1',
                    yDecimals: 2,
                    suffix: '%'
                });

                // Editable tenor inputs
                if (inputRow) {
                    var html = '<div style="display:flex;gap:12px;align-items:center;flex-wrap:wrap;">';
                    html += '<span style="font-size:10px;font-weight:600;color:#555;">Rates:</span>';
                    for (var i = 0; i < tenors.length; i++) {
                        var rate = (tdYieldCurve[tenors[i]] || 0) * 100;
                        html += '<div style="display:flex;align-items:center;gap:2px;">' +
                            '<span style="font-size:10px;color:#888;">' + tenors[i] + 'Y</span>' +
                            '<input type="number" value="' + rate.toFixed(2) + '" step="0.05" min="0" max="20" ' +
                                'data-tenor="' + tenors[i] + '" data-mode="yield" ' +
                                'onchange="tdCurveInputChanged(this)" oninput="tdCurveInputChanged(this)" ' +
                                'style="width:52px;font-size:10px;padding:2px 4px;border:1px solid #ddd;border-radius:3px;text-align:right;">' +
                            '<span style="font-size:9px;color:#999;">%</span>' +
                        '</div>';
                    }
                    html += '</div>';
                    inputRow.innerHTML = html;
                }

                // Info bar + commit button dirty state
                if (info) {
                    var avg = rates.reduce(function(a, b) { return a + b; }, 0) / rates.length;
                    info.innerHTML = 'Average yield: ' + avg.toFixed(2) + '% | Peak: ' + Math.max.apply(null, rates).toFixed(2) + '%' +
                        (tdYieldDirty ? ' | <span style="color:#e65100;font-weight:600;">UNCOMMITTED</span>' : '');
                }
                var commitBtn = document.getElementById('td-commit-btn');
                if (commitBtn) {
                    var anyDirty = tdYieldDirty || Object.keys(tdHazardDirtyKeys).some(function(k) { return tdHazardDirtyKeys[k]; });
                    commitBtn.style.background = anyDirty ? '#e65100' : '#1976d2';
                    commitBtn.textContent = anyDirty ? 'Commit*' : 'Commit';
                }
            }

            function renderHazardCurve(chartArea, inputRow, label, info) {
                var trigger = tdCurveMode;
                var gaugeName = tdSelectedGauge;
                if (tdMarketData && tdMarketData[tdSelectedGauge]) {
                    gaugeName = tdExtractAreaName(tdMarketData[tdSelectedGauge].gauge_name || tdSelectedGauge);
                }

                if (label) label.textContent = gaugeName + ' \u2014 ' + trigger.charAt(0).toUpperCase() + trigger.slice(1);

                var triggerTS = (tdHazardTS[tdSelectedGauge] && tdHazardTS[tdSelectedGauge][trigger]) || {};
                var tenors = ['1', '2', '3', '4', '5'];
                var rates = tenors.map(function(t) { return (triggerTS[t] || 0) * 10000; });

                var colors = {alert: '#fbc02d', warning: '#f57c00', severe: '#d32f2f'};
                var darks = {alert: '#f9a825', warning: '#e65100', severe: '#b71c1c'};
                var color = colors[trigger] || '#1565c0';
                var dark = darks[trigger] || '#0d47a1';

                // Get base flat rate for annotation line
                var baseRate = 0;
                if (tdMarketData && tdMarketData[tdSelectedGauge]) {
                    baseRate = (tdMarketData[tdSelectedGauge]['annual_hazard_rate_' + trigger] || 0) * 10000;
                }

                tdRenderLineChart(chartArea, tenors.map(function(t) { return t + 'Y'; }), rates, {
                    title: 'Hazard Term Structure \u2014 ' + trigger.charAt(0).toUpperCase() + trigger.slice(1),
                    yLabel: 'Hazard Rate (bps)',
                    lineColor: color,
                    pointColor: dark,
                    yDecimals: 1,
                    suffix: ' bps',
                    beginAtZero: true,
                    annotationY: baseRate,
                    annotationLabel: 'Historical (flat)'
                });

                // Editable tenor inputs
                if (inputRow) {
                    var html = '<div style="display:flex;gap:12px;align-items:center;flex-wrap:wrap;">';
                    html += '<span style="font-size:10px;font-weight:600;color:' + color + ';">' + trigger.charAt(0).toUpperCase() + trigger.slice(1) + ':</span>';
                    for (var i = 0; i < tenors.length; i++) {
                        var rate = (triggerTS[tenors[i]] || 0) * 10000;
                        html += '<div style="display:flex;align-items:center;gap:2px;">' +
                            '<span style="font-size:10px;color:#888;">' + tenors[i] + 'Y</span>' +
                            '<input type="number" value="' + rate.toFixed(1) + '" step="1" min="0" max="5000" ' +
                                'data-tenor="' + tenors[i] + '" data-mode="hazard" data-trigger="' + trigger + '" data-gauge="' + tdSelectedGauge + '" ' +
                                'onchange="tdCurveInputChanged(this)" oninput="tdCurveInputChanged(this)" ' +
                                'style="width:55px;font-size:10px;padding:2px 4px;border:1px solid #ddd;border-radius:3px;text-align:right;">' +
                            '<span style="font-size:9px;color:#999;">bps</span>' +
                        '</div>';
                    }
                    html += '</div>';
                    inputRow.innerHTML = html;
                }

                // Info bar
                var isDirty = tdHazardDirtyKeys[tdSelectedGauge + ':' + trigger];
                if (info && tdMarketData && tdMarketData[tdSelectedGauge]) {
                    info.innerHTML =
                        'Historical (flat): ' + baseRate.toFixed(1) + ' bps | ' +
                        'Short end: ' + rates[0].toFixed(1) + ' bps | Long end: ' + rates[rates.length - 1].toFixed(1) + ' bps' +
                        (tdMarketData[tdSelectedGauge].is_adjusted ? ' | <span style="color:#f57c00;font-weight:600;">ADJUSTED</span>' : '') +
                        (isDirty ? ' | <span style="color:#e65100;font-weight:600;">UNCOMMITTED</span>' : '');
                }
                // Highlight commit button if there are uncommitted changes
                var commitBtn = document.getElementById('td-commit-btn');
                if (commitBtn) {
                    commitBtn.style.background = isDirty ? '#e65100' : '#1976d2';
                    commitBtn.textContent = isDirty ? 'Commit*' : 'Commit';
                }
            }

            function tdRenderLineChart(container, labels, data, opts) {
                // Destroy old chart
                if (tdMarketChart) {
                    tdMarketChart.destroy();
                    tdMarketChart = null;
                }

                // Guard: Chart.js must be loaded
                if (typeof Chart === 'undefined') {
                    console.error('[Market] Chart.js not loaded');
                    container.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:100%;color:#c62828;font-size:12px;">Chart.js not loaded — refresh the page</div>';
                    return;
                }

                // Ensure canvas — must recreate to avoid stale context
                container.innerHTML = '';
                var canvas = document.createElement('canvas');
                canvas.id = 'td-market-canvas';
                canvas.style.cssText = 'width:100%;height:100%;';
                container.appendChild(canvas);

                // Check if dragData plugin is available (global is ChartJSDragDataPlugin with capital D)
                var hasDrag = typeof ChartJSDragDataPlugin !== 'undefined' || (Chart.registry && Chart.registry.plugins && Chart.registry.plugins.get('dragData'));

                var chartOpts = {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        title: {display: true, text: opts.title, font: {size: 13}},
                        legend: {display: false},
                        tooltip: {
                            callbacks: {
                                label: function(ctx) {
                                    return ctx.parsed.y.toFixed(opts.yDecimals) + (opts.suffix || '');
                                }
                            }
                        },
                        dragData: {
                            round: opts.yDecimals,
                            showTooltip: true,
                            onDragEnd: function(e, datasetIndex, index, value) {
                                var tenorNum = labels[index].replace('Y', '');
                                console.log('[Market] Drag end: tenor=' + tenorNum + 'Y value=' + value.toFixed(opts.yDecimals));
                                var inputs = document.querySelectorAll('#td-market-inputs input[data-tenor]');
                                var found = false;
                                for (var j = 0; j < inputs.length; j++) {
                                    if (inputs[j].getAttribute('data-tenor') === tenorNum) {
                                        inputs[j].value = value.toFixed(opts.yDecimals);
                                        tdCurveInputChanged(inputs[j]);
                                        found = true;
                                        break;
                                    }
                                }
                                if (!found) console.error('[Market] Drag: no input found for tenor ' + tenorNum);
                            }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: !!opts.beginAtZero,
                            suggestedMin: opts.suggestedMin != null ? opts.suggestedMin : undefined,
                            suggestedMax: (function() {
                                var peak = Math.max.apply(null, data);
                                if (opts.annotationY && opts.annotationY > peak) peak = opts.annotationY;
                                return peak > 0 ? peak * 1.25 : 1;
                            })(),
                            title: {display: true, text: opts.yLabel},
                            ticks: {
                                callback: function(val) { return val.toFixed(opts.yDecimals > 1 ? 1 : 0); }
                            }
                        },
                        x: {
                            title: {display: true, text: 'Tenor'}
                        }
                    }
                };

                // Add annotation line for historical base rate
                if (opts.annotationY && opts.annotationY > 0) {
                    chartOpts.plugins.annotation = {
                        annotations: {
                            baseLine: {
                                type: 'line',
                                yMin: opts.annotationY,
                                yMax: opts.annotationY,
                                borderColor: '#90a4ae',
                                borderWidth: 1.5,
                                borderDash: [6, 3],
                                label: {
                                    display: true,
                                    content: opts.annotationLabel || 'Base',
                                    position: 'start',
                                    font: {size: 9},
                                    backgroundColor: 'rgba(144,164,174,0.8)'
                                }
                            }
                        }
                    };
                }

                // If dragData not available, remove the plugin config to avoid errors
                if (!hasDrag) {
                    delete chartOpts.plugins.dragData;
                }

                try {
                    tdMarketChart = new Chart(canvas.getContext('2d'), {
                        type: 'line',
                        data: {
                            labels: labels,
                            datasets: [{
                                label: opts.title,
                                data: data,
                                borderColor: opts.lineColor,
                                backgroundColor: opts.lineColor + '20',
                                pointBackgroundColor: opts.pointColor,
                                pointBorderColor: opts.pointColor,
                                pointRadius: 7,
                                pointHoverRadius: 10,
                                pointHitRadius: 15,
                                borderWidth: 2,
                                fill: true,
                                tension: 0.3
                            }]
                        },
                        options: chartOpts
                    });
                } catch(e) {
                    console.error('[Market] Chart render error:', e);
                    // Retry without dragData
                    delete chartOpts.plugins.dragData;
                    container.innerHTML = '';
                    canvas = document.createElement('canvas');
                    canvas.id = 'td-market-canvas';
                    canvas.style.cssText = 'width:100%;height:100%;';
                    container.appendChild(canvas);
                    tdMarketChart = new Chart(canvas.getContext('2d'), {
                        type: 'line',
                        data: {
                            labels: labels,
                            datasets: [{
                                label: opts.title,
                                data: data,
                                borderColor: opts.lineColor,
                                backgroundColor: opts.lineColor + '20',
                                pointBackgroundColor: opts.pointColor,
                                pointBorderColor: opts.pointColor,
                                pointRadius: 7,
                                pointHoverRadius: 10,
                                pointHitRadius: 15,
                                borderWidth: 2,
                                fill: true,
                                tension: 0.3
                            }]
                        },
                        options: chartOpts
                    });
                }
            }
