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
Gauge hazard curve — Hazard Rate tab.

Tab 1 (reordered): Conditional hazard rate h(t) in bps across alert/warning/severe.
Overlays market curves (dashed) from the trading desk alongside base rates.
"""


def get_js() -> str:
    """Return JS fragment for hazard rate and exceedance tabs."""
    return """
            // ================================================================
            // Hazard Curve — conditional hazard rate h(t) in bps
            // h(t) = P(flood in year t | no flood before t) = [S(t-1) - S(t)] / S(t-1)
            // Overlays market curves (dashed) from trading desk
            // ================================================================
            var _mktHazardTS = null;
            var _hcTriggerFilter = 'all';

            function _fetchMarketHazardTS() {
                var cfg = window.__BACKEND_CONFIG || {};
                var baseUrl = cfg.url || '';
                var url = baseUrl + '/api/v1/trading/hazard-term-structure?_=' + Date.now();
                console.log('[GaugeHazard] Fetching market HTS from:', url);
                return fetch(url, {mode: 'cors', cache: 'no-store'})
                    .then(function(r) {
                        console.log('[GaugeHazard] HTS response status:', r.status);
                        return r.json();
                    })
                    .then(function(data) {
                        if (data.status === 'success') {
                            _mktHazardTS = data.hazard_term_structure || {};
                            window._mktHazardTS = _mktHazardTS;
                            console.log('[GaugeHazard] HTS loaded:', Object.keys(_mktHazardTS).length, 'gauges');
                            return _mktHazardTS;
                        }
                        console.warn('[GaugeHazard] HTS API returned non-success:', data.status, data.message);
                        return null;
                    })
                    .catch(function(err) {
                        console.error('[GaugeHazard] HTS fetch failed:', err);
                        return null;
                    });
            }

            function renderHazardRate() {
                var ctx = document.getElementById('hazard-chart').getContext('2d');
                if (currentChart) currentChart.destroy();

                var ts = hazardData.term_structures || {};
                var tsAlert = ts.alert || [];
                var tsWarning = ts.warning || [];
                var tsSevere = ts.severe || [];

                if (tsAlert.length === 0) {
                    document.getElementById('hazard-stats-bar').innerHTML =
                        '<span>No term structure data available</span>';
                    return;
                }

                var tenors = tsAlert.map(function(t) { return t.year + 'Y'; });

                function hazardRates(arr) {
                    return arr.map(function(t, i) {
                        var sPrev = i === 0 ? 1.0 : arr[i - 1].survival_prob;
                        var sCurr = t.survival_prob;
                        if (sPrev <= 0) return 0;
                        var h = (sPrev - sCurr) / sPrev;
                        return h * 10000; // convert to bps
                    });
                }

                var alertRates = hazardRates(tsAlert);
                var warningRates = hazardRates(tsWarning);
                var severeRates = hazardRates(tsSevere);

                var filter = _hcTriggerFilter;
                var triggerDefs = [
                    {key:'alert', label:'Alert', color:'#FFC107', rates: alertRates},
                    {key:'warning', label:'Warning', color:'#FF9800', rates: warningRates},
                    {key:'severe', label:'Severe', color:'#F44336', rates: severeRates}
                ];

                var datasets = [];
                triggerDefs.forEach(function(td) {
                    if (filter !== 'all' && filter !== td.key) return;
                    datasets.push({
                        label: td.label + ' (base)',
                        data: td.rates,
                        borderColor: td.color,
                        backgroundColor: td.color.replace(')', ',0.08)').replace('rgb', 'rgba').replace('#FFC107', 'rgba(255,193,7,0.08)').replace('#FF9800', 'rgba(255,152,0,0.08)').replace('#F44336', 'rgba(244,67,54,0.08)'),
                        fill: true, tension: 0, pointRadius: 4,
                        pointBackgroundColor: td.color, borderWidth: 2
                    });
                });

                // Fix backgroundColor for hex colors
                datasets.forEach(function(ds) {
                    if (ds.borderColor === '#FFC107') ds.backgroundColor = 'rgba(255,193,7,0.08)';
                    else if (ds.borderColor === '#FF9800') ds.backgroundColor = 'rgba(255,152,0,0.08)';
                    else if (ds.borderColor === '#F44336') ds.backgroundColor = 'rgba(244,67,54,0.08)';
                });

                // Overlay market curves if available
                var gaugeId = hazardData.gauge_id || '';
                if (_mktHazardTS && _mktHazardTS[gaugeId]) {
                    var gts = _mktHazardTS[gaugeId];
                    triggerDefs.forEach(function(td) {
                        if (filter !== 'all' && filter !== td.key) return;
                        var mktRates = gts[td.key] || {};
                        var mktData = tsAlert.map(function(t) {
                            var r = mktRates[String(t.year)];
                            return r != null ? r * 10000 : null;
                        });
                        if (mktData.some(function(v) { return v != null; })) {
                            datasets.push({
                                label: td.label + ' (market)',
                                data: mktData,
                                borderColor: td.color,
                                borderDash: [6, 3],
                                backgroundColor: 'transparent',
                                fill: false, tension: 0, pointRadius: 3,
                                pointBackgroundColor: td.color, borderWidth: 2,
                                pointStyle: 'rectRot'
                            });
                        }
                    });
                }

                currentChart = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: tenors,
                        datasets: datasets
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        interaction: { intersect: false, mode: 'index' },
                        plugins: {
                            legend: {
                                position: 'top',
                                labels: { usePointStyle: true, boxWidth: 8, font: { size: 10 } }
                            },
                            tooltip: {
                                callbacks: {
                                    title: function(items) {
                                        return items[0].label;
                                    },
                                    label: function(ctx) {
                                        var bps = ctx.parsed.y;
                                        var pct = (bps / 100).toFixed(2);
                                        return ctx.dataset.label + ': ' + bps.toFixed(1) + ' bps (' + pct + '%)';
                                    }
                                }
                            }
                        },
                        scales: {
                            x: { title: { display: true, text: 'Tenor' } },
                            y: { title: { display: true, text: 'Hazard Rate (bps)' } }
                        }
                    }
                });

                // Stats bar with trigger dropdown
                var bar = document.getElementById('hazard-stats-bar');
                var selHtml = '<select id="hc-trigger-select" onchange="window._hcTriggerChanged(this.value)" ' +
                    'style="padding:2px 6px;font-size:10px;border:1px solid #ccc;border-radius:3px;background:white;margin-right:8px;">' +
                    '<option value="all"' + (filter === 'all' ? ' selected' : '') + '>All Triggers</option>' +
                    '<option value="alert"' + (filter === 'alert' ? ' selected' : '') + '>Alert</option>' +
                    '<option value="warning"' + (filter === 'warning' ? ' selected' : '') + '>Warning</option>' +
                    '<option value="severe"' + (filter === 'severe' ? ' selected' : '') + '>Severe</option>' +
                    '</select>';

                var statsItems = [];
                triggerDefs.forEach(function(td) {
                    if (filter !== 'all' && filter !== td.key) return;
                    var r1 = td.rates[0] ? td.rates[0].toFixed(1) : '0';
                    var rLast = td.rates.length > 0 ? td.rates[td.rates.length - 1].toFixed(1) : '0';
                    statsItems.push('<span style="color:' + td.color + ';"><b>' + td.label + ' 1Y:</b> ' + r1 + ' bps</span>');
                    statsItems.push('<span style="color:' + td.color + ';"><b>5Y:</b> ' + rLast + ' bps</span>');
                });
                statsItems.push('<span style="color:#666;"><i>1 bp = 0.01%</i></span>');

                bar.innerHTML = selHtml + statsItems.join('');
            }

            window._hcTriggerChanged = function(val) {
                _hcTriggerFilter = val;
                renderHazardRate();
            }
"""
