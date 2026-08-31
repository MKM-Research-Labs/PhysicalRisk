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

            function _clRenderDetail(g) {
                var pane = document.getElementById('cl-detail-pane');
                if (!pane) return;

                // Destroy existing chart
                if (clFeatureChart) {
                    clFeatureChart.destroy();
                    clFeatureChart = null;
                }

                if (!g.has_model) {
                    pane.innerHTML =
                        '<div style="text-align:center;padding-top:var(--space-inset);">' +
                        '<div style="font-size:var(--size-md);font-weight:600;color:var(--text);margin-bottom:var(--space-4);">' +
                        g.gauge_name + '</div>' +
                        '<div style="font-size:var(--size-xs);color:var(--muted-2);margin-bottom:var(--space-8);">' + g.gauge_id + '</div>' +
                        '<div style="color:var(--muted-2);font-size:var(--size-sm);margin-bottom:var(--space-wide);">No classifier trained</div>' +
                        '<button id="cl-detail-train-btn" data-train-gauge="' + g.gauge_id + '" ' +
                        'style="padding:var(--space-4) var(--space-10);font-size:var(--size-sm);font-weight:600;background:var(--accent);' +
                        'color:var(--inverse);border:none;border-radius:var(--radius-4);cursor:pointer;">Train Now</button>' +
                        '</div>';
                    var btn = document.getElementById('cl-detail-train-btn');
                    if (btn) {
                        btn.addEventListener('click', function() {
                            _clStartSingleTraining(g.gauge_id);
                        });
                    }
                    return;
                }

                var html = '';

                // Header
                html += '<div style="margin-bottom:var(--space-6);">';
                html += '<div style="font-size:var(--size-md);font-weight:600;color:var(--text);">' + g.gauge_name + '</div>';
                html += '<div style="font-size:var(--size-xxs);color:var(--muted-2);">' + g.gauge_id + '</div>';
                html += '</div>';

                // Metrics grid (2x2)
                html += '<div style="display:grid;grid-template-columns:1fr 1fr;gap:var(--space-4);margin-bottom:var(--space-8);">';

                // AUC-ROC
                var auc = g.auc_roc;
                var aucColor = auc >= 0.95 ? Theme.value('green-dark') : (auc >= 0.90 ? Theme.value('gold-dark') : Theme.value('red-dark'));
                html += _clMetricCard('AUC-ROC', auc != null ? auc.toFixed(4) : '\u2014', aucColor);

                // Accuracy
                html += _clMetricCard('Accuracy', g.accuracy != null ? g.accuracy.toFixed(4) : '\u2014', Theme.value('accent-mid'));

                // Brier Score
                var brier = g.brier_score;
                var brierColor = brier != null && brier < 0.05 ? Theme.value('green-dark') : Theme.value('gold-dark');
                html += _clMetricCard('Brier Score', brier != null ? brier.toFixed(4) : '\u2014', brierColor);

                // Flood Rate
                html += _clMetricCard('Flood Rate',
                    g.flood_rate != null ? (g.flood_rate * 100).toFixed(1) + '%' : '\u2014', Theme.value('purple-deep'));

                html += '</div>';

                // Info line
                html += '<div style="font-size:var(--size-xxs);color:var(--muted);margin-bottom:var(--space-6);">';
                if (g.n_samples) html += g.n_samples.toLocaleString() + ' samples';
                if (g.label_threshold) html += '  \u00b7  label: ' + g.label_threshold;
                if (g.severe_level) html += '  \u00b7  severe: ' + g.severe_level.toFixed(2) + 'm';
                html += '</div>';

                // Chart canvas
                html += '<div style="font-size:var(--size-xs);font-weight:600;color:var(--text);margin-bottom:var(--space-4);">Feature Importance</div>';
                html += '<div style="height:180px;"><canvas id="cl-feature-chart"></canvas></div>';

                pane.innerHTML = html;

                // Render feature importance chart
                _clRenderFeatureChart(g.feature_importance);
            }

            function _clMetricCard(label, value, color) {
                return '<div style="background:var(--wash);border-radius:var(--radius-md);padding:var(--space-5);text-align:center;">' +
                    '<div style="font-size:var(--size-xxs);color:var(--muted);text-transform:uppercase;letter-spacing:0.5px;margin-bottom:var(--space-2);">' +
                    label + '</div>' +
                    '<div style="font-size:var(--size-18);font-weight:700;color:' + color + ';">' + value + '</div>' +
                    '</div>';
            }

            function _clRenderFeatureChart(fi) {
                if (!fi) return;
                var canvas = document.getElementById('cl-feature-chart');
                if (!canvas) return;

                var labels = ['log(w/s)', 'log(t/T)', '\u0394 log(w/s)', '\u0394\u00b2 log(w/s)'];
                var keys = ['log_h_s', 'log_t_end', 'delta_log_h', 'delta2_log_h'];
                var values = keys.map(function(k) { return fi[k] || 0; });
                var colors = [Theme.value('accent'), Theme.value('green'), Theme.value('gold-dark'), Theme.value('red-dark')];

                clFeatureChart = new Chart(canvas, {
                    type: 'bar',
                    data: {
                        labels: labels,
                        datasets: [{
                            data: values,
                            backgroundColor: colors,
                            borderRadius: 4,
                            barThickness: 24
                        }]
                    },
                    options: {
                        indexAxis: 'y',
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { display: false },
                            tooltip: {
                                callbacks: {
                                    label: function(ctx) {
                                        return (ctx.raw * 100).toFixed(1) + '%';
                                    }
                                }
                            }
                        },
                        scales: {
                            x: {
                                beginAtZero: true,
                                max: 1.0,
                                ticks: { font: { size: 10 }, callback: function(v) { return (v * 100) + '%'; } },
                                grid: { color: Theme.value('code') }
                            },
                            y: {
                                ticks: { font: { size: 10 } },
                                grid: { display: false }
                            }
                        }
                    }
                });
            }
