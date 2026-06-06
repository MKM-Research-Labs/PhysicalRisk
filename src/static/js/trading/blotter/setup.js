
            // ==============================================================
            // Tab 1: Trade Blotter
            // ==============================================================
            var tdBlotterData = null;
            var tdBlotterSummary = null;
            var tdBlotterFilters = {};

            function createBlotterView() {
                var view = document.createElement('div');
                view.id = 'td-blotter-view';
                view.style.cssText = 'flex:1;display:flex;flex-direction:column;overflow:hidden;';

                // P&L header bar
                var pnlBar = document.createElement('div');
                pnlBar.id = 'td-pnl-bar';
                pnlBar.style.cssText = 'display:flex;gap:20px;padding:10px 16px;background:#f0f4f8;border-bottom:1px solid #e0e0e0;align-items:center;flex-wrap:wrap;';
                view.appendChild(pnlBar);

                // Filter bar
                var filterBar = document.createElement('div');
                filterBar.id = 'td-filter-bar';
                filterBar.style.cssText = 'display:flex;gap:8px;padding:6px 16px;background:#fafafa;border-bottom:1px solid #eee;align-items:center;flex-wrap:wrap;font-size:11px;';
                view.appendChild(filterBar);

                // Sortable table container
                var tableWrap = document.createElement('div');
                tableWrap.id = 'td-blotter-table-wrap';
                tableWrap.style.cssText = 'flex:1;overflow:auto;padding:0;';
                view.appendChild(tableWrap);

                return view;
            }

            function _applyBlotterResult(result) {
                if (result.status === 'success') {
                    tdBlotterData = result.trades || [];
                    tdBlotterSummary = result.summary || {};
                    renderBlotterPnlBar();
                    if (window._tdPendingFilter) {
                        tdBlotterFilters = window._tdPendingFilter;
                        window._tdPendingFilter = null;
                    }
                    renderFilterBar();
                    renderBlotterTable();
                } else {
                    console.error('[Blotter] Load error:', result.message);
                }
            }

            function loadBlotterData() {
                // Use preloaded data on first open (avoids double fetch)
                if (window._tdPreBlotter) {
                    var cached = window._tdPreBlotter;
                    window._tdPreBlotter = null;
                    _applyBlotterResult(cached);
                    return;
                }
                var url = getBaseUrl() + '/api/v1/trading/blotter?include_closed=true&_=' + Date.now();
                fetch(url, {mode: 'cors', cache: 'no-store'})
                    .then(function(r) { return r.json(); })
                    .then(_applyBlotterResult)
                    .catch(function(err) {
                        console.error('[Blotter] Fetch error:', err);
                    });
            }

            function renderBlotterPnlBar() {
                var bar = document.getElementById('td-pnl-bar');
                if (!bar || !tdBlotterSummary) return;

                var hasFilter = tdBlotterFilters && Object.keys(tdBlotterFilters).length > 0;
                var trades = hasFilter ? getFilteredTrades() : tdBlotterData;

                // Compute stats from visible trades
                var numTrades = trades ? trades.length : 0;
                var liveTrades = 0;
                var closedTrades = 0;
                var netNotional = 0;
                var dailyPnl = 0;
                var runningPnl = 0;
                var fromTrades = 0;
                var fromMarket = 0;
                var realizedPnl = 0;
                if (trades) {
                    for (var ni = 0; ni < trades.length; ni++) {
                        var nt = trades[ni];
                        var isClosed = (nt.trade_status || 'Open').toLowerCase() === 'closed';
                        if (isClosed) {
                            closedTrades++;
                            realizedPnl += (nt.final_pnl || 0);
                        } else {
                            liveTrades++;
                            netNotional += nt.is_payer ? -(nt.notional || 0) : (nt.notional || 0);
                            dailyPnl += (nt.daily_pnl || (nt.new_trade_pnl || 0) + (nt.market_pnl || 0));
                            runningPnl += (nt.mtm || 0);
                            fromTrades += (nt.new_trade_pnl || 0);
                            fromMarket += (nt.market_pnl || 0);
                        }
                    }
                }

                var dailyColor = dailyPnl >= 0 ? '#2e7d32' : '#c62828';
                var runColor = runningPnl >= 0 ? '#2e7d32' : '#c62828';

                var realColor = realizedPnl >= 0 ? '#2e7d32' : '#c62828';
                var tradeLabel = liveTrades + (closedTrades > 0 ? ' <span style="font-size:10px;color:#999;">(' + closedTrades + ' closed)</span>' : '');

                bar.innerHTML =
                    '<div style="display:flex;flex-direction:column;align-items:center;">' +
                        '<span style="font-size:10px;color:#888;text-transform:uppercase;">Trades</span>' +
                        '<span style="font-size:16px;font-weight:bold;">' + tradeLabel + '</span>' +
                    '</div>' +
                    '<div style="display:flex;flex-direction:column;align-items:center;">' +
                        '<span style="font-size:10px;color:#888;text-transform:uppercase;">Notional</span>' +
                        '<span style="font-size:16px;font-weight:bold;">' + fmtGBP(netNotional) + '</span>' +
                    '</div>' +
                    '<div style="width:1px;height:30px;background:#ccc;"></div>' +
                    '<div style="display:flex;flex-direction:column;align-items:center;">' +
                        '<span style="font-size:10px;color:#888;text-transform:uppercase;">Daily P&amp;L</span>' +
                        '<span style="font-size:18px;font-weight:bold;color:' + dailyColor + ';">' + fmtGBP(dailyPnl) + '</span>' +
                    '</div>' +
                    '<div style="display:flex;flex-direction:column;align-items:center;">' +
                        '<span style="font-size:10px;color:#888;text-transform:uppercase;">Running P&amp;L</span>' +
                        '<span style="font-size:18px;font-weight:bold;color:' + runColor + ';">' + fmtGBP(runningPnl) + '</span>' +
                    '</div>' +
                    (closedTrades > 0 ?
                    '<div style="display:flex;flex-direction:column;align-items:center;">' +
                        '<span style="font-size:10px;color:#888;text-transform:uppercase;">Realized</span>' +
                        '<span style="font-size:18px;font-weight:bold;color:' + realColor + ';">' + fmtGBP(realizedPnl) + '</span>' +
                    '</div>' : '') +
                    '<div style="width:1px;height:30px;background:#ccc;"></div>' +
                    '<div style="display:flex;flex-direction:column;align-items:center;">' +
                        '<span style="font-size:10px;color:#888;text-transform:uppercase;">From Trades</span>' +
                        '<span style="font-size:13px;font-weight:600;">' + fmtGBP(fromTrades) + '</span>' +
                    '</div>' +
                    '<div style="display:flex;flex-direction:column;align-items:center;">' +
                        '<span style="font-size:10px;color:#888;text-transform:uppercase;">From Market</span>' +
                        '<span style="font-size:13px;font-weight:600;">' + fmtGBP(fromMarket) + '</span>' +
                    '</div>';
            }
