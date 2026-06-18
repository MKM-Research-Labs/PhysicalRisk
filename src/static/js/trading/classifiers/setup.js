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
            // Tab 9: Classifiers — GBM flood classifier management
            // ==============================================================
            var clSummary = null;
            var clSelectedGaugeId = null;
            var clFeatureChart = null;
            var clBatchPollTimer = null;
            var clDataVersion = null;  // tracks classifier state on disk

            function createClassifiersView() {
                var view = document.createElement('div');
                view.id = 'td-classifiers-view';
                view.style.cssText = 'flex:1;display:none;flex-direction:column;overflow:hidden;';

                // Top bar: Train All button + summary stats
                var topBar = document.createElement('div');
                topBar.id = 'cl-top-bar';
                topBar.style.cssText = 'padding:8px 16px;border-bottom:1px solid #eee;display:flex;align-items:center;gap:12px;background:#f5f7fa;flex-shrink:0;';
                topBar.innerHTML =
                    '<button id="cl-train-all-btn" style="padding:5px 14px;font-size:11px;font-weight:600;' +
                    'background:#1976d2;color:white;border:none;border-radius:3px;cursor:pointer;">' +
                    'Train All Untrained</button>' +
                    '<button id="cl-clear-all-btn" style="padding:5px 14px;font-size:11px;font-weight:600;' +
                    'background:#e53935;color:white;border:none;border-radius:3px;cursor:pointer;">' +
                    'Clear All</button>' +
                    '<span id="cl-summary-stats" style="flex:1;font-size:11px;color:#666;text-align:right;"></span>';
                view.appendChild(topBar);

                // Progress bar (hidden by default)
                var progressWrap = document.createElement('div');
                progressWrap.id = 'cl-progress-wrap';
                progressWrap.style.cssText = 'display:none;padding:6px 16px;border-bottom:1px solid #eee;background:#fafbfc;flex-shrink:0;';
                progressWrap.innerHTML =
                    '<div style="display:flex;align-items:center;gap:10px;">' +
                    '<div style="flex:1;height:18px;background:#e0e0e0;border-radius:9px;overflow:hidden;position:relative;">' +
                    '<div id="cl-progress-bar" style="height:100%;width:0%;background:linear-gradient(90deg,#1976d2,#42a5f5);' +
                    'border-radius:9px;transition:width 0.5s ease;"></div>' +
                    '</div>' +
                    '<span id="cl-progress-text" style="font-size:10px;color:#555;min-width:200px;"></span>' +
                    '</div>';
                view.appendChild(progressWrap);

                // Progress results table (hidden by default, shown during batch training)
                var progressResults = document.createElement('div');
                progressResults.id = 'cl-progress-results';
                progressResults.style.cssText = 'display:none;max-height:140px;overflow-y:auto;' +
                    'font-family:monospace;font-size:10px;line-height:1.6;padding:4px 16px;' +
                    'background:#fafbfc;border-bottom:1px solid #eee;flex-shrink:0;';
                view.appendChild(progressResults);

                // Main body: table (left) + detail (right)
                var body = document.createElement('div');
                body.style.cssText = 'flex:1;display:flex;overflow:hidden;';

                var tablePane = document.createElement('div');
                tablePane.id = 'cl-table-pane';
                tablePane.style.cssText = 'width:55%;overflow-y:auto;border-right:1px solid #eee;';

                var detailPane = document.createElement('div');
                detailPane.id = 'cl-detail-pane';
                detailPane.style.cssText = 'width:45%;overflow-y:auto;padding:16px;';
                detailPane.innerHTML =
                    '<div style="text-align:center;color:#999;font-size:12px;padding-top:40px;">' +
                    'Select a gauge to view classifier details</div>';

                body.appendChild(tablePane);
                body.appendChild(detailPane);
                view.appendChild(body);

                return view;
            }

            function loadClassifiersData() {
                var cfg = window.__BACKEND_CONFIG || {};
                var baseUrl = cfg.url || '';

                fetch(baseUrl + '/api/v1/trading/classifiers/summary', {mode: 'cors'})
                    .then(function(r) { return r.json(); })
                    .then(function(data) {
                        if (data.status === 'success') {
                            // Detect data change (port run or retrain in another session)
                            if (clDataVersion && data.data_version && clDataVersion !== data.data_version) {
                                console.info('[Classifiers] Data changed on disk — refreshing');
                            }
                            clDataVersion = data.data_version || null;
                            clSummary = data;
                            _clUpdateStatsBar(data);
                            _clRenderSummaryTable(data.gauges || []);
                            // Reselect previously selected gauge
                            if (clSelectedGaugeId) {
                                var g = (data.gauges || []).find(function(x) {
                                    return x.gauge_id === clSelectedGaugeId;
                                });
                                if (g) _clRenderDetail(g);
                            }
                        }
                    })
                    .catch(function(err) {
                        console.error('[Classifiers] Summary fetch error:', err);
                    });
            }

            function _clUpdateStatsBar(data) {
                var el = document.getElementById('cl-summary-stats');
                if (!el) return;
                var trained = data.num_trained || 0;
                var total = data.num_total || 0;
                var auc = data.avg_auc_roc;
                var txt = trained + '/' + total + ' trained';
                if (auc) txt += '  \u00b7  avg AUC ' + auc.toFixed(4);
                el.textContent = txt;
            }

            function clCleanupCharts() {
                if (clFeatureChart) {
                    clFeatureChart.destroy();
                    clFeatureChart = null;
                }
                if (clBatchPollTimer) {
                    clearInterval(clBatchPollTimer);
                    clBatchPollTimer = null;
                }
            }
