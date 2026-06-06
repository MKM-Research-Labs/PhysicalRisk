
            // ==============================================================
            // P&L History Modal
            // ==============================================================
            var tdPLHistChart = null;

            window.tdShowPLHistory = function() {
                var overlay = document.createElement('div');
                overlay.id = 'td-plhist-overlay';
                overlay.style.cssText = 'position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.55);z-index:9000;display:flex;align-items:center;justify-content:center;';
                overlay.addEventListener('click', function(e) {
                    if (e.target === overlay) tdClosePLHistory();
                });

                var modal = document.createElement('div');
                modal.style.cssText = 'background:#fff;border-radius:8px;box-shadow:0 8px 32px rgba(0,0,0,0.25);width:92vw;max-width:1300px;height:82vh;display:flex;flex-direction:column;overflow:hidden;';

                // Header
                var header = document.createElement('div');
                header.style.cssText = 'display:flex;align-items:center;padding:14px 20px;border-bottom:1px solid #eee;background:#f8f9fa;flex-shrink:0;';
                header.innerHTML =
                    '<span style="font-size:14px;font-weight:700;color:#333;">P&amp;L History</span>' +
                    '<span style="margin:0 10px;color:#aaa;">|</span>' +
                    '<span style="font-size:12px;color:#555;">Daily P&amp;L with market move vs trade components</span>' +
                    '<span style="flex:1;"></span>' +
                    '<button onclick="tdClosePLHistory()" style="padding:4px 12px;font-size:11px;background:#78909c;color:white;border:none;border-radius:3px;cursor:pointer;">Close</button>';
                modal.appendChild(header);

                // Stats bar
                var statsRow = document.createElement('div');
                statsRow.id = 'td-plhist-stats';
                statsRow.style.cssText = 'display:flex;gap:24px;padding:8px 20px;border-bottom:1px solid #eee;background:#fafafa;font-size:11px;color:#555;flex-shrink:0;';
                statsRow.innerHTML = '<span style="color:#aaa;">Loading…</span>';
                modal.appendChild(statsRow);

                // Chart body
                var body = document.createElement('div');
                body.id = 'td-plhist-body';
                body.style.cssText = 'flex:1;padding:16px 20px;min-height:0;position:relative;';
                body.innerHTML = '<canvas id="td-plhist-canvas" style="width:100%;height:100%;"></canvas>';
                modal.appendChild(body);

                overlay.appendChild(modal);
                document.body.appendChild(overlay);

                // Fetch P&L series
                var url = getBaseUrl() + '/api/v1/trading/pnl-series?_=' + Date.now();
                fetch(url, {mode: 'cors', cache: 'no-store'})
                    .then(function(r) { return r.json(); })
                    .then(function(result) {
                        if (result.status !== 'success' || !result.series || result.series.length === 0) {
                            body.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:100%;"><span style="color:#c62828;font-size:13px;">No P&L history available — run EOD first</span></div>';
                            statsRow.innerHTML = '';
                            return;
                        }
                        tdBuildPLHistChart(body, statsRow, result.series);
                    })
                    .catch(function(err) {
                        body.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:100%;"><span style="color:#c62828;font-size:13px;">Error: ' + err.message + '</span></div>';
                    });
            };

            window.tdClosePLHistory = function() {
                if (tdPLHistChart) {
                    try { tdPLHistChart.destroy(); } catch(e) {}
                    tdPLHistChart = null;
                }
                var overlay = document.getElementById('td-plhist-overlay');
                if (overlay) overlay.remove();
            };

            function tdBuildPLHistChart(container, statsRow, series) {
                var labels = series.map(function(s) { return s.date.slice(5); });
                var step = Math.max(1, Math.floor(labels.length / 15));
                var xLabels = labels.map(function(d, i) { return (i % step === 0) ? d : ''; });

                var dailyPnl   = series.map(function(s) { return s.daily_pnl; });
                var fromMarket = series.map(function(s) { return s.from_market; });
                var runningPnl = series.map(function(s) { return s.running_pnl; });

                // Stats
                var finalPnl      = runningPnl[runningPnl.length - 1] || 0;
                var positiveDays  = dailyPnl.filter(function(v) { return v > 0; }).length;
                var negativeDays  = dailyPnl.filter(function(v) { return v < 0; }).length;
                var totalMktMove  = fromMarket.reduce(function(a, b) { return a + b; }, 0);

                statsRow.innerHTML =
                    '<span>Running P&amp;L: <strong>' + fmtGBP(finalPnl) + '</strong></span>' +
                    '<span style="color:#2e7d32;">▲ Positive days: <strong>' + positiveDays + '</strong></span>' +
                    '<span style="color:#c62828;">▼ Negative days: <strong>' + negativeDays + '</strong></span>' +
                    '<span>Curve move P&amp;L: <strong>' + fmtGBP(totalMktMove) + '</strong></span>' +
                    '<span style="color:#999;">' + series.length + ' trading days</span>';

                var canvas = document.getElementById('td-plhist-canvas');
                if (!canvas || typeof Chart === 'undefined') return;

                var barBg     = dailyPnl.map(function(v) { return v >= 0 ? 'rgba(46,125,50,0.65)' : 'rgba(198,40,40,0.65)'; });
                var barBorder = dailyPnl.map(function(v) { return v >= 0 ? '#2e7d32' : '#c62828'; });

                try {
                    tdPLHistChart = new Chart(canvas.getContext('2d'), {
                        type: 'bar',
                        data: {
                            labels: xLabels,
                            datasets: [
                                {
                                    type: 'bar',
                                    label: 'Daily P&L',
                                    data: dailyPnl,
                                    backgroundColor: barBg,
                                    borderColor: barBorder,
                                    borderWidth: 1,
                                    order: 3,
                                    yAxisID: 'y',
                                },
                                {
                                    type: 'line',
                                    label: 'Market Move Component',
                                    data: fromMarket,
                                    borderColor: '#f57c00',
                                    backgroundColor: 'transparent',
                                    borderWidth: 1.5,
                                    borderDash: [5, 3],
                                    pointRadius: 0,
                                    pointHoverRadius: 3,
                                    tension: 0.3,
                                    order: 2,
                                    yAxisID: 'y',
                                },
                                {
                                    type: 'line',
                                    label: 'Running P&L',
                                    data: runningPnl,
                                    borderColor: '#1b5e20',
                                    backgroundColor: 'transparent',
                                    borderWidth: 2,
                                    pointRadius: 0,
                                    pointHoverRadius: 4,
                                    tension: 0.3,
                                    order: 1,
                                    yAxisID: 'y2',
                                }
                            ]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            animation: false,
                            interaction: {mode: 'index', intersect: false},
                            plugins: {
                                title: {
                                    display: true,
                                    text: 'Daily P⁠&⁠L — bars = daily total, orange line = curve move component, green line = running P⁠&⁠L',
                                    font: {size: 11},
                                    color: '#555',
                                    padding: {bottom: 6}
                                },
                                legend: {
                                    display: true,
                                    position: 'top',
                                    labels: {font: {size: 10}, boxWidth: 12}
                                },
                                tooltip: {
                                    callbacks: {
                                        title: function(items) { return series[items[0].dataIndex].date; },
                                        label: function(ctx) { return ctx.dataset.label + ': ' + fmtGBP(ctx.parsed.y); }
                                    }
                                }
                            },
                            scales: {
                                x: {
                                    ticks: {font: {size: 8}, maxRotation: 0, autoSkip: false},
                                    grid: {display: false}
                                },
                                y: {
                                    position: 'left',
                                    title: {display: true, text: 'Daily P&L (£)', font: {size: 9}},
                                    ticks: {
                                        font: {size: 9},
                                        callback: function(v) { return fmtGBP(v); }
                                    }
                                },
                                y2: {
                                    position: 'right',
                                    title: {display: true, text: 'Running P&L (£)', font: {size: 9}},
                                    ticks: {
                                        font: {size: 9},
                                        callback: function(v) { return fmtGBP(v); }
                                    },
                                    grid: {drawOnChartArea: false}
                                }
                            }
                        }
                    });
                } catch(e) {
                    console.error('[PLHist] Chart error:', e);
                    container.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:100%;"><span style="color:#c62828;font-size:12px;">Chart error: ' + e.message + '</span></div>';
                }
            }
