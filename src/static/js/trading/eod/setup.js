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

            var tdEodHistory = null;
            var tdEodPnlSeries = null;
            var tdEodChart = null;

            function createEodView() {
                var view = document.createElement('div');
                view.id = 'td-eod-view';
                view.style.cssText = 'flex:1;display:none;flex-direction:column;overflow:hidden;';

                // Submit bar
                var submitBar = document.createElement('div');
                submitBar.id = 'td-eod-submit-bar';
                submitBar.style.cssText = 'padding:var(--space-6) var(--space-8);border-bottom:1px solid var(--line-soft);display:flex;align-items:center;gap:var(--space-8);background:var(--header-from);';

                var today = new Date().toISOString().split('T')[0];
                submitBar.innerHTML =
                    '<button id="td-eod-submit-btn" onclick="tdSubmitEod()" ' +
                        'style="padding:var(--space-4) var(--space-10);font-size:var(--size-md);font-weight:700;background:var(--accent);color:var(--inverse);border:none;border-radius:var(--radius-4);cursor:pointer;">' +
                        'EOD Submit</button>' +
                    '<input type="date" id="td-eod-date" value="' + today + '" ' +
                        'style="padding:var(--space-3) var(--space-4);font-size:var(--size-sm);border:1px solid var(--divider);border-radius:var(--radius-4);">' +
                    '<span id="td-eod-status" style="font-size:var(--size-sm);color:var(--text-3);"></span>';
                view.appendChild(submitBar);

                // P&L summary cards
                var cards = document.createElement('div');
                cards.id = 'td-eod-cards';
                cards.style.cssText = 'padding:var(--space-5) var(--space-8);display:flex;gap:var(--space-8);border-bottom:1px solid var(--line-soft);flex-wrap:wrap;';
                view.appendChild(cards);

                // Two-column layout: history table + chart/attribution
                var body = document.createElement('div');
                body.style.cssText = 'flex:1;display:flex;overflow:hidden;';

                // Left: history table
                var histWrap = document.createElement('div');
                histWrap.id = 'td-eod-history-wrap';
                histWrap.style.cssText = 'width:340px;overflow-y:auto;border-right:1px solid var(--line-soft);padding:var(--space-4);';
                histWrap.innerHTML = '<div style="font-size:var(--size-xs);font-weight:600;color:var(--text-2);padding:var(--space-2) var(--space-4);">EOD History</div>';
                body.appendChild(histWrap);

                // Right: chart + attribution
                var rightPane = document.createElement('div');
                rightPane.style.cssText = 'flex:1;display:flex;flex-direction:column;overflow:hidden;';

                var chartWrap = document.createElement('div');
                chartWrap.id = 'td-eod-chart-wrap';
                chartWrap.style.cssText = 'flex:1;padding:var(--space-6);min-height:200px;';
                rightPane.appendChild(chartWrap);

                var attrWrap = document.createElement('div');
                attrWrap.id = 'td-eod-attribution';
                attrWrap.style.cssText = 'height:180px;padding:var(--space-4) var(--space-6);border-top:1px solid var(--line-soft);overflow-y:auto;';
                rightPane.appendChild(attrWrap);

                body.appendChild(rightPane);
                view.appendChild(body);
                return view;
            }

            var tdLiveSummary = null;

            function loadEodData() {
                // Load history, P&L series, and live blotter summary in parallel
                var base = getBaseUrl();
                Promise.all([
                    fetch(base + '/api/v1/trading/eod/history', {mode: 'cors'}).then(function(r) { return r.json(); }),
                    fetch(base + '/api/v1/trading/pnl-series', {mode: 'cors'}).then(function(r) { return r.json(); }),
                    fetch(base + '/api/v1/trading/blotter', {mode: 'cors'}).then(function(r) { return r.json(); })
                ]).then(function(results) {
                    if (results[0].status === 'success') {
                        tdEodHistory = results[0].history || [];
                    }
                    if (results[1].status === 'success') {
                        tdEodPnlSeries = results[1].series || [];
                    }
                    if (results[2].status === 'success') {
                        tdLiveSummary = results[2].summary || {};
                        // Store blotter trades for attribution (if blotter tab not yet loaded)
                        if (!tdBlotterData) tdBlotterData = results[2].trades || [];
                    }
                    renderEodCards();
                    renderEodHistory();
                    renderEodChart();
                    renderEodAttribution();
                }).catch(function(err) {
                    console.error('[EOD] Fetch error:', err);
                });
            }
