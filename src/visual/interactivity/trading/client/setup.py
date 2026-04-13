# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""
Client tab — setup sub-module.

State variables, DOM construction, and data loading for property PRS trades.
"""


def get_js() -> str:
    """Return JavaScript fragment for client tab state, DOM, and loading."""
    return """
            // ==============================================================
            // Tab: Client (Property PRS)
            // ==============================================================
            var tdClientData = null;
            var tdClientSummary = null;

            function createClientView() {
                var view = document.createElement('div');
                view.id = 'td-client-view';
                view.style.cssText = 'flex:1;display:none;flex-direction:column;overflow:hidden;';

                // Summary header bar
                var summaryBar = document.createElement('div');
                summaryBar.id = 'td-client-summary-bar';
                summaryBar.style.cssText = 'display:flex;gap:20px;padding:10px 16px;background:#f0f4f8;border-bottom:1px solid #e0e0e0;align-items:center;flex-wrap:wrap;';
                view.appendChild(summaryBar);

                // Scrollable table container
                var tableWrap = document.createElement('div');
                tableWrap.id = 'td-client-table-wrap';
                tableWrap.style.cssText = 'flex:1;overflow:auto;padding:0;';
                view.appendChild(tableWrap);

                return view;
            }

            function loadClientData() {
                var url = getBaseUrl() + '/api/v1/trading/client?_=' + Date.now();
                fetch(url, {mode: 'cors', cache: 'no-store'})
                    .then(function(r) { return r.json(); })
                    .then(function(result) {
                        if (result.status === 'success') {
                            tdClientData = result.trades || [];
                            tdClientSummary = result.summary || {};
                            renderClientSummaryBar();
                            renderClientTable();
                        } else {
                            console.error('[Client] Load error:', result.message);
                        }
                    })
                    .catch(function(err) {
                        console.error('[Client] Fetch error:', err);
                    });
            }

            function renderClientSummaryBar() {
                var bar = document.getElementById('td-client-summary-bar');
                if (!bar || !tdClientData) return;

                var numTrades = tdClientData.length;
                var totalNotional = 0;
                var totalNpv = 0;
                var totalPropValue = 0;
                var totalSpread = 0;
                var spreadCount = 0;
                for (var i = 0; i < tdClientData.length; i++) {
                    var t = tdClientData[i];
                    totalNotional += (t.notional || 0);
                    totalNpv += (t.npv || 0);
                    totalPropValue += (t.property_value || 0);
                    if (t.spread_bps > 0) { totalSpread += t.spread_bps; spreadCount++; }
                }
                var avgSpread = spreadCount > 0 ? (totalSpread / spreadCount).toFixed(1) : '0.0';
                var npvColor = totalNpv >= 0 ? '#2e7d32' : '#c62828';

                bar.innerHTML =
                    '<div style="display:flex;flex-direction:column;align-items:center;">' +
                        '<span style="font-size:10px;color:#888;text-transform:uppercase;">Client Trades</span>' +
                        '<span style="font-size:16px;font-weight:bold;">' + numTrades + '</span>' +
                    '</div>' +
                    '<div style="display:flex;flex-direction:column;align-items:center;">' +
                        '<span style="font-size:10px;color:#888;text-transform:uppercase;">Notional Sold</span>' +
                        '<span style="font-size:16px;font-weight:bold;">' + fmtGBP(totalNotional) + '</span>' +
                    '</div>' +
                    '<div style="display:flex;flex-direction:column;align-items:center;">' +
                        '<span style="font-size:10px;color:#888;text-transform:uppercase;">Avg Spread</span>' +
                        '<span style="font-size:16px;font-weight:bold;">' + avgSpread + ' bps</span>' +
                    '</div>' +
                    '<div style="display:flex;flex-direction:column;align-items:center;">' +
                        '<span style="font-size:10px;color:#888;text-transform:uppercase;">Property Value Covered</span>' +
                        '<span style="font-size:16px;font-weight:bold;">' + fmtGBP(totalPropValue) + '</span>' +
                    '</div>' +
                    '<div style="width:1px;height:30px;background:#ccc;"></div>' +
                    '<div style="display:flex;flex-direction:column;align-items:center;">' +
                        '<span style="font-size:10px;color:#888;text-transform:uppercase;">Total NPV</span>' +
                        '<span style="font-size:18px;font-weight:bold;color:' + npvColor + ';">' + fmtGBP(totalNpv) + '</span>' +
                    '</div>' +
                    '<div style="flex:1;"></div>' +
                    '<div style="font-size:10px;color:#78909c;font-style:italic;">Client Property PRS \\u2014 Trader\\u2019s Book</div>';
            }
"""
