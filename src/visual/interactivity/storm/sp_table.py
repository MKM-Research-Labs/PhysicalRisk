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
Storm portfolio — Table tab sub-module.

Summary cards, sortable property damage table, storm list loading,
and portfolio impact data loading.
"""


from config.format import storm_option_js as _storm_opt


def get_js() -> str:
    """Return JS fragment for table tab (injected into parent IIFE)."""
    return """
            // ================================================================
            // Table tab — state
            // ================================================================
            var spData = null;
            var spSortCol = 'damage_amount';
            var spSortAsc = false;

            // ================================================================
            // Table tab — DOM creation
            // ================================================================
            var spTableSubTab = 'damage';  // 'portfolio', 'damage', 'trades', or 'basis'
            var spBlotterData = null;
            var spBasisData = null;
            var spTradesData = null;

            function createTableView() {
                var view = document.createElement('div');
                view.id = 'sp-table-view';
                view.style.cssText = 'display:flex;flex-direction:column;flex:1;overflow:hidden;';

                // Sub-tab toggle: REIT Portfolio | Damage | REIT Blotter | Basis
                var subTabBar = document.createElement('div');
                subTabBar.id = 'sp-sub-tab-bar';
                subTabBar.style.cssText = 'display:flex;gap:0;padding:8px 16px 0;';
                var inactiveStyle = 'padding:5px 16px;font-size:11px;border:1px solid #ddd;border-bottom:none;border-radius:4px 4px 0 0;cursor:pointer;background:white;color:#555;';
                var activeStyle = 'padding:5px 16px;font-size:11px;border:1px solid #1976d2;border-bottom:none;border-radius:4px 4px 0 0;cursor:pointer;background:#1976d2;color:white;';
                var subBtnPortfolio = document.createElement('button');
                subBtnPortfolio.id = 'sp-sub-portfolio';
                subBtnPortfolio.textContent = 'REIT Portfolio';
                subBtnPortfolio.style.cssText = inactiveStyle;
                subBtnPortfolio.onclick = function() { switchSubTab('portfolio'); };
                var subBtnDamage = document.createElement('button');
                subBtnDamage.id = 'sp-sub-damage';
                subBtnDamage.textContent = 'Damage';
                subBtnDamage.style.cssText = activeStyle;
                subBtnDamage.onclick = function() { switchSubTab('damage'); };
                var subBtnTrades = document.createElement('button');
                subBtnTrades.id = 'sp-sub-trades';
                subBtnTrades.textContent = 'REIT Blotter';
                subBtnTrades.style.cssText = inactiveStyle;
                subBtnTrades.onclick = function() { switchSubTab('trades'); };
                var subBtnBasis = document.createElement('button');
                subBtnBasis.id = 'sp-sub-basis';
                subBtnBasis.textContent = 'Basis';
                subBtnBasis.style.cssText = inactiveStyle;
                subBtnBasis.onclick = function() { switchSubTab('basis'); };
                subTabBar.appendChild(subBtnPortfolio);
                subTabBar.appendChild(subBtnDamage);
                subTabBar.appendChild(subBtnTrades);
                subTabBar.appendChild(subBtnBasis);
                view.appendChild(subTabBar);

                var summaryRow = document.createElement('div');
                summaryRow.id = 'sp-summary';
                summaryRow.style.cssText = 'padding:10px 16px;border-bottom:1px solid #eee;display:flex;gap:10px;flex-wrap:wrap;';

                var tableContainer = document.createElement('div');
                tableContainer.id = 'sp-table-container';
                tableContainer.style.cssText = 'flex:1;overflow-y:auto;padding:0;';

                view.appendChild(summaryRow);
                view.appendChild(tableContainer);
                return view;
            }

            function switchSubTab(sub) {
                spTableSubTab = sub;
                var btns = [
                    document.getElementById('sp-sub-portfolio'),
                    document.getElementById('sp-sub-damage'),
                    document.getElementById('sp-sub-trades'),
                    document.getElementById('sp-sub-basis'),
                ];
                btns.forEach(function(b) {
                    if (b) { b.style.background = 'white'; b.style.color = '#555'; b.style.borderColor = '#ddd'; }
                });
                var active = document.getElementById('sp-sub-' + sub);
                if (active) { active.style.background = '#1976d2'; active.style.color = 'white'; active.style.borderColor = '#1976d2'; }

                if (sub === 'portfolio') {
                    loadBlotterData();
                } else if (sub === 'trades') {
                    loadTradesData();
                } else if (sub === 'basis') {
                    var ss = document.getElementById('sp-storm-select');
                    var sid = ss ? ss.value : '';
                    if (sid) loadBasisData(sid);
                } else {
                    if (spData) {
                        renderSummary(spData.portfolio, spData.derivatives);
                        renderTable(spData.properties);
                    }
                }
            }

            // ================================================================
            // REIT Blotter — property headlines
            // ================================================================
            function loadBlotterData() {
                var summary = document.getElementById('sp-summary');
                var container = document.getElementById('sp-table-container');
                summary.innerHTML = '<div style="padding:4px;color:#888;font-size:11px;">Loading REIT portfolio...</div>';
                container.innerHTML = '';

                if (spBlotterData) {
                    renderBlotterSummary(spBlotterData);
                    renderBlotterTable(spBlotterData.properties);
                    return;
                }

                var baseUrl = getBaseUrl();
                fetch(baseUrl + '/api/v1/propertyts/blotter', {mode: 'cors'})
                    .then(function(r) { return r.json(); })
                    .then(function(data) {
                        if (data.status === 'success') {
                            spBlotterData = data;
                            renderBlotterSummary(data);
                            renderBlotterTable(data.properties);
                        } else {
                            summary.innerHTML = '<div style="color:red;">Error loading blotter</div>';
                        }
                    })
                    .catch(function(err) {
                        summary.innerHTML = '<div style="color:red;">Failed to load blotter</div>';
                        console.error('[StormPortfolio] Blotter error:', err);
                    });
            }

            function renderBlotterSummary(data) {
                var summary = document.getElementById('sp-summary');
                var s = data.summary || {};
                var cards = [
                    { label: 'Properties', value: s.num_properties || 0, color: '#1976d2' },
                    { label: 'Total Value', value: fmtGBP(s.total_property_value || 0), color: '#388e3c' },
                    { label: 'Mortgage Exposure', value: fmtGBP(s.total_mortgage_exposure || 0), color: '#7b1fa2' },
                ];
                summary.innerHTML = '';
                cards.forEach(function(c) {
                    var card = document.createElement('div');
                    card.style.cssText = 'flex:1;min-width:120px;padding:8px 12px;border-radius:6px;background:#f5f5f5;border-left:3px solid ' + c.color + ';';
                    card.innerHTML = '<div style="font-size:10px;color:#888;text-transform:uppercase;letter-spacing:0.5px;">' + c.label + '</div>' +
                        '<div style="font-size:16px;font-weight:700;color:' + c.color + ';margin-top:2px;">' + c.value + '</div>';
                    summary.appendChild(card);
                });
            }

            function renderBlotterTable(properties) {
                var container = document.getElementById('sp-table-container');
                var blotterCols = [
                    { key: 'property_id', label: 'Property', fmt: function(v) { return v; } },
                    { key: 'property_address', label: 'Address', fmt: function(v) { return v || '\\u2014'; } },
                    { key: 'property_value', label: 'Value', fmt: fmtGBP },
                    { key: 'river_distance_km', label: 'River Dist (km)', fmt: function(v) { return (v !== null && v !== undefined) ? v.toFixed(2) : '\\u2014'; } },
                    { key: 'elevation_m', label: 'Elevation (m)', fmt: function(v) { return (v !== null && v !== undefined) ? (typeof v === 'number' ? v.toFixed(2) : v) : '\\u2014'; } },
                    { key: 'ea_flood_zone', label: 'Flood Zone', fmt: function(v) { return v || '\\u2014'; } },
                    { key: 'outstanding_balance', label: 'Mortgage', fmt: fmtGBP },
                    { key: 'current_ltv', label: 'LTV', fmt: fmtPct },
                    { key: 'remaining_term_months', label: 'Remaining', fmt: fmtMonths },
                ];

                var table = document.createElement('table');
                table.style.cssText = 'width:100%;border-collapse:collapse;font-size:11px;';

                var thead = document.createElement('thead');
                var tr = document.createElement('tr');
                blotterCols.forEach(function(col) {
                    var th = document.createElement('th');
                    th.textContent = col.label;
                    th.style.cssText = 'padding:6px 8px;text-align:right;border-bottom:2px solid #ddd;background:#fafafa;white-space:nowrap;font-size:10px;color:#555;position:sticky;top:0;';
                    if (col.key === 'property_id' || col.key === 'property_address' || col.key === 'ea_flood_zone') th.style.textAlign = 'left';
                    tr.appendChild(th);
                });
                thead.appendChild(tr);
                table.appendChild(thead);

                var tbody = document.createElement('tbody');
                (properties || []).forEach(function(p, idx) {
                    var row = document.createElement('tr');
                    // Shade rows: high LTV red, moderate LTV orange, else alternate grey
                    if (p.current_ltv > 90) {
                        row.style.background = '#ffebee';
                    } else if (p.current_ltv > 75) {
                        row.style.background = '#fff3e0';
                    } else if (idx % 2 === 1) {
                        row.style.background = '#fafafa';
                    }
                    row.style.cursor = 'pointer';
                    row.onmouseenter = function() { this.style.opacity = '0.8'; };
                    row.onmouseleave = function() { this.style.opacity = '1'; };
                    row.onclick = (function(pid) {
                        return function() {
                            hidePanel();
                            if (window.PropertyStormAnalysis && window.PropertyStormAnalysis.show) {
                                window.PropertyStormAnalysis.show(pid);
                            } else {
                                document.dispatchEvent(new CustomEvent('propertyStormRequested', {
                                    detail: { propertyId: pid }, bubbles: true
                                }));
                            }
                        };
                    })(p.property_id);

                    blotterCols.forEach(function(col) {
                        var td = document.createElement('td');
                        td.textContent = col.fmt(p[col.key]);
                        td.style.cssText = 'padding:5px 8px;border-bottom:1px solid #f0f0f0;text-align:right;white-space:nowrap;';
                        if (col.key === 'property_id' || col.key === 'property_address' || col.key === 'ea_flood_zone') td.style.textAlign = 'left';
                        if (col.key === 'current_ltv' && p.current_ltv > 90) {
                            td.style.color = '#d32f2f';
                            td.style.fontWeight = 'bold';
                        }
                        row.appendChild(td);
                    });
                    tbody.appendChild(row);
                });
                table.appendChild(tbody);

                container.innerHTML = '';
                container.appendChild(table);
            }

            // ================================================================
            // REIT Blotter — PRS trades
            // ================================================================
            function loadTradesData() {
                var summary = document.getElementById('sp-summary');
                var container = document.getElementById('sp-table-container');
                summary.innerHTML = '<div style="padding:4px;color:#888;font-size:11px;">Loading PRS trades...</div>';
                container.innerHTML = '';

                if (spTradesData) {
                    renderTradesSummary(spTradesData);
                    renderTradesTable(spTradesData.trades);
                    return;
                }

                var baseUrl = getBaseUrl();
                fetch(baseUrl + '/api/v1/trading/blotter', {mode: 'cors'})
                    .then(function(r) { return r.json(); })
                    .then(function(data) {
                        if (data.status === 'success') {
                            spTradesData = data;
                            renderTradesSummary(data);
                            renderTradesTable(data.trades);
                        } else {
                            summary.innerHTML = '<div style="color:red;">Error loading trades</div>';
                        }
                    })
                    .catch(function(err) {
                        summary.innerHTML = '<div style="color:red;">Failed to load trades</div>';
                        console.error('[StormPortfolio] Trades error:', err);
                    });
            }

            function renderTradesSummary(data) {
                var summary = document.getElementById('sp-summary');
                var s = data.summary || {};
                var pnlColor = (s.total_running_pnl || 0) >= 0 ? '#388e3c' : '#d32f2f';
                var dailyColor = (s.total_daily_pnl || 0) >= 0 ? '#388e3c' : '#d32f2f';
                var cards = [
                    { label: 'Open Trades', value: s.num_trades || 0, color: '#1976d2' },
                    { label: 'Total Notional', value: fmtGBP(s.total_notional || 0), color: '#7b1fa2' },
                    { label: 'Daily P&L', value: fmtGBP(s.total_daily_pnl || 0), color: dailyColor },
                    { label: 'Running P&L', value: fmtGBP(s.total_running_pnl || 0), color: pnlColor },
                ];
                summary.innerHTML = '';
                cards.forEach(function(c) {
                    var card = document.createElement('div');
                    card.style.cssText = 'flex:1;min-width:120px;padding:8px 12px;border-radius:6px;background:#f5f5f5;border-left:3px solid ' + c.color + ';';
                    card.innerHTML = '<div style="font-size:10px;color:#888;text-transform:uppercase;letter-spacing:0.5px;">' + c.label + '</div>' +
                        '<div style="font-size:16px;font-weight:700;color:' + c.color + ';margin-top:2px;">' + c.value + '</div>';
                    summary.appendChild(card);
                });
            }

            function renderTradesTable(trades) {
                var container = document.getElementById('sp-table-container');
                var tradeCols = [
                    { key: 'swap_id', label: 'Trade ID', fmt: function(v) { return v || '\\u2014'; } },
                    { key: 'gauge_name', label: 'Gauge', fmt: function(v) { return v || '\\u2014'; } },
                    { key: 'property_id', label: 'Property', fmt: function(v) { return v || '\\u2014'; } },
                    { key: 'trade_date', label: 'Trade Date', fmt: function(v) { return v ? v.substring(0, 10) : '\\u2014'; } },
                    { key: 'notional', label: 'Notional', fmt: fmtGBP },
                    { key: 'fixed_spread_bps', label: 'Fixed (bps)', fmt: function(v) { return v ? v.toFixed(1) : '\\u2014'; } },
                    { key: 'fair_spread_bps', label: 'Fair (bps)', fmt: function(v) { return v ? v.toFixed(1) : '\\u2014'; } },
                    { key: 'mtm', label: 'MTM', fmt: fmtGBP },
                    { key: 'running_pnl', label: 'Running P&L', fmt: fmtGBP },
                    { key: 'trade_status', label: 'Status', fmt: function(v) { return v || 'Open'; } },
                ];

                var table = document.createElement('table');
                table.style.cssText = 'width:100%;border-collapse:collapse;font-size:11px;';

                var thead = document.createElement('thead');
                var tr = document.createElement('tr');
                tradeCols.forEach(function(col) {
                    var th = document.createElement('th');
                    th.textContent = col.label;
                    th.style.cssText = 'padding:6px 8px;text-align:right;border-bottom:2px solid #ddd;background:#fafafa;white-space:nowrap;font-size:10px;color:#555;position:sticky;top:0;';
                    if (col.key === 'swap_id' || col.key === 'gauge_name' || col.key === 'property_id' || col.key === 'trade_status') th.style.textAlign = 'left';
                    tr.appendChild(th);
                });
                thead.appendChild(tr);
                table.appendChild(thead);

                var tbody = document.createElement('tbody');
                (trades || []).forEach(function(t, idx) {
                    var row = document.createElement('tr');
                    // Shade: negative P&L red, positive green tint, else alternate
                    if ((t.running_pnl || 0) < -1000) {
                        row.style.background = '#ffebee';
                    } else if ((t.running_pnl || 0) > 1000) {
                        row.style.background = '#e8f5e9';
                    } else if (idx % 2 === 1) {
                        row.style.background = '#fafafa';
                    }
                    row.style.cursor = 'pointer';
                    row.onmouseenter = function() { this.style.opacity = '0.8'; };
                    row.onmouseleave = function() { this.style.opacity = '1'; };

                    tradeCols.forEach(function(col) {
                        var td = document.createElement('td');
                        td.textContent = col.fmt(t[col.key]);
                        td.style.cssText = 'padding:5px 8px;border-bottom:1px solid #f0f0f0;text-align:right;white-space:nowrap;';
                        if (col.key === 'swap_id' || col.key === 'gauge_name' || col.key === 'property_id' || col.key === 'trade_status') td.style.textAlign = 'left';
                        if (col.key === 'mtm' || col.key === 'running_pnl') {
                            td.style.color = (t[col.key] || 0) >= 0 ? '#2e7d32' : '#c62828';
                            td.style.fontWeight = 'bold';
                        }
                        if (col.key === 'trade_status') {
                            td.style.color = t.trade_status === 'Closed' ? '#888' : '#1976d2';
                        }
                        row.appendChild(td);
                    });
                    tbody.appendChild(row);
                });
                table.appendChild(tbody);

                container.innerHTML = '';
                container.appendChild(table);
            }

            // ================================================================
            // Basis — synthetic gauge flood transmission
            // ================================================================
            function loadBasisData(stormId) {
                var summary = document.getElementById('sp-summary');
                var container = document.getElementById('sp-table-container');
                summary.innerHTML = '<div style="padding:4px;color:#888;font-size:11px;">Loading basis data...</div>';
                container.innerHTML = '';

                var baseUrl = getBaseUrl();
                fetch(baseUrl + '/api/v1/propertyts/' + stormId + '/basis', {mode: 'cors'})
                    .then(function(r) { return r.json(); })
                    .then(function(data) {
                        if (data.status === 'success') {
                            spBasisData = data;
                            renderBasisSummary(data.summary);
                            renderBasisTable(data.gauges);
                        } else {
                            summary.innerHTML = '';
                            container.innerHTML = '<div style="padding:40px;text-align:center;color:#999;font-size:13px;">No basis data for this storm</div>';
                        }
                    })
                    .catch(function(err) {
                        summary.innerHTML = '';
                        container.innerHTML = '<div style="padding:20px;color:red;">Failed to load basis data</div>';
                        console.error('[StormPortfolio] Basis error:', err);
                    });
            }

            function renderBasisSummary(s) {
                var summary = document.getElementById('sp-summary');
                var transmColor = (s.portfolio_transmission_pct || 0) >= 50 ? '#d32f2f' : '#388e3c';
                var cards = [
                    { label: 'Synthetic Gauges', value: s.num_synthetic_gauges || 0, color: '#1976d2' },
                    { label: 'Gauges Severe', value: s.gauges_severe || 0, color: '#d32f2f' },
                    { label: 'With Flooding', value: s.gauges_with_flooding || 0, color: '#f57c00' },
                    { label: 'Basis Only', value: s.gauges_basis_only || 0, color: '#7b1fa2' },
                    { label: 'Properties Flooded', value: (s.total_flooded || 0) + ' / ' + (s.total_properties || 0), color: '#1565c0' },
                    { label: 'Transmission', value: (s.portfolio_transmission_pct || 0) + '%', color: transmColor },
                ];
                summary.innerHTML = '';
                cards.forEach(function(c) {
                    var card = document.createElement('div');
                    card.style.cssText = 'flex:1;min-width:100px;padding:8px 12px;border-radius:6px;background:#f5f5f5;border-left:3px solid ' + c.color + ';';
                    card.innerHTML = '<div style="font-size:10px;color:#888;text-transform:uppercase;letter-spacing:0.5px;">' + c.label + '</div>' +
                        '<div style="font-size:16px;font-weight:700;color:' + c.color + ';margin-top:2px;">' + c.value + '</div>';
                    summary.appendChild(card);
                });
            }

            function renderBasisTable(gauges) {
                var container = document.getElementById('sp-table-container');
                var basisCols = [
                    { key: 'gauge_name', label: 'Gauge', fmt: function(v) { return v; } },
                    { key: 'threshold', label: 'Threshold', fmt: function(v) { return v ? v.charAt(0).toUpperCase() + v.slice(1) : '\\u2014'; } },
                    { key: 'peak_wse_m', label: 'Peak (m)', fmt: function(v) { return v ? v.toFixed(2) : '\\u2014'; } },
                    { key: 'severe_m', label: 'Severe (m)', fmt: function(v) { return v ? v.toFixed(2) : '\\u2014'; } },
                    { key: 'properties_linked', label: 'Linked', fmt: function(v) { return v; } },
                    { key: 'properties_flooded', label: 'Flooded', fmt: function(v) { return v; } },
                    { key: 'properties_not_flooded', label: 'Not Flooded', fmt: function(v) { return v; } },
                    { key: 'transmission_pct', label: 'Transmission', fmt: function(v) { return v + '%'; } },
                    { key: 'avg_retention', label: 'Avg Retention', fmt: function(v) { return v ? (v * 100).toFixed(1) + '%' : '\\u2014'; } },
                    { key: 'avg_flood_depth_m', label: 'Avg Depth', fmt: fmtDepth },
                    { key: 'real_gauge_peak_m', label: 'Real Gauge (m)', fmt: function(v) { return v ? v.toFixed(2) : '\\u2014'; } },
                ];

                var table = document.createElement('table');
                table.style.cssText = 'width:100%;border-collapse:collapse;font-size:11px;';

                var thead = document.createElement('thead');
                var tr = document.createElement('tr');
                basisCols.forEach(function(col) {
                    var th = document.createElement('th');
                    th.textContent = col.label;
                    th.style.cssText = 'padding:6px 8px;text-align:right;border-bottom:2px solid #ddd;background:#fafafa;white-space:nowrap;font-size:10px;color:#555;position:sticky;top:0;cursor:pointer;';
                    if (col.key === 'gauge_name' || col.key === 'threshold') th.style.textAlign = 'left';
                    tr.appendChild(th);
                });
                thead.appendChild(tr);
                table.appendChild(thead);

                var tbody = document.createElement('tbody');
                (gauges || []).forEach(function(g) {
                    var row = document.createElement('tr');

                    // Row colour by threshold
                    if (g.threshold === 'severe' && g.properties_flooded === 0) {
                        row.style.background = '#f3e5f5';  // purple tint — basis risk
                    } else if (g.threshold === 'severe') {
                        row.style.background = '#ffebee';  // red tint — severe with flooding
                    } else if (g.threshold === 'warning') {
                        row.style.background = '#fff3e0';  // orange tint
                    }

                    basisCols.forEach(function(col) {
                        var td = document.createElement('td');
                        var val = g[col.key];
                        td.textContent = col.fmt(val);
                        td.style.cssText = 'padding:5px 8px;border-bottom:1px solid #f0f0f0;text-align:right;white-space:nowrap;';
                        if (col.key === 'gauge_name' || col.key === 'threshold') td.style.textAlign = 'left';

                        // Colour coding
                        if (col.key === 'threshold') {
                            var tc = {'severe':'#d32f2f','warning':'#f57c00','alert':'#1976d2','clean':'#888'};
                            td.style.color = tc[val] || '#333';
                            td.style.fontWeight = 'bold';
                        }
                        if (col.key === 'transmission_pct') {
                            td.style.color = val >= 50 ? '#d32f2f' : (val > 0 ? '#f57c00' : '#388e3c');
                            td.style.fontWeight = 'bold';
                        }
                        if (col.key === 'properties_flooded' && val > 0) td.style.color = '#d32f2f';
                        if (col.key === 'properties_not_flooded' && val > 0 && g.threshold === 'severe') {
                            td.style.color = '#7b1fa2';  // basis risk highlight
                            td.style.fontWeight = 'bold';
                        }

                        row.appendChild(td);
                    });
                    tbody.appendChild(row);
                });
                table.appendChild(tbody);

                if (!gauges || gauges.length === 0) {
                    var emptyRow = document.createElement('tr');
                    var emptyTd = document.createElement('td');
                    emptyTd.colSpan = basisCols.length;
                    emptyTd.style.cssText = 'padding:40px;text-align:center;color:#999;';
                    emptyTd.textContent = 'No gauge data for this storm';
                    emptyRow.appendChild(emptyTd);
                    tbody.appendChild(emptyRow);
                }

                container.innerHTML = '';
                container.appendChild(table);
            }

            // ================================================================
            // Summary cards
            // ================================================================
            function renderSummary(portfolio, derivatives) {
                var summary = document.getElementById('sp-summary');
                var cards = [
                    { label: 'Properties Affected', value: portfolio.properties_affected + ' / ' + portfolio.total_properties, color: '#1976d2' },
                    { label: 'Portfolio Value', value: fmtGBP(portfolio.total_affected_value), color: '#388e3c' },
                    { label: 'Total Damage', value: fmtGBP(portfolio.total_damage), color: '#d32f2f' },
                    { label: 'Mortgage Exposure', value: fmtGBP(portfolio.total_affected_mortgages), color: '#7b1fa2' },
                    { label: 'Negative Equity', value: portfolio.mortgages_in_negative_equity, color: portfolio.mortgages_in_negative_equity > 0 ? '#d32f2f' : '#388e3c' },
                ];

                // Derivatives cards
                var d = derivatives || {};
                var netColor = (d.net_portfolio_pnl || 0) >= 0 ? '#2e7d32' : '#c62828';
                cards.push({ label: 'PRS Payout', value: fmtGBP(d.total_prs_payout || 0), color: '#2e7d32' });
                cards.push({ label: 'Trades Triggered', value: d.num_trades_triggered || 0, color: '#1565c0' });
                cards.push({ label: 'Net P&L', value: fmtGBP(d.net_portfolio_pnl || 0), color: netColor });

                summary.innerHTML = '';
                cards.forEach(function(c) {
                    var card = document.createElement('div');
                    card.style.cssText = 'flex:1;min-width:100px;padding:8px 12px;border-radius:6px;background:#f5f5f5;border-left:3px solid ' + c.color + ';';
                    card.innerHTML = '<div style="font-size:10px;color:#888;text-transform:uppercase;letter-spacing:0.5px;">' + c.label + '</div>' +
                        '<div style="font-size:16px;font-weight:700;color:' + c.color + ';margin-top:2px;">' + c.value + '</div>';
                    summary.appendChild(card);
                });
            }

            // ================================================================
            // Sortable table
            // ================================================================
            var columns = [
                { key: 'property_id', label: 'Property', fmt: function(v) { return v; } },
                { key: 'property_value', label: 'Value', fmt: fmtGBP },
                { key: 'flood_depth_m', label: 'Depth', fmt: fmtDepth },
                { key: 'damage_ratio', label: 'Damage %', fmt: function(v) { return (v * 100).toFixed(1) + '%'; } },
                { key: 'damage_amount', label: 'Damage \u00a3', fmt: fmtGBP },
                { key: 'prs_payout', label: 'PRS Payout', fmt: fmtGBP },
                { key: 'net_pnl', label: 'Net P&L', fmt: fmtGBP },
                { key: 'outstanding_balance', label: 'Mortgage', fmt: fmtGBP },
                { key: 'current_ltv', label: 'LTV', fmt: fmtPct },
                { key: 'post_damage_ltv', label: 'Post LTV', fmt: fmtPct },
            ];

            function renderTable(properties) {
                var container = document.getElementById('sp-table-container');
                var table = document.createElement('table');
                table.style.cssText = 'width:100%;border-collapse:collapse;font-size:11px;';

                var thead = document.createElement('thead');
                var tr = document.createElement('tr');
                columns.forEach(function(col) {
                    var th = document.createElement('th');
                    th.textContent = col.label + (spSortCol === col.key ? (spSortAsc ? ' \u25b2' : ' \u25bc') : '');
                    th.style.cssText = 'padding:6px 8px;text-align:right;border-bottom:2px solid #ddd;background:#fafafa;cursor:pointer;white-space:nowrap;font-size:10px;color:#555;position:sticky;top:0;';
                    if (col.key === 'property_id') th.style.textAlign = 'left';
                    th.onclick = (function(k) {
                        return function() {
                            if (spSortCol === k) spSortAsc = !spSortAsc;
                            else { spSortCol = k; spSortAsc = false; }
                            renderTable(properties);
                        };
                    })(col.key);
                    tr.appendChild(th);
                });
                thead.appendChild(tr);
                table.appendChild(thead);

                var sorted = properties.slice().sort(function(a, b) {
                    var va = a[spSortCol], vb = b[spSortCol];
                    if (typeof va === 'string') return spSortAsc ? va.localeCompare(vb) : vb.localeCompare(va);
                    return spSortAsc ? va - vb : vb - va;
                });

                var tbody = document.createElement('tbody');
                sorted.forEach(function(p) {
                    var row = document.createElement('tr');
                    if (p.negative_equity) {
                        row.style.background = '#ffebee';
                    } else if (p.post_damage_ltv > 90) {
                        row.style.background = '#fff3e0';
                    }
                    row.style.cursor = 'pointer';
                    row.onmouseenter = function() { this.style.opacity = '0.8'; };
                    row.onmouseleave = function() { this.style.opacity = '1'; };
                    row.onclick = (function(pid) {
                        return function() {
                            hidePanel();
                            if (window.PropertyStormAnalysis && window.PropertyStormAnalysis.show) {
                                window.PropertyStormAnalysis.show(pid);
                            } else {
                                document.dispatchEvent(new CustomEvent('propertyStormRequested', {
                                    detail: { propertyId: pid }, bubbles: true
                                }));
                            }
                        };
                    })(p.property_id);

                    columns.forEach(function(col) {
                        var td = document.createElement('td');
                        td.textContent = col.fmt(p[col.key]);
                        td.style.cssText = 'padding:5px 8px;border-bottom:1px solid #f0f0f0;text-align:right;white-space:nowrap;';
                        if (col.key === 'property_id') td.style.textAlign = 'left';
                        if (col.key === 'damage_amount') td.style.color = '#d32f2f';
                        if (col.key === 'prs_payout' && p.prs_payout > 0) td.style.color = '#2e7d32';
                        if (col.key === 'net_pnl') td.style.color = (p.net_pnl || 0) >= 0 ? '#2e7d32' : '#c62828';
                        if (col.key === 'post_damage_ltv' && p.post_damage_ltv > 100) {
                            td.style.color = '#d32f2f';
                            td.style.fontWeight = 'bold';
                        }
                        row.appendChild(td);
                    });
                    tbody.appendChild(row);
                });
                table.appendChild(tbody);

                container.innerHTML = '';
                container.appendChild(table);
            }

            // ================================================================
            // Data loading
            // ================================================================
            function loadStormList(sortMode) {
                var select = document.getElementById('sp-storm-select');
                select.innerHTML = '<option value="">Loading storms...</option>';
                var baseUrl = getBaseUrl();
                sortMode = sortMode || 'damage';

                // Use page-load preloaded cache only for default sort
                if (!sortMode || sortMode === 'damage') {
                    if (window._preStorms) {
                        var cached = window._preStorms;
                        window._preStorms = null;
                        _applyStormList(cached);
                        return;
                    }
                }

                console.log('[StormPortfolio] Fetching storm list, sort=' + sortMode);
                fetch(baseUrl + '/api/v1/propertyts/storms?sort=' + sortMode, {mode: 'cors'})
                    .then(function(r) { return r.json(); })
                    .then(function(data) { _applyStormList(data); })
                    .catch(function(err) {
                        select.innerHTML = '<option value="">Error loading storms</option>';
                        console.error('Storm list error:', err);
                    });
            }

            function _applyStormList(data) {
                var select = document.getElementById('sp-storm-select');
                if (!select) return;
                select.innerHTML = '';
                select.setAttribute('data-total', data.total_storms || (data.storms || []).length);
                if (data.status !== 'success' || !data.storms || data.storms.length === 0) {
                    console.log('[StormPortfolio] No flooding storms found');
                    select.innerHTML = '<option value="">No flooding storms found</option>';
                    return;
                }
                console.log('[StormPortfolio] Loaded', data.storms.length, 'storms');
                data.storms.forEach(function(s) {
                    var opt = document.createElement('option');
                    opt.value = s.storm_id;
                    opt.textContent = __STORM_OPT__;
                    select.appendChild(opt);
                });
                if (data.storms.length > 0) {
                    onStormChanged(data.storms[0].storm_id);
                }
            }

            function loadPortfolioImpact(stormId) {
                if (!stormId) return;
                console.log('[StormPortfolio] Loading impact for', stormId);
                var statsBar = document.getElementById('sp-stats-bar');
                statsBar.innerHTML = '<span>Loading portfolio impact...</span>';
                var summary = document.getElementById('sp-summary');
                summary.innerHTML = '<div style="padding:8px;color:#888;font-size:12px;">Loading...</div>';
                var tableContainer = document.getElementById('sp-table-container');
                tableContainer.innerHTML = '';

                var baseUrl = getBaseUrl();
                fetch(baseUrl + '/api/v1/propertyts/' + stormId + '/portfolio-impact', {mode: 'cors'})
                    .then(function(r) { return r.json(); })
                    .then(function(data) {
                        if (data.status !== 'success') {
                            spData = null;
                            spBasisData = null;
                            // Show empty state — storm exists but causes no property flooding
                            var emptyPortfolio = {
                                properties_affected: 0, total_properties: summary.dataset.totalProps || 0,
                                total_affected_value: 0, total_damage: 0, total_post_damage_value: 0,
                                total_affected_mortgages: 0, mortgages_in_negative_equity: 0, damage_pct: 0,
                                total_portfolio_value: 0, total_portfolio_mortgages: 0
                            };
                            var emptyDerivatives = {
                                total_prs_payout: 0, total_prs_notional: 0,
                                num_trades_triggered: 0, net_portfolio_pnl: 0
                            };
                            renderSummary(emptyPortfolio, emptyDerivatives);
                            tableContainer.innerHTML = '<div style="padding:40px;text-align:center;color:#999;font-size:13px;">This storm does not cause any property flooding</div>';
                            statsBar.innerHTML = '<span style="color:#888;">No properties affected by this storm</span>';
                            return;
                        }
                        spData = data;
                        spBasisData = null;  // invalidate basis cache on storm change
                        console.log('[StormPortfolio] Impact loaded:', data.portfolio.properties_affected, 'affected, damage', data.portfolio.total_damage);
                        var _spSelect = document.getElementById('sp-storm-select');
                        var _stormLabel = _spSelect
                            ? _spSelect.options[_spSelect.selectedIndex].textContent
                            : stormId;
                        document.getElementById('sp-panel-title').textContent =
                            'Portfolio Storm Impact \u2014 ' + _stormLabel;

                        // Switch to damage sub-tab on storm change
                        switchSubTab('damage');

                        renderSummary(data.portfolio, data.derivatives);
                        renderTable(data.properties);

                        var pf = data.portfolio;
                        statsBar.innerHTML =
                            '<span>Value loss: <b>' + pf.damage_pct.toFixed(1) + '%</b> of affected portfolio</span>' +
                            '<span>Portfolio value: <b>' + fmtGBP(pf.total_portfolio_value) + '</b></span>' +
                            '<span>Portfolio mortgages: <b>' + fmtGBP(pf.total_portfolio_mortgages) + '</b></span>' +
                            '<span>Impaired: <b>' + pf.mortgages_in_negative_equity + '</b> mortgages</span>';
                    })
                    .catch(function(err) {
                        statsBar.innerHTML = '<span style="color:red;">Failed to load portfolio impact</span>';
                        console.error('Portfolio impact error:', err);
                    });
            }
""".replace('__STORM_OPT__', _storm_opt('s'))
