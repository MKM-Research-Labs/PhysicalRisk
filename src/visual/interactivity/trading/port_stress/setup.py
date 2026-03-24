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
Port Stress — setup sub-module.

State variables, DOM construction, storm loading, dropdown population,
sub-tab switching, and stats bar update.
All rendering sub-tabs are imported and concatenated here.
"""

from . import pfloods, portfolio_pnl, gauge_pnl, severity
from config.format import storm_option_js as _storm_opt


def get_js() -> str:
    """Return JavaScript fragment for the full Port Stress tab (Tab 8)."""
    return (
        _get_setup_js()
        + pfloods.get_js()
        + portfolio_pnl.get_js()
        + gauge_pnl.get_js()
        + severity.get_js()
    )


def _get_setup_js() -> str:
    """Return JavaScript for state, DOM, loading, and sub-tab switching."""
    return """
            // ==============================================================
            // Tab 8: Port Stress — Portfolio-wide storm stress assessment
            // ==============================================================
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
                stormBar.style.cssText = 'padding:8px 16px;border-bottom:1px solid #eee;display:flex;align-items:center;gap:12px;background:#f5f7fa;flex-shrink:0;';
                stormBar.innerHTML =
                    '<span style="font-size:11px;font-weight:600;color:#333;">Storm:</span>' +
                    '<select id="ps-storm-sel" style="padding:4px 8px;font-size:11px;border:1px solid #ccc;border-radius:3px;min-width:380px;">' +
                    '<option value="">Loading storms\u2026</option>' +
                    '</select>' +
                    '<span id="ps-storm-info" style="flex:1;font-size:10px;color:#666;"></span>';
                view.appendChild(stormBar);

                // Sub-tab bar
                var subTabBar = document.createElement('div');
                subTabBar.style.cssText = 'display:flex;gap:0;border-bottom:1px solid #ddd;background:#f8f9fa;flex-shrink:0;';

                var subTabs = [
                    {id: 'pflood',     label: 'P(flood)'},
                    {id: 'portpnl',    label: 'Port P\u0026L'},
                    {id: 'gaugepnl',   label: 'Gauge P\u0026L'},
                    {id: 'severity',   label: 'Severity'}
                ];

                subTabs.forEach(function(st) {
                    var btn = document.createElement('button');
                    btn.id = 'ps-tab-' + st.id;
                    btn.textContent = st.label;
                    var isActive = st.id === psActiveSubTab;
                    btn.style.cssText =
                        'padding:5px 16px;font-size:10px;font-weight:600;border:none;cursor:pointer;border-bottom:2px solid transparent;' +
                        (isActive ? 'background:#1976d2;color:white;border-bottom-color:#1976d2;' : 'background:#f5f5f5;color:#555;');
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
                    '<div style="color:#999;text-align:center;padding:40px 0;">Select a storm to run portfolio stress assessment</div>';
                view.appendChild(contentDiv);

                // Stats bar
                var statsBar = document.createElement('div');
                statsBar.id = 'ps-stats-bar';
                statsBar.style.cssText = 'padding:6px 16px;border-top:1px solid #eee;font-size:10px;color:#666;background:#f9f9f9;flex-shrink:0;';
                statsBar.textContent = 'MKM Research Labs \u2014 Portfolio Stress Assessment';
                view.appendChild(statsBar);

                return view;
            }

            function _applyPortStorms(data) {
                if (data.status !== 'success') return;
                var storms = data.storms || [];
                var sel = document.getElementById('ps-storm-sel');
                if (!sel) return;

                sel.innerHTML = '';
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
                var cfg = window.__BACKEND_CONFIG || {};
                var baseUrl = cfg.url || '';

                // Check classifier readiness before loading storms
                fetch(baseUrl + '/api/v1/trading/classifiers/readiness', {mode: 'cors'})
                    .then(function(r) { return r.json(); })
                    .then(function(data) {
                        if (data.status === 'success' && !data.ready) {
                            _psShowClassifierGate(data);
                            return;
                        }
                        _psLoadStorms();
                    })
                    .catch(function() {
                        // If readiness check fails, proceed anyway
                        _psLoadStorms();
                    });
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

            function _psShowClassifierGate(data) {
                var content = document.getElementById('ps-content');
                if (!content) return;

                var trained = data.trained || 0;
                var total = data.total || 0;
                var missing = data.missing || 0;

                content.innerHTML =
                    '<div style="text-align:center;padding:60px 40px;max-width:480px;margin:0 auto;">' +
                    '<div style="font-size:36px;margin-bottom:16px;">\\u26a0\\ufe0f</div>' +
                    '<div style="font-size:14px;font-weight:600;color:#333;margin-bottom:8px;">' +
                    'Classifiers Required</div>' +
                    '<div style="font-size:12px;color:#666;margin-bottom:20px;line-height:1.5;">' +
                    'Portfolio stress requires a trained flood classifier for every gauge. ' +
                    'Currently <b>' + trained + ' of ' + total + '</b> gauges have classifiers ' +
                    '(' + missing + ' missing).</div>' +
                    '<button id="ps-train-all-btn" style="padding:8px 24px;font-size:12px;font-weight:600;' +
                    'background:#1976d2;color:white;border:none;border-radius:4px;cursor:pointer;">' +
                    'Train All Classifiers</button>' +
                    '<div id="ps-train-progress" style="margin-top:16px;font-size:11px;color:#666;display:none;"></div>' +
                    '</div>';

                // Hide the storm selector bar — not relevant until classifiers are ready
                var stormBar = document.getElementById('ps-storm-bar');
                if (stormBar) stormBar.style.display = 'none';

                var btn = document.getElementById('ps-train-all-btn');
                if (btn) {
                    btn.addEventListener('click', function() {
                        _psStartTrainAll(btn);
                    });
                }
            }

            function _psStartTrainAll(btn) {
                var cfg = window.__BACKEND_CONFIG || {};
                var baseUrl = cfg.url || '';
                btn.disabled = true;
                btn.textContent = 'Training\\u2026';
                btn.style.background = '#90a4ae';

                var progress = document.getElementById('ps-train-progress');
                if (progress) {
                    progress.style.display = 'block';
                    progress.innerHTML =
                        '<div style="color:#1976d2;font-weight:600;margin-bottom:4px;">Training in progress\u2026</div>' +
                        '<div style="color:#888;line-height:1.5;">This will take approximately 10\u201320 minutes for all gauges. ' +
                        'Feel free to navigate elsewhere \u2014 training continues in the background ' +
                        'and you will be notified when it completes.</div>';
                }

                fetch(baseUrl + '/api/v1/trading/classifiers/train-all', {
                    method: 'POST',
                    mode: 'cors'
                })
                .then(function(r) { return r.json(); })
                .then(function(data) {
                    if (data.status === 'complete') {
                        // All already trained — reload
                        loadPortStressData();
                        return;
                    }
                    // Poll for completion
                    var pollId = setInterval(function() {
                        fetch(baseUrl + '/api/v1/trading/classifiers/train-all/status', {mode: 'cors'})
                            .then(function(r) { return r.json(); })
                            .then(function(st) {
                                if (progress) {
                                    var msg = st.completed + '/' + st.total + ' trained';
                                    if (st.current_gauge_id) msg += ' \\u2014 ' + st.current_gauge_id;
                                    if (st.eta_seconds > 0) {
                                        if (st.eta_seconds < 60) msg += ' (ETA ' + Math.round(st.eta_seconds) + 's)';
                                        else msg += ' (ETA ' + (st.eta_seconds / 60).toFixed(1) + 'm)';
                                    }
                                    progress.textContent = msg;
                                }
                                if (st.status === 'complete') {
                                    clearInterval(pollId);
                                    // Notify the user
                                    if (window.showSuccess) {
                                        window.showSuccess(
                                            'Classifier training complete! ' +
                                            st.completed + '/' + st.total + ' gauges trained. ' +
                                            'Portfolio stress is now available.'
                                        );
                                    }
                                    // Restore storm bar and reload
                                    var stormBar = document.getElementById('ps-storm-bar');
                                    if (stormBar) stormBar.style.display = 'flex';
                                    loadPortStressData();
                                }
                            })
                            .catch(function() { clearInterval(pollId); });
                    }, 5000);
                })
                .catch(function(err) {
                    console.error('[PortStress] Train-all error:', err);
                    btn.disabled = false;
                    btn.textContent = 'Train All Classifiers';
                    btn.style.background = '#1976d2';
                });
            }

            function psStormChanged() {
                var sel = document.getElementById('ps-storm-sel');
                if (!sel || !sel.value) return;

                var stormId = sel.value;
                var content = document.getElementById('ps-content');
                if (content) {
                    content.innerHTML =
                        '<div style="color:#999;text-align:center;padding:40px 0;">Running portfolio stress\u2026</div>';
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
                                '<div style="color:#c00;text-align:center;padding:40px 0;">' +
                                (data.message || 'Error running portfolio stress') +
                                '</div>';
                        }
                    }
                })
                .catch(function(err) {
                    console.error('[PortStress] Run error:', err);
                    if (content) {
                        content.innerHTML =
                            '<div style="color:#c00;text-align:center;padding:40px 0;">Network error running portfolio stress</div>';
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
                            btn.style.background = '#1976d2';
                            btn.style.color = 'white';
                        } else {
                            btn.style.background = '#f5f5f5';
                            btn.style.color = '#555';
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
                var pnlColor = pnl >= 0 ? '#2e7d32' : '#c62828';
                statsBar.innerHTML =
                    '<span style="margin-right:20px;">Portfolio Stress P&amp;L: ' +
                    '<b style="color:' + pnlColor + ';">' + fmtGBP(pnl) + '</b></span>' +
                    '<span style="margin-right:20px;">Gauges: ' +
                    '<b style="color:#c62828;">' + (result.gauges_severe || []).length + ' severe</b>' +
                    ' &nbsp;' +
                    '<b style="color:#e65100;">' + (result.gauges_warning || []).length + ' warning</b>' +
                    ' &nbsp;' +
                    '<b style="color:#f9a825;">' + (result.gauges_alert || []).length + ' alert</b>' +
                    '</span>';
            }

            function psCleanupCharts() {
                if (psPortPnlChart) { psPortPnlChart.destroy(); psPortPnlChart = null; }
                if (psPFloodChart)  { psPFloodChart.destroy();  psPFloodChart = null;  }
            }
""".replace('__STORM_OPT__', _storm_opt('s', show_warning=True))
