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
Property hazard curve — Term Structure tab sub-module.

Survival probability curves and hazard rates across tenors
for three flood severity thresholds.
"""


def get_js() -> str:
    """Return JS fragment for term structure tab (injected into parent IIFE)."""
    return """
            // ================================================================
            // Tab 1: Term Structure (Survival Probability)
            // ================================================================
            function renderTermStructure() {
                var ctx = document.getElementById('phc-chart').getContext('2d');
                if (currentChart) currentChart.destroy();

                var ts = phcData.term_structure || {};
                var tenors = ts.tenors || [];
                var labels = tenors.map(function(t) { return t + 'yr'; });

                var datasets = [];
                var thresholdInfo = {
                    'any_flood': { color: '#4CAF50', label: 'Any Flood (>0m)' },
                    'moderate': { color: '#FF9800', label: 'Moderate (>0.5m)' },
                    'severe': { color: '#F44336', label: 'Severe (>1.0m)' }
                };

                var thresholdProbs = phcData.depth_thresholds || {};

                Object.keys(thresholdInfo).forEach(function(key) {
                    var info = thresholdInfo[key];
                    var data = ts[key] || {};
                    var survival = data.survival || [];

                    datasets.push({
                        label: info.label + ' (survival)',
                        data: survival.map(function(s) { return s * 100; }),
                        borderColor: info.color,
                        backgroundColor: info.color + '22',
                        fill: false, tension: 0.3, pointRadius: 4,
                        pointBackgroundColor: info.color, borderWidth: 2,
                        yAxisID: 'y'
                    });

                    var lambda = (thresholdProbs[key] || {}).annual_probability || 0;
                    if (lambda > 0) {
                        datasets.push({
                            label: info.label + ' (hazard rate)',
                            data: Array(tenors.length).fill(lambda * 100),
                            borderColor: info.color,
                            borderDash: [6, 3],
                            borderWidth: 1.5,
                            pointRadius: 0,
                            fill: false,
                            yAxisID: 'y1'
                        });
                    }
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
                                        return ctx.dataset.label + ': ' + ctx.parsed.y.toFixed(2) + '%';
                                    }
                                }
                            }
                        },
                        scales: {
                            x: { title: { display: true, text: 'Tenor (years)' } },
                            y: { title: { display: true, text: 'Survival Probability (%)' }, min: 0, max: 100, position: 'left' },
                            y1: { title: { display: true, text: 'Hazard Rate (%/yr)' }, position: 'right', grid: { drawOnChartArea: false } }
                        }
                    }
                });

                var bar = document.getElementById('phc-stats-bar');
                var summary = phcData.summary || {};
                var methodTag = phcData.has_gev ?
                    '<span style="color:#1976D2;font-weight:bold;">GEV Fitted</span>' :
                    '<span style="color:#FF9800;font-weight:bold;">Floor (' + (phcData.min_spread_bps || 2) + 'bp)</span>';
                bar.innerHTML = [
                    methodTag,
                    '<span><b>Floods:</b> ' + phcData.flood_count + '</span>',
                    '<span><b>Max Depth:</b> ' + (summary.max_depth_m || 0).toFixed(2) + 'm</span>',
                    '<span><b>Mean Depth:</b> ' + (summary.mean_depth_m || 0).toFixed(2) + 'm</span>',
                    '<span><b>Elevation:</b> ' + (phcData.elevation_m || 0).toFixed(1) + 'm</span>',
                    '<span><b>Floor:</b> ' + (phcData.floor_level_m || 0).toFixed(2) + 'm</span>',
                    '<span><b>Transmission:</b> ' + ((summary.flood_transmission_rate || 0) * 100).toFixed(1) + '%</span>'
                ].join('');
            }
"""
