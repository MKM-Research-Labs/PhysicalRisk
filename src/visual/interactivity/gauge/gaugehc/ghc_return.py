# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Gauge hazard curve — Return Period and Flood Probability tabs.

Tab 2: Return period vs water level with flood stage overlays.
Tab 4: Cumulative flood probability term structure by severity.
"""


def get_js() -> str:
    """Return JS fragment for return period and flood probability tabs."""
    return """
            // ================================================================
            // Tab 2: Return Period (Return Period vs Water Level)
            // ================================================================
            function renderReturnPeriod() {
                var ctx = document.getElementById('hazard-chart').getContext('2d');
                if (currentChart) currentChart.destroy();

                var rpl = hazardData.return_period_levels || {};
                var fs = hazardData.flood_stages || {};

                var periods = ['2yr', '5yr', '10yr', '20yr', '50yr', '100yr'];
                var labels = periods.map(function(p) { return p.replace('yr', ''); });
                var levels = periods.map(function(p) { return rpl[p] || null; });

                var n = labels.length;
                var datasets = [{
                    label: 'Water Level (m)',
                    data: levels,
                    borderColor: '#2196F3',
                    backgroundColor: 'rgba(33,150,243,0.1)',
                    fill: true,
                    tension: 0.4,
                    pointRadius: 4,
                    pointBackgroundColor: '#2196F3',
                    borderWidth: 2
                }];

                if (fs.FloodAlert) datasets.push({
                    label: 'Alert (' + fs.FloodAlert.toFixed(1) + 'm)',
                    data: Array(n).fill(fs.FloodAlert),
                    borderColor: '#FFC107', borderDash: [5,5], borderWidth: 2, pointRadius: 0, fill: false
                });
                if (fs.FloodWarning) datasets.push({
                    label: 'Warning (' + fs.FloodWarning.toFixed(1) + 'm)',
                    data: Array(n).fill(fs.FloodWarning),
                    borderColor: '#FF9800', borderDash: [5,5], borderWidth: 2, pointRadius: 0, fill: false
                });
                if (fs.SevereFloodWarning) datasets.push({
                    label: 'Severe (' + fs.SevereFloodWarning.toFixed(1) + 'm)',
                    data: Array(n).fill(fs.SevereFloodWarning),
                    borderColor: '#F44336', borderDash: [5,5], borderWidth: 2, pointRadius: 0, fill: false
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
                                    title: function(items) {
                                        return '1-in-' + labels[items[0].dataIndex] + ' year event';
                                    },
                                    label: function(ctx) {
                                        return ctx.dataset.label + ': ' + ctx.parsed.y.toFixed(2) + 'm';
                                    }
                                }
                            }
                        },
                        scales: {
                            x: { title: { display: true, text: 'Return Period (years)' } },
                            y: { title: { display: true, text: 'Water Level (m)' }, min: 0 }
                        }
                    }
                });

                var gev = hazardData.gev_parameters || {};
                var probs = hazardData.annual_flood_probs || {};
                var bar = document.getElementById('hazard-stats-bar');
                bar.innerHTML = [
                    '<span><b>GEV \\u03BC:</b> ' + (gev.location != null ? gev.location.toFixed(2) : 'N/A') + '</span>',
                    '<span><b>GEV \\u03C3:</b> ' + (gev.scale != null ? gev.scale.toFixed(4) : 'N/A') + '</span>',
                    '<span><b>GEV \\u03BE:</b> ' + (gev.shape != null ? gev.shape.toFixed(3) : 'N/A') + '</span>',
                    '<span style="color:#FFC107;"><b>P(Alert):</b> ' + (probs.alert ? (probs.alert * 100).toFixed(2) : '0') + '%/yr</span>',
                    '<span style="color:#FF9800;"><b>P(Warning):</b> ' + (probs.warning ? (probs.warning * 100).toFixed(2) : '0') + '%/yr</span>',
                    '<span style="color:#F44336;"><b>P(Severe):</b> ' + (probs.severe ? (probs.severe * 100).toFixed(2) : '0') + '%/yr</span>'
                ].join('');
            }

            // ================================================================
            // Tab 4: Flood Probability (Term Structure)
            // ================================================================
            function renderFloodProbability() {
                var ctx = document.getElementById('hazard-chart').getContext('2d');
                if (currentChart) currentChart.destroy();

                var ts = hazardData.term_structures || {};
                var tsAlert = ts.alert || [];
                var tsWarning = ts.warning || [];
                var tsSevere = ts.severe || [];

                var years = tsAlert.map(function(t) { return t.year + 'Y'; });

                currentChart = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: years,
                        datasets: [
                            {
                                label: 'Alert \\u2014 P(flood)',
                                data: tsAlert.map(function(t) { return t.cumulative_default_prob * 100; }),
                                borderColor: '#FFC107',
                                backgroundColor: 'rgba(255,193,7,0.15)',
                                fill: true, tension: 0.3, pointRadius: 5,
                                pointBackgroundColor: '#FFC107', borderWidth: 2
                            },
                            {
                                label: 'Warning \\u2014 P(flood)',
                                data: tsWarning.map(function(t) { return t.cumulative_default_prob * 100; }),
                                borderColor: '#FF9800',
                                backgroundColor: 'rgba(255,152,0,0.15)',
                                fill: true, tension: 0.3, pointRadius: 5,
                                pointBackgroundColor: '#FF9800', borderWidth: 2
                            },
                            {
                                label: 'Severe \\u2014 P(flood)',
                                data: tsSevere.map(function(t) { return t.cumulative_default_prob * 100; }),
                                borderColor: '#F44336',
                                backgroundColor: 'rgba(244,67,54,0.15)',
                                fill: true, tension: 0.3, pointRadius: 5,
                                pointBackgroundColor: '#F44336', borderWidth: 2
                            }
                        ]
                    },
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
                                        var idx = ctx.dataIndex;
                                        var ds = ctx.datasetIndex;
                                        var arr = [tsAlert, tsWarning, tsSevere][ds];
                                        var point = arr[idx];
                                        var survival = point ? (point.survival_prob * 100).toFixed(2) : '?';
                                        return ctx.dataset.label + ': ' + ctx.parsed.y.toFixed(2) + '% (survival: ' + survival + '%)';
                                    }
                                }
                            }
                        },
                        scales: {
                            x: { title: { display: true, text: 'Tenor' } },
                            y: { title: { display: true, text: 'Cumulative Flood Probability (%)' } }
                        }
                    }
                });

                var bar = document.getElementById('hazard-stats-bar');
                var a1 = tsAlert[0] ? (tsAlert[0].cumulative_default_prob * 100).toFixed(2) : '0';
                var a5 = tsAlert[4] ? (tsAlert[4].cumulative_default_prob * 100).toFixed(2) : '0';
                var w1 = tsWarning[0] ? (tsWarning[0].cumulative_default_prob * 100).toFixed(2) : '0';
                var w5 = tsWarning[4] ? (tsWarning[4].cumulative_default_prob * 100).toFixed(2) : '0';
                var s1 = tsSevere[0] ? (tsSevere[0].cumulative_default_prob * 100).toFixed(2) : '0';
                var s5 = tsSevere[4] ? (tsSevere[4].cumulative_default_prob * 100).toFixed(2) : '0';

                bar.innerHTML = [
                    '<span style="color:#FFC107;"><b>Alert 1yr:</b> ' + a1 + '%</span>',
                    '<span style="color:#FFC107;"><b>5yr:</b> ' + a5 + '%</span>',
                    '<span style="color:#FF9800;"><b>Warning 1yr:</b> ' + w1 + '%</span>',
                    '<span style="color:#FF9800;"><b>5yr:</b> ' + w5 + '%</span>',
                    '<span style="color:#F44336;"><b>Severe 1yr:</b> ' + s1 + '%</span>',
                    '<span style="color:#F44336;"><b>5yr:</b> ' + s5 + '%</span>'
                ].join('');
            }
"""
