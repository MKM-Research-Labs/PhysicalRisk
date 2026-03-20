# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial 
# research and educational use only. Any commercial use, including 
# but not limited to use in or for products or services offered for sale, 
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Trading Desk — Market tab: setup, data loading, and gauge list.

State variables, DOM construction (createMarketView), market state
fetching (loadMarketData), gauge list rendering, and mode switching.
"""


def get_js() -> str:
    """Return JS fragment for market tab setup and data loading."""
    return """
            // ==============================================================
            // Tab 2: Market-Making / Curves
            // ==============================================================
            var tdMarketData = null;
            var tdMarketChart = null;
            var tdSelectedGauge = null;
            var tdCurveMode = 'severe';
            var tdYieldCurve = {};
            var tdYieldDirty = false;
            var tdHazardTS = {};
            var tdHazardDirtyKeys = {};

            function createMarketView() {
                var view = document.createElement('div');
                view.id = 'td-market-view';
                view.style.cssText = 'flex:1;display:none;flex-direction:row;overflow:hidden;';

                // Left: gauge list
                var left = document.createElement('div');
                left.id = 'td-market-gauge-list';
                left.style.cssText = 'width:220px;overflow-y:auto;border-right:1px solid #eee;background:#fafafa;padding:8px;';
                left.innerHTML = '<div style="font-size:11px;font-weight:600;color:#555;padding:4px 8px;margin-bottom:4px;">Gauges</div>';

                // Right: mode selector + chart + inputs
                var right = document.createElement('div');
                right.style.cssText = 'flex:1;display:flex;flex-direction:column;';

                // Mode selector row
                var modeBar = document.createElement('div');
                modeBar.id = 'td-market-mode-bar';
                modeBar.style.cssText = 'padding:10px 16px;border-bottom:1px solid #eee;display:flex;align-items:center;gap:12px;';
                modeBar.innerHTML =
                    '<select id="td-curve-mode" onchange="tdCurveModeChanged(this.value)" style="padding:4px 8px;font-size:11px;border:1px solid #ccc;border-radius:4px;background:white;">' +
                        '<option value="yield">Yield Curve</option>' +
                        '<option value="alert">Hazard \\u2014 Alert</option>' +
                        '<option value="warning">Hazard \\u2014 Warning</option>' +
                        '<option value="severe">Hazard \\u2014 Severe</option>' +
                    '</select>' +
                    '<span id="td-curve-label" style="font-size:12px;font-weight:600;color:#333;"></span>' +
                    '<span style="flex:1;"></span>' +
                    '<div style="display:flex;border:1px solid #ddd;border-radius:4px;overflow:hidden;">' +
                        '<button id="td-newtrade-btn" onclick="tdMarketNewTrade()" style="padding:4px 14px;font-size:11px;border:none;cursor:pointer;font-weight:600;background:#f5f5f5;color:#555;">New Trade</button>' +
                        '<button id="td-history-btn" onclick="tdShowCurveHistory()" style="padding:4px 14px;font-size:11px;border:none;cursor:pointer;font-weight:600;background:#f5f5f5;color:#555;">History</button>' +
                        '<button id="td-plhist-btn" onclick="tdShowPLHistory()" style="padding:4px 14px;font-size:11px;border:none;cursor:pointer;font-weight:600;background:#f5f5f5;color:#555;">PL Hist</button>' +
                        '<button id="td-commit-btn" onclick="tdCommitMarket()" style="padding:4px 14px;font-size:11px;border:none;cursor:pointer;font-weight:600;background:#1976d2;color:white;">Commit</button>' +
                        '<button onclick="tdResetCurve()" style="padding:4px 14px;font-size:11px;border:none;cursor:pointer;font-weight:600;background:#f5f5f5;color:#555;">Reset</button>' +
                    '</div>';

                // Chart area
                var chartArea = document.createElement('div');
                chartArea.id = 'td-market-chart-area';
                chartArea.style.cssText = 'flex:1;padding:12px 16px;min-height:200px;';
                chartArea.innerHTML = '<canvas id="td-market-canvas" style="width:100%;height:100%;"></canvas>';

                // Tenor inputs row
                var inputRow = document.createElement('div');
                inputRow.id = 'td-market-inputs';
                inputRow.style.cssText = 'padding:8px 16px;border-top:1px solid #eee;background:#f9f9f9;';

                // Info bar
                var info = document.createElement('div');
                info.id = 'td-market-info';
                info.style.cssText = 'padding:6px 16px;border-top:1px solid #eee;font-size:10px;color:#888;background:#fafafa;';

                right.appendChild(modeBar);
                right.appendChild(chartArea);
                right.appendChild(inputRow);
                right.appendChild(info);

                view.appendChild(left);
                view.appendChild(right);
                return view;
            }

            function loadMarketData(gaugeHint) {
                var url = getBaseUrl() + '/api/v1/trading/market-state?_=' + Date.now();
                fetch(url, {mode: 'cors', cache: 'no-store'})
                    .then(function(r) { return r.json(); })
                    .then(function(result) {
                        if (result.status === 'success') {
                            tdMarketData = result.gauges || {};
                            var ms = result.market_state || {};
                            tdYieldCurve = ms.yield_curve || {};
                            tdHazardTS = ms.hazard_term_structure || {};
                            tdYieldDirty = false;
                            tdHazardDirtyKeys = {};

                            // Use gauge hint from blotter filter if provided
                            if (gaugeHint && tdMarketData[gaugeHint]) {
                                tdSelectedGauge = gaugeHint;
                            } else if (!tdSelectedGauge) {
                                // Auto-select: prefer most recently adjusted gauge, else first
                                var bestGauge = null;
                                var bestTime = '';
                                var gaugeIds = Object.keys(tdMarketData);
                                for (var gi = 0; gi < gaugeIds.length; gi++) {
                                    var gd = tdMarketData[gaugeIds[gi]];
                                    if (gd.is_adjusted && gd.adjusted_at && gd.adjusted_at > bestTime) {
                                        bestTime = gd.adjusted_at;
                                        bestGauge = gaugeIds[gi];
                                    }
                                }
                                tdSelectedGauge = bestGauge || gaugeIds[0] || null;
                            }

                            // Sync dropdown to default mode
                            var modeEl = document.getElementById('td-curve-mode');
                            if (modeEl) modeEl.value = tdCurveMode;

                            renderGaugeList();
                            renderCurveChart();
                        }
                    })
                    .catch(function(err) {
                        console.error('[Market] Fetch error:', err);
                    });
            }

            function tdExtractAreaName(name) {
                if (!name) return '';
                return name;
            }

            function renderGaugeList() {
                var list = document.getElementById('td-market-gauge-list');
                if (!list || !tdMarketData) return;

                var isYield = tdCurveMode === 'yield';
                var opacity = isYield ? '0.5' : '1';
                var header = isYield ? 'Gauges (select hazard mode)' : 'Gauges';
                var html = '<div style="font-size:11px;font-weight:600;color:#555;padding:4px 8px;margin-bottom:4px;opacity:' + opacity + ';">' + header + '</div>';
                var gaugeIds = Object.keys(tdMarketData).sort();

                for (var i = 0; i < gaugeIds.length; i++) {
                    var gid = gaugeIds[i];
                    var g = tdMarketData[gid];
                    var name = tdExtractAreaName(g.gauge_name || gid);
                    var isAdj = g.is_adjusted;
                    var isSelected = gid === tdSelectedGauge;
                    var bg = isSelected && !isYield ? '#e3f2fd' : (isAdj ? '#fff3e0' : 'transparent');
                    var dot = isAdj ? '<span style="color:#f57c00;margin-right:4px;">\\u25cf</span>' : '';
                    var cursor = isYield ? 'default' : 'pointer';

                    html += '<div onclick="tdSelectGauge(\\'' + gid + '\\')" style="padding:5px 8px;cursor:' + cursor + ';background:' + bg + ';border-radius:4px;margin-bottom:2px;font-size:11px;opacity:' + opacity + ';">' +
                        dot + name + '</div>';
                }

                list.innerHTML = html;
            }

            window.tdSelectGauge = function(gaugeId) {
                if (tdCurveMode === 'yield') return;
                tdSelectedGauge = gaugeId;
                renderGaugeList();
                renderCurveChart();
            };

            window.tdCurveModeChanged = function(mode) {
                tdCurveMode = mode;
                renderGaugeList();
                renderCurveChart();
            };

            function renderCurveChart() {
                var chartArea = document.getElementById('td-market-chart-area');
                var inputRow = document.getElementById('td-market-inputs');
                var label = document.getElementById('td-curve-label');
                var info = document.getElementById('td-market-info');
                if (!chartArea) return;

                if (tdCurveMode === 'yield') {
                    renderYieldCurve(chartArea, inputRow, label, info);
                } else {
                    if (!tdSelectedGauge) {
                        // Clear chart area with prompt
                        if (tdMarketChart) { tdMarketChart.destroy(); tdMarketChart = null; }
                        chartArea.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:100%;"><span style="color:#aaa;font-size:13px;">Select a gauge from the list</span></div>';
                        if (inputRow) inputRow.innerHTML = '';
                        if (label) label.textContent = '';
                        if (info) info.innerHTML = '';
                        return;
                    }
                    renderHazardCurve(chartArea, inputRow, label, info);
                }
            }
"""
