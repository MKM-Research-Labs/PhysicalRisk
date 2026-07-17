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
        
