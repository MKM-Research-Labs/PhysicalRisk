
            // ==============================================================
            // Show / hide
            // ==============================================================
            function showPanel() {
                console.log('[TradingDesk] Opening panel');
                if (window._tdPreloadDone) {
                    // Data already cached — open immediately
                    _tdOpenPanel();
                } else {
                    // First open: preload all datasets with progress popup
                    _tdRunPreload(function() {
                        _tdOpenPanel();
                    });
                }
            }

            function _tdOpenPanel() {
                createPanel();
                tdPanel.style.display = 'flex';
                tdActiveTab = 'blotter';
                switchTab('blotter');
            }

            function hidePanel() {
                if (tdPanel) tdPanel.style.display = 'none';
                console.log('[TradingDesk] Panel closed');
                // Cleanup
                if (typeof tdCleanupMap === 'function') tdCleanupMap();
                if (typeof tdCleanupMarketCharts === 'function') tdCleanupMarketCharts();
                if (typeof tdCleanupEodCharts === 'function') tdCleanupEodCharts();
                if (typeof tdCleanupCurveCharts === 'function') tdCleanupCurveCharts();
                if (typeof tdCleanupStressCharts === 'function') tdCleanupStressCharts();
                if (typeof psCleanupCharts === 'function') psCleanupCharts();
                if (typeof clCleanupCharts === 'function') clCleanupCharts();
            }

            // Global entry points
            window.TradingDesk = { show: showPanel, hide: hidePanel };
            window.showTradingDesk = showPanel;

            // Add map control button on load
            addMapControl();
