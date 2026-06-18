// Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
//
// This software is licensed by MKM Research Labs for non-commercial 
// research and educational use only. Any commercial use, including 
// but not limited to use in or for products or services offered for sale, 
// internal business operations intended for commercial advantage, or
// research and development conducted for a commercial entity, is expressly
// prohibited unless separately authorized in writing by MKM Research Labs.
//
// Use, reproduction, distribution, or modification of this code is subject to the
// terms and conditions of the license agreement provided with this software.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
// SOFTWARE.

            // ==============================================================
            // Tab 5: EOD (End of Day)
            // ==============================================================
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
                submitBar.style.cssText = 'padding:12px 16px;border-bottom:1px solid #eee;display:flex;align-items:center;gap:16px;background:#f5f7fa;';

                var today = new Date().toISOString().split('T')[0];
                submitBar.innerHTML =
                    '<button id="td-eod-submit-btn" onclick="tdSubmitEod()" ' +
                        'style="padding:8px 24px;font-size:13px;font-weight:700;background:#1976d2;color:white;border:none;border-radius:4px;cursor:pointer;">' +
                        'EOD Submit</button>' +
                    '<input type="date" id="td-eod-date" value="' + today + '" ' +
                        'style="padding:5px 8px;font-size:12px;border:1px solid #ccc;border-radius:4px;">' +
                    '<span id="td-eod-status" style="font-size:12px;color:#666;"></span>';
                view.appendChild(submitBar);

                // P&L summary cards
                var cards = document.createElement('div');
                cards.id = 'td-eod-cards';
                cards.style.cssText = 'padding:10px 16px;display:flex;gap:16px;border-bottom:1px solid #eee;flex-wrap:wrap;';
                view.appendChild(cards);

                // Two-column layout: history table + chart/attribution
                var body = document.createElement('div');
                body.style.cssText = 'flex:1;display:flex;overflow:hidden;';

                // Left: history table
                var histWrap = document.createElement('div');
                histWrap.id = 'td-eod-history-wrap';
                histWrap.style.cssText = 'width:340px;overflow-y:auto;border-right:1px solid #eee;padding:8px;';
                histWrap.innerHTML = '<div style="font-size:11px;font-weight:600;color:#555;padding:4px 8px;">EOD History</div>';
                body.appendChild(histWrap);

                // Right: chart + attribution
                var rightPane = document.createElement('div');
                rightPane.style.cssText = 'flex:1;display:flex;flex-direction:column;overflow:hidden;';

                var chartWrap = document.createElement('div');
                chartWrap.id = 'td-eod-chart-wrap';
                chartWrap.style.cssText = 'flex:1;padding:12px;min-height:200px;';
                rightPane.appendChild(chartWrap);

                var attrWrap = document.createElement('div');
                attrWrap.id = 'td-eod-attribution';
                attrWrap.style.cssText = 'height:180px;padding:8px 12px;border-top:1px solid #eee;overflow-y:auto;';
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
