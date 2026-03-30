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

"""Property hazard curve — PRS analytical pricer (survival interpolation + cashflows)."""


def get_js():
    """Return JS fragment for PRS analytical pricer."""
    return """
            // ================================================================
            // Yield curve (fetched from market state)
            // ================================================================
            var phcYieldCurve = {'1': 0.035, '2': 0.04, '3': 0.043, '4': 0.045, '5': 0.04, '6': 0.04};

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

            (function() {
                var cfg = window.__BACKEND_CONFIG || {};
                var baseUrl = cfg.url || '';
                if (!baseUrl) return;
                fetch(baseUrl + '/api/v1/trading/yield-curve', {mode: 'cors'})
                    .then(function(r) { return r.json(); })
                    .then(function(data) {
                        if (data.yield_curve) phcYieldCurve = data.yield_curve;
                    })
                    .catch(function() {});
            })();

            // ================================================================
            // PRS Analytical Pricer — semi-annual cashflow computation
            // ================================================================
            function interpolateSurvival(survivalArr, tenorArr, t) {
                // Log-linear interpolation of survival probability at time t
                if (t <= 0) return 1.0;
                if (!survivalArr || survivalArr.length === 0) return 1.0;

                var prevYear = 0, prevS = 1.0;
                for (var i = 0; i < survivalArr.length; i++) {
                    var curYear = tenorArr[i];
                    var curS = survivalArr[i];
                    if (t <= curYear) {
                        if (curYear === prevYear) return curS;
                        var frac = (t - prevYear) / (curYear - prevYear);
                        var lnPrev = prevS > 0 ? Math.log(prevS) : -20;
                        var lnCur = curS > 0 ? Math.log(curS) : -20;
                        return Math.exp((1 - frac) * lnPrev + frac * lnCur);
                    }
                    prevYear = curYear;
                    prevS = curS;
                }
                // Extrapolate beyond last point
                var lastYear = tenorArr[tenorArr.length - 1];
                var lastS = survivalArr[survivalArr.length - 1];
                if (lastS <= 0 || lastYear <= 0) return 0;
                var lambda = -Math.log(lastS) / lastYear;
                return Math.exp(-lambda * t);
            }

            function computePropertyPRSCashflows() {
                var triggerKey = 'severe';
                var notionalStr = document.getElementById('phc-notional').value.replace(/,/g, '');
                var notional = parseFloat(notionalStr) || 10000000;
                var tenor = parseInt(document.getElementById('phc-tenor').value) || 5;
                var spreadBps = parseFloat(document.getElementById('phc-spread').value) || 100;
                var spread = spreadBps / 10000;
                var recovery = 0.0;

                var ts = phcData.term_structure || {};
                var tsData = ts[triggerKey] || {};
                var tenors = ts.tenors || [];
                var survivalArr = tsData.survival || [];
                var propSpreadArr = tsData.prs_spread_bps || [];

                // Build semi-annual schedule using property survival
                var nPeriods = tenor * 2;
                var dt = 0.5;
                var periods = [];
                var totalPremPV = 0, totalProtPV = 0, riskyAnnuity = 0;

                for (var i = 1; i <= nPeriods; i++) {
                    var t = i * dt;
                    var tPrev = (i - 1) * dt;
                    var S_t = interpolateSurvival(survivalArr, tenors, t);
                    var S_prev = interpolateSurvival(survivalArr, tenors, tPrev);
                    var rf = interpolateYieldRate(phcYieldCurve, t);
                    var df = Math.exp(-rf * t);

                    var premCF = spread * dt * notional * S_t;
                    var premPV = premCF * df;
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
                var npv = totalProtPV - totalPremPV;

                // Compute gauge spreads and basis at selected tenor
                var nearestGauges = phcData.nearest_gauges || [];
                var tenorIdx = tenors.indexOf(tenor);
                if (tenorIdx < 0) {
                    // Find closest tenor
                    tenorIdx = 0;
                    for (var j = 1; j < tenors.length; j++) {
                        if (Math.abs(tenors[j] - tenor) < Math.abs(tenors[tenorIdx] - tenor)) tenorIdx = j;
                    }
                }

                var propSpreadAtTenor = propSpreadArr[tenorIdx] || 0;

                var gaugeComponents = nearestGauges.slice(0, 3).map(function(ng) {
                    var basisData = (ng.basis_bps || {})[triggerKey] || {};
                    var basisVals = basisData.values || [];
                    var basisAtTenor = basisVals[tenorIdx] || 0;
                    var gaugeSpreadAtTenor = propSpreadAtTenor + basisAtTenor;
                    return {
                        gauge_id: ng.gauge_id,
                        distance_km: ng.distance_km || 0,
                        gauge_elevation_m: ng.gauge_elevation_m || 0,
                        gauge_spread: gaugeSpreadAtTenor,
                        basis: basisAtTenor,
                        property_flood_count: ng.property_flood_count || 0,
                        gauge_flood_count: ng.gauge_flood_count || 0,
                        flood_transmission_rate: ng.flood_transmission_rate || 0
                    };
                });

                var avgBasis = 0;
                if (gaugeComponents.length > 0) {
                    var sumBasis = gaugeComponents.reduce(function(s, g) { return s + g.basis; }, 0);
                    avgBasis = sumBasis / gaugeComponents.length;
                }

                return {
                    periods: periods,
                    totalPremPV: totalPremPV,
                    totalProtPV: totalProtPV,
                    riskyAnnuity: riskyAnnuity,
                    fairSpread: fairSpread,
                    fairSpreadBps: fairSpread * 10000,
                    npv: npv,
                    notional: notional,
                    tenor: tenor,
                    spread: spread,
                    spreadBps: spreadBps,
                    yieldCurve: phcYieldCurve,
                    recovery: recovery,
                    triggerKey: triggerKey,
                    propSpreadAtTenor: propSpreadAtTenor,
                    gaugeComponents: gaugeComponents,
                    avgBasis: avgBasis
                };
            }
"""
