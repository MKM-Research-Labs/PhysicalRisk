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

            function computePRSCashflows() {
                // The PRS inputs (prs-trigger / prs-notional) are built by
                // buildPRSControls() after the async hazard load. If they — or
                // hazardData — aren't ready yet, bail rather than dereferencing
                // null; the caller re-renders once controls exist.
                var triggerEl = document.getElementById('prs-trigger');
                var notionalEl = document.getElementById('prs-notional');
                if (!triggerEl || !notionalEl || !hazardData) return null;
                var trigger = triggerEl.value;
                var notionalStr = notionalEl.value.replace(/,/g, '');
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
