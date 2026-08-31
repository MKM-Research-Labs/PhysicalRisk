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

            var _stressStorms = null;
            var _stressResult = null;
            var _stressChart = null;
            var _stressChartTab = 0;  // 0 = Flood Probability, 1 = Stress P&L

            function renderStressTest() {
                var container = document.getElementById('hazard-chart-container');
                if (!container) return;
                if (currentChart) { currentChart.destroy(); currentChart = null; }

                var gaugeId = _ghcGaugeId();
                if (!gaugeId) return;

                // Check classifier status before rendering full UI
                var cfg = window.__BACKEND_CONFIG || {};
                var baseUrl = cfg.url || '';
                var statusEl = document.getElementById('hazard-status');
                if (statusEl) statusEl.textContent = 'Checking classifier...';

                fetch(baseUrl + '/api/v1/trading/stress/classifier-status/' + gaugeId, {mode: 'cors'})
                    .then(function(r) { return r.json(); })
                    .then(function(data) {
                        if (data.status === 'ready') {
                            _renderStressUI(gaugeId);
                        } else if (data.status === 'training') {
                            _showClassifierTraining(container, gaugeId, data.elapsed_seconds || 0);
                        } else if (data.status === 'not_trained') {
                            _showClassifierNotTrained(container, gaugeId);
                        } else if (data.status === 'failed') {
                            _showClassifierFailed(container, gaugeId, data.error || 'Unknown error');
                        }
                    })
                    .catch(function(err) {
                        console.error('[Stress] Classifier status error:', err);
                        // Fall through to normal UI — scenario run will report the error
                        _renderStressUI(gaugeId);
                    });
            }

            function _renderStressUI(gaugeId) {
                if (_stressTrainingPollTimer) { clearInterval(_stressTrainingPollTimer); _stressTrainingPollTimer = null; }
                var container = document.getElementById('hazard-chart-container');
                if (!container) return;

                container.innerHTML =
                    '<div style="display:flex;flex-direction:column;height:100%;gap:0;">' +
                    // Storm selector bar
                    '<div id="stress-selector" style="display:flex;align-items:center;gap:10px;' +
                        'padding:8px 12px;border-bottom:1px solid var(--line-soft);background:var(--wash);flex-shrink:0;">' +
                        '<span style="font-size:11px;font-weight:600;color:var(--text);">Storm:</span>' +
                        '<select id="stress-storm-select" style="padding:3px 8px;font-size:11px;' +
                            'border:1px solid var(--divider);border-radius:3px;min-width:200px;">' +
                            '<option value="">Loading storms...</option>' +
                        '</select>' +
                        '__PCT_HTML__' +
                        '<span id="stress-storm-info" style="font-size:10px;color:var(--text-3);"></span>' +
                    '</div>' +
                    // Main content: table + chart
                    '<div style="display:flex;flex:1;min-height:0;overflow:hidden;">' +
                        // Left: trade table
                        '<div id="stress-table-wrap" style="width:42%;overflow-y:auto;border-right:1px solid var(--line-soft);' +
                            'padding:8px;font-size:11px;">' +
                            '<div style="color:var(--muted-2);text-align:center;padding:40px 0;">Select a storm to run stress test</div>' +
                        '</div>' +
                        // Right: chart with sub-tabs
                        '<div style="flex:1;display:flex;flex-direction:column;min-width:0;">' +
                            // Chart sub-tabs
                            '<div id="stress-chart-tabs" style="display:flex;gap:0;border-bottom:1px solid var(--line-strong);' +
                                'background:var(--wash);flex-shrink:0;position:relative;z-index:2;">' +
                                '<div id="stress-ctab-0" ' +
                                    'style="padding:5px 14px;font-size:10px;font-weight:600;cursor:pointer;' +
                                    'border-bottom:2px solid var(--accent-mid);color:var(--accent-mid);">Flood Probability</div>' +
                                '<div id="stress-ctab-1" ' +
                                    'style="padding:5px 14px;font-size:10px;font-weight:600;cursor:pointer;' +
                                    'border-bottom:2px solid transparent;color:var(--muted-2);">Stress P&amp;L</div>' +
                                '<div id="stress-ctab-2" ' +
                                    'style="padding:5px 14px;font-size:10px;font-weight:600;cursor:pointer;' +
                                    'border-bottom:2px solid transparent;color:var(--muted-2);">Surface</div>' +
                            '</div>' +
                            // Chart canvas
                            '<div id="stress-chart-wrap" style="flex:1;padding:8px;min-width:0;position:relative;overflow:hidden;">' +
                                '<canvas id="stress-chart-canvas" style="width:100%;height:100%;"></canvas>' +
                            '</div>' +
                        '</div>' +
                    '</div>' +
                    '</div>';

                _stressChartTab = 0;

                // Bind chart tab clicks (can't use inline onclick — we're inside an IIFE)
                document.getElementById('stress-ctab-0').addEventListener('click', function() { _switchStressChart(0); });
                document.getElementById('stress-ctab-1').addEventListener('click', function() { _switchStressChart(1); });
                document.getElementById('stress-ctab-2').addEventListener('click', function() { _switchStressChart(2); });

                if (_stressStorms && _stressStorms._gaugeId === gaugeId) {
                    _populateStormSelect();
                } else {
                    _loadStressStorms(gaugeId);
                }
            }

            function _loadStressStorms(gaugeId) {
                var cfg = window.__BACKEND_CONFIG || {};
                var baseUrl = cfg.url || '';
                var statusEl = document.getElementById('hazard-status');
                if (statusEl) statusEl.textContent = 'Loading stress storms...';

                fetch(baseUrl + '/api/v1/trading/stress/storms?gauge_id=' + gaugeId, {mode: 'cors'})
                    .then(function(r) { return r.json(); })
                    .then(function(data) {
                        if (data.status === 'success') {
                            _stressStorms = data;
                            _stressStorms._gaugeId = gaugeId;
                            _populateStormSelect();
                            if (statusEl) statusEl.textContent = data.count + ' stress storms loaded';
                        } else {
                            if (statusEl) statusEl.textContent = 'Error: ' + (data.message || 'No storms');
                        }
                    })
                    .catch(function(err) {
                        console.error('[Stress] Fetch error:', err);
                        if (statusEl) statusEl.textContent = 'Error loading stress storms';
                    });
            }

            function _populateStormSelect() {
                var sel = document.getElementById('stress-storm-select');
                if (!sel || !_stressStorms) return;

                var storms = _stressStorms.storms || [];
                sel.setAttribute('data-total', _stressStorms.total_storms || storms.length);
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
                        var gaugeId = _ghcGaugeId();
                        _runStressScenario(gaugeId, this.value);

                        var storm = storms.find(function(s) { return s.storm_id === sel.value; });
                        var infoEl = document.getElementById('stress-storm-info');
                        if (infoEl && storm) {
                            var peakHour = Math.round(storm.duration_hours * (storm.peak_position || 0.5));
                            infoEl.textContent = storm.duration_hours + 'hr | ' +
                                'base ' + storm.base_level_m.toFixed(2) + 'm | ' +
                                'peak ' + storm.peak_level_m.toFixed(2) + 'm (+' +
                                storm.level_change_m.toFixed(2) + 'm) | ' +
                                'peak at H' + peakHour;
                        }
                    }
                };

                // Auto-select: use hint from Historical tab if available, else worst case
                var hint = window._stressStormHint || null;
                window._stressStormHint = null;  // Clear hint after use
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
                    targetId = storms[0].storm_id;  // Worst case (sorted by peak level desc)
                }
                if (targetId) {
                    sel.value = targetId;
                    sel.onchange();
                }
            }

            function _runStressScenario(gaugeId, stormId) {
                var cfg = window.__BACKEND_CONFIG || {};
                var baseUrl = cfg.url || '';
                var statusEl = document.getElementById('hazard-status');
                if (statusEl) statusEl.textContent = 'Running stress scenario...';

                var tableWrap = document.getElementById('stress-table-wrap');
                if (tableWrap) tableWrap.innerHTML = '<div style="color:var(--muted-2);text-align:center;padding:40px 0;">Running...</div>';

                fetch(baseUrl + '/api/v1/trading/stress/run', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    mode: 'cors',
                    body: JSON.stringify({gauge_id: gaugeId, storm_id: stormId})
                })
                .then(function(r) { return r.json(); })
                .then(function(data) {
                    if (data.status === 'success') {
                        _stressResult = data;
                        _renderStressTable(data);
                        _drawStressChart();
                        _renderStressStats(data);
                        if (statusEl) statusEl.textContent = 'Stress scenario complete';
                    } else {
                        if (statusEl) statusEl.textContent = 'Error: ' + (data.message || 'Failed');
                        if (tableWrap) tableWrap.innerHTML =
                            '<div style="color:var(--red);text-align:center;padding:40px 0;">' + (data.message || 'Error') + '</div>';
                    }
                })
                .catch(function(err) {
                    console.error('[Stress] Run error:', err);
                    if (statusEl) statusEl.textContent = 'Error running stress scenario';
                });
            }

            function _switchStressChart(idx) {
                _stressChartTab = idx;
                // Update tab styling
                for (var i = 0; i < 3; i++) {
                    var tab = document.getElementById('stress-ctab-' + i);
                    if (tab) {
                        tab.style.borderBottomColor = (i === idx) ? 'var(--accent-mid)' : 'transparent';
                        tab.style.color = (i === idx) ? 'var(--accent-mid)' : 'var(--muted-2)';
                    }
                }
                _drawStressChart();
            }

            function _drawStressChart() {
                if (!_stressResult) return;
                var chartWrap = document.getElementById('stress-chart-wrap');
                if (_stressChartTab === 2) {
                    // Surface tab: show table, hide canvas
                    if (_stressChart) { _stressChart.destroy(); _stressChart = null; }
                    if (chartWrap) chartWrap.innerHTML = '<div id="stress-surface-wrap" style="width:100%;height:100%;overflow:auto;"></div>';
                    _renderSurfaceTable(_stressResult);
                } else {
                    // Chart tabs: restore canvas if needed
                    if (chartWrap && !document.getElementById('stress-chart-canvas')) {
                        chartWrap.innerHTML = '<canvas id="stress-chart-canvas" style="width:100%;height:100%;"></canvas>';
                    }
                    if (_stressChartTab === 0) {
                        _renderProbabilityChart(_stressResult);
                    } else {
                        _renderStressPnlChart(_stressResult);
                    }
                }
            }
