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
Curves tab for the Trading Desk panel.

Shows all gauge hazard term structures on a single Chart.js chart:
- One line per gauge (40 lines), x-axis = tenor (1Y-5Y), y-axis = hazard rate (bps)
- Trigger selector (alert/warning/severe)
- Hover tooltip shows gauge name and rate
"""


def get_js() -> str:
    """Return JavaScript fragment for the curves tab."""
    return """
            // ==============================================================
            // Curves tab — all gauge hazard term structures
            // ==============================================================
            var tdCurveChart = null;
            var tdCurveAllData = null;

            function createCurvesView() {
                var view = document.createElement('div');
                view.id = 'td-curves-view';
                view.style.cssText = 'flex:1;display:none;flex-direction:column;overflow:hidden;';

                // Controls bar
                var controls = document.createElement('div');
                controls.style.cssText = 'display:flex;align-items:center;gap:12px;padding:8px 16px;border-bottom:1px solid #eee;background:#f8f9fa;flex-shrink:0;';

                controls.innerHTML =
                    '<span style="font-size:11px;font-weight:600;color:#555;">Trigger:</span>' +
                    '<select id="td-curve-trigger" style="padding:4px 8px;font-size:11px;border:1px solid #ccc;border-radius:4px;">' +
                    '<option value="severe">Severe</option>' +
                    '<option value="warning">Warning</option>' +
                    '<option value="alert">Alert</option>' +
                    '</select>' +
                    '<span id="td-curve-info" style="font-size:10px;color:#888;margin-left:auto;"></span>';
                view.appendChild(controls);

                // Attach event listener (IIFE-safe, no inline onchange)
                setTimeout(function() {
                    var sel = document.getElementById('td-curve-trigger');
                    if (sel) sel.addEventListener('change', function() { tdRenderAllCurves(); });
                }, 0);

                // Chart container
                var chartWrap = document.createElement('div');
                chartWrap.style.cssText = 'flex:1;padding:12px 16px;overflow:hidden;position:relative;';
                var canvas = document.createElement('canvas');
                canvas.id = 'td-curve-canvas';
                chartWrap.appendChild(canvas);
                view.appendChild(chartWrap);

                return view;
            }

            function tdLoadCurveGauges() {
                // Fetch all hazard term structures from market-state
                var url = getBaseUrl() + '/api/v1/trading/market-state';
                fetch(url, {mode: 'cors'})
                    .then(function(r) { return r.json(); })
                    .then(function(result) {
                        if (result.status !== 'success') return;
                        tdCurveAllData = {
                            gauges: result.gauges || {},
                            hazard_ts: (result.market_state || {}).hazard_term_structure || {}
                        };
                        tdRenderAllCurves();
                    })
                    .catch(function(err) {
                        console.error('[Curves] Fetch error:', err);
                    });
            }

            function tdRenderAllCurves() {
                if (!tdCurveAllData) return;

                if (tdCurveChart) {
                    tdCurveChart.destroy();
                    tdCurveChart = null;
                }

                if (typeof Chart === 'undefined') {
                    console.error('[Curves] Chart.js not loaded');
                    return;
                }

                var canvas = document.getElementById('td-curve-canvas');
                if (!canvas) return;

                // Recreate canvas to avoid stale context
                var parent = canvas.parentNode;
                parent.innerHTML = '';
                canvas = document.createElement('canvas');
                canvas.id = 'td-curve-canvas';
                parent.appendChild(canvas);

                var triggerSel = document.getElementById('td-curve-trigger');
                var trigger = triggerSel ? triggerSel.value : 'severe';
                var info = document.getElementById('td-curve-info');

                var gauges = tdCurveAllData.gauges;
                var hazardTS = tdCurveAllData.hazard_ts;
                var gaugeIds = Object.keys(gauges).sort(function(a, b) {
                    var na = (gauges[a].gauge_name || a).toLowerCase();
                    var nb = (gauges[b].gauge_name || b).toLowerCase();
                    return na < nb ? -1 : na > nb ? 1 : 0;
                });

                var tenorLabels = ['1Y', '2Y', '3Y', '4Y', '5Y'];
                var tenorKeys = ['1', '2', '3', '4', '5'];

                // Generate distinct colours using HSL
                var datasets = [];
                var n = gaugeIds.length;
                for (var i = 0; i < n; i++) {
                    var gid = gaugeIds[i];
                    var ts = (hazardTS[gid] && hazardTS[gid][trigger]) || {};
                    var rates = [];
                    for (var ti = 0; ti < tenorKeys.length; ti++) {
                        var r = ts[tenorKeys[ti]];
                        rates.push(r != null ? r * 10000 : null);
                    }

                    // HSL colour — spread hues evenly
                    var hue = Math.round((i / n) * 360);
                    var sat = 65 + (i % 3) * 10;
                    var light = 40 + (i % 4) * 5;
                    var color = 'hsl(' + hue + ',' + sat + '%,' + light + '%)';

                    var isAdjusted = gauges[gid].is_adjusted;
                    var gaugeName = gauges[gid].gauge_name || gid;
                    // Strip 'Thames ' prefix for legend brevity
                    var shortName = gaugeName.replace(/^Thames\\s+/i, '');

                    datasets.push({
                        label: shortName,
                        data: rates,
                        borderColor: color,
                        backgroundColor: color,
                        borderWidth: isAdjusted ? 2.5 : 1.2,
                        pointRadius: isAdjusted ? 4 : 2,
                        pointHitRadius: 8,
                        tension: 0.3,
                        fill: false,
                        borderDash: isAdjusted ? [] : [3, 2],
                    });
                }

                if (info) info.textContent = n + ' gauges | ' + trigger.charAt(0).toUpperCase() + trigger.slice(1) + ' trigger';

                // Compute dynamic y-axis bounds from all data points
                var allMin = Infinity;
                var allMax = -Infinity;
                for (var di = 0; di < datasets.length; di++) {
                    var dd = datasets[di].data;
                    for (var dj = 0; dj < dd.length; dj++) {
                        if (dd[dj] != null) {
                            if (dd[dj] < allMin) allMin = dd[dj];
                            if (dd[dj] > allMax) allMax = dd[dj];
                        }
                    }
                }
                if (!isFinite(allMin)) allMin = 0;
                if (!isFinite(allMax)) allMax = 100;
                var range = allMax - allMin;
                var pad = Math.max(range * 0.15, 5);
                var yMin = Math.max(0, Math.floor((allMin - pad) / 5) * 5);
                var yMax = Math.ceil((allMax + pad) / 5) * 5;

                tdCurveChart = new Chart(canvas.getContext('2d'), {
                    type: 'line',
                    data: {
                        labels: tenorLabels,
                        datasets: datasets,
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        interaction: {
                            mode: 'index',
                            intersect: false,
                        },
                        plugins: {
                            title: {
                                display: true,
                                text: 'Hazard Term Structures \\u2014 ' + trigger.charAt(0).toUpperCase() + trigger.slice(1),
                                font: {size: 13, weight: 'bold'},
                                color: '#333',
                            },
                            legend: {
                                display: true,
                                position: 'right',
                                labels: {
                                    font: {size: 9},
                                    boxWidth: 12,
                                    padding: 4,
                                    usePointStyle: true,
                                },
                            },
                            tooltip: {
                                callbacks: {
                                    label: function(ctx) {
                                        return ctx.dataset.label + ': ' + (ctx.parsed.y != null ? ctx.parsed.y.toFixed(1) + ' bps' : '\\u2014');
                                    }
                                }
                            },
                        },
                        scales: {
                            x: {
                                title: {
                                    display: true,
                                    text: 'Tenor',
                                    font: {size: 10},
                                },
                                grid: {display: false},
                            },
                            y: {
                                min: yMin,
                                max: yMax,
                                title: {
                                    display: true,
                                    text: 'Hazard Rate (bps)',
                                    font: {size: 10},
                                },
                                ticks: {font: {size: 9}},
                            },
                        },
                    },
                });
            }

            function tdCleanupCurveCharts() {
                if (tdCurveChart) {
                    tdCurveChart.destroy();
                    tdCurveChart = null;
                }
            }
"""
