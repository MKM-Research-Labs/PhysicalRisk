
            // ================================================================
            // Yield curve (fetched from market state)
            // ================================================================
            var prsYieldCurve = {'1': 0.035, '2': 0.04, '3': 0.043, '4': 0.045, '5': 0.04, '6': 0.04};

            function interpolateYieldRate(curve, t) {
                if (!curve || Object.keys(curve).length === 0) return 0.04;
                var keys = Object.keys(curve).map(Number).sort(function(a,b){return a-b;});
                if (t <= keys[0]) return curve[String(keys[0])];
                if (t >= keys[keys.length-1]) return curve[String(keys[keys.length-1])];
                for (var i = 0; i < keys.length - 1; i++) {
                    if (t >= keys[i] && t <= keys[i+1]) {
                        var frac = (t - keys[i]) / (keys[i+1] - keys[i]);
                        return curve[String(keys[i])] * (1-frac) + curve[String(keys[i+1])] * frac;
                    }
                }
                return curve[String(keys[keys.length-1])];
            }

            function fetchYieldCurve() {
                var cfg = window.__BACKEND_CONFIG || {};
                var baseUrl = cfg.url || '';
                fetch(baseUrl + '/api/v1/trading/yield-curve?_=' + Date.now(), {mode: 'cors', cache: 'no-store'})
                    .then(function(r) { return r.json(); })
                    .then(function(data) {
                        if (data.yield_curve) prsYieldCurve = data.yield_curve;
                    })
                    .catch(function() {});
            }
            fetchYieldCurve();

            // ================================================================
            // Maturity date convention (JS port of models/schedule/maturity.py)
            // Roll dates: last Friday of Feb and Aug
            // Maturity months: May (Feb roll) and Nov (Aug roll)
            // ================================================================
            function lastFridayOfMonth(year, month) {
                // month is 1-based
                var lastDay = new Date(year, month, 0).getDate();
                var d = new Date(year, month - 1, lastDay);
                var offset = (d.getDay() + 2) % 7; // days back to Friday (5)
                // getDay(): 0=Sun..6=Sat, Friday=5
                // offset = (getDay() - 5 + 7) % 7
                offset = (d.getDay() - 5 + 7) % 7;
                d.setDate(lastDay - offset);
                return d;
            }

            function currentRollDate(refDate) {
                if (!refDate) refDate = new Date();
                var month = refDate.getMonth() + 1; // 1-based
                var year = refDate.getFullYear();
                if (month >= 2 && month <= 7) {
                    return lastFridayOfMonth(year, 2);
                } else if (month >= 8) {
                    return lastFridayOfMonth(year, 8);
                } else {
                    // January: use previous year's Aug roll
                    return lastFridayOfMonth(year - 1, 8);
                }
            }

            function computeMaturityDate(tenorYears, refDate) {
                var roll = currentRollDate(refDate);
                var rollMonth = roll.getMonth() + 1; // 1-based
                var matMonth = rollMonth + 3; // Feb->May, Aug->Nov
                var matYear = roll.getFullYear() + tenorYears;
                if (matMonth > 12) { matMonth -= 12; matYear += 1; }
                return lastFridayOfMonth(matYear, matMonth);
            }

            function formatMaturityDate(d) {
                var months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
                return d.getDate() + ' ' + months[d.getMonth()] + ' ' + d.getFullYear();
            }

            function formatMaturityShort(d) {
                var months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
                return months[d.getMonth()] + '-' + String(d.getFullYear()).slice(2);
            }

            function maturityDateToStr(d) {
                // YYYY-MM-DD for backend
                var mm = String(d.getMonth() + 1).padStart(2, '0');
                var dd = String(d.getDate()).padStart(2, '0');
                return d.getFullYear() + '-' + mm + '-' + dd;
            }

            // ================================================================
            // Survival probability — log-linear interpolation
            // ================================================================
            function interpolateSurvival(ts, t) {
                // Log-linear interpolation of survival probability at time t
                // ts = [{year:1, survival_prob:0.85}, {year:2, ...}, ...]
                if (t <= 0) return 1.0;
                if (ts.length === 0) return 1.0;

                // Find bracketing points
                var prevYear = 0, prevS = 1.0;
                for (var i = 0; i < ts.length; i++) {
                    var curYear = ts[i].year;
                    var curS = ts[i].survival_prob;
                    if (t <= curYear) {
                        // Interpolate between prevYear and curYear
                        if (curYear === prevYear) return curS;
                        var frac = (t - prevYear) / (curYear - prevYear);
                        // Log-linear: ln(S(t)) = (1-frac)*ln(S_prev) + frac*ln(S_cur)
                        var lnPrev = prevS > 0 ? Math.log(prevS) : -20;
                        var lnCur = curS > 0 ? Math.log(curS) : -20;
                        return Math.exp((1 - frac) * lnPrev + frac * lnCur);
                    }
                    prevYear = curYear;
                    prevS = curS;
                }
                // Extrapolate beyond last point using constant hazard
                var lastYear = ts[ts.length - 1].year;
                var lastS = ts[ts.length - 1].survival_prob;
                if (lastS <= 0 || lastYear <= 0) return 0;
                var lambda = -Math.log(lastS) / lastYear;
                return Math.exp(-lambda * t);
            }
