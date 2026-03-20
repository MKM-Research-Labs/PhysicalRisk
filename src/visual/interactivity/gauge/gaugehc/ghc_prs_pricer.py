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
Gauge hazard curve — PRS Pricing: analytical pricer and chart rendering.

Semi-annual cashflow computation (premium + protection legs),
fair spread calculation, and dual-chart layout (hazard curve + cashflow bars).
"""


def get_js() -> str:
    """Return JS fragment for PRS cashflow engine and chart rendering."""
    return """
            // ================================================================
            // PRS Analytical Pricer — semi-annual cashflow computation
            // ================================================================
            function computePRSCashflows() {
                var trigger = document.getElementById('prs-trigger').value;
                var notionalStr = document.getElementById('prs-notional').value.replace(/,/g, '');
                var notional = parseFloat(notionalStr) || 10000000;

                // Get tenor from maturity select's data attribute
                var matSel = document.getElementById('prs-maturity');
                var tenor = 5;
                if (matSel && matSel.selectedOptions && matSel.selectedOptions[0]) {
                    tenor = parseInt(matSel.selectedOptions[0].dataset.tenor) || 5;
                }
                var maturityValue = matSel ? matSel.value : '';

                var spreadBps = parseFloat(document.getElementById('prs-spread').value) || 0;
                var spread = spreadBps / 10000;
                var recovery = 0;

                // Payer/Receiver direction
                var dirEl = document.getElementById('prs-direction');
                var isPayer = !dirEl || dirEl.value === 'payer';

                // Use market hazard curve if available, else fall back to base term structures
                var ts;
                var gaugeId = hazardData.gauge_id || '';
                if (_mktHazardTS && _mktHazardTS[gaugeId] && _mktHazardTS[gaugeId][trigger]) {
                    // Build synthetic term structure from market rates
                    var mktRates = _mktHazardTS[gaugeId][trigger];
                    ts = [];
                    var cumSurv = 1.0;
                    for (var yr = 1; yr <= 5; yr++) {
                        var lambda = mktRates[String(yr)] || 0.02;
                        cumSurv = cumSurv * (1 - lambda);
                        ts.push({year: yr, survival_prob: cumSurv, cumulative_default_prob: 1 - cumSurv});
                    }
                } else {
                    ts = (hazardData.term_structures || {})[trigger] || [];
                }

                // Build semi-annual schedule
                var nPeriods = tenor * 2;
                var dt = 0.5; // semi-annual
                var periods = [];
                var totalPremPV = 0, totalProtPV = 0, riskyAnnuity = 0;

                for (var i = 1; i <= nPeriods; i++) {
                    var t = i * dt;
                    var tPrev = (i - 1) * dt;
                    var S_t = interpolateSurvival(ts, t);
                    var S_prev = interpolateSurvival(ts, tPrev);
                    var rf = interpolateYieldRate(prsYieldCurve, t);
                    var df = Math.exp(-rf * t);

                    // Premium leg: spread * dt * notional * S(t)
                    var premCF = spread * dt * notional * S_t;
                    var premPV = premCF * df;

                    // Protection leg: (1-R) * notional * [S(t-1) - S(t)]
                    var protCF = (1 - recovery) * notional * (S_prev - S_t);
                    var protPV = protCF * df;

                    totalPremPV += premPV;
                    totalProtPV += protPV;
                    riskyAnnuity += dt * S_t * df;

                    periods.push({
                        period: i,
                        t: t,
                        label: t.toFixed(1) + 'y',
                        S_t: S_t,
                        df: df,
                        premCF: premCF,
                        premPV: premPV,
                        protCF: protCF,
                        protPV: protPV
                    });
                }

                var fairSpread = riskyAnnuity > 0 ? totalProtPV / (riskyAnnuity * notional) : 0;
                var npv = totalProtPV - totalPremPV; // buyer perspective

                // Flip NPV for receiver (selling protection = opposite perspective)
                var directedNpv = isPayer ? npv : -npv;

                return {
                    periods: periods,
                    totalPremPV: totalPremPV,
                    totalProtPV: totalProtPV,
                    riskyAnnuity: riskyAnnuity,
                    fairSpread: fairSpread,
                    fairSpreadBps: fairSpread * 10000,
                    npv: directedNpv,
                    notional: notional,
                    tenor: tenor,
                    maturityDate: maturityValue,
                    spread: spread,
                    spreadBps: spreadBps,
                    yieldCurve: prsYieldCurve,
                    recovery: recovery,
                    trigger: trigger,
                    isPayer: isPayer
                };
            }

            // ================================================================
            // Tab 3: PRS Pricing — analytical cashflow breakdown
            // ================================================================
            function renderPRSPricing() {
                if (currentChart) { currentChart.destroy(); currentChart = null; }

                var result = computePRSCashflows();
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
                        '<td style="padding:2px 8px;font-weight:600;">' + p.label + '</td>' +
                        '<td style="padding:2px 8px;text-align:right;">' + (p.S_t * 100).toFixed(2) + '%</td>' +
                        '<td style="padding:2px 8px;text-align:right;">' + p.df.toFixed(4) + '</td>' +
                        '<td style="padding:2px 8px;text-align:right;color:#1976D2;">' + fmtNum(p.premCF) + '</td>' +
                        '<td style="padding:2px 8px;text-align:right;color:#1976D2;">' + fmtNum(p.premPV) + '</td>' +
                        '<td style="padding:2px 8px;text-align:right;color:#F44336;">' + fmtNum(p.protCF) + '</td>' +
                        '<td style="padding:2px 8px;text-align:right;color:#F44336;">' + fmtNum(p.protPV) + '</td>' +
                        '</tr>';
                });

                // Totals row
                tableRows +=
                    '<tr style="border-top:2px solid #333;font-weight:bold;background:#f0f0f0;">' +
                    '<td style="padding:4px 8px;">TOTAL</td>' +
                    '<td></td><td></td>' +
                    '<td style="padding:4px 8px;text-align:right;color:#1976D2;">' +
                        fmtNum(periods.reduce(function(s,p){ return s+p.premCF; }, 0)) + '</td>' +
                    '<td style="padding:4px 8px;text-align:right;color:#1976D2;font-weight:bold;">' +
                        fmtMoney(result.totalPremPV) + '</td>' +
                    '<td style="padding:4px 8px;text-align:right;color:#F44336;">' +
                        fmtNum(periods.reduce(function(s,p){ return s+p.protCF; }, 0)) + '</td>' +
                    '<td style="padding:4px 8px;text-align:right;color:#F44336;font-weight:bold;">' +
                        fmtMoney(result.totalProtPV) + '</td>' +
                    '</tr>';

                var tableHtml =
                    '<div style="display:flex;gap:16px;height:100%;">' +
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
                                backgroundColor: 'rgba(25,118,210,0.6)',
                                borderColor: '#1976D2',
                                borderWidth: 1
                            },
                            {
                                label: 'PV Protection ($K)',
                                data: protPVs,
                                backgroundColor: 'rgba(244,67,54,0.6)',
                                borderColor: '#F44336',
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
                                    borderColor: '#1565c0',
                                    backgroundColor: 'rgba(21,101,192,0.1)',
                                    fill: true,
                                    tension: 0.3,
                                    pointRadius: 5,
                                    pointBackgroundColor: '#1565c0',
                                    borderWidth: 2
                                },
                                {
                                    label: 'Trade Spread',
                                    data: Array(hcLabels.length).fill(tradeSpdVal),
                                    borderColor: '#c62828',
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
                    result = computePRSCashflows();
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
                var npvColor = result.npv >= 0 ? '#4CAF50' : '#F44336';
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
                    commitBtn = '<span style="color:#1565c0;font-size:10px;font-weight:600;margin-left:8px;">Trade Review</span>';
                } else if (isCloseOut) {
                    commitBtn = ctpySelected ?
                        '<button id="prs-commit-btn" onclick="commitPRSTrade()" ' +
                        'style="padding:4px 14px;background:#ef5350;color:white;border:none;border-radius:3px;' +
                        'cursor:pointer;font-weight:bold;font-size:11px;margin-left:8px;">Close Out</button>' :
                        '<span style="color:#aaa;font-size:10px;margin-left:8px;">(select ctpy to close out)</span>';
                } else if (ctpySelected) {
                    commitBtn = '<button id="prs-commit-btn" onclick="commitPRSTrade()" ' +
                    'style="padding:4px 14px;background:#4CAF50;color:white;border:none;border-radius:3px;' +
                    'cursor:pointer;font-weight:bold;font-size:11px;margin-left:8px;">Commit</button>';
                } else {
                    commitBtn = '<span style="color:#aaa;font-size:10px;margin-left:8px;">(select ctpy to commit)</span>';
                }

                var ctpyTag = ctpyDisplayName ?
                    '<span><b>Ctpy:</b> <span style="color:#1565C0;">' + ctpyDisplayName + '</span></span>' :
                    '<span style="color:#aaa;"><b>Ctpy:</b> none</span>';

                bar.innerHTML = [
                    ctpyTag,
                    '<span style="font-weight:bold;color:' + (result.isPayer ? '#1976D2' : '#E65100') + ';">' + dirLabel + '</span>',
                    '<span><b>Fair Spread:</b> <span style="font-size:13px;color:#1976D2;">' + result.fairSpreadBps.toFixed(1) + ' bps</span></span>',
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
"""
