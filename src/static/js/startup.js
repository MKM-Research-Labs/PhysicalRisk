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

            window._tdPreBlotter      = null;
            window._tdPreMarket       = null;
            window._tdPreGauges       = null;
            window._tdPreStressStorms = null;
            window._tdPrePortStorms   = null;
            window._tdPreEodHistory   = null;
            window._tdPreYieldCurve   = null;
            window._preStorms         = null;
            window._prePropertyTS     = null;
            window._preGaugeHist      = null;
            window._preMortgages      = null;
            window._preCommercial     = null;
            window._preCommercialLoans = null;
            window._propertyNames     = {};  // propertyId → address lookup
                                              // (covers residential PROP-* and commercial CPROP-* ids)
            window._gaugeNames        = {};  // gaugeId → gauge name lookup

            // Global helper: canonical property display label "Address (PROP-xxx)"
            window.propertyDisplayName = function(propertyId, address) {
                var addr = address || (window._propertyNames || {})[propertyId] || '';
                return addr ? addr + ' (' + propertyId + ')' : propertyId;
            };

            // Global helper: canonical gauge display label "GaugeName (GAUGE-xxx)"
            window.gaugeDisplayName = function(gaugeId, name) {
                var gName = name || (window._gaugeNames || {})[gaugeId] || '';
                return gName ? gName + ' (' + gaugeId + ')' : gaugeId;
            };

            // Global helper: prompt for credentials and sign in via /auth/login (WP5).
            // Returns a Promise<boolean> — true if the session is now authenticated.
            window.__mkmLogin = function() {
                var u = window.prompt('Sign in to modify port data — username:');
                if (!u) return Promise.resolve(false);
                var p = window.prompt('Password for ' + u + ':');
                if (p === null) return Promise.resolve(false);
                return fetch('/auth/login', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    credentials: 'same-origin',
                    body: JSON.stringify({username: u, password: p})
                }).then(function(r) { return r.ok; });
            };

            // Global helper: perform a port-mutating fetch as the signed-in user (WP5).
            // The mutations (market state, yield/hazard curves, EOD, trade close, PRS
            // commit, classifier train/clear) are gated by @require("Func003", ...),
            // which checks the session user's capability — so this sends the session
            // cookie and, on 401 (not signed in), prompts to log in and retries once.
            // Same signature + Promise shape as before, so callers are unchanged;
            // rejects with 'cancelled' if the user dismisses the sign-in prompt.
            //   usage: window.__mkmAdminFetch(url, {method: 'POST', body: ...})
            window.__mkmAdminFetch = function(url, opts) {
                opts = opts || {};
                var headers = Object.assign({}, opts.headers || {});
                if (opts.body && !headers['Content-Type'] && !headers['content-type']) {
                    headers['Content-Type'] = 'application/json';
                }
                opts.headers = headers;
                opts.credentials = 'same-origin';
                return fetch(url, opts).then(function(resp) {
                    if (resp.status !== 401) return resp;
                    // Not signed in — prompt to log in, then retry the request once.
                    return window.__mkmLogin().then(function(ok) {
                        if (!ok) return Promise.reject(new Error('cancelled'));
                        return fetch(url, opts);
                    });
                });
            };

            // Flag read by trading/preloader.py — on window so it is accessible
            // from any IIFE scope (var declaration would be local to this IIFE)
            window._tdPreloadDone = false;

            // All datasets: [cacheKey, displayLabel, endpoint]
            var _startupDatasets = [
                ['_tdPreBlotter',      'Blotter trades',       '/api/v1/trading/blotter'],
                ['_tdPreMarket',       'Hazard curves',        '/api/v1/trading/market-state'],
                ['_tdPreGauges',       'Gauge locations',      '/api/v1/gauges'],
                ['_tdPreStressStorms', 'Stress scenarios',     '/api/v1/trading/stress/storms'],
                ['_tdPrePortStorms',   'Portfolio storms',     '/api/v1/trading/stress/portfolio-storms'],
                ['_tdPreEodHistory',   'EOD history',          '/api/v1/trading/eod/history'],
                ['_tdPreYieldCurve',   'Yield curve',          '/api/v1/trading/yield-curve'],
                ['_preStorms',         'Storm scenarios',      '/api/v1/propertyts/storms'],
                ['_prePropertyTS',     'Property flood TS',    '/api/v1/propertyts/summary'],
                ['_preGaugeHist',      'Gauge history',        '/api/v1/gauges/history/summary'],
                ['_preMortgages',      'Mortgages',            '/api/v1/rloans'],
                ['_prePropertyNames',  'Property names',       '/api/v1/properties'],
                ['_preCommercial',     'Commercial assets',    '/api/v1/commercial'],
                ['_preCommercialLoans', 'Commercial loans',    '/api/v1/commercial-loans'],
                ['_preFire',           'Fire model',           '/api/v1/fire'],
                ['_preSeismic',        'Seismic model',        '/api/v1/seismic'],
            ];

            function _startupDetail(key, data) {
                if (!data) return null;
                if (key === '_tdPreBlotter'      && data.trades)       return data.trades.length + ' trades';
                if (key === '_tdPreMarket'        && data.gauges)       return Object.keys(data.gauges).length + ' gauges';
                if (key === '_tdPreGauges'        && data.gauges)       return data.gauges.length + ' gauges';
                if (key === '_tdPreStressStorms'  && data.storms)       return data.storms.length + ' scenarios';
                if (key === '_tdPrePortStorms'    && data.storms)       return data.storms.length + ' storms';
                if (key === '_tdPreEodHistory'    && data.history)      return data.history.length + ' snapshots';
                if (key === '_tdPreYieldCurve'    && data.yield_curve)  return Object.keys(data.yield_curve).length + ' tenors';
                if (key === '_preStorms'          && data.storms)       return data.storms.length + ' storms';
                if (key === '_prePropertyTS'      && data.data && data.data.summary) return data.data.summary.properties_with_floods + ' flooded';
                if (key === '_preGaugeHist'       && data.count != null) return data.count + ' gauges';
                if (key === '_preMortgages'       && data.mortgages)     return data.mortgages.length + ' mortgages';
                if (key === '_prePropertyNames'   && data.properties)   return data.properties.length + ' properties';
                if (key === '_preCommercial'      && data.commercial_assets) return data.commercial_assets.length + ' assets';
                if (key === '_preCommercialLoans' && data.commercial_loans)  return data.commercial_loans.length + ' loans';
                if (key === '_preFire'            && data.assets)            return data.assets.length + ' assets';
                if (key === '_preSeismic'         && data.assets)            return data.assets.length + ' assets';
                return null;
            }

            function _runStartupPreload() {
                var baseUrl = (window.__BACKEND_CONFIG || {}).url || '';
                var popup = _createStartupPopup();
                var settled = 0;
                var total = _startupDatasets.length;

                // Prime storm control hours so FloodPoly and any other consumer reads
                // the same value the backend is using — single source of truth.
                fetch(baseUrl + '/api/v1/trading/control/params', {mode: 'cors'})
                    .then(function(r) { return r.json(); })
                    .then(function(resp) {
                        var hrs = (((resp || {}).params || {}).sections || {})
                                  .storm_generation && resp.params.sections.storm_generation.event_window_hours;
                        if (typeof hrs === 'number' && hrs > 0) {
                            window.__STORM_CONTROL_HOURS = hrs;
                        }
                    })
                    .catch(function() { /* fallback to 168 in consumers */ });

                _startupDatasets.forEach(function(ds) {
                    var key = ds[0], endpoint = ds[2];
                    fetch(baseUrl + endpoint, {mode: 'cors'})
                        .then(function(r) { return r.json(); })
                        .then(function(data) {
                            window[key] = data;
                            // Build gauge name lookup from /api/v1/gauges
                            if (key === '_tdPreGauges' && data && data.gauges) {
                                var gmap = {};
                                data.gauges.forEach(function(g) {
                                    var gid = g.gaugeId || '';
                                    var gname = g.name || '';
                                    if (gid && gname) gmap[gid] = gname;
                                });
                                window._gaugeNames = gmap;
                            }
                            // Build property name lookup from /api/v1/properties
                            if (key === '_prePropertyNames' && data && data.properties) {
                                var map = window._propertyNames || {};
                                data.properties.forEach(function(p) {
                                    var hdr = (p.PropertyHeader || {});
                                    var loc = hdr.Location || {};
                                    var pid = (hdr.Header || {}).PropertyID || '';
                                    var addr = ((loc.BuildingNumber || '') + ' ' + (loc.StreetName || '')).trim();
                                    if (pid) map[pid] = addr;
                                });
                                window._propertyNames = map;
                            }
                            // Same lookup for commercial assets (CPROP-* ids).
                            // BuildingName is preferred over BuildingNumber +
                            // StreetName for commercial since commercial
                            // tooltips use the building name.
                            if (key === '_preCommercial' && data && data.commercial_assets) {
                                var cmap = window._propertyNames || {};
                                data.commercial_assets.forEach(function(rec) {
                                    var ca = rec.CommercialAsset || {};
                                    var hdr = ca.Header || {};
                                    var loc = ca.Location || {};
                                    var pid = hdr.PropertyID || '';
                                    var name = loc.BuildingName
                                        || ((loc.BuildingNumber || '') + ' '
                                            + (loc.StreetName || '')).trim();
                                    if (pid) cmap[pid] = name;
                                });
                                window._propertyNames = cmap;
                            }
                            _startupMarkItem(key, true, _startupDetail(key, data));
                        })
                        .catch(function() {
                            _startupMarkItem(key, false, null);
                        })
                        .finally(function() {
                            settled++;
                            var bar = document.getElementById('startup-pre-bar');
                            if (bar) bar.style.width = Math.round(100 * settled / total) + '%';
                            if (settled === total) {
                                // Mark trading desk preload as done — it uses the same cache vars
                                window._tdPreloadDone = true;
                                // Shrink and move to bottom-left corner, stay for 10s
                                popup.style.transition = 'all 0.6s ease';
                                popup.style.top = 'auto';
                                popup.style.left = '16px';
                                popup.style.bottom = '16px';
                                popup.style.transform = 'none';
                                popup.style.minWidth = '280px';
                                popup.style.padding = '14px 18px';
                                popup.style.fontSize = '11px';
                                popup.style.opacity = '0.92';
                                popup.style.boxShadow = Theme.value('shadow-toast');
                                setTimeout(function() {
                                    popup.style.transition = 'opacity 0.8s ease';
                                    popup.style.opacity = '0';
                                    setTimeout(function() { popup.remove(); }, 800);
                                }, 10000);
                            }
                        });
                });
            }

            // Fire on DOMContentLoaded — the data download is gated behind
            // licence acceptance: Accept starts the preloader, Cancel aborts.
            function _startupEntry() {
                if (typeof _showLicenseGate === 'function') {
                    _showLicenseGate(_runStartupPreload, _onLicenseDeclined);
                } else {
                    _runStartupPreload();  // gate unavailable — fail open
                }
            }
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', _startupEntry);
            } else {
                // Already loaded (script injected late)
                _startupEntry();
            }
