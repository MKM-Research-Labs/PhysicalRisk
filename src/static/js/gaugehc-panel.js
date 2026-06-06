        (function() {
            var PANEL_W = '__PANEL_W__';
            var PANEL_H = '__PANEL_H__';
            var currentChart = null;
            var hazardPanel = null;
            var hazardData = null;
            var counterpartyData = [];

            // ==============================================================
            // Sub-module code (state vars + functions)
            // ==============================================================
__GHC_HAZARD_JS__
__GHC_RETURN_JS__
__GHC_PRS_JS__
__GHC_HISTORICAL_JS__
__GHC_STRESS_JS__

__GHC_CREATE_PANEL_JS__
__GHC_NAV_JS__
__GHC_DATA_JS__

            // ================================================================
            // Event listeners
            // ================================================================
            document.addEventListener('hazardCurveRequested', function(e) {
                if (e.detail && e.detail.gaugeId) showPanel(e.detail.gaugeId);
            });

            document.addEventListener('keydown', function(e) {
                if (e.key === 'Escape' && hazardPanel && hazardPanel.style.display !== 'none') {
                    hidePanel();
                }
            });

            window.GaugeHazardCurve = {
                show: showPanel,
                hide: hidePanel
            };

            console.log('Gauge hazard curve ready');
        })();
        
