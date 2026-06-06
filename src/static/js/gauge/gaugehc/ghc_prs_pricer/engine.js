
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
