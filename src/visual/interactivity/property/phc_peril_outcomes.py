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
Basis Explorer — Peril Outcomes fan (Stage 7).

The basis waterfall (Gauge -> SHE -> SHD -> Property -> BRI) carries the
FLOOD spread to the property/BRI node. At that node the spread fans out into
the four PRS peril outcomes (coupling_spec.md Stage 6/7):

    Flood only       — severe flood triggers (the flood spine itself)
    Wind only        — binary is_prs_wind damage-onset triggers
    Flood OR Wind     — union over the 1:1-paired event set (the headline PRS)
    Flood AND Wind    — intersection (both perils on one event)

The four obey inclusion-exclusion: union = flood + wind - joint. Wind has no
gauge propagation — it is a pure intersect/union at the property node — so the
fan lives at the OUTPUT end of the waterfall, not along the geographic spine.

The peril data is ``spread_decomposition.peril_outcomes`` (preferred; the
BRI-adjusted node when present) with a fallback to the top-level ``prs_perils``.
Absent for flood-only catchments (no typhoon stage) — the renderer then draws
nothing and the caller keeps the flood-only layout (byte-identical).
"""


def get_js() -> str:
    """Return JS fragment for the peril-outcomes fan renderer."""
    return """
            // ================================================================
            // Basis Explorer — Peril Outcomes fan (Stage 7)
            // ================================================================
            var _perilOutcomesChart = null;

            // Peril data for the active property, or null for flood-only
            // catchments (no typhoon stage). Prefer the decomposition mirror
            // (BRI-adjusted node) and fall back to the top-level prs_perils.
            function _perilOutcomesData() {
                var sd = phcData.spread_decomposition || {};
                return sd.peril_outcomes || phcData.prs_perils || null;
            }

            function _renderPerilOutcomes(canvasId) {
                if (_perilOutcomesChart) { _perilOutcomesChart.destroy(); _perilOutcomesChart = null; }

                var perils = _perilOutcomesData();
                if (!perils) return false;  // flood-only fallback: nothing to draw

                var order = ['flood_only', 'wind_only', 'flood_or_wind', 'flood_and_wind'];
                var labels = ['Flood only', 'Wind only', 'Flood \\u222A Wind', 'Flood \\u2229 Wind'];
                var colors = ['#42A5F5', '#26A69A', '#7E57C2', '#5E35B1'];

                var spreads = order.map(function(k) {
                    return (perils[k] && perils[k].spread_bps) || 0;
                });
                var counts = order.map(function(k) {
                    return (perils[k] && perils[k].count) || 0;
                });

                var ctx = document.getElementById(canvasId).getContext('2d');
                _perilOutcomesChart = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: labels,
                        datasets: [{
                            label: 'Spread (bps)',
                            data: spreads,
                            backgroundColor: colors,
                            borderColor: colors,
                            borderWidth: 1,
                            barPercentage: 0.7,
                            categoryPercentage: 0.8,
                        }]
                    },
                    options: {
                        indexAxis: 'y',
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { display: false },
                            title: {
                                display: true,
                                text: 'Peril outcomes (property node)',
                                font: { size: 11, weight: 'bold' },
                                color: '#444',
                            },
                            tooltip: {
                                callbacks: {
                                    label: function(c) {
                                        return [c.raw.toFixed(1) + ' bps',
                                                counts[c.dataIndex] + ' events'];
                                    }
                                }
                            }
                        },
                        layout: { padding: { right: 60 } },
                        scales: {
                            x: {
                                beginAtZero: true,
                                suggestedMax: Math.max.apply(null, spreads) * 1.15 || 1,
                                title: { display: true, text: 'Spread (bps)', font: { size: 10 } },
                                grid: { color: '#f0f0f0' },
                            },
                            y: { grid: { display: false }, ticks: { font: { size: 10 } } }
                        },
                        animation: {
                            onComplete: function() {
                                var chart = _perilOutcomesChart;
                                if (!chart) return;
                                var cCtx = chart.ctx;
                                cCtx.font = '10px Arial';
                                cCtx.textBaseline = 'middle';
                                cCtx.textAlign = 'left';
                                chart.data.datasets[0].data.forEach(function(val, i) {
                                    var bar = chart.getDatasetMeta(0).data[i];
                                    cCtx.fillStyle = colors[i];
                                    cCtx.fillText(val.toFixed(1) + ' bps', bar.x + 6, bar.y);
                                });
                            }
                        }
                    }
                });
                return true;
            }
"""
