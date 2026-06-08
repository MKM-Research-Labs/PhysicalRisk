        (function() {
            var PANEL_W = '__PANEL_W__';
            var PANEL_H = '__PANEL_H__';
            var currentChart = null;
            var phcPanel = null;
            var phcData = null;
            var counterpartyData = [];

            // ==============================================================
            // Sub-module code (state vars + functions)
            // ==============================================================
__PHC_HAZARD_JS__
__PHC_TERM_JS__
__PHC_PRS_JS__
__PHC_BASIS_JS__
__PHC_BASIS_WATERFALL_JS__
__PHC_PERIL_OUTCOMES_JS__
__PHC_BASIS_GAUGE_JS__
__PHC_BASIS_SHE_JS__
__PHC_BASIS_SHD_JS__
__PHC_BASIS_PROPERTY_JS__

            // ==============================================================
            // Panel creation
            // ==============================================================
__PHC_PANEL_CREATE_JS__

            // ==============================================================
            // Tab switching
            // ==============================================================
__PHC_PANEL_TABS_JS__

            // ==============================================================
            // Show / Hide
            // ==============================================================
            function showPanel(propertyId) {
                console.log('[PropertyHazard] Opening panel for', propertyId);
                // Both panels are centered modals at z-index 2000, so they
                // overlap and intercept each other's clicks if both are open.
                // Close the loan pricer before showing this panel.
                if (window.LoanPricerPanel && window.LoanPricerPanel.hide) {
                    window.LoanPricerPanel.hide();
                }
                var panel = createPanel();
                panel.dataset.propertyId = propertyId;
                var isCommercial = (typeof propertyId === 'string'
                                     && propertyId.indexOf('CPROP-') === 0);
                var titleLabel = isCommercial
                    ? 'Commercial PRS Pricer: '
                    : 'PRS Pricer: ';
                document.getElementById('phc-panel-title').textContent =
                    titleLabel + window.propertyDisplayName(propertyId);
                document.getElementById('phc-status').textContent = 'Loading...';
                panel.style.display = 'flex';

                activeTab = 0;
                switchTab(0);
                loadData(propertyId);
            }

            function hidePanel() {
                if (phcPanel) phcPanel.style.display = 'none';
                if (currentChart) { currentChart.destroy(); currentChart = null; }
                if (basisGaugeChart) { basisGaugeChart.destroy(); basisGaugeChart = null; }
                if (basisSHEChart) { basisSHEChart.destroy(); basisSHEChart = null; }
                if (basisSHDChart) { basisSHDChart.destroy(); basisSHDChart = null; }
                if (basisPropertyChart) { basisPropertyChart.destroy(); basisPropertyChart = null; }
                if (_basisWaterfallChart) { _basisWaterfallChart.destroy(); _basisWaterfallChart = null; }
                if (_perilOutcomesChart) { _perilOutcomesChart.destroy(); _perilOutcomesChart = null; }
                var subBar = document.getElementById('phc-basis-subtab-bar');
                if (subBar) subBar.remove();
                basisSelectedStorm = null;
                basisActiveSubTab = 0;
                phcData = null;
                console.log('[PropertyHazard] Panel closed');
            }

            // ==============================================================
            // Data loading
            // ==============================================================
__PHC_PANEL_DATA_JS__

            // ==============================================================
            // Basis summary strip — storm journey at a glance
            // ==============================================================
__PHC_PANEL_BASIS_STRIP_JS__

            // ==============================================================
            // Event listeners
            // ==============================================================
            document.addEventListener('propertyHazardRequested', function(e) {
                if (e.detail && e.detail.propertyId) showPanel(e.detail.propertyId);
            });

            document.addEventListener('keydown', function(e) {
                if (e.key === 'Escape' && phcPanel && phcPanel.style.display !== 'none') {
                    hidePanel();
                }
            });

            window.PropertyHazardCurvePanel = {
                show: showPanel,
                hide: hidePanel
            };

            console.log('Property hazard curve panel ready');
        })();
        
