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
Property hazard curve — Hazard Curve tab sub-module.

Exceedance probability vs flood depth chart with GEV curve
and threshold annotations, plus floor pricing fallback display.
"""


def get_js() -> str:
    """Return JS fragment for hazard curve tab (injected into parent IIFE)."""
    return """
            // ================================================================
            // Tab 0: Hazard Curve (Exceedance Prob vs Flood Depth)
            // ================================================================
            function renderHazardCurve() {
                var ctx = document.getElementById('phc-chart').getContext('2d');
                if (currentChart) currentChart.destroy();

                var hasGev = phcData.has_gev;
                var thresholds = phcData.depth_thresholds || {};
                var pricingMethod = phcData.pricing_method || 'gev';
                var minSpread = phcData.min_spread_bps || 2.0;
                var bar = document.getElementById('phc-stats-bar');

                if (!hasGev) {
                    // Floor-priced property: no GEV curve to show
                    var container = document.getElementById('phc-chart-container');
                    container.innerHTML =
                        '<div style="text-align:center;padding:40px 20px;color:#555;">' +
                        '<p style="font-size:18px;font-weight:600;color:#FF9800;margin-bottom:12px;">Floor Priced (' + minSpread.toFixed(0) + 'bp)</p>' +
                        '<p style="font-size:13px;margin-bottom:16px;">This property has ' + phcData.flood_count +
                        ' flood event(s) \\u2014 insufficient for GEV curve fitting (requires \\u2265 3).</p>' +
                        '<p style="font-size:13px;margin-bottom:8px;">All thresholds priced at the FloodRE minimum floor of <b>' +
                        minSpread.toFixed(1) + ' bps</b>.</p>' +
                        '<p style="font-size:12px;color:#888;margin-top:24px;">The PRS Pricing and Basis Analysis tabs are fully functional with floor pricing.</p>' +
                        '</div>';

                    bar.innerHTML = [
                        '<span style="color:#FF9800;font-weight:bold;">Floor Priced (' + minSpread.toFixed(0) + 'bp)</span>',
                        '<span><b>Floods:</b> ' + phcData.flood_count + '</span>',
                        '<span style="color:#4CAF50;"><b>P(>0m):</b> ' + ((thresholds.any_flood || {}).annual_probability * 100 || 0).toFixed(4) + '%/yr</span>',
                        '<span style="color:#FF9800;"><b>P(>0.5m):</b> ' + ((thresholds.moderate || {}).annual_probability * 100 || 0).toFixed(4) + '%/yr</span>',
                        '<span style="color:#F44336;"><b>P(>1.0m):</b> ' + ((thresholds.severe || {}).annual_probability * 100 || 0).toFixed(4) + '%/yr</span>'
                    ].join('');
                    return;
                }

                var gev = phcData.gev_params || {};
                var shape = gev.shape || 0;
                var loc = gev.loc || 0;
                var scale = gev.scale || 0.01;

                var depths = [];
                var probs = [];
                for (var d = 0; d <= 5.0; d += 0.1) {
                    depths.push(d.toFixed(1));
                    var p = gevExceedance(d, shape, loc, scale);
                    probs.push(Math.max(0, Math.min(100, p * 100)));
                }

                var datasets = [{
                    label: 'Property Exceedance Probability (%)',
                    data: probs,
                    borderColor: '#2196F3',
                    backgroundColor: 'rgba(33,150,243,0.1)',
                    fill: true, tension: 0.3, pointRadius: 0, borderWidth: 2
                }];

                var thresholdColors = {'any_flood': '#4CAF50', 'moderate': '#FF9800', 'severe': '#F44336'};
                var thresholdNames = {'any_flood': 'Any (0m)', 'moderate': 'Moderate (0.5m)', 'severe': 'Severe (1.0m)'};

                Object.keys(thresholds).forEach(function(key) {
                    var t = thresholds[key];
                    var color = thresholdColors[key] || '#999';
                    var n = depths.length;
                    datasets.push({
                        label: thresholdNames[key] || key,
                        data: Array(n).fill(t.annual_probability * 100),
                        borderColor: color, borderDash: [5,5], borderWidth: 2,
                        pointRadius: 0, fill: false
                    });
                });

                currentChart = new Chart(ctx, {
                    type: 'line',
                    data: { labels: depths, datasets: datasets },
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
                                    title: function(items) { return items[0].label + 'm depth'; },
                                    label: function(ctx) {
                                        return ctx.dataset.label + ': ' + ctx.parsed.y.toFixed(3) + '%';
                                    }
                                }
                            }
                        },
                        scales: {
                            x: {
                                title: { display: true, text: 'Flood Depth (m)' },
                                ticks: { maxTicksLimit: 15, font: { size: 10 } }
                            },
                            y: {
                                title: { display: true, text: 'Annual Exceedance Probability (%)' },
                                min: 0
                            }
                        }
                    }
                });

                bar.innerHTML = [
                    '<span style="color:#1976D2;font-weight:bold;">GEV Fitted</span>',
                    '<span><b>GEV \\u03BC:</b> ' + loc.toFixed(4) + '</span>',
                    '<span><b>GEV \\u03C3:</b> ' + scale.toFixed(4) + '</span>',
                    '<span><b>GEV \\u03BE:</b> ' + shape.toFixed(4) + '</span>',
                    '<span style="color:#4CAF50;"><b>P(>0m):</b> ' + ((thresholds.any_flood || {}).annual_probability * 100 || 0).toFixed(2) + '%/yr</span>',
                    '<span style="color:#FF9800;"><b>P(>0.5m):</b> ' + ((thresholds.moderate || {}).annual_probability * 100 || 0).toFixed(2) + '%/yr</span>',
                    '<span style="color:#F44336;"><b>P(>1.0m):</b> ' + ((thresholds.severe || {}).annual_probability * 100 || 0).toFixed(2) + '%/yr</span>'
                ].join('');
            }

            // GEV exceedance probability
            function gevExceedance(x, shape, loc, scale) {
                if (scale <= 0) return 0;
                var z = (x - loc) / scale;
                var cdf;
                if (Math.abs(shape) < 1e-10) {
                    cdf = Math.exp(-Math.exp(-z));
                } else {
                    var t = 1 + shape * z;
                    if (t <= 0) return shape > 0 ? 0 : 1;
                    cdf = Math.exp(-Math.pow(t, -1/shape));
                }
                return 1 - cdf;
            }
"""
