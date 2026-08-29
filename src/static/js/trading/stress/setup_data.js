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
                if (tableWrap) tableWrap.innerHTML = '<div style="color:var(--muted-2);text-align:center;padding:40px 0;">Checking classifier...</div>';

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
                if (tableWrap) tableWrap.innerHTML = '<div style="color:var(--muted-2);text-align:center;padding:40px 0;">Loading storms...</div>';

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
                                '<div style="color:var(--red);text-align:center;padding:40px 0;">' + (data.message || 'No storms found') + '</div>';
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
                sel.setAttribute('data-total', tdStressStorms.total_storms || storms.length);
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
                if (tableWrap) tableWrap.innerHTML = '<div style="color:var(--muted-2);text-align:center;padding:40px 0;">Running scenario...</div>';

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
                            '<div style="color:var(--red);text-align:center;padding:40px 0;">' + (data.message || 'Error') + '</div>';
                    }
                })
                .catch(function(err) {
                    console.error('[Stress] Run error:', err);
                    if (tableWrap) tableWrap.innerHTML =
                        '<div style="color:var(--red);text-align:center;padding:40px 0;">Error running stress scenario</div>';
                });
            }
