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

            var activeTab = 0;
            var isTradeReview = false;
            var isCloseOut = false;
            var closeOutSwapId = null;
            var closeOutIsPayer = true;

            function ensureCanvas() {
                // PRS tab replaces container innerHTML; restore canvas for other tabs
                var container = document.getElementById('hazard-chart-container');
                if (!document.getElementById('hazard-chart') || document.getElementById('hazard-chart').tagName !== 'CANVAS') {
                    container.innerHTML = '';
                    var canvas = document.createElement('canvas');
                    canvas.id = 'hazard-chart';
                    container.appendChild(canvas);
                }
            }

            // Resolve the active gauge id. Prefer the loaded hazard payload,
            // but fall back to the panel's dataset (set in showPanel) so the
            // Historical / Stress tabs still work when the hazard-curve fetch
            // failed and hazardData is null.
            function _ghcGaugeId() {
                if (hazardData && hazardData.gauge_id) return hazardData.gauge_id;
                var p = document.getElementById('hazard-curve-panel');
                return (p && p.dataset.gaugeId) || '';
            }

            function switchTab(idx) {
                activeTab = idx;
                var tabs = document.querySelectorAll('.hazard-tab');
                tabs.forEach(function(t, i) {
                    if (i === idx) {
                        t.style.background = '#1976d2';
                        t.style.color = Theme.value('panel');
                    } else {
                        t.style.background = '#f5f5f5';
                        t.style.color = '#555';
                    }
                });

                var controls = document.getElementById('hazard-controls');
                controls.style.display = idx === 0 ? 'block' : 'none';

                // Tabs 0-3 plot the hazard payload; Historical (4) and Stress
                // (5) fetch their own data and only need the gauge id, so they
                // render even when the hazard-curve fetch failed (hazardData null).
                if (!hazardData && idx !== 4 && idx !== 5) return;

                // Restore canvas for single-chart tabs (PRS and Historical manage their own layout)
                if (idx !== 0 && idx !== 4 && idx !== 5) ensureCanvas();

                if (idx === 0) renderPRSPricing();
                else if (idx === 1) renderHazardRate();
                else if (idx === 2) renderReturnPeriod();
                else if (idx === 3) renderFloodProbability();
                else if (idx === 4) renderHistorical();
                else if (idx === 5) renderStressTest();
            }

            // ================================================================
            // Show / Hide
            // ================================================================
            function showPanel(gaugeId) {
                console.log('[GaugeHazard] Opening panel for', gaugeId);
                var panel = createPanel();
                panel.dataset.gaugeId = gaugeId;
                document.getElementById('hazard-panel-title').textContent = 'Loading ' + gaugeId + '…';
                document.getElementById('hazard-status').textContent = 'Loading...';
                panel.style.display = 'flex';
                activeTab = 0;
                switchTab(0);
                loadHazardData(gaugeId);
            }

            function hidePanel() {
                if (hazardPanel) hazardPanel.style.display = 'none';
                if (currentChart) { currentChart.destroy(); currentChart = null; }
                if (typeof _cleanupHistCharts === 'function') _cleanupHistCharts();
                if (typeof _cleanupStressCharts === 'function') _cleanupStressCharts();

                // Re-enable all inputs
                var allIds = ['prs-direction', 'prs-counterparty', 'prs-trigger', 'prs-notional', 'prs-spread', 'prs-maturity', 'prs-maturity-info'];
                allIds.forEach(function(id) {
                    var el = document.getElementById(id);
                    if (el) { el.disabled = false; el.style.opacity = '1'; el.style.cursor = ''; }
                });

                // Remove maturity popup if visible
                var popup = document.getElementById('maturity-popup');
                if (popup) popup.remove();

                var wasFromBlotter = isTradeReview || isCloseOut;
                isTradeReview = false;
                isCloseOut = false;
                closeOutSwapId = null;
                hazardData = null;

                // If opened from blotter, return to Trading Desk
                if (wasFromBlotter && window.TradingDesk && window.TradingDesk.show) {
                    window.TradingDesk.show();
                }

                console.log('[GaugeHazard] Panel closed');
            }
