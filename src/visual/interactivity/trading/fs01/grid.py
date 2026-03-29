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
Portfolio Risk Grid tab (Tab 3) for the Trading Desk panel.

Shows a heatmap table: gauges (rows) x maturity buckets (columns).
Cell values = net DV01 in GBP. Color-coded: blue = long, red = short.
Row and column totals included.
"""


def get_js() -> str:
    """Return JavaScript fragment for the portfolio risk grid tab."""
    return """
            // ==============================================================
            // Tab 3: Portfolio Risk Grid
            // ==============================================================
            var tdRiskGridData = null;

            function createRiskView() {
                var view = document.createElement('div');
                view.id = 'td-risk-view';
                view.style.cssText = 'flex:1;display:none;flex-direction:column;overflow:hidden;';

                // Title bar
                var titleBar = document.createElement('div');
                titleBar.style.cssText = 'padding:10px 16px;border-bottom:1px solid #eee;display:flex;justify-content:space-between;align-items:center;';
                titleBar.innerHTML =
                    '<span style="font-weight:600;font-size:13px;color:#333;">FS01 Risk Matrix \\u2014 Net FS01 by Gauge \\u00d7 Maturity</span>' +
                    '<span id="td-risk-total" style="font-size:13px;font-weight:700;"></span>';
                view.appendChild(titleBar);

                // Grid container
                var gridWrap = document.createElement('div');
                gridWrap.id = 'td-risk-grid-wrap';
                gridWrap.style.cssText = 'flex:1;overflow:auto;padding:12px 16px;';
                gridWrap.innerHTML = '<span style="color:#aaa;font-size:12px;">Loading risk grid\\u2026</span>';
                view.appendChild(gridWrap);

                return view;
            }

            function loadRiskData() {
                var url = getBaseUrl() + '/api/v1/trading/risk-grid';
                fetch(url, {mode: 'cors'})
                    .then(function(r) { return r.json(); })
                    .then(function(result) {
                        if (result.status === 'success') {
                            tdRiskGridData = result.grid;
                            renderRiskGrid();
                        }
                    })
                    .catch(function(err) {
                        console.error('[Risk] Fetch error:', err);
                    });
            }

            function riskCellColor(val) {
                if (val === 0) return '#fff';
                var abs = Math.abs(val);
                var intensity = Math.min(abs / 50000, 1);
                if (val > 0) {
                    // Long risk: blue
                    var r = Math.round(227 - intensity * 130);
                    var g = Math.round(242 - intensity * 80);
                    return 'rgb(' + r + ',' + g + ',255)';
                } else {
                    // Short risk: red
                    var g2 = Math.round(227 - intensity * 130);
                    var b = Math.round(242 - intensity * 130);
                    return 'rgb(255,' + g2 + ',' + b + ')';
                }
            }

            function renderRiskGrid() {
                var wrap = document.getElementById('td-risk-grid-wrap');
                if (!wrap || !tdRiskGridData) return;

                var grid = tdRiskGridData;
                var buckets = grid.buckets || [];
                var gauges = grid.gauges || [];
                var colTotals = grid.column_totals || {};

                // Total
                var totalEl = document.getElementById('td-risk-total');
                if (totalEl) {
                    var gt = grid.grand_total || 0;
                    var color = gt >= 0 ? '#1565c0' : '#c62828';
                    totalEl.innerHTML = 'Grand Total FS01: <span style="color:' + color + ';">' + fmtGBP(gt) + '</span>';
                }

                if (gauges.length === 0) {
                    wrap.innerHTML = '<div style="color:#aaa;font-size:12px;padding:20px;">No open trades with delta exposure.</div>';
                    return;
                }

                var html = '<table style="width:100%;border-collapse:collapse;font-size:11px;table-layout:fixed;">';

                // Header row
                // Build tenor tooltip: show maturity date range from trades
                var tenorTooltips = {};
                if (tdBlotterData) {
                    for (var ti = 0; ti < tdBlotterData.length; ti++) {
                        var trade = tdBlotterData[ti];
                        var tLabel = trade.tenor + 'Y';
                        if (!tenorTooltips[tLabel]) tenorTooltips[tLabel] = {min: trade.maturity, max: trade.maturity};
                        if (trade.maturity && trade.maturity < tenorTooltips[tLabel].min) tenorTooltips[tLabel].min = trade.maturity;
                        if (trade.maturity && trade.maturity > tenorTooltips[tLabel].max) tenorTooltips[tLabel].max = trade.maturity;
                    }
                }

                html += '<thead><tr style="background:#1565c0;color:white;">';
                html += '<th style="padding:6px 10px;text-align:left;position:sticky;top:0;z-index:1;background:#1565c0;white-space:nowrap;width:22%;">Gauge</th>';
                for (var b = 0; b < buckets.length; b++) {
                    var tt = tenorTooltips[buckets[b]];
                    var tip = buckets[b];
                    if (tt) {
                        var fmtShort = function(d) { if (!d) return ''; var p = d.split('-'); var m = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']; return m[parseInt(p[1])-1] + ' ' + p[0]; };
                        tip += ' (maturities: ' + fmtShort(tt.min) + ' \\u2013 ' + fmtShort(tt.max) + ')';
                    }
                    html += '<th style="padding:6px 8px;text-align:right;position:sticky;top:0;z-index:1;background:#1565c0;cursor:help;" title="' + tip + '">' + buckets[b] + '</th>';
                }
                html += '<th style="padding:6px 10px;text-align:right;position:sticky;top:0;z-index:1;background:#1565c0;font-weight:700;">Total</th>';
                html += '</tr></thead><tbody>';

                // Gauge rows
                for (var i = 0; i < gauges.length; i++) {
                    var g = gauges[i];
                    var displayName = g.gauge_name || g.gauge_id;
                    html += '<tr style="border-bottom:1px solid #eee;">';
                    html += '<td style="padding:5px 10px;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;cursor:pointer;color:#1565c0;text-decoration:underline;" title="Click to view blotter for ' + displayName + '" onclick="tdRiskGaugeClick(\\'' + g.gauge_id + '\\')">' + displayName + '</td>';

                    for (var b = 0; b < buckets.length; b++) {
                        var val = (g.cells && g.cells[buckets[b]]) || 0;
                        var bg = riskCellColor(val);
                        var display = val !== 0 ? fmtGBP(val) : '';
                        var cursor = val !== 0 ? 'cursor:pointer;' : '';
                        var click = val !== 0 ? ' onclick="tdRiskCellClick(\\'' + g.gauge_id + '\\',\\'' + buckets[b] + '\\')"' : '';
                        html += '<td style="padding:5px 8px;text-align:right;background:' + bg + ';' + cursor + '"' + click + ' title="Click to filter blotter">' + display + '</td>';
                    }

                    var totalColor = g.total >= 0 ? '#1565c0' : '#c62828';
                    html += '<td style="padding:5px 10px;text-align:right;font-weight:700;color:' + totalColor + ';">' + fmtGBP(g.total) + '</td>';
                    html += '</tr>';
                }

                // Column totals row
                html += '<tr style="background:#eceff1;border-top:2px solid #90a4ae;">';
                html += '<td style="padding:6px 10px;font-weight:700;">Total</td>';
                for (var b = 0; b < buckets.length; b++) {
                    var ct = colTotals[buckets[b]] || 0;
                    var ctColor = ct >= 0 ? '#1565c0' : '#c62828';
                    html += '<td style="padding:6px 8px;text-align:right;font-weight:700;color:' + ctColor + ';">' + fmtGBP(ct) + '</td>';
                }
                var gtColor = (grid.grand_total || 0) >= 0 ? '#1565c0' : '#c62828';
                html += '<td style="padding:6px 10px;text-align:right;font-weight:700;color:' + gtColor + ';">' + fmtGBP(grid.grand_total) + '</td>';
                html += '</tr></tbody></table>';

                wrap.innerHTML = html;
            }

            // Click gauge name → switch to blotter filtered by gauge
            window.tdRiskGaugeClick = function(gaugeId) {
                console.log('[FS01] Gauge click:', gaugeId);
                switchTab('blotter');
                setTimeout(function() {
                    if (window.tdApplyFilter) window.tdApplyFilter({gauge_id: gaugeId});
                }, 100);
            };

            // Click a risk cell → switch to blotter filtered by gauge + tenor
            window.tdRiskCellClick = function(gaugeId, bucket) {
                console.log('[FS01] Cell click:', gaugeId, bucket);
                var filters = {gauge_id: gaugeId};
                // Bucket is now the exact tenor label (e.g. "5Y", "3Y")
                if (bucket) filters.tenor = bucket;
                switchTab('blotter');
                // Small delay to let blotter tab render
                setTimeout(function() {
                    if (window.tdApplyFilter) window.tdApplyFilter(filters);
                }, 100);
            };
"""
