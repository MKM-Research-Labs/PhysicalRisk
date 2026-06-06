
            // ==============================================================
            // New Trade — navigate to PRS pricing screen for selected gauge
            // ==============================================================
            window.tdMarketNewTrade = function() {
                var gaugeId = tdSelectedGauge;
                if (!gaugeId) {
                    if (window.showError) window.showError('Select a gauge first');
                    return;
                }
                if (window.TradingDesk && window.TradingDesk.hide) window.TradingDesk.hide();
                if (window.GaugeHazardCurve && window.GaugeHazardCurve.show) {
                    window.GaugeHazardCurve.show(gaugeId);
                } else if (window.viewHazardCurve) {
                    window.viewHazardCurve(gaugeId);
                } else {
                    if (window.showError) window.showError('PRS pricer not available');
                }
            };
