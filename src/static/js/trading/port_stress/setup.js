// Copyright (c) 2022-2026 MKM Research Labs.
//
// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files (the "Software"), to deal
// in the Software without restriction, including without limitation the rights
// to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
// copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions:
//
// The above copyright notice and this permission notice shall be included in all
// copies or substantial portions of the Software.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
// SOFTWARE.

            var psResult = null;
            var psActiveSubTab = 'pflood';
            var psSelectedGaugeId = null;
            var psPortPnlChart = null;
            var psPFloodChart = null;

            function createPortStressView() {
                var view = document.createElement('div');
                view.id = 'td-portstress-view';
                view.style.cssText = 'flex:1;display:none;flex-direction:column;overflow:hidden;';

                // Storm selector bar
                var stormBar = document.createElement('div');
                stormBar.id = 'ps-storm-bar';
                stormBar.style.cssText = 'padding:var(--space-4) var(--space-8);border-bottom:1px solid var(--line-soft);display:flex;align-items:center;gap:var(--space-6);background:var(--header-from);flex-shrink:0;';
                stormBar.innerHTML =
                    '<span style="font-size:var(--size-xs);font-weight:600;color:var(--text);">Storm:</span>' +
                    '<select id="ps-storm-sel" style="padding:var(--space-2) var(--space-4);font-size:var(--size-xs);border:1px solid var(--divider);border-radius:var(--radius-sm);min-width:380px;">' +
                    '<option value="">Loading storms…</option>' +
                    '</select>' +
                    '__PCT_HTML__' +
                    '<span id="ps-storm-info" style="flex:1;font-size:var(--size-xxs);color:var(--text-3);"></span>';
                view.appendChild(stormBar);

                // Sub-tab bar
                var subTabBar = document.createElement('div');
                subTabBar.style.cssText = 'display:flex;gap:0;border-bottom:1px solid var(--line-strong);background:var(--wash);flex-shrink:0;';

                var subTabs = [
                    {id: 'pflood',     label: 'P(flood)'},
                    {id: 'portpnl',    label: 'Port P&L'},
                    {id: 'gaugepnl',   label: 'Gauge P&L'},
                    {id: 'severity',   label: 'Severity'}
                ];

                subTabs.forEach(function(st) {
                    var btn = document.createElement('button');
                    btn.id = 'ps-tab-' + st.id;
                    btn.textContent = st.label;
                    var isActive = st.id === psActiveSubTab;
                    btn.style.cssText =
                        'padding:var(--space-3) var(--space-8);font-size:var(--size-xxs);font-weight:600;border:none;cursor:pointer;border-bottom:2px solid transparent;' +
                        (isActive ? 'background:var(--accent);color:var(--inverse);border-bottom-color:var(--accent);' : 'background:var(--sunken);color:var(--text-2);');
                    btn.addEventListener('click', (function(tabId) {
                        return function() { psSwitchSubTab(tabId); };
                    })(st.id));
                    subTabBar.appendChild(btn);
                });
                view.appendChild(subTabBar);

                // Content area
                var contentDiv = document.createElement('div');
                contentDiv.id = 'ps-content';
                contentDiv.style.cssText = 'flex:1;overflow:hidden;display:flex;flex-direction:column;';
                contentDiv.innerHTML =
                    '<div style="color:var(--muted-2);text-align:center;padding:var(--space-inset) 0;">Select a storm to run portfolio stress assessment</div>';
                view.appendChild(contentDiv);

                // Stats bar
                var statsBar = document.createElement('div');
                statsBar.id = 'ps-stats-bar';
                statsBar.style.cssText = 'padding:var(--space-3) var(--space-8);border-top:1px solid var(--line-soft);font-size:var(--size-xxs);color:var(--text-3);background:var(--control);flex-shrink:0;';
                statsBar.textContent = 'MKM Research Labs — Portfolio Stress Assessment';
                view.appendChild(statsBar);

                return view;
            }

            function _applyPortStorms(data) {
                if (data.status !== 'success') return;
                var storms = data.storms || [];
                var sel = document.getElementById('ps-storm-sel');
                if (!sel) return;

                sel.innerHTML = '';
                sel.setAttribute('data-total', data.total_storms || storms.length);
                if (storms.length === 0) {
                    sel.innerHTML = '<option value="">No storms available</option>';
                    return;
                }

                storms.forEach(function(s) {
                    var opt = document.createElement('option');
                    opt.value = s.storm_id;
                    opt.textContent = __STORM_OPT__;
                    sel.appendChild(opt);
                });

                sel.onchange = function() { psStormChanged(); };

                if (storms.length > 0) {
                    sel.value = storms[0].storm_id;
                }
                psStormChanged();
            }

            function loadPortStressData() {
                _psLoadStorms();
            }

            function _psLoadStorms() {
                if (window._tdPrePortStorms) {
                    var cached = window._tdPrePortStorms;
                    window._tdPrePortStorms = null;
                    _applyPortStorms(cached);
                    return;
                }
                var cfg = window.__BACKEND_CONFIG || {};
                var baseUrl = cfg.url || '';
                fetch(baseUrl + '/api/v1/trading/stress/portfolio-storms', {mode: 'cors'})
                    .then(function(r) { return r.json(); })
                    .then(_applyPortStorms)
                    .catch(function(err) {
                        console.error('[PortStress] Storm list error:', err);
                    });
            }

            function psStormChanged() {
                var sel = document.getElementById('ps-storm-sel');
                if (!sel || !sel.value) return;

                var stormId = sel.value;
                var content = document.getElementById('ps-content');
                if (content) {
                    content.innerHTML =
                        '<div style="color:var(--muted-2);text-align:center;padding:var(--space-inset) 0;">Running portfolio stress…</div>';
                }

                var cfg = window.__BACKEND_CONFIG || {};
                var baseUrl = cfg.url || '';

                fetch(baseUrl + '/api/v1/trading/stress/portfolio-run', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    mode: 'cors',
                    body: JSON.stringify({storm_id: stormId})
                })
                .then(function(r) { return r.json(); })
                // The model's parameters arrive with the first run, before anything draws.
                .then(function(data) { return _fpLoad(baseUrl).then(function() { return data; }); })
                .then(function(data) {
                    if (data.status === 'success') {
                        psResult = data;

                        // Update storm info span
                        var infoEl = document.getElementById('ps-storm-info');
                        if (infoEl) {
                            infoEl.textContent =
                                data.intensity_category +
                                ' | ' + Math.round(data.effective_precipitation_mm || 0) + 'mm' +
                                ' | ' + data.duration_hours + 'hr' +
                                ' | ' + (data.gauges_severe || []).length + ' severe' +
                                ' | ' + (data.gauges_warning || []).length + ' warning' +
                                ' | ' + (data.gauges_alert || []).length + ' alert';
                        }

                        psUpdateStatsBar(data);
                        psSwitchSubTab(psActiveSubTab);
                    } else {
                        if (content) {
                            content.innerHTML =
                                '<div style="color:var(--red);text-align:center;padding:var(--space-inset) 0;">' +
                                (data.message || 'Error running portfolio stress') +
                                '</div>';
                        }
                    }
                })
                .catch(function(err) {
                    console.error('[PortStress] Run error:', err);
                    if (content) {
                        content.innerHTML =
                            '<div style="color:var(--red);text-align:center;padding:var(--space-inset) 0;">Network error running portfolio stress</div>';
                    }
                });
            }

            function psSwitchSubTab(tab) {
                psActiveSubTab = tab;

                var subTabIds = ['pflood', 'portpnl', 'gaugepnl', 'severity'];
                subTabIds.forEach(function(id) {
                    var btn = document.getElementById('ps-tab-' + id);
                    if (btn) {
                        if (id === tab) {
                            btn.style.background = Theme.value('accent');
                            btn.style.color = Theme.value('panel');
                        } else {
                            btn.style.background = Theme.value('sunken');
                            btn.style.color = Theme.value('text-2');
                        }
                    }
                });

                if (!psResult) return;

                psCleanupCharts();

                if (tab === 'pflood')   _psRenderPFloodTab(psResult);
                else if (tab === 'portpnl')  _psRenderPortPnlTab(psResult);
                else if (tab === 'gaugepnl') _psRenderGaugePnlTab(psResult);
                else if (tab === 'severity') _psRenderSeverityTab(psResult);
            }

            function psUpdateStatsBar(result) {
                var statsBar = document.getElementById('ps-stats-bar');
                if (!statsBar) return;
                var pnl = result.portfolio_stress_pnl || 0;
                var pnlColor = pnl >= 0 ? 'var(--green-dark)' : 'var(--red-dark)';
                statsBar.innerHTML =
                    '<span style="margin-right:var(--space-wide);">Portfolio Stress P&amp;L: ' +
                    '<b style="color:' + pnlColor + ';">' + fmtGBP(pnl) + '</b></span>' +
                    '<span style="margin-right:var(--space-wide);">Gauges: ' +
                    '<b style="color:var(--red-dark);">' + (result.gauges_severe || []).length + ' severe</b>' +
                    ' &nbsp;' +
                    '<b style="color:var(--amber-deep);">' + (result.gauges_warning || []).length + ' warning</b>' +
                    ' &nbsp;' +
                    '<b style="color:var(--gold-deep);">' + (result.gauges_alert || []).length + ' alert</b>' +
                    '</span>';
            }

            var psGaugeHourlyChart = null;

            // FloodPoly (MKM-FPO-001) client-side. The parameters are served from the
            // model's own config (/trading/stress/flood-poly) rather than copied here:
            // a copy in this file drifted to coefficients matching no released version.
            // Mirrors src/models/stress/flood_poly.py: P = 1 at or above severe, the
            // level held at the floor below it, storm time over the fitted T.
            var _fpModel = null;
            function _fpLoad(baseUrl) {
                if (_fpModel) return Promise.resolve(_fpModel);
                return fetch(baseUrl + '/api/v1/trading/stress/flood-poly', {mode: 'cors'})
                    .then(function(r) { return r.json(); })
                    .then(function(resp) { _fpModel = resp.model; return _fpModel; });
            }
            // The earliest log time any storm reached log level h (flood_poly.envelope_t):
            // the model holds the hour there rather than extrapolate earlier.
            function _fpEnvelopeT(m, h) {
                var env = m.envelope, n = env.length;
                var hk = function(k) { return Math.log(env[k][0]); };
                var tk = function(k) { return Math.log((env[k][1] + 1) / m.storm_hours); };
                if (h <= hk(0)) return -Infinity;
                for (var k = 0; k < n - 1; k++) {
                    if (h <= hk(k + 1)) return tk(k) + (h - hk(k)) / (hk(k + 1) - hk(k)) * (tk(k + 1) - tk(k));
                }
                return tk(n - 1);
            }
            function _fpPFlood(waterLevel, hour, severeLevel) {
                var m = _fpModel;
                if (!m || severeLevel <= 0) return 0;
                var ratio = waterLevel / severeLevel;
                if (ratio >= 1) return 1;
                var h = Math.log(Math.max(ratio, m.level_floor));
                var t = Math.max(Math.log((hour + 1) / m.storm_hours), _fpEnvelopeT(m, h));
                var z = 0;
                for (var k = 0; k < m.coeffs.length; k++) {
                    z += m.coeffs[k] * Math.pow(h, m.terms[k][0]) * Math.pow(t, m.terms[k][1]);
                }
                z = Math.max(-m.exp_clamp, Math.min(m.exp_clamp, z));
                return 1.0 / (1.0 + Math.exp(-z));
            }

            function psCleanupCharts() {
                if (psPortPnlChart) { psPortPnlChart.destroy(); psPortPnlChart = null; }
                if (psPFloodChart)  { psPFloodChart.destroy();  psPFloodChart = null;  }
                if (psGaugeHourlyChart) { psGaugeHourlyChart.destroy(); psGaugeHourlyChart = null; }
            }
