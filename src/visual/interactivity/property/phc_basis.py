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
Property hazard curve — Basis Analysis tab sub-module.

Grouped bar chart showing gauge-vs-property basis (bps) at 5yr
tenor across three flood severity thresholds.
"""


def get_js() -> str:
    """Return JS fragment for basis analysis tab (injected into parent IIFE)."""
    return """
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
                    return ng.gauge_id.substring(0, 14) + '\\n(' + ng.distance_km + 'km)';
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
"""
