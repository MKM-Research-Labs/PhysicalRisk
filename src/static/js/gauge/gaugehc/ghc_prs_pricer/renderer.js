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

            function renderPRSPricing() {
                if (currentChart) { currentChart.destroy(); currentChart = null; }

                var result = computePRSCashflows();
                if (!result) return;  // PRS controls not built yet; re-renders once they are
                var periods = result.periods;
                var container = document.getElementById('hazard-chart-container');

                function fmtNum(v) {
                    return v.toLocaleString('en-GB', {minimumFractionDigits: 2, maximumFractionDigits: 2});
                }

                function fmtMoney(v) {
                    return (v < 0 ? '-' : '') + 'GBP ' + fmtNum(Math.abs(v));
                }

                // Build table + chart side by side
                var tableRows = '';
                periods.forEach(function(p) {
                    tableRows +=
                        '<tr>' +
                        '<td style="padding:var(--space-1) var(--space-4);font-weight:600;">' + p.label + '</td>' +
                        '<td style="padding:var(--space-1) var(--space-4);text-align:right;">' + (p.S_t * 100).toFixed(2) + '%</td>' +
                        '<td style="padding:var(--space-1) var(--space-4);text-align:right;">' + p.df.toFixed(4) + '</td>' +
                        '<td style="padding:var(--space-1) var(--space-4);text-align:right;color:var(--accent);">' + fmtNum(p.premCF) + '</td>' +
                        '<td style="padding:var(--space-1) var(--space-4);text-align:right;color:var(--accent);">' + fmtNum(p.premPV) + '</td>' +
                        '<td style="padding:var(--space-1) var(--space-4);text-align:right;color:var(--red-bright);">' + fmtNum(p.protCF) + '</td>' +
                        '<td style="padding:var(--space-1) var(--space-4);text-align:right;color:var(--red-bright);">' + fmtNum(p.protPV) + '</td>' +
                        '</tr>';
                });

                // Totals row
                tableRows +=
                    '<tr style="border-top:2px solid var(--text);font-weight:bold;background:var(--code);">' +
                    '<td style="padding:var(--space-2) var(--space-4);">TOTAL</td>' +
                    '<td></td><td></td>' +
                    '<td style="padding:var(--space-2) var(--space-4);text-align:right;color:var(--accent);">' +
                        fmtNum(periods.reduce(function(s,p){ return s+p.premCF; }, 0)) + '</td>' +
                    '<td style="padding:var(--space-2) var(--space-4);text-align:right;color:var(--accent);font-weight:bold;">' +
                        fmtMoney(result.totalPremPV) + '</td>' +
                    '<td style="padding:var(--space-2) var(--space-4);text-align:right;color:var(--red-bright);">' +
                        fmtNum(periods.reduce(function(s,p){ return s+p.protCF; }, 0)) + '</td>' +
                    '<td style="padding:var(--space-2) var(--space-4);text-align:right;color:var(--red-bright);font-weight:bold;">' +
                        fmtMoney(result.totalProtPV) + '</td>' +
                    '</tr>';

                var tableHtml =
                    '<div style="display:flex;gap:var(--space-8);height:100%;">' +
                    '<div style="flex:1;min-width:0;display:flex;align-items:center;">' +
                    '<canvas id="prs-hazard-curve-chart" style="width:100%;height:100%;"></canvas>' +
                    '</div>' +
                    '<div style="flex:1;min-width:0;display:flex;align-items:center;">' +
                    '<canvas id="hazard-chart" style="width:100%;height:100%;"></canvas>' +
                    '</div></div>';

                container.innerHTML = tableHtml;

                // Render bar chart
                var ctx = document.getElementById('hazard-chart').getContext('2d');
                var labels = periods.map(function(p) { return p.label; });
                var premPVs = periods.map(function(p) { return p.premPV / 1000; });
                var protPVs = periods.map(function(p) { return p.protPV / 1000; });

                currentChart = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: labels,
                        datasets: [
                            {
                                label: 'PV Premium ($K)',
                                data: premPVs,
                                backgroundColor: Theme.value('chart-fill-accent-mid'),
                                borderColor: Theme.value('accent'),
                                borderWidth: 1
                            },
                            {
                                label: 'PV Protection ($K)',
                                data: protPVs,
                                backgroundColor: Theme.value('chart-fill-severe'),
                                borderColor: Theme.value('red-bright'),
                                borderWidth: 1
                            }
                        ]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                position: 'top',
                                labels: { usePointStyle: true, boxWidth: 8, font: { size: 10 } }
                            },
                            tooltip: {
                                callbacks: {
                                    label: function(ctx) {
                                        return ctx.dataset.label + ': $' + ctx.parsed.y.toFixed(1) + 'K';
                                    }
                                }
                            }
                        },
                        scales: {
                            x: { title: { display: true, text: 'Semi-Annual Period', font: { size: 10 } } },
                            y: { title: { display: true, text: 'PV ($K)', font: { size: 10 } }, min: 0 }
                        }
                    }
                });

                // Render hazard curve term structure chart (left panel)
                var hcCtx = document.getElementById('prs-hazard-curve-chart');
                if (hcCtx) {
                    var _gid2 = hazardData ? hazardData.gauge_id : '';
                    var _trig2 = result.trigger;
                    console.log('[PRSRender] Chart: gauge=' + _gid2 + ', trigger=' + _trig2 + ', _mktHazardTS=' + (_mktHazardTS ? Object.keys(_mktHazardTS).length + ' gauges' : 'null') + ', has gauge=' + (_mktHazardTS && _mktHazardTS[_gid2] ? 'yes' : 'no'));
                    var hcTenors = ['1','2','3','4','5'];
                    var hcLabels = hcTenors.map(function(t) { return t + 'Y'; });
                    var hcRates = [];
                    if (_mktHazardTS && _mktHazardTS[_gid2] && _mktHazardTS[_gid2][_trig2]) {
                        hcRates = hcTenors.map(function(t) {
                            var r = _mktHazardTS[_gid2][_trig2][t];
                            return r != null ? r * 10000 : null;
                        });
                    }
                    // Also show trade spread as horizontal line
                    var tradeSpdVal = parseFloat(document.getElementById('prs-spread').value) || 0;
                    if (window._prsHazardCurveChart) window._prsHazardCurveChart.destroy();
                    window._prsHazardCurveChart = new Chart(hcCtx.getContext('2d'), {
                        type: 'line',
                        data: {
                            labels: hcLabels,
                            datasets: [
                                {
                                    label: 'Hazard Curve (' + _trig2 + ')',
                                    data: hcRates,
                                    borderColor: Theme.value('accent-mid'),
                                    backgroundColor: Theme.value('chart-fill-accent'),
                                    fill: true,
                                    tension: 0.3,
                                    pointRadius: 5,
                                    pointBackgroundColor: Theme.value('accent-mid'),
                                    borderWidth: 2
                                },
                                {
                                    label: 'Trade Spread',
                                    data: Array(hcLabels.length).fill(tradeSpdVal),
                                    borderColor: Theme.value('red-dark'),
                                    borderDash: [6, 3],
                                    borderWidth: 1.5,
                                    pointRadius: 0,
                                    fill: false
                                }
                            ]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: {
                                legend: { position: 'top', labels: { usePointStyle: true, boxWidth: 8, font: { size: 10 } } },
                                tooltip: {
                                    callbacks: {
                                        label: function(ctx) { return ctx.dataset.label + ': ' + (ctx.parsed.y != null ? ctx.parsed.y.toFixed(1) : '-') + ' bps'; }
                                    }
                                }
                            },
                            scales: {
                                x: { title: { display: true, text: 'Tenor', font: { size: 10 } } },
                                y: { title: { display: true, text: 'Rate (bps)', font: { size: 10 } } }
                            }
                        }
                    });
                }

                // Maturity label for display
                var matSel = document.getElementById('prs-maturity');
                var matLabel = matSel && matSel.selectedOptions && matSel.selectedOptions[0]
                    ? matSel.selectedOptions[0].text : result.tenor + 'Y';

                // Auto-populate spread to hazard curve rate if currently zero (first render)
                var spdInput = document.getElementById('prs-spread');
                if (spdInput && parseFloat(spdInput.value) === 0) {
                    // Default to market hazard curve rate (not fair spread)
                    var _gid = hazardData ? hazardData.gauge_id : '';
                    var _trig = result.trigger;
                    var _tnr = result.tenor;
                    var _hzRate = null;
                    if (_mktHazardTS && _mktHazardTS[_gid] && _mktHazardTS[_gid][_trig]) {
                        _hzRate = _mktHazardTS[_gid][_trig][String(_tnr)];
                    }
                    if (_hzRate != null && _hzRate > 0) {
                        spdInput.value = (_hzRate * 10000).toFixed(1);
                    } else if (result.fairSpreadBps > 0) {
                        spdInput.value = result.fairSpreadBps.toFixed(1);
                    }
                    // Re-render with populated spread (avoids zero-premium first frame)
                    return renderPRSPricing();
                }

                // Show market hazard rate in display span
                var hazDisplay = document.getElementById('prs-hazard-display');
                if (hazDisplay) {
                    var gaugeId = hazardData ? hazardData.gauge_id : '';
                    var trigger = result.trigger;
                    var tenor = result.tenor;
                    if (_mktHazardTS && _mktHazardTS[gaugeId] && _mktHazardTS[gaugeId][trigger]) {
                        var mktRate = _mktHazardTS[gaugeId][trigger][String(tenor)];
                        if (mktRate != null) {
                            hazDisplay.innerHTML = '<b>Hazard:</b> ' + (mktRate * 10000).toFixed(1) + ' bps (' + tenor + 'Y ' + trigger + ')';
                        } else {
                            hazDisplay.textContent = '';
                        }
                    } else {
                        hazDisplay.textContent = '';
                    }
                }

                // Stats bar
                var bar = document.getElementById('hazard-stats-bar');
                var npvColor = result.npv >= 0 ? Theme.value('green-bright') : Theme.value('red-bright');
                var dirLabel = result.isPayer ? 'Pay' : 'Rcv';

                // Check if counterparty selected for commit button
                var ctpyEl = document.getElementById('prs-counterparty');
                var ctpySelected = ctpyEl && ctpyEl.value;
                var ctpyDisplayName = '';
                if (ctpySelected && ctpyEl.selectedIndex > 0) {
                    ctpyDisplayName = ctpyEl.options[ctpyEl.selectedIndex].text;
                }
                var commitBtn = '';
                if (isTradeReview) {
                    commitBtn = '<span style="color:var(--accent-mid);font-size:var(--size-xxs);font-weight:600;margin-left:var(--space-4);">Trade Review</span>';
                } else if (isCloseOut) {
                    commitBtn = ctpySelected ?
                        '<button id="prs-commit-btn" onclick="commitPRSTrade()" ' +
                        'style="padding:var(--space-2) var(--space-7);background:var(--red-soft);color:var(--inverse);border:none;border-radius:var(--radius-sm);' +
                        'cursor:pointer;font-weight:bold;font-size:var(--size-xs);margin-left:var(--space-4);">Close Out</button>' :
                        '<span style="color:var(--disabled);font-size:var(--size-xxs);margin-left:var(--space-4);">(select ctpy to close out)</span>';
                } else if (ctpySelected) {
                    commitBtn = '<button id="prs-commit-btn" onclick="commitPRSTrade()" ' +
                    'style="padding:var(--space-2) var(--space-7);background:var(--green-bright);color:var(--inverse);border:none;border-radius:var(--radius-sm);' +
                    'cursor:pointer;font-weight:bold;font-size:var(--size-xs);margin-left:var(--space-4);">Commit</button>';
                } else {
                    commitBtn = '<span style="color:var(--disabled);font-size:var(--size-xxs);margin-left:var(--space-4);">(select ctpy to commit)</span>';
                }

                var ctpyTag = ctpyDisplayName ?
                    '<span><b>Ctpy:</b> <span style="color:var(--accent-mid);">' + ctpyDisplayName + '</span></span>' :
                    '<span style="color:var(--disabled);"><b>Ctpy:</b> none</span>';

                bar.innerHTML = [
                    ctpyTag,
                    '<span style="font-weight:bold;color:' + (result.isPayer ? Theme.value('accent') : Theme.value('amber-deep')) + ';">' + dirLabel + '</span>',
                    '<span><b>Fair Spread:</b> <span style="font-size:var(--size-md);color:var(--accent);">' + result.fairSpreadBps.toFixed(1) + ' bps</span></span>',
                    '<span><b>Running:</b> ' + result.spreadBps.toFixed(0) + ' bps</span>',
                    '<span style="color:' + npvColor + ';"><b>NPV:</b> ' + fmtMoney(result.npv) + '</span>',
                    '<span><b>Premium Leg:</b> ' + fmtMoney(result.totalPremPV) + '</span>',
                    '<span><b>Protection Leg:</b> ' + fmtMoney(result.totalProtPV) + '</span>',
                    '<span><b>Risky Annuity:</b> ' + result.riskyAnnuity.toFixed(3) + '</span>',
                    commitBtn
                ].join('');

                document.getElementById('hazard-status').textContent =
                    result.trigger.charAt(0).toUpperCase() + result.trigger.slice(1) + ' trigger | ' +
                    matLabel + ' | Fair=' + result.fairSpreadBps.toFixed(1) + 'bps';
            }
