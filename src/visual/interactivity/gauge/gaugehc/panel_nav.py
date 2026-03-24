# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""Panel tab navigation — state vars, switchTab(), showPanel(), hidePanel()."""


def get_nav_js() -> str:
    """Return JS for tab switching and panel show/hide."""
    return """
            // ================================================================
            // Tab switching
            // ================================================================
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

            function switchTab(idx) {
                activeTab = idx;
                var tabs = document.querySelectorAll('.hazard-tab');
                tabs.forEach(function(t, i) {
                    if (i === idx) {
                        t.style.background = '#1976d2';
                        t.style.color = 'white';
                    } else {
                        t.style.background = '#f5f5f5';
                        t.style.color = '#555';
                    }
                });

                var controls = document.getElementById('hazard-controls');
                controls.style.display = idx === 0 ? 'block' : 'none';

                if (!hazardData) return;

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
                document.getElementById('hazard-panel-title').textContent = 'Loading ' + gaugeId + '\u2026';
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
"""
