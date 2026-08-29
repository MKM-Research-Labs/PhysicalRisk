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

            window.tdCommitMarket = function() {
                var btn = document.getElementById('td-commit-btn');
                if (btn) { btn.disabled = true; btn.textContent = 'Committing...'; }

                var commitQueue = [];

                // Queue yield curve commit if dirty
                if (tdYieldDirty) {
                    commitQueue.push({type: 'yield', rates: Object.assign({}, tdYieldCurve)});
                    console.log('[Market] Queued yield curve commit:', JSON.stringify(tdYieldCurve));
                }

                // Queue dirty hazard curve commits
                var keys = Object.keys(tdHazardDirtyKeys);
                for (var dk = 0; dk < keys.length; dk++) {
                    if (tdHazardDirtyKeys[keys[dk]]) {
                        var parts = keys[dk].split(':');
                        var gid = parts[0];
                        var trig = parts[1];
                        var ts = (tdHazardTS[gid] && tdHazardTS[gid][trig]) || {};
                        commitQueue.push({type: 'hazard', gauge_id: gid, trigger: trig, rates: Object.assign({}, ts), key: keys[dk]});
                        console.log('[Market] Queued hazard commit: ' + gid + ' ' + trig + ' rates=' + JSON.stringify(ts));
                    }
                }

                console.log('[Market] Commit queue length: ' + commitQueue.length +
                    ', tdYieldDirty=' + tdYieldDirty +
                    ', tdHazardDirtyKeys=' + JSON.stringify(tdHazardDirtyKeys));

                if (commitQueue.length === 0) {
                    console.warn('[Market] Nothing to commit — no dirty curves detected');
                    if (window.showError) window.showError('No curve changes to commit. Edit the tenor inputs below the chart first.');
                    if (btn) { btn.textContent = 'Commit'; btn.disabled = false; }
                    return;
                }

                // Process commits sequentially — accumulate P&L impact
                var totalImpact = 0;
                var grossImpact = 0;
                var totalAffected = 0;
                var totalFs01 = 0;
                var commitIdx = 0;

                function processNextCommit() {
                    if (commitIdx >= commitQueue.length) {
                        var impactMsg = 'Committed ' + commitQueue.length + ' curve(s) — ' +
                            totalAffected + ' trades revalued, P&L impact: ' + fmtGBP(totalImpact);
                        console.log('[Market] COMMIT DONE: ' + impactMsg);
                        if (window.showSuccess) window.showSuccess(impactMsg);
                        if (btn) { btn.textContent = 'Commit'; btn.disabled = false; btn.style.background = 'var(--accent)'; }

                        // Reload market data to confirm curve saved, then switch to blotter
                        tdYieldDirty = false;
                        tdHazardDirtyKeys = {};
                        loadMarketData();
                        // Switch to blotter after a short delay so market data confirms save
                        setTimeout(function() {
                            if (typeof switchTab === 'function') switchTab('blotter');
                        }, 300);
                        if (window.refreshMainMapFS01) window.refreshMainMapFS01();
                        return;
                    }

                    var item = commitQueue[commitIdx++];
                    var url, body;
                    if (item.type === 'yield') {
                        url = getBaseUrl() + '/api/v1/trading/yield-curve/commit';
                        body = {rates: item.rates};
                    } else {
                        url = getBaseUrl() + '/api/v1/trading/hazard-term-structure/commit';
                        body = {gauge_id: item.gauge_id, trigger: item.trigger, rates: item.rates};
                    }

                    console.log('[Market] Sending commit ' + commitIdx + '/' + commitQueue.length + ': ' + item.type + ' ' + (item.gauge_id || '') + ' ' + (item.trigger || ''));
                    console.log('[Market] POST body: ' + JSON.stringify(body));

                    window.__mkmAdminFetch(url + '?_=' + Date.now(), {
                        method: 'POST',
                        body: JSON.stringify(body),
                        mode: 'cors',
                        cache: 'no-store'
                    })
                    .then(function(r) { return r.json(); })
                    .then(function(result) {
                        console.log('[Market] Commit response:', JSON.stringify(result));
                        if (result.status === 'success') {
                            totalImpact += result.total_pnl_impact || 0;
                            grossImpact += result.gross_pnl_impact || 0;
                            totalAffected = result.affected_trades || totalAffected;
                            totalFs01 = result.total_fs01 || totalFs01;
                            if (item.type === 'yield') {
                                tdYieldDirty = false;
                                tdYieldCurve = result.yield_curve || tdYieldCurve;
                            } else {
                                delete tdHazardDirtyKeys[item.key];
                            }
                        } else {
                            console.error('[Market] Commit failed:', result.message);
                            if (window.showError) window.showError(result.message || 'Commit failed');
                        }
                        processNextCommit();
                    })
                    .catch(function(err) {
                        console.error('[Market] Commit fetch error:', err);
                        if (window.showError) window.showError('Commit failed: ' + err.message);
                        if (btn) { btn.textContent = 'Commit'; btn.disabled = false; }
                    });
                }

                processNextCommit();
            };

            function tdCleanupMarketCharts() {
                if (tdMarketChart) {
                    tdMarketChart.destroy();
                    tdMarketChart = null;
                }
            }
