        (function() {
            var _cfg = window.__GAUGEHA_CONFIG || {};
            var PANEL_W = _cfg.panelWidth || '700px';
            var PANEL_H = _cfg.panelHeight || '500px';
            var currentChart = null;
            var graphPanel = null;

            function createGraphPanel() {
                if (graphPanel) return graphPanel;

                graphPanel = document.createElement('div');
                graphPanel.id = 'gauge-graph-panel';
                graphPanel.style.cssText =
                    'position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);' +
                    'width:' + PANEL_W + ';height:' + PANEL_H + ';' +
                    'background:white;border:1px solid #ccc;border-radius:8px;' +
                    'box-shadow:0 4px 20px rgba(0,0,0,0.3);z-index:2000;' +
                    'display:none;flex-direction:column;font-family:Arial,sans-serif;';

                // Header
                var header = document.createElement('div');
                header.style.cssText =
                    'display:flex;justify-content:space-between;align-items:center;' +
                    'padding:10px 16px;border-bottom:1px solid #eee;background:#f8f9fa;' +
                    'border-radius:8px 8px 0 0;';

                var title = document.createElement('span');
                title.id = 'gauge-graph-title';
                title.style.cssText = 'font-weight:bold;font-size:14px;color:#333;';

                var closeBtn = document.createElement('button');
                closeBtn.innerHTML = '&times;';
                closeBtn.style.cssText =
                    'border:none;background:none;font-size:24px;cursor:pointer;' +
                    'color:#666;padding:0 8px;line-height:1;';
                closeBtn.onclick = hideGraphPanel;

                header.appendChild(title);
                header.appendChild(closeBtn);

                // Chart container
                var chartBox = document.createElement('div');
                chartBox.id = 'gauge-chart-container';
                chartBox.style.cssText = 'flex:1;padding:12px 16px;position:relative;min-height:0;';

                var canvas = document.createElement('canvas');
                canvas.id = 'gauge-history-chart';
                chartBox.appendChild(canvas);

                // Stats bar
                var statsBar = document.createElement('div');
                statsBar.id = 'gauge-stats-bar';
                statsBar.style.cssText =
                    'padding:8px 16px;border-top:1px solid #eee;font-size:12px;color:#555;' +
                    'display:flex;gap:16px;flex-wrap:wrap;';

                // Footer with time range
                var footer = document.createElement('div');
                footer.style.cssText =
                    'display:flex;justify-content:space-between;align-items:center;' +
                    'padding:8px 16px;border-top:1px solid #eee;background:#f8f9fa;' +
                    'border-radius:0 0 8px 8px;font-size:12px;';

                var timeRange = document.createElement('div');
                timeRange.innerHTML =
                    '<select id="gauge-time-range" style="padding:4px 8px;border:1px solid #ccc;border-radius:4px;">' +
                    '<option value="30">Last 30 Days</option>' +
                    '<option value="90">Last 90 Days</option>' +
                    '<option value="365" selected>Last Year</option>' +
                    '<option value="1825">Last 5 Years</option>' +
                    '<option value="0">All Data (50 years)</option>' +
                    '</select>';

                var status = document.createElement('span');
                status.id = 'gauge-graph-status';
                status.style.color = '#666';

                footer.appendChild(timeRange);
                footer.appendChild(status);

                graphPanel.appendChild(header);
                graphPanel.appendChild(chartBox);
                graphPanel.appendChild(statsBar);
                graphPanel.appendChild(footer);
                document.body.appendChild(graphPanel);

                document.getElementById('gauge-time-range').onchange = function() {
                    var gaugeId = graphPanel.dataset.gaugeId;
                    if (gaugeId) loadGaugeData(gaugeId, parseInt(this.value));
                };

                return graphPanel;
            }

            function showGraphPanel(gaugeId) {
                var panel = createGraphPanel();
                panel.dataset.gaugeId = gaugeId;
                document.getElementById('gauge-graph-title').textContent = 'History: ' + gaugeId;
                document.getElementById('gauge-graph-status').textContent = 'Loading...';
                panel.style.display = 'flex';

                var days = parseInt(document.getElementById('gauge-time-range').value);
                loadGaugeData(gaugeId, days);
            }

            function hideGraphPanel() {
                if (graphPanel) graphPanel.style.display = 'none';
                if (currentChart) { currentChart.destroy(); currentChart = null; }
            }

            async function loadGaugeData(gaugeId, days) {
                var status = document.getElementById('gauge-graph-status');
                status.textContent = 'Loading...';

                try {
                    var cfg = window.__BACKEND_CONFIG || {};
                    var baseUrl = cfg.url || '';
                    var url = baseUrl + '/api/v1/gauges/' + gaugeId + '/history';
                    if (days > 0) url += '?days=' + days;

                    var response = await fetch(url, {mode: 'cors'});
                    if (!response.ok) throw new Error('HTTP ' + response.status);

                    var data = await response.json();
                    if (data.status !== 'success') throw new Error(data.message || 'Failed');

                    renderChart(data);
                    renderStats(data);
                    status.textContent = data.daily_observations.length + ' days';
                    var meta = data.gauge_metadata || {};
                    var gaugeName = meta.gauge_name || '';
                    var titleEl = document.getElementById('gauge-graph-title');
                    if (titleEl) {
                        titleEl.textContent = gaugeName
                            ? 'History: ' + gaugeName + ' (' + gaugeId + ')'
                            : 'History: ' + gaugeId;
                    }
                } catch (error) {
                    console.error('Gauge history error:', error);
                    status.textContent = 'Error: ' + error.message;
                    if (window.showError) window.showError('Failed to load gauge history');
                }
            }

            function renderStats(data) {
                var bar = document.getElementById('gauge-stats-bar');
                var s = data.statistics || {};
                var fs = data.flood_stages || {};
                var exc = s.flood_exceedances || {};

                var items = [];
                if (s.mean_level != null) items.push('<b>Mean:</b> ' + s.mean_level.toFixed(2) + 'm');
                if (s.max_level != null) items.push('<b>Max:</b> ' + s.max_level.toFixed(2) + 'm' +
                    (s.max_level_date ? ' (' + s.max_level_date + ')' : ''));
                if (exc.flood_alert) items.push('<b>Alert exceedances:</b> ' +
                    exc.flood_alert.count + ' (' + exc.flood_alert.frequency_per_year.toFixed(1) + '/yr)');
                if (exc.severe_warning) items.push('<b>Severe:</b> ' +
                    exc.severe_warning.count + ' (' + exc.severe_warning.frequency_per_year.toFixed(1) + '/yr)');

                bar.innerHTML = items.map(function(t) {
                    return '<span>' + t + '</span>';
                }).join('');
            }

            function renderChart(data) {
                var ctx = document.getElementById('gauge-history-chart').getContext('2d');
                if (currentChart) currentChart.destroy();

                var obs = data.daily_observations || [];
                var fs = data.flood_stages || {};

                var labels = obs.map(function(p) { return p.date; });
                var levels = obs.map(function(p) { return p.level_meters; });
                var n = labels.length;

                var datasets = [
                    {
                        label: 'Water Level (m)',
                        data: levels,
                        borderColor: '#2196F3',
                        backgroundColor: 'rgba(33,150,243,0.1)',
                        fill: true,
                        tension: 0.3,
                        pointRadius: 0,
                        borderWidth: 1.5
                    }
                ];

                if (fs.FloodAlert) datasets.push({
                    label: 'Alert (' + fs.FloodAlert.toFixed(1) + 'm)',
                    data: Array(n).fill(fs.FloodAlert),
                    borderColor: '#FFC107', borderDash: [5,5], borderWidth: 1, pointRadius: 0, fill: false
                });
                if (fs.FloodWarning) datasets.push({
                    label: 'Warning (' + fs.FloodWarning.toFixed(1) + 'm)',
                    data: Array(n).fill(fs.FloodWarning),
                    borderColor: '#FF9800', borderDash: [5,5], borderWidth: 1, pointRadius: 0, fill: false
                });
                if (fs.SevereFloodWarning) datasets.push({
                    label: 'Severe (' + fs.SevereFloodWarning.toFixed(1) + 'm)',
                    data: Array(n).fill(fs.SevereFloodWarning),
                    borderColor: '#F44336', borderDash: [5,5], borderWidth: 1, pointRadius: 0, fill: false
                });

                currentChart = new Chart(ctx, {
                    type: 'line',
                    data: { labels: labels, datasets: datasets },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        interaction: { intersect: false, mode: 'index' },
                        plugins: {
                            legend: {
                                position: 'top',
                                labels: { usePointStyle: true, boxWidth: 8, font: { size: 11 } }
                            },
                            tooltip: {
                                callbacks: {
                                    label: function(ctx) {
                                        return ctx.dataset.label + ': ' + ctx.parsed.y.toFixed(2) + 'm';
                                    }
                                }
                            }
                        },
                        scales: {
                            x: {
                                display: true,
                                title: { display: true, text: 'Date' },
                                ticks: { maxTicksLimit: 10, font: { size: 10 } }
                            },
                            y: {
                                display: true,
                                title: { display: true, text: 'Water Level (m)' },
                                min: 0
                            }
                        }
                    }
                });
            }

            document.addEventListener('gaugeHistoryRequested', function(e) {
                if (e.detail && e.detail.gaugeId) showGraphPanel(e.detail.gaugeId);
            });

            window.GaugeGraphInteraction = {
                show: showGraphPanel,
                hide: hideGraphPanel
            };

            console.log('Gauge graph interaction ready');
        })();
        
