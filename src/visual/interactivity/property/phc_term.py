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

Survival probability curve from Monte Carlo event count.
S(t) = (1 - p)^t where p = flood_count / num_storms.
"""


def get_js() -> str:
    """Return JS fragment for term structure tab (injected into parent IIFE)."""
    return """
            // ================================================================
            // Tab 1: Term Structure — Survival from Event Count
            // ================================================================
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
                        borderColor: '#1976D2',
                        backgroundColor: '#1976D222',
                        fill: true, tension: 0.3, pointRadius: 5,
                        pointBackgroundColor: '#1976D2', borderWidth: 2,
                        yAxisID: 'y'
                    },
                    {
                        label: 'Severe Spread (bp)',
                        data: spreadLine,
                        borderColor: '#F44336',
                        borderDash: [6, 3],
                        borderWidth: 2,
                        pointRadius: 3,
                        pointBackgroundColor: '#F44336',
                        fill: false,
                        yAxisID: 'y1'
                    }
                ];

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

                bar.innerHTML = [
                    '<span style="color:#1976D2;font-weight:bold;">Event Count</span>',
                    '<span><b>Zone:</b> ' + zone + '</span>',
                    '<span><b>Floods:</b> ' + phcData.flood_count + '</span>',
                    '<span><b>Spread:</b> <span style="color:#F44336;">' + spreadBps.toFixed(1) + ' bp</span></span>',
                    '<span><b>P(annual):</b> ' + (annualProb * 100).toFixed(3) + '%</span>',
                    '<span><b>S(5yr):</b> ' + survivalPct[survivalPct.length - 1].toFixed(2) + '%</span>',
                    '<span><b>Max Depth:</b> ' + (summary.max_depth_m || 0).toFixed(2) + 'm</span>',
                    '<span><b>Transmission:</b> ' + ((summary.flood_transmission_rate || 0) * 100).toFixed(1) + '%</span>'
                ].join('');
            }
"""
