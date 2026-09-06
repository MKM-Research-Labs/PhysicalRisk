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

            function showPanel() {
                console.log('[TradingDesk] Opening panel');
                // Fresh open: forget any tab clicked during a previous one.
                window._tdTabClickedDuringOpen = null;
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
                // Opening the desk shows the blotter. The exception is a tab
                // the user clicked while this open's preload was still in
                // flight — switching them back when the callback lands
                // discards a deliberate choice.
                //
                // Scoped to this open cycle on purpose: tdActiveTab persists
                // for the life of the page, so keying off it made the desk
                // reopen on whatever tab was last used, which is a different
                // behaviour from the one this fixes.
                var target = window._tdTabClickedDuringOpen || 'blotter';
                window._tdTabClickedDuringOpen = null;
                tdActiveTab = target;
                switchTab(target);
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
