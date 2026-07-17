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
                        '<div style="text-align:center;padding-top:40px;">' +
                        '<div style="font-size:13px;font-weight:600;color:#333;margin-bottom:8px;">' +
                        g.gauge_name + '</div>' +
                        '<div style="font-size:11px;color:#999;margin-bottom:16px;">' + g.gauge_id + '</div>' +
                        '<div style="color:#999;font-size:12px;margin-bottom:20px;">No classifier trained</div>' +
                        '<button id="cl-detail-train-btn" data-train-gauge="' + g.gauge_id + '" ' +
                        'style="padding:8px 24px;font-size:12px;font-weight:600;background:#1976d2;' +
                        'color:white;border:none;border-radius:4px;cursor:pointer;">Train Now</button>' +
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
                html += '<div style="margin-bottom:12px;">';
                html += '<div style="font-size:13px;font-weight:600;color:#333;">' + g.gauge_name + '</div>';
                html += '<div style="font-size:10px;color:#999;">' + g.gauge_id + '</div>';
                html += '</div>';

                // Metrics grid (2x2)
                html += '<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:16px;">';

                // AUC-ROC
                var auc = g.auc_roc;
                var aucColor = auc >= 0.95 ? '#2e7d32' : (auc >= 0.90 ? '#f57f17' : '#c62828');
                html += _clMetricCard('AUC-ROC', auc != null ? auc.toFixed(4) : '\u2014', aucColor);

                // Accuracy
                html += _clMetricCard('Accuracy', g.accuracy != null ? g.accuracy.toFixed(4) : '\u2014', '#1565c0');

                // Brier Score
                var brier = g.brier_score;
                var brierColor = brier != null && brier < 0.05 ? '#2e7d32' : '#f57f17';
                html += _clMetricCard('Brier Score', brier != null ? brier.toFixed(4) : '\u2014', brierColor);

                // Flood Rate
                html += _clMetricCard('Flood Rate',
                    g.flood_rate != null ? (g.flood_rate * 100).toFixed(1) + '%' : '\u2014', '#6a1b9a');

                html += '</div>';

                // Info line
                html += '<div style="font-size:10px;color:#888;margin-bottom:12px;">';
                if (g.n_samples) html += g.n_samples.toLocaleString() + ' samples';
                if (g.label_threshold) html += '  \u00b7  label: ' + g.label_threshold;
                if (g.severe_level) html += '  \u00b7  severe: ' + g.severe_level.toFixed(2) + 'm';
                html += '</div>';

                // Chart canvas
                html += '<div style="font-size:11px;font-weight:600;color:#333;margin-bottom:8px;">Feature Importance</div>';
                html += '<div style="height:180px;"><canvas id="cl-feature-chart"></canvas></div>';

                pane.innerHTML = html;

                // Render feature importance chart
                _clRenderFeatureChart(g.feature_importance);
            }

            function _clMetricCard(label, value, color) {
                return '<div style="background:#f8f9fa;border-radius:6px;padding:10px;text-align:center;">' +
                    '<div style="font-size:9px;color:#888;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:4px;">' +
                    label + '</div>' +
                    '<div style="font-size:18px;font-weight:700;color:' + color + ';">' + value + '</div>' +
                    '</div>';
            }

            function _clRenderFeatureChart(fi) {
                if (!fi) return;
                var canvas = document.getElementById('cl-feature-chart');
                if (!canvas) return;

                var labels = ['log(w/s)', 'log(t/T)', '\u0394 log(w/s)', '\u0394\u00b2 log(w/s)'];
                var keys = ['log_h_s', 'log_t_end', 'delta_log_h', 'delta2_log_h'];
                var values = keys.map(function(k) { return fi[k] || 0; });
                var colors = ['#1976d2', '#388e3c', '#f57f17', '#c62828'];

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
                                grid: { color: '#f0f0f0' }
                            },
                            y: {
                                ticks: { font: { size: 10 } },
                                grid: { display: false }
                            }
                        }
                    }
                });
            }
