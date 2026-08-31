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

            var _histData = null;
            var _histChart1 = null;
            var _histChart2 = null;

            function renderHistorical() {
                var container = document.getElementById('hazard-chart-container');
                if (!container) return;
                if (currentChart) { currentChart.destroy(); currentChart = null; }

                // Build dual layout: chart (left) + storms panel (right)
                container.innerHTML =
                    '<div style="display:flex;gap:var(--space-8);height:100%;">' +
                    '<div style="flex:3;min-width:0;">' +
                    '<canvas id="hist-timeseries-chart" style="width:100%;height:100%;"></canvas>' +
                    '</div>' +
                    '<div id="hist-storms-panel" style="flex:2;min-width:0;display:flex;flex-direction:column;overflow:hidden;">' +
                    '<div style="font-size:var(--size-xs);font-weight:700;color:var(--text);padding:var(--space-2) var(--space-4);border-bottom:1px solid var(--line-soft);background:var(--wash);">Flood Storm Scenarios</div>' +
                    '<div id="hist-storms-list" style="flex:1;overflow-y:auto;padding:var(--space-2);font-size:var(--size-xxs);color:var(--muted);">Loading storms...</div>' +
                    '</div></div>';

                var gaugeId = _ghcGaugeId();
                if (!gaugeId) return;

                // Use cached data or fetch
                if (_histData && _histData._gaugeId === gaugeId) {
                    _renderHistCharts();
                    _loadStormScenarios(gaugeId);
                    return;
                }

                var cfg = window.__BACKEND_CONFIG || {};
                var baseUrl = cfg.url || '';
                var statusEl = document.getElementById('hazard-status');
                if (statusEl) statusEl.textContent = 'Loading historical data...';

                fetch(baseUrl + '/api/v1/gauges/' + gaugeId + '/history', {mode: 'cors'})
                    .then(function(r) { return r.json(); })
                    .then(function(data) {
                        if (data.status === 'success') {
                            _histData = data;
                            _histData._gaugeId = gaugeId;
                            _renderHistCharts();
                            _loadStormScenarios(gaugeId);
                            if (statusEl) statusEl.textContent = 'Historical data loaded';
                        } else {
                            if (statusEl) statusEl.textContent = 'Error: ' + (data.message || 'No data');
                        }
                    })
                    .catch(function(err) {
                        console.error('[Historical] Fetch error:', err);
                        if (statusEl) statusEl.textContent = 'Error loading historical data';
                    });
            }

            function _renderHistCharts() {
                if (!_histData) return;

                var stats = _histData.statistics || {};
                var obs = _histData.daily_observations || [];
                var stages = _histData.flood_stages || {};

                // Subsample daily observations for performance (every 7th day)
                var sampleObs = [];
                for (var si = 0; si < obs.length; si += 7) {
                    sampleObs.push(obs[si]);
                }

                // Time series chart (left)
                var tsCtx = document.getElementById('hist-timeseries-chart');
                if (tsCtx) {
                    if (_histChart1) _histChart1.destroy();
                    var tsLabels = sampleObs.map(function(o) { return o.date; });
                    var tsLevels = sampleObs.map(function(o) { return o.level_meters; });
                    var n = tsLabels.length;

                    var datasets = [{
                        label: 'Water Level',
                        data: tsLevels,
                        borderColor: Theme.value('accent-bright'),
                        backgroundColor: Theme.value('chart-wash-bright'),
                        fill: true,
                        borderWidth: 0.8,
                        pointRadius: 0,
                        tension: 0
                    }];

                    // Threshold lines
                    if (stages.FloodAlert) datasets.push({
                        label: 'Alert (' + stages.FloodAlert.toFixed(1) + 'm)',
                        data: Array(n).fill(stages.FloodAlert),
                        borderColor: Theme.value('amber-yellow'), borderDash: [5,5], borderWidth: 1.5, pointRadius: 0, fill: false
                    });
                    if (stages.FloodWarning) datasets.push({
                        label: 'Warning (' + stages.FloodWarning.toFixed(1) + 'm)',
                        data: Array(n).fill(stages.FloodWarning),
                        borderColor: Theme.value('amber-bright'), borderDash: [5,5], borderWidth: 1.5, pointRadius: 0, fill: false
                    });
                    if (stages.SevereFloodWarning) datasets.push({
                        label: 'Severe (' + stages.SevereFloodWarning.toFixed(1) + 'm)',
                        data: Array(n).fill(stages.SevereFloodWarning),
                        borderColor: Theme.value('red-bright'), borderDash: [5,5], borderWidth: 1.5, pointRadius: 0, fill: false
                    });

                    _histChart1 = new Chart(tsCtx.getContext('2d'), {
                        type: 'line',
                        data: { labels: tsLabels, datasets: datasets },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            interaction: { intersect: false, mode: 'nearest' },
                            plugins: {
                                title: { display: true, text: 'Daily Water Levels (50yr)', font: { size: 12 } },
                                legend: { position: 'top', labels: { usePointStyle: true, boxWidth: 8, font: { size: 9 } } },
                                tooltip: {
                                    callbacks: {
                                        label: function(ctx) { return ctx.dataset.label + ': ' + ctx.parsed.y.toFixed(2) + 'm'; }
                                    }
                                }
                            },
                            scales: {
                                x: {
                                    title: { display: true, text: 'Date' },
                                    ticks: { maxTicksLimit: 10, font: { size: 9 } }
                                },
                                y: {
                                    title: { display: true, text: 'Water Level (m)' },
                                    min: 0
                                }
                            }
                        }
                    });
                }

                // Stats bar
                var bar = document.getElementById('hazard-stats-bar');
                if (bar) {
                    var annualMaxima = stats.annual_maxima || [];
                    var mean = stats.mean_level != null ? stats.mean_level.toFixed(2) : 'N/A';
                    var sd = stats.std_dev != null ? stats.std_dev.toFixed(3) : 'N/A';
                    var maxL = stats.max_level != null ? stats.max_level.toFixed(2) : 'N/A';
                    var period = stats.record_years || annualMaxima.length || 0;
                    var exc = stats.flood_exceedances || {};
                    bar.innerHTML = [
                        '<span><b>Record:</b> ' + period + ' years</span>',
                        '<span><b>Mean:</b> ' + mean + 'm</span>',
                        '<span><b>Std Dev:</b> ' + sd + 'm</span>',
                        '<span><b>Max:</b> ' + maxL + 'm</span>',
                        '<span style="color:var(--amber-yellow);"><b>Alert:</b> ' + (exc.alert || 0) + ' yr</span>',
                        '<span style="color:var(--amber-bright);"><b>Warning:</b> ' + (exc.warning || 0) + ' yr</span>',
                        '<span style="color:var(--red-bright);"><b>Severe:</b> ' + (exc.severe || 0) + ' yr</span>'
                    ].join('');
                }
            }

            function _loadStormScenarios(gaugeId) {
                var listEl = document.getElementById('hist-storms-list');
                if (!listEl) return;

                var cfg = window.__BACKEND_CONFIG || {};
                var baseUrl = cfg.url || '';

                fetch(baseUrl + '/api/v1/trading/stress/storms?gauge_id=' + encodeURIComponent(gaugeId), {mode: 'cors'})
                    .then(function(r) { return r.json(); })
                    .then(function(result) {
                        if (result.status !== 'success' || !result.storms || result.storms.length === 0) {
                            listEl.innerHTML = '<div style="padding:var(--space-6);color:var(--disabled);text-align:center;">No storm scenarios available for this gauge</div>';
                            return;
                        }
                        _renderStormList(result.storms, gaugeId);
                    })
                    .catch(function(err) {
                        console.error('[Historical] Storm fetch error:', err);
                        listEl.innerHTML = '<div style="padding:var(--space-6);color:var(--red-dark);">Failed to load storms</div>';
                    });
            }

            function _renderStormList(storms, gaugeId) {
                var listEl = document.getElementById('hist-storms-list');
                if (!listEl) return;

                var triggerColors = Theme.ramp('trigger_level');

                var html = '<div style="padding:var(--space-1) var(--space-2);font-size:var(--size-xxs);color:var(--muted);margin-bottom:var(--space-2);">' +
                    storms.length + ' storms breached alert at this gauge</div>';

                // Show top 30 storms (sorted by peak level desc)
                var shown = Math.min(storms.length, 30);
                for (var i = 0; i < shown; i++) {
                    var s = storms[i];
                    var maxTrig = s.max_trigger || 'alert';
                    var trigColor = triggerColors[maxTrig] || Theme.value('muted');
                    var peakLevel = s.peak_level_m ? s.peak_level_m.toFixed(2) : '?';
                    var durationHrs = s.duration_hours || 0;
                    var category = s.intensity_category || '';

                    html +=
                        '<div class="hist-storm-row" data-storm-id="' + s.storm_id + '" data-gauge-id="' + gaugeId + '" ' +
                        'style="padding:var(--space-3) var(--space-4);border-bottom:1px solid var(--code);cursor:pointer;display:flex;align-items:center;gap:var(--space-3);" ' +
                        'onmouseover="this.style.background=\'' + Theme.value('accent-soft') + '\'" ' +
                        'onmouseout="this.style.background=\'\'">' +
                        '<span style="width:6px;height:6px;border-radius:50%;background:' + trigColor + ';flex-shrink:0;"></span>' +
                        '<div style="flex:1;min-width:0;">' +
                        '<div style="font-size:var(--size-xxs);font-weight:600;color:var(--text);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">' +
                        (s.name ? s.name + ' (' + s.storm_id + ')' : s.storm_id) + '</div>' +
                        '<div style="font-size:var(--size-xxs);color:var(--muted);">' + category + ' | ' + (s.gauges_severe || 0) + ' sev | ' + Math.round(s.effective_precipitation_mm || 0) + 'mm</div>' +
                        '</div>' +
                        '<span style="font-size:var(--size-xxs);color:var(--accent-mid);">\u2192</span>' +
                        '</div>';
                }

                if (storms.length > shown) {
                    html += '<div style="padding:var(--space-3) var(--space-4);font-size:var(--size-xxs);color:var(--muted);text-align:center;">+ ' + (storms.length - shown) + ' more storms</div>';
                }

                listEl.innerHTML = html;

                // Attach click handlers (IIFE-safe, no inline onclick)
                var rows = listEl.querySelectorAll('.hist-storm-row');
                for (var ri = 0; ri < rows.length; ri++) {
                    rows[ri].addEventListener('click', function() {
                        var stormId = this.getAttribute('data-storm-id');
                        var gid = this.getAttribute('data-gauge-id');
                        _navigateToStress(gid, stormId);
                    });
                }
            }

            function _navigateToStress(gaugeId, stormId) {
                // Switch to Stress Test tab (index 5)
                if (typeof switchTab === 'function') {
                    // Store the storm hint for auto-selection
                    window._stressStormHint = stormId;
                    switchTab(5);
                }
            }

            function _cleanupHistCharts() {
                if (_histChart1) { _histChart1.destroy(); _histChart1 = null; }
                if (_histChart2) { _histChart2.destroy(); _histChart2 = null; }
            }
