// Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
//
// This software is licensed by MKM Research Labs for non-commercial 
// research and educational use only. Any commercial use, including 
// but not limited to use in or for products or services offered for sale, 
// internal business operations intended for commercial advantage, or
// research and development conducted for a commercial entity, is expressly
// prohibited unless separately authorized in writing by MKM Research Labs.
//
// Use, reproduction, distribution, or modification of this code is subject to the
// terms and conditions of the license agreement provided with this software.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
// SOFTWARE.

            // ==============================================================
            // Hazard Curve History Modal — 5 tenor time-series charts
            // ==============================================================
            var tdHistoryCharts = [];
            var tdHistoryTrigColors = {alert:'#f9a825', warning:'#e65100', severe:'#c62828'};
            var tdHistoryTrigBg    = {alert:'#fff8e1', warning:'#fff3e0', severe:'#ffebee'};

            window.tdShowCurveHistory = function() {
                if (tdCurveMode === 'yield' || !tdSelectedGauge) {
                    if (window.showError) window.showError('Select a hazard trigger and gauge first');
                    return;
                }

                var trigger = tdCurveMode;
                var gaugeName = (tdMarketData && tdMarketData[tdSelectedGauge])
                    ? (tdMarketData[tdSelectedGauge].gauge_name || tdSelectedGauge)
                    : tdSelectedGauge;

                // Build modal overlay
                var overlay = document.createElement('div');
                overlay.id = 'td-history-overlay';
                overlay.style.cssText = 'position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.55);z-index:9000;display:flex;align-items:center;justify-content:center;';
                overlay.addEventListener('click', function(e) {
                    if (e.target === overlay) tdCloseCurveHistory();
                });

                var modal = document.createElement('div');
                modal.style.cssText = 'background:#fff;border-radius:8px;box-shadow:0 8px 32px rgba(0,0,0,0.25);width:92vw;max-width:1300px;height:82vh;display:flex;flex-direction:column;overflow:hidden;';

                // Header
                var header = document.createElement('div');
                header.style.cssText = 'display:flex;align-items:center;padding:14px 20px;border-bottom:1px solid #eee;background:#f8f9fa;flex-shrink:0;';
                var trigLabel = trigger.charAt(0).toUpperCase() + trigger.slice(1);
                header.innerHTML =
                    '<span style="font-size:14px;font-weight:700;color:#333;">Hazard Curve History</span>' +
                    '<span style="margin:0 10px;color:#aaa;">|</span>' +
                    '<span style="font-size:12px;color:#555;">' + gaugeName + '</span>' +
                    '<span style="margin:0 8px;padding:2px 8px;border-radius:10px;font-size:10px;font-weight:700;color:white;background:' + (tdHistoryTrigColors[trigger]||'#546e7a') + ';">' + trigLabel + '</span>' +
                    '<span style="flex:1;"></span>' +
                    '<button onclick="tdCloseCurveHistory()" style="padding:4px 12px;font-size:11px;background:#78909c;color:white;border:none;border-radius:3px;cursor:pointer;">Close</button>';
                modal.appendChild(header);

                // Loading state
                var body = document.createElement('div');
                body.id = 'td-history-body';
                body.style.cssText = 'flex:1;display:flex;align-items:center;justify-content:center;overflow:hidden;';
                body.innerHTML = '';
                modal.appendChild(body);

                overlay.appendChild(modal);
                document.body.appendChild(overlay);

                // Fetch history
                var url = getBaseUrl() + '/api/v1/trading/curve-history?gauge_id=' + encodeURIComponent(tdSelectedGauge) + '&trigger=' + encodeURIComponent(trigger) + '&_=' + Date.now();
                fetch(url, {mode: 'cors', cache: 'no-store'})
                    .then(function(r) { return r.json(); })
                    .then(function(result) {
                        if (result.status !== 'success' || !result.history || result.history.length === 0) {
                            body.innerHTML = '<span style="color:#c62828;font-size:13px;">No history available for this gauge/trigger</span>';
                            return;
                        }
                        tdBuildHistoryCharts(body, result.history, trigger);
                    })
                    .catch(function(err) {
                        body.innerHTML = '<span style="color:#c62828;font-size:13px;">Error loading history: ' + err.message + '</span>';
                    });
            };

            window.tdCloseCurveHistory = function() {
                // Destroy all history charts
                for (var i = 0; i < tdHistoryCharts.length; i++) {
                    try { tdHistoryCharts[i].destroy(); } catch(e) {}
                }
                tdHistoryCharts = [];
                var overlay = document.getElementById('td-history-overlay');
                if (overlay) overlay.remove();
            };

            function tdBuildHistoryCharts(container, history, trigger) {
                var tenors = ['1', '2', '3', '4', '5'];
                var dates = history.map(function(h) { return h.date; });

                // Thin dates for x-axis readability (show every Nth label)
                var step = Math.max(1, Math.floor(dates.length / 10));
                var xLabels = dates.map(function(d, i) {
                    return (i % step === 0) ? d.slice(5) : '';  // MM-DD
                });

                var lineColor = tdHistoryTrigColors[trigger] || '#546e7a';
                var fillColor = tdHistoryTrigBg[trigger] || '#eceff1';

                // Grid: row 1 = 1Y 2Y 3Y, row 2 = 4Y 5Y (centred)
                container.style.cssText = 'flex:1;display:flex;flex-direction:column;padding:16px 20px;gap:14px;overflow:hidden;';

                var row1 = document.createElement('div');
                row1.style.cssText = 'display:flex;flex:1;gap:14px;';
                var row2 = document.createElement('div');
                row2.style.cssText = 'display:flex;flex:1;gap:14px;justify-content:center;';

                container.appendChild(row1);
                container.appendChild(row2);

                tenors.forEach(function(tenor, idx) {
                    var rates = history.map(function(h) {
                        var r = (h.hazard_rates || {})[tenor];
                        return r != null ? +(r * 10000).toFixed(2) : null;
                    });

                    // Y-axis range
                    var valid = rates.filter(function(v) { return v != null; });
                    var yMin = valid.length ? Math.floor((Math.min.apply(null, valid) - 2) / 2) * 2 : 0;
                    var yMax = valid.length ? Math.ceil((Math.max.apply(null, valid) + 2) / 2) * 2 : 100;
                    if (yMin < 0) yMin = 0;

                    // Chart wrapper
                    var wrap = document.createElement('div');
                    wrap.style.cssText = 'flex:1;max-width:' + (idx < 3 ? '33%' : '40%') + ';position:relative;background:#fafafa;border-radius:6px;border:1px solid #e0e0e0;padding:8px;';
                    var canvas = document.createElement('canvas');
                    canvas.style.cssText = 'width:100%;height:100%;';
                    wrap.appendChild(canvas);
                    (idx < 3 ? row1 : row2).appendChild(wrap);

                    if (typeof Chart === 'undefined') return;

                    var chart = new Chart(canvas.getContext('2d'), {
                        type: 'line',
                        data: {
                            labels: xLabels,
                            datasets: [{
                                label: tenor + 'Y Hazard Rate',
                                data: rates,
                                borderColor: lineColor,
                                backgroundColor: fillColor,
                                borderWidth: 1.5,
                                pointRadius: 0,
                                pointHoverRadius: 4,
                                fill: true,
                                tension: 0.3,
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            animation: false,
                            plugins: {
                                title: {
                                    display: true,
                                    text: tenor + 'Y Tenor',
                                    font: {size: 11, weight: '600'},
                                    color: '#333',
                                    padding: {bottom: 4}
                                },
                                legend: {display: false},
                                tooltip: {
                                    callbacks: {
                                        title: function(items) { return dates[items[0].dataIndex] || ''; },
                                        label: function(ctx) { return (ctx.parsed.y != null ? ctx.parsed.y.toFixed(1) : '—') + ' bps'; }
                                    }
                                }
                            },
                            scales: {
                                x: {
                                    ticks: {font: {size: 8}, maxRotation: 0, autoSkip: false},
                                    grid: {display: false}
                                },
                                y: {
                                    min: yMin,
                                    max: yMax,
                                    title: {display: true, text: 'bps', font: {size: 8}},
                                    ticks: {font: {size: 8}, callback: function(v) { return v.toFixed(0); }}
                                }
                            }
                        }
                    });
                    tdHistoryCharts.push(chart);
                });
            }
