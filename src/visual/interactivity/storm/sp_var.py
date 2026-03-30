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
Storm portfolio — VaR tab sub-module.

Property Damage / Mortgage Impairment distribution histogram with
VaR and Expected Shortfall annotations at 95% and 99.9% confidence.
"""


def get_js() -> str:
    """Return JS fragment for VaR tab (injected into parent IIFE)."""
    return """
            // ================================================================
            // VaR tab — state
            // ================================================================
            var spVarData = null;
            var spVarChart = null;
            var spVarMode = 'property';

            // ================================================================
            // VaR tab — DOM creation
            // ================================================================
            function createVarView() {
                var view = document.createElement('div');
                view.id = 'sp-var-view';
                view.style.cssText = 'display:none;flex-direction:column;flex:1;overflow:hidden;';

                var toggleRow = document.createElement('div');
                toggleRow.style.cssText = 'padding:8px 16px;border-bottom:1px solid #eee;display:flex;align-items:center;gap:12px;background:#fafafa;';
                var toggleLabel = document.createElement('span');
                toggleLabel.textContent = 'Distribution:';
                toggleLabel.style.cssText = 'font-size:12px;font-weight:600;color:#555;';
                var toggleWrap = document.createElement('div');
                toggleWrap.style.cssText = 'display:flex;border:1px solid #ddd;border-radius:4px;overflow:hidden;';
                var propBtn = document.createElement('button');
                propBtn.id = 'sp-var-prop-btn';
                propBtn.textContent = 'Property Damage';
                propBtn.style.cssText = 'padding:4px 14px;font-size:11px;border:none;cursor:pointer;background:#1976d2;color:white;';
                propBtn.onclick = function() { switchVarMode('property'); };
                var mortBtn = document.createElement('button');
                mortBtn.id = 'sp-var-mort-btn';
                mortBtn.textContent = 'Mortgage Impairment';
                mortBtn.style.cssText = 'padding:4px 14px;font-size:11px;border:none;cursor:pointer;background:white;color:#333;';
                mortBtn.onclick = function() { switchVarMode('mortgage'); };
                toggleWrap.appendChild(propBtn);
                toggleWrap.appendChild(mortBtn);
                toggleRow.appendChild(toggleLabel);
                toggleRow.appendChild(toggleWrap);

                var chartWrap = document.createElement('div');
                chartWrap.id = 'sp-var-chart-wrap';
                chartWrap.style.cssText = 'flex:1;padding:12px 16px;position:relative;';

                var metrics = document.createElement('div');
                metrics.id = 'sp-var-metrics';
                metrics.style.cssText = 'padding:10px 16px;border-top:1px solid #eee;display:flex;gap:10px;flex-wrap:wrap;';

                view.appendChild(toggleRow);
                view.appendChild(chartWrap);
                view.appendChild(metrics);
                return view;
            }

            // ================================================================
            // VaR mode switching
            // ================================================================
            function switchVarMode(mode) {
                spVarMode = mode;
                var propBtn = document.getElementById('sp-var-prop-btn');
                var mortBtn = document.getElementById('sp-var-mort-btn');
                if (mode === 'property') {
                    propBtn.style.background = '#1976d2';
                    propBtn.style.color = 'white';
                    mortBtn.style.background = 'white';
                    mortBtn.style.color = '#333';
                } else {
                    mortBtn.style.background = '#7b1fa2';
                    mortBtn.style.color = 'white';
                    propBtn.style.background = 'white';
                    propBtn.style.color = '#333';
                }
                if (spVarData) {
                    renderVarChart(spVarData, mode);
                    renderVarMetrics(spVarData, mode);
                }
            }

            // ================================================================
            // VaR chart rendering
            // ================================================================
            function renderVarChart(data, mode) {
                if (!mode) mode = spVarMode;
                var wrap = document.getElementById('sp-var-chart-wrap');
                wrap.innerHTML = '<canvas id="sp-var-canvas"></canvas>';

                if (spVarChart) {
                    spVarChart.destroy();
                    spVarChart = null;
                }

                var isProp = mode === 'property';
                var bins = isProp ? data.prop_histogram : data.mort_histogram;
                var pd = isProp ? data.property_damage : data.mortgage_impairment;
                var chartColor = isProp ? 'rgba(25,118,210' : 'rgba(123,31,162';
                var lineColor = isProp ? '#1976d2' : '#7b1fa2';
                var distLabel = isProp ? 'Property Damage' : 'Mortgage Impairment';
                var labels = [];
                var propCounts = [];
                bins.forEach(function(b) {
                    if (b.count === 0) return;
                    var mid = (b.lo + b.hi) / 2;
                    labels.push(mid);
                    propCounts.push(b.count);
                });

                var ctx = document.getElementById('sp-var-canvas').getContext('2d');
                spVarChart = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: labels,
                        datasets: [{
                            label: distLabel,
                            data: propCounts,
                            backgroundColor: labels.map(function(v) {
                                if (v >= pd.cond_var_999) return 'rgba(211,47,47,0.7)';
                                if (v >= pd.cond_var_95) return 'rgba(245,124,0,0.6)';
                                return chartColor + ',0.5)';
                            }),
                            borderColor: labels.map(function(v) {
                                if (v >= pd.cond_var_999) return '#d32f2f';
                                if (v >= pd.cond_var_95) return '#f57c00';
                                return lineColor;
                            }),
                            borderWidth: 1,
                            barPercentage: 1.0,
                            categoryPercentage: 1.0,
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        interaction: {
                            mode: 'index',
                            intersect: false,
                        },
                        plugins: {
                            legend: { display: false },
                            title: {
                                display: true,
                                text: distLabel + ' Distribution (' + data.storm_count.toLocaleString() + ' storms, ' + data.storms_with_damage + ' with damage)',
                                font: { size: 13, weight: 'bold' },
                                color: '#333',
                            },
                            tooltip: {
                                callbacks: {
                                    title: function(items) {
                                        var b = bins[items[0].dataIndex];
                                        return fmtGBP(b.lo) + ' \u2013 ' + fmtGBP(b.hi);
                                    },
                                    label: function(item) {
                                        return item.parsed.y + ' storms';
                                    }
                                }
                            },
                            annotation: {
                                annotations: {
                                    var95Line: {
                                        type: 'line',
                                        xMin: pd.cond_var_95,
                                        xMax: pd.cond_var_95,
                                        borderColor: '#f57c00',
                                        borderWidth: 2,
                                        borderDash: [6, 4],
                                        label: {
                                            display: true,
                                            content: 'VaR 95%: ' + fmtGBP(pd.cond_var_95),
                                            position: 'start',
                                            backgroundColor: 'rgba(245,124,0,0.9)',
                                            color: 'white',
                                            font: { size: 10, weight: 'bold' },
                                            padding: 4,
                                        }
                                    },
                                    var999Line: {
                                        type: 'line',
                                        xMin: pd.cond_var_999,
                                        xMax: pd.cond_var_999,
                                        borderColor: '#d32f2f',
                                        borderWidth: 2,
                                        borderDash: [6, 4],
                                        label: {
                                            display: true,
                                            content: 'VaR 99.9%: ' + fmtGBP(pd.cond_var_999),
                                            position: 'start',
                                            backgroundColor: 'rgba(211,47,47,0.9)',
                                            color: 'white',
                                            font: { size: 10, weight: 'bold' },
                                            padding: 4,
                                            yAdjust: 20,
                                        }
                                    }
                                }
                            }
                        },
                        scales: {
                            x: {
                                type: 'linear',
                                title: {
                                    display: true,
                                    text: distLabel + ' (\u00a3)',
                                    font: { size: 11 },
                                },
                                ticks: {
                                    callback: function(v) {
                                        if (v >= 1000000) return '\u00a3' + (v / 1000000).toFixed(1) + 'M';
                                        if (v >= 1000) return '\u00a3' + (v / 1000).toFixed(0) + 'K';
                                        return '\u00a3' + v;
                                    },
                                    font: { size: 10 },
                                },
                                min: 0,
                            },
                            y: {
                                title: {
                                    display: true,
                                    text: 'Number of Storms',
                                    font: { size: 11 },
                                },
                                beginAtZero: true,
                                ticks: { font: { size: 10 } },
                            }
                        }
                    }
                });
            }

            function renderVarMetrics(data, mode) {
                if (!mode) mode = spVarMode;
                var metrics = document.getElementById('sp-var-metrics');
                var isProp = mode === 'property';
                var d = isProp ? data.property_damage : data.mortgage_impairment;
                var labelColor = isProp ? '#1976d2' : '#7b1fa2';
                var label = isProp ? 'Property Damage' : 'Mortgage Impairment';
                metrics.innerHTML = '';

                var probRow = document.createElement('div');
                probRow.style.cssText = 'width:100%;padding:6px 10px;margin-bottom:6px;font-size:11px;color:#555;background:#f0f4f8;border-radius:4px;';
                probRow.innerHTML = 'P(loss) = <b>' + data.prob_loss_pct.toFixed(2) + '%</b> (' + data.storms_with_damage + ' of ' + data.storm_count.toLocaleString() + ' storms)' +
                    ' &mdash; Conditional metrics below given a damaging storm occurs';
                metrics.appendChild(probRow);

                var row = document.createElement('div');
                row.style.cssText = 'display:flex;gap:8px;width:100%;';
                var lbl = document.createElement('div');
                lbl.style.cssText = 'min-width:130px;padding:8px 10px;font-size:11px;font-weight:700;color:' + labelColor + ';display:flex;align-items:center;';
                lbl.textContent = label;
                row.appendChild(lbl);
                [
                    { label: 'Cond. Mean', value: fmtGBP(d.cond_mean), color: labelColor },
                    { label: 'VaR 95%', value: fmtGBP(d.cond_var_95), color: '#f57c00' },
                    { label: 'VaR 99.9%', value: fmtGBP(d.cond_var_999), color: '#d32f2f' },
                    { label: 'ES 95%', value: fmtGBP(d.cond_es_95), color: '#f57c00' },
                    { label: 'ES 99.9%', value: fmtGBP(d.cond_es_999), color: '#d32f2f' },
                    { label: 'Max', value: fmtGBP(d.max), color: '#7b1fa2' },
                ].forEach(function(c) {
                    var card = document.createElement('div');
                    card.style.cssText = 'flex:1;padding:8px 10px;border-radius:5px;background:#f5f5f5;border-left:3px solid ' + c.color + ';';
                    card.innerHTML = '<div style="font-size:9px;color:#888;text-transform:uppercase;">' + c.label + '</div>' +
                        '<div style="font-size:14px;font-weight:700;color:' + c.color + ';">' + c.value + '</div>';
                    card.appendChild(document.createElement('div'));
                    row.appendChild(card);
                });
                metrics.appendChild(row);
            }

            // ================================================================
            // VaR data loading
            // ================================================================
            function loadVarData() {
                console.log('[StormPortfolio] Fetching VaR distribution');
                var statsBar = document.getElementById('sp-stats-bar');
                statsBar.innerHTML = '<span>Loading VaR distribution...</span>';
                var wrap = document.getElementById('sp-var-chart-wrap');
                wrap.innerHTML = '<div style="padding:40px;text-align:center;color:#888;">Loading VaR data...</div>';
                var metrics = document.getElementById('sp-var-metrics');
                metrics.innerHTML = '';

                var baseUrl = getBaseUrl();
                fetch(baseUrl + '/api/v1/propertyts/portfolio-var', {mode: 'cors'})
                    .then(function(r) { return r.json(); })
                    .then(function(data) {
                        if (data.status !== 'success') {
                            wrap.innerHTML = '<div style="padding:40px;text-align:center;color:red;">Error: ' + (data.message || 'Unknown') + '</div>';
                            return;
                        }
                        spVarData = data;
                        console.log('[StormPortfolio] VaR loaded:', data.storm_count, 'storms,', data.storms_with_damage, 'with damage');
                        document.getElementById('sp-panel-title').textContent =
                            'Portfolio VaR \u2014 Loss Distribution';

                        renderVarChart(data, spVarMode);
                        renderVarMetrics(data, spVarMode);

                        statsBar.innerHTML =
                            '<span>Scenarios: <b>' + data.storm_count.toLocaleString() + '</b> storms</span>' +
                            '<span>Damaging: <b>' + data.storms_with_damage + '</b></span>' +
                            '<span>Portfolio value: <b>' + fmtGBP(data.total_portfolio_value) + '</b></span>' +
                            '<span>Portfolio mortgages: <b>' + fmtGBP(data.total_portfolio_mortgages) + '</b></span>';
                    })
                    .catch(function(err) {
                        wrap.innerHTML = '<div style="padding:40px;text-align:center;color:red;">Failed to load VaR data</div>';
                        console.error('VaR error:', err);
                    });
            }
"""
