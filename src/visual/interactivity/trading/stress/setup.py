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
Stress Test — setup sub-module.

State variables, DOM construction, data loading, gauge/storm dropdown
population and change handlers, chart tab switching.

On-demand classifier training UI is in training_ui.py.
"""

from config.format import storm_option_js as _storm_opt


def get_js() -> str:
    """Return JavaScript fragment for stress test state, DOM, and loading."""
    return """
            // ==============================================================
            // Tab 7: Stress Test — CDS-in-stress cash pricing
            // ==============================================================
            var tdStressGauges = null;
            var tdStressStorms = null;
            var tdStressResult = null;
            var tdStressChart = null;
            var tdStressChartTab = 0;  // 0 = Flood Probability, 1 = Stress P&L, 2 = Surface
            var tdStressGaugeHint = null;

            function createStressView() {
                var view = document.createElement('div');
                view.id = 'td-stress-view';
                view.style.cssText = 'flex:1;display:none;flex-direction:column;overflow:hidden;';

                // Selector bar: gauge + storm dropdowns
                var selectorBar = document.createElement('div');
                selectorBar.id = 'td-stress-selector-bar';
                selectorBar.style.cssText = 'padding:8px 16px;border-bottom:1px solid #eee;display:flex;align-items:center;gap:12px;background:#f5f7fa;flex-shrink:0;';
                selectorBar.innerHTML =
                    '<span style="font-size:11px;font-weight:600;color:#333;">Gauge:</span>' +
                    '<select id="td-stress-gauge" style="padding:4px 8px;font-size:11px;border:1px solid #ccc;border-radius:3px;min-width:240px;max-width:300px;">' +
                        '<option value="">Loading gauges...</option>' +
                    '</select>' +
                    '<span style="font-size:11px;font-weight:600;color:#333;margin-left:8px;">Storm:</span>' +
                    '<select id="td-stress-storm" style="padding:4px 8px;font-size:11px;border:1px solid #ccc;border-radius:3px;min-width:300px;max-width:420px;">' +
                        '<option value="">Select gauge first</option>' +
                    '</select>' +
                    '<span id="td-stress-storm-info" style="font-size:10px;color:#666;flex:1;"></span>';
                view.appendChild(selectorBar);

                // Main content: table (left) + chart (right)
                var body = document.createElement('div');
                body.style.cssText = 'flex:1;display:flex;overflow:hidden;min-height:0;';

                // Left: trade table
                var tableWrap = document.createElement('div');
                tableWrap.id = 'td-stress-table-wrap';
                tableWrap.style.cssText = 'width:42%;overflow-y:auto;border-right:1px solid #eee;padding:8px;font-size:11px;';
                tableWrap.innerHTML = '<div style="color:#999;text-align:center;padding:40px 0;">Select a gauge and storm to run stress test</div>';
                body.appendChild(tableWrap);

                // Right: chart with sub-tabs
                var chartPane = document.createElement('div');
                chartPane.style.cssText = 'flex:1;display:flex;flex-direction:column;min-width:0;overflow:hidden;';

                // Chart sub-tabs
                var chartTabs = document.createElement('div');
                chartTabs.id = 'td-stress-chart-tabs';
                chartTabs.style.cssText = 'display:flex;gap:0;border-bottom:1px solid #ddd;background:#f8f9fa;flex-shrink:0;position:relative;z-index:2;';
                chartTabs.innerHTML =
                    '<div id="td-stress-ctab-0" style="padding:5px 14px;font-size:10px;font-weight:600;cursor:pointer;border-bottom:2px solid #1565c0;color:#1565c0;">Flood Probability</div>' +
                    '<div id="td-stress-ctab-1" style="padding:5px 14px;font-size:10px;font-weight:600;cursor:pointer;border-bottom:2px solid transparent;color:#999;">Stress P&amp;L</div>' +
                    '<div id="td-stress-ctab-2" style="padding:5px 14px;font-size:10px;font-weight:600;cursor:pointer;border-bottom:2px solid transparent;color:#999;">Surface</div>';
                chartPane.appendChild(chartTabs);

                // Chart canvas
                var chartWrap = document.createElement('div');
                chartWrap.id = 'td-stress-chart-wrap';
                chartWrap.style.cssText = 'flex:1;padding:8px;min-width:0;position:relative;overflow:hidden;';
                chartWrap.innerHTML = '<canvas id="td-stress-chart-canvas" style="width:100%;height:100%;"></canvas>';
                chartPane.appendChild(chartWrap);

                body.appendChild(chartPane);
                view.appendChild(body);

                // Stats/links bar at bottom
                var statsBar = document.createElement('div');
                statsBar.id = 'td-stress-stats-bar';
                statsBar.style.cssText = 'padding:6px 16px;border-top:1px solid #eee;font-size:10px;color:#666;background:#f9f9f9;display:flex;align-items:center;gap:16px;flex-shrink:0;';
                statsBar.innerHTML = '<span style="color:#999;">Run a stress scenario to see results</span>';
                view.appendChild(statsBar);

                return view;
            }

            function loadStressData(gaugeHint) {
                if (gaugeHint) tdStressGaugeHint = gaugeHint;
                var cfg = window.__BACKEND_CONFIG || {};
                var baseUrl = cfg.url || '';

                // Fetch gauge list
                fetch(baseUrl + '/api/v1/trading/stress/gauges', {mode: 'cors'})
                    .then(function(r) { return r.json(); })
                    .then(function(data) {
                        if (data.status === 'success') {
                            tdStressGauges = data.gauges || [];
                            _tdPopulateGaugeDropdown();
                        }
                    })
                    .catch(function(err) {
                        console.error('[Stress] Gauge fetch error:', err);
                    });
            }

            function _tdPopulateGaugeDropdown() {
                var sel = document.getElementById('td-stress-gauge');
                if (!sel || !tdStressGauges) return;

                sel.innerHTML = '';
                tdStressGauges.forEach(function(g) {
                    var opt = document.createElement('option');
                    opt.value = g.gauge_id;
                    var tradeInfo = g.trade_count > 0 ? ' [' + g.trade_count + ' trades]' : '';
                    opt.textContent = g.gauge_name + ' (' + g.gauge_id + ')' + tradeInfo;
                    sel.appendChild(opt);
                });

                // Pre-select: use market gauge hint first, then blotter filter, else first with trades
                var hint = tdStressGaugeHint ||
                    ((typeof tdBlotterFilters !== 'undefined' && tdBlotterFilters.gauge_id) ? tdBlotterFilters.gauge_id : null);
                tdStressGaugeHint = null;  // consume hint
                if (hint) {
                    for (var i = 0; i < tdStressGauges.length; i++) {
                        if (tdStressGauges[i].gauge_id === hint) {
                            sel.value = hint;
                            break;
                        }
                    }
                }
                if (!sel.value && tdStressGauges.length > 0) {
                    // Pick first gauge with trades, or just the first
                    var withTrades = tdStressGauges.find(function(g) { return g.trade_count > 0; });
                    sel.value = withTrades ? withTrades.gauge_id : tdStressGauges[0].gauge_id;
                }

                sel.onchange = function() { tdStressGaugeChanged(); };

                // Bind chart tab clicks
                var ctab0 = document.getElementById('td-stress-ctab-0');
                var ctab1 = document.getElementById('td-stress-ctab-1');
                var ctab2 = document.getElementById('td-stress-ctab-2');
                if (ctab0) ctab0.addEventListener('click', function() { _tdSwitchStressChart(0); });
                if (ctab1) ctab1.addEventListener('click', function() { _tdSwitchStressChart(1); });
                if (ctab2) ctab2.addEventListener('click', function() { _tdSwitchStressChart(2); });

                // Auto-load storms for selected gauge
                tdStressGaugeChanged();
            }

            function tdStressGaugeChanged() {
                var gaugeSel = document.getElementById('td-stress-gauge');
                var stormSel = document.getElementById('td-stress-storm');
                if (!gaugeSel || !stormSel) return;

                var gaugeId = gaugeSel.value;
                if (!gaugeId) return;

                // Stop any previous training poll
                if (_tdStressTrainingPollTimer) { clearInterval(_tdStressTrainingPollTimer); _tdStressTrainingPollTimer = null; }

                stormSel.innerHTML = '<option value="">Checking classifier...</option>';
                var tableWrap = document.getElementById('td-stress-table-wrap');
                if (tableWrap) tableWrap.innerHTML = '<div style="color:#999;text-align:center;padding:40px 0;">Checking classifier...</div>';

                var cfg = window.__BACKEND_CONFIG || {};
                var baseUrl = cfg.url || '';

                fetch(baseUrl + '/api/v1/trading/stress/classifier-status/' + gaugeId, {mode: 'cors'})
                    .then(function(r) { return r.json(); })
                    .then(function(data) {
                        if (data.status === 'ready') {
                            _tdLoadStorms(gaugeId);
                        } else if (data.status === 'training') {
                            _tdShowTrainingInProgress(gaugeId, data.elapsed_seconds || 0);
                        } else if (data.status === 'not_trained') {
                            _tdShowNotTrained(gaugeId);
                        } else if (data.status === 'failed') {
                            _tdShowTrainingFailed(gaugeId, data.error || 'Unknown error');
                        } else {
                            _tdLoadStorms(gaugeId);
                        }
                    })
                    .catch(function(err) {
                        console.error('[Stress] Classifier status error:', err);
                        _tdLoadStorms(gaugeId);
                    });
            }

            function _tdLoadStorms(gaugeId) {
                if (_tdStressTrainingPollTimer) { clearInterval(_tdStressTrainingPollTimer); _tdStressTrainingPollTimer = null; }
                var stormSel = document.getElementById('td-stress-storm');
                var tableWrap = document.getElementById('td-stress-table-wrap');

                if (stormSel) stormSel.innerHTML = '<option value="">Loading storms...</option>';
                if (tableWrap) tableWrap.innerHTML = '<div style="color:#999;text-align:center;padding:40px 0;">Loading storms...</div>';

                var cfg = window.__BACKEND_CONFIG || {};
                var baseUrl = cfg.url || '';

                fetch(baseUrl + '/api/v1/trading/stress/storms?gauge_id=' + gaugeId, {mode: 'cors'})
                    .then(function(r) { return r.json(); })
                    .then(function(data) {
                        if (data.status === 'success') {
                            tdStressStorms = data;
                            _tdPopulateStormDropdown();
                        } else {
                            if (stormSel) stormSel.innerHTML = '<option value="">No storms: ' + (data.message || 'error') + '</option>';
                            if (tableWrap) tableWrap.innerHTML =
                                '<div style="color:#c00;text-align:center;padding:40px 0;">' + (data.message || 'No storms found') + '</div>';
                        }
                    })
                    .catch(function(err) {
                        console.error('[Stress] Storm fetch error:', err);
                        if (stormSel) stormSel.innerHTML = '<option value="">Error loading storms</option>';
                    });
            }

            function _tdPopulateStormDropdown() {
                var sel = document.getElementById('td-stress-storm');
                if (!sel || !tdStressStorms) return;

                var storms = tdStressStorms.storms || [];
                sel.innerHTML = '<option value="">-- Select storm (' + storms.length + ' scenarios) --</option>';

                storms.forEach(function(s) {
                    var opt = document.createElement('option');
                    opt.value = s.storm_id;
                    var label = __STORM_OPT__;
                    opt.textContent = label;
                    sel.appendChild(opt);
                });

                sel.onchange = function() {
                    if (this.value) {
                        _tdUpdateStormInfo(this.value, storms);
                        tdStressStormChanged();
                    }
                };

                // Auto-select: use hint from Historical tab if available, else worst case
                var hint = window._stressStormHint || null;
                window._stressStormHint = null;
                var targetId = null;
                if (hint) {
                    for (var si = 0; si < storms.length; si++) {
                        if (storms[si].storm_id === hint) {
                            targetId = hint;
                            break;
                        }
                    }
                }
                if (!targetId && storms.length > 0) {
                    targetId = storms[0].storm_id;  // Worst case (sorted by peak desc)
                }
                if (targetId) {
                    sel.value = targetId;
                    _tdUpdateStormInfo(targetId, storms);
                    tdStressStormChanged();
                }
            }

            function _tdUpdateStormInfo(stormId, storms) {
                var storm = storms.find(function(s) { return s.storm_id === stormId; });
                var infoEl = document.getElementById('td-stress-storm-info');
                if (infoEl && storm) {
                    var peakHour = Math.round(storm.duration_hours * (storm.peak_position || 0.5));
                    infoEl.textContent = storm.duration_hours + 'hr | ' +
                        'base ' + storm.base_level_m.toFixed(2) + 'm | ' +
                        'peak ' + storm.peak_level_m.toFixed(2) + 'm (+' +
                        storm.level_change_m.toFixed(2) + 'm) | ' +
                        'peak at H' + peakHour;
                }
            }

            function tdStressStormChanged() {
                var gaugeSel = document.getElementById('td-stress-gauge');
                var stormSel = document.getElementById('td-stress-storm');
                if (!gaugeSel || !stormSel) return;

                var gaugeId = gaugeSel.value;
                var stormId = stormSel.value;
                if (!gaugeId || !stormId) return;

                var tableWrap = document.getElementById('td-stress-table-wrap');
                if (tableWrap) tableWrap.innerHTML = '<div style="color:#999;text-align:center;padding:40px 0;">Running scenario...</div>';

                var cfg = window.__BACKEND_CONFIG || {};
                var baseUrl = cfg.url || '';

                fetch(baseUrl + '/api/v1/trading/stress/run', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    mode: 'cors',
                    body: JSON.stringify({gauge_id: gaugeId, storm_id: stormId})
                })
                .then(function(r) { return r.json(); })
                .then(function(data) {
                    if (data.status === 'success') {
                        tdStressResult = data;
                        _tdRenderStressTable(data);
                        _tdDrawStressChart();
                        _tdRenderStressStats(data);
                    } else {
                        if (tableWrap) tableWrap.innerHTML =
                            '<div style="color:#c00;text-align:center;padding:40px 0;">' + (data.message || 'Error') + '</div>';
                    }
                })
                .catch(function(err) {
                    console.error('[Stress] Run error:', err);
                    if (tableWrap) tableWrap.innerHTML =
                        '<div style="color:#c00;text-align:center;padding:40px 0;">Error running stress scenario</div>';
                });
            }

            // ---- Chart tab switching ----
            function _tdSwitchStressChart(idx) {
                tdStressChartTab = idx;
                for (var i = 0; i < 3; i++) {
                    var tab = document.getElementById('td-stress-ctab-' + i);
                    if (tab) {
                        tab.style.borderBottomColor = (i === idx) ? '#1565c0' : 'transparent';
                        tab.style.color = (i === idx) ? '#1565c0' : '#999';
                    }
                }
                _tdDrawStressChart();
            }

            function _tdDrawStressChart() {
                if (!tdStressResult) return;
                var chartWrap = document.getElementById('td-stress-chart-wrap');
                if (tdStressChartTab === 2) {
                    // Surface tab: show table, hide canvas
                    if (tdStressChart) { tdStressChart.destroy(); tdStressChart = null; }
                    if (chartWrap) chartWrap.innerHTML = '<div id="td-stress-surface-wrap" style="width:100%;height:100%;overflow:auto;"></div>';
                    _tdRenderSurfaceTable(tdStressResult);
                } else {
                    // Chart tabs: restore canvas if needed
                    if (chartWrap && !document.getElementById('td-stress-chart-canvas')) {
                        chartWrap.innerHTML = '<canvas id="td-stress-chart-canvas" style="width:100%;height:100%;"></canvas>';
                    }
                    if (tdStressChartTab === 0) {
                        _tdRenderProbabilityChart(tdStressResult);
                    } else {
                        _tdRenderStressPnlChart(tdStressResult);
                    }
                }
            }
""".replace('__STORM_OPT__', _storm_opt('s', show_peak=True))
