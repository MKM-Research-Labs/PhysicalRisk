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

"""Gauge Storm Analysis — distribution histogram (Tab 0) with slider filter."""


def get_js():
    """Return JS fragment for distribution slider and histogram chart."""
    return """
            // ================================================================
            // Distribution slider (for focus on tail)
            // ================================================================
            function buildDistSlider() {
                var distCtrl = document.getElementById('storm-dist-controls');
                var responses = stormData.storm_responses.responses || [];
                var peaks = responses.map(function(r) { return r.peak_level_m; });
                var dataMax = Math.max.apply(null, peaks);

                distCtrl.innerHTML =
                    '<div style="display:flex;align-items:center;gap:8px;">' +
                    '<label style="font-weight:600;white-space:nowrap;">Min Level:</label>' +
                    '<span id="dist-min-label" style="min-width:30px;font-weight:600;">0m</span>' +
                    '<input id="dist-min-slider" type="range" min="0" max="' + dataMax.toFixed(2) + '" ' +
                    'value="0" step="0.1" style="flex:1;cursor:pointer;">' +
                    '<span style="min-width:50px;text-align:right;font-weight:600;">' + dataMax.toFixed(1) + 'm</span>' +
                    '</div>';

                var slider = document.getElementById('dist-min-slider');
                slider.oninput = function() {
                    document.getElementById('dist-min-label').textContent = parseFloat(this.value).toFixed(1) + 'm';
                    renderDistribution();
                };
            }

            // ================================================================
            // Tab 0: Distribution histogram
            // ================================================================
            function renderDistribution() {
                var ctx = document.getElementById('storm-chart').getContext('2d');
                if (currentChart) currentChart.destroy();

                var responses = stormData.storm_responses.responses || [];
                var fs = stormData.flood_stages || {};
                var allPeaks = responses.map(function(r) { return r.peak_level_m; });

                // Apply slider filter
                var slider = document.getElementById('dist-min-slider');
                var filterMin = slider ? parseFloat(slider.value) : -Infinity;
                var peaks = allPeaks.filter(function(p) { return p >= filterMin; });
                if (peaks.length === 0) peaks = [filterMin];

                // Compute histogram bins
                var min = Math.min.apply(null, peaks);
                var max = Math.max.apply(null, peaks);
                var nBins = 30;
                var binWidth = (max - min) / nBins;
                if (binWidth === 0) { binWidth = 1; nBins = 1; }

                var bins = new Array(nBins).fill(0);
                var labels = [];
                for (var i = 0; i < nBins; i++) {
                    var lo = min + i * binWidth;
                    labels.push(lo.toFixed(2));
                }

                peaks.forEach(function(p) {
                    var idx = Math.min(Math.floor((p - min) / binWidth), nBins - 1);
                    bins[idx]++;
                });

                // Color each bin by threshold
                var alertVal = fs.FloodAlert || Infinity;
                var warnVal = fs.FloodWarning || Infinity;
                var severeVal = fs.SevereFloodWarning || Infinity;

                var colors = labels.map(function(l) {
                    var v = parseFloat(l) + binWidth / 2;
                    if (v >= severeVal) return 'rgba(244,67,54,0.7)';
                    if (v >= warnVal) return 'rgba(255,152,0,0.7)';
                    if (v >= alertVal) return 'rgba(255,193,7,0.7)';
                    return 'rgba(76,175,80,0.7)';
                });

                var datasets = [{
                    label: 'Storm Count',
                    data: bins,
                    backgroundColor: colors,
                    borderColor: colors.map(function(c) { return c.replace('0.7', '1'); }),
                    borderWidth: 1
                }];

                // Annotation lines for thresholds
                var annotations = {};
                if (fs.FloodAlert) annotations.alert = {
                    type: 'line', scaleID: 'x',
                    value: ((fs.FloodAlert - min) / binWidth).toFixed(1),
                    borderColor: '#FFC107', borderDash: [5,5], borderWidth: 2,
                    label: { display: true, content: 'Alert', position: 'start', font: { size: 10 } }
                };
                if (fs.FloodWarning) annotations.warning = {
                    type: 'line', scaleID: 'x',
                    value: ((fs.FloodWarning - min) / binWidth).toFixed(1),
                    borderColor: '#FF9800', borderDash: [5,5], borderWidth: 2,
                    label: { display: true, content: 'Warning', position: 'start', font: { size: 10 } }
                };
                if (fs.SevereFloodWarning) annotations.severe = {
                    type: 'line', scaleID: 'x',
                    value: ((fs.SevereFloodWarning - min) / binWidth).toFixed(1),
                    borderColor: '#F44336', borderDash: [5,5], borderWidth: 2,
                    label: { display: true, content: 'Severe', position: 'start', font: { size: 10 } }
                };

                currentChart = new Chart(ctx, {
                    type: 'bar',
                    data: { labels: labels, datasets: datasets },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { display: false },
                            tooltip: {
                                callbacks: {
                                    title: function(items) {
                                        var i = items[0].dataIndex;
                                        var lo = (min + i * binWidth).toFixed(2);
                                        var hi = (min + (i+1) * binWidth).toFixed(2);
                                        return lo + 'm - ' + hi + 'm';
                                    },
                                    label: function(ctx) {
                                        return ctx.parsed.y + ' storms';
                                    }
                                }
                            }
                        },
                        scales: {
                            x: { title: { display: true, text: 'Peak Water Level (m)' }, ticks: { maxTicksLimit: 10, font: { size: 10 } } },
                            y: { title: { display: true, text: 'Number of Storms' }, beginAtZero: true, ticks: { stepSize: 1 } }
                        }
                    }
                });

                // Stats — filter responses to match slider, count thresholds from filtered set
                var filteredResponses = responses.filter(function(r) { return r.peak_level_m >= filterMin; });
                var nAlert = filteredResponses.filter(function(r) { return r.exceeded_alert; }).length;
                var nWarn = filteredResponses.filter(function(r) { return r.exceeded_warning; }).length;
                var nSevere = filteredResponses.filter(function(r) { return r.exceeded_severe; }).length;
                var mean = peaks.reduce(function(a,b) { return a+b; }, 0) / peaks.length;
                var sorted = peaks.slice().sort(function(a,b) { return a-b; });
                var median = sorted[Math.floor(sorted.length / 2)];

                var bar = document.getElementById('storm-stats-bar');
                var showing = peaks.length < allPeaks.length
                    ? '<span><b>Showing:</b> ' + peaks.length + ' / ' + allPeaks.length + '</span>'
                    : '<span><b>Storms:</b> ' + peaks.length + '</span>';
                bar.innerHTML = [
                    showing,
                    '<span><b>Mean:</b> ' + mean.toFixed(2) + 'm</span>',
                    '<span><b>Median:</b> ' + median.toFixed(2) + 'm</span>',
                    '<span><b>Max:</b> ' + max.toFixed(2) + 'm</span>',
                    '<span style="color:#FFC107;"><b>Alert:</b> ' + nAlert + ' (' + (peaks.length > 0 ? (nAlert/peaks.length*100).toFixed(1) : '0') + '%)</span>',
                    '<span style="color:#FF9800;"><b>Warning:</b> ' + nWarn + ' (' + (peaks.length > 0 ? (nWarn/peaks.length*100).toFixed(1) : '0') + '%)</span>',
                    '<span style="color:#F44336;"><b>Severe:</b> ' + nSevere + ' (' + (peaks.length > 0 ? (nSevere/peaks.length*100).toFixed(1) : '0') + '%)</span>',
                ].join('');
            }
"""
