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

"""Port Stress — Gauge P&L sub-tab."""


def get_js() -> str:
    """Return JavaScript fragment for the Gauge P&L sub-tab."""
    return """
            // ---- Port Stress: Gauge P&L Sub-Tab ----
            function _psRenderGaugePnlTab(result) {
                var content = document.getElementById('ps-content');
                if (!content) return;

                var gaugesWithTrades = (result.gauges || []).filter(function(g) {
                    return g.num_trades > 0;
                });

                if (gaugesWithTrades.length === 0) {
                    content.innerHTML =
                        '<div style="padding:40px;text-align:center;color:#999;">No open trades in portfolio for this storm.</div>';
                    return;
                }

                // Build dropdown
                var dropdownHtml =
                    '<div style="padding:8px 12px;border-bottom:1px solid #eee;display:flex;align-items:center;gap:10px;background:#f5f7fa;flex-shrink:0;">' +
                    '<span style="font-size:11px;font-weight:600;color:#333;">Gauge:</span>' +
                    '<select id="ps-gaugepnl-sel" style="padding:4px 8px;font-size:11px;border:1px solid #ccc;border-radius:3px;min-width:300px;">';

                gaugesWithTrades.forEach(function(g) {
                    var thresholdBadge = g.threshold !== 'clean' ? ' [' + g.threshold.toUpperCase() + ']' : '';
                    var selected = (g.gauge_id === psSelectedGaugeId) ? ' selected' : '';
                    dropdownHtml += '<option value="' + g.gauge_id + '"' + selected + '>' +
                        g.gauge_name + thresholdBadge +
                        ' \u2014 P=' + g.p_flood_pct.toFixed(1) + '%' +
                        ' | ' + g.num_trades + ' trade' + (g.num_trades !== 1 ? 's' : '') +
                        '</option>';
                });
                dropdownHtml +=
                    '</select>' +
                    '</div>' +
                    '<div id="ps-gauge-table-area" style="flex:1;overflow-y:auto;padding:0;"></div>';

                content.innerHTML = dropdownHtml;

                var sel = document.getElementById('ps-gaugepnl-sel');
                var tableArea = document.createElement('div');
                tableArea.id = 'ps-gauge-table-area';
                tableArea.style.cssText = 'flex:1;overflow-y:auto;padding:0;';
                content.appendChild(tableArea);

                function renderForGauge(gaugeId) {
                    var g = gaugesWithTrades.find(function(x) { return x.gauge_id === gaugeId; });
                    if (g) _psRenderGaugeTable(g, tableArea);
                }

                if (sel) {
                    sel.onchange = function() {
                        psSelectedGaugeId = this.value;
                        renderForGauge(this.value);
                    };
                    // Initial render: pre-selected or first
                    var initialId = psSelectedGaugeId && gaugesWithTrades.find(function(g) {
                        return g.gauge_id === psSelectedGaugeId;
                    }) ? psSelectedGaugeId : gaugesWithTrades[0].gauge_id;
                    sel.value = initialId;
                    renderForGauge(initialId);
                }
            }

            function _psRenderGaugeTable(gaugeData, container) {
                if (!container) container = document.getElementById('ps-gauge-table-area');
                if (!container) return;

                var thresholdColor = gaugeData.threshold === 'severe' ? '#c62828' :
                                     gaugeData.threshold === 'warning' ? '#e65100' :
                                     gaugeData.threshold === 'alert' ? '#f9a825' : '#757575';
                var thresholdBg = gaugeData.threshold === 'severe' ? '#ffebee' :
                                  gaugeData.threshold === 'warning' ? '#fff3e0' :
                                  gaugeData.threshold === 'alert' ? '#fffde7' : '#f5f5f5';
                var pnlColor = gaugeData.stress_pnl >= 0 ? '#2e7d32' : '#c62828';

                var headerHtml =
                    '<div style="padding:10px 16px;border-bottom:1px solid #eee;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;">' +
                    '<div style="display:flex;align-items:center;gap:10px;">' +
                    '<span style="font-size:13px;font-weight:700;color:#333;">' + gaugeData.gauge_name + '</span>' +
                    '<span style="background:' + thresholdBg + ';color:' + thresholdColor + ';border:1px solid ' + thresholdColor + ';' +
                    'padding:1px 8px;border-radius:10px;font-size:10px;font-weight:700;">' + gaugeData.threshold.toUpperCase() + '</span>' +
                    '</div>' +
                    '<div style="display:flex;align-items:center;gap:16px;">' +
                    '<span style="font-size:11px;color:#666;">P(flood): <b>' + gaugeData.p_flood_pct.toFixed(1) + '%</b></span>' +
                    '<span style="font-size:11px;color:#666;">Peak: <b>' + gaugeData.peak_water_level_m.toFixed(2) + 'm</b></span>' +
                    '<span style="font-size:13px;font-weight:700;color:' + pnlColor + ';">Total Stress P&amp;L: ' + fmtGBP(gaugeData.stress_pnl) + '</span>' +
                    '<button data-gaugeid="' + gaugeData.gauge_id + '" class="ps-detail-btn" style="padding:3px 10px;font-size:10px;background:#1976d2;color:white;border:none;border-radius:3px;cursor:pointer;">' +
                    '\u2192 Full Detail \u2197' +
                    '</button>' +
                    '</div>' +
                    '</div>';

                var tradesHtml = '';
                if (gaugeData.trades && gaugeData.trades.length > 0) {
                    tradesHtml =
                        '<table style="width:100%;border-collapse:collapse;font-size:10px;">' +
                        '<thead><tr style="background:#f5f5f5;border-bottom:2px solid #ddd;">' +
                        '<th style="padding:5px 8px;text-align:left;">Trade</th>' +
                        '<th style="padding:5px 4px;text-align:center;">Dir</th>' +
                        '<th style="padding:5px 4px;text-align:center;">Trigger</th>' +
                        '<th style="padding:5px 4px;text-align:center;">Tenor</th>' +
                        '<th style="padding:5px 8px;text-align:right;">Notional</th>' +
                        '<th style="padding:5px 8px;text-align:right;">P(flood)</th>' +
                        '<th style="padding:5px 8px;text-align:right;">MTM</th>' +
                        '<th style="padding:5px 8px;text-align:right;">Stress P&amp;L</th>' +
                        '</tr></thead><tbody>';

                    var totalNotional = 0, totalMtm = 0, totalStress = 0;
                    gaugeData.trades.forEach(function(t) {
                        var dirColor = t.is_payer ? '#c62828' : '#2e7d32';
                        var spnlColor = t.stress_pnl >= 0 ? '#2e7d32' : '#c62828';
                        totalNotional += t.notional;
                        totalMtm += t.mtm;
                        totalStress += t.stress_pnl;
                        tradesHtml +=
                            '<tr style="border-bottom:1px solid #f0f0f0;">' +
                            '<td style="padding:4px 8px;font-family:monospace;font-size:9px;">' + t.swap_id.substring(0, 14) + '</td>' +
                            '<td style="padding:4px 4px;text-align:center;color:' + dirColor + ';font-weight:600;">' + (t.is_payer ? 'Pay' : 'Rcv') + '</td>' +
                            '<td style="padding:4px 4px;text-align:center;font-size:9px;text-transform:capitalize;">' + (t.trigger || '\u2014') + '</td>' +
                            '<td style="padding:4px 4px;text-align:center;font-size:9px;">' + (t.tenor ? t.tenor + 'Y' : '\u2014') + '</td>' +
                            '<td style="padding:4px 8px;text-align:right;">' + fmtGBP(t.notional) + '</td>' +
                            '<td style="padding:4px 8px;text-align:right;">' + gaugeData.p_flood_pct.toFixed(1) + '%</td>' +
                            '<td style="padding:4px 8px;text-align:right;">' + fmtGBP(t.mtm) + '</td>' +
                            '<td style="padding:4px 8px;text-align:right;font-weight:700;color:' + spnlColor + ';">' + fmtGBP(t.stress_pnl) + '</td>' +
                            '</tr>';
                    });

                    tradesHtml +=
                        '<tr style="border-top:2px solid #333;background:#f8f9fa;font-weight:700;">' +
                        '<td style="padding:5px 8px;" colspan="4">TOTAL</td>' +
                        '<td style="padding:5px 8px;text-align:right;">' + fmtGBP(totalNotional) + '</td>' +
                        '<td style="padding:5px 8px;text-align:right;">' + gaugeData.p_flood_pct.toFixed(1) + '%</td>' +
                        '<td style="padding:5px 8px;text-align:right;color:' + (totalMtm >= 0 ? '#2e7d32' : '#c62828') + ';">' + fmtGBP(totalMtm) + '</td>' +
                        '<td style="padding:5px 8px;text-align:right;color:' + (totalStress >= 0 ? '#2e7d32' : '#c62828') + ';">' + fmtGBP(totalStress) + '</td>' +
                        '</tr></tbody></table>';
                } else {
                    tradesHtml = '<div style="padding:24px;color:#999;text-align:center;">No open trades at this gauge.</div>';
                }

                container.innerHTML = headerHtml + tradesHtml;

                // Bind "Full Detail" button via event delegation (avoids quote-escaping in onclick)
                var detailBtn = container.querySelector('.ps-detail-btn');
                if (detailBtn) {
                    detailBtn.addEventListener('click', function() {
                        var gid = this.getAttribute('data-gaugeid');
                        if (psResult) window._stressStormHint = psResult.storm_id;
                        tdStressGaugeHint = gid;
                        switchTab('stress');
                    });
                }
            }
"""
