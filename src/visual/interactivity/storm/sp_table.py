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
Storm portfolio — Table tab assembler.

Returns the JS body for the Table tab, composed from sibling sub-modules:

- sp_table_blotter:    Residential property blotter sub-tab
- sp_table_commercial: Commercial asset blotter sub-tab
- sp_table_trades:     REIT PRS trades sub-tab
- sp_table_basis:      Basis (synthetic-gauge transmission) sub-tab
- sp_table_damage:     Per-storm damage summary + sortable damage table

This file owns the cross-sub-tab state, DOM creation, sub-tab switching,
and storm-list / portfolio-impact loaders (which reads the
``window._preStorms`` startup cache).
"""


from config.format import storm_option_js as _storm_opt

from . import (
    sp_table_basis,
    sp_table_blotter,
    sp_table_commercial,
    sp_table_damage,
    sp_table_trades,
)


def get_js() -> str:
    """Return JS fragment for table tab (injected into parent IIFE)."""
    state_dom_loaders = """
            // ================================================================
            // Table tab — state
            // ================================================================
            var spData = null;
            var spSortCol = 'damage_amount';
            var spSortAsc = false;

            // ================================================================
            // Table tab — DOM creation
            // ================================================================
            var spTableSubTab = 'damage';  // 'portfolio', 'commercial', 'damage', 'trades', or 'basis'
            var spBlotterData = null;
            var spCommercialData = null;
            var spBasisData = null;
            var spTradesData = null;

            function createTableView() {
                var view = document.createElement('div');
                view.id = 'sp-table-view';
                view.style.cssText = 'display:flex;flex-direction:column;flex:1;overflow:hidden;';

                // Sub-tab toggle: Residential | Commercial | Damage | REIT Blotter | Basis
                var subTabBar = document.createElement('div');
                subTabBar.id = 'sp-sub-tab-bar';
                subTabBar.style.cssText = 'display:flex;gap:0;padding:8px 16px 0;';
                var inactiveStyle = 'padding:5px 16px;font-size:11px;border:1px solid #ddd;border-bottom:none;border-radius:4px 4px 0 0;cursor:pointer;background:white;color:#555;';
                var activeStyle = 'padding:5px 16px;font-size:11px;border:1px solid #1976d2;border-bottom:none;border-radius:4px 4px 0 0;cursor:pointer;background:#1976d2;color:white;';
                var subBtnPortfolio = document.createElement('button');
                subBtnPortfolio.id = 'sp-sub-portfolio';
                subBtnPortfolio.textContent = 'Residential';
                subBtnPortfolio.style.cssText = inactiveStyle;
                subBtnPortfolio.onclick = function() { switchSubTab('portfolio'); };
                var subBtnCommercial = document.createElement('button');
                subBtnCommercial.id = 'sp-sub-commercial';
                subBtnCommercial.textContent = 'Commercial';
                subBtnCommercial.style.cssText = inactiveStyle;
                subBtnCommercial.onclick = function() { switchSubTab('commercial'); };
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
                subTabBar.appendChild(subBtnCommercial);
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
                    document.getElementById('sp-sub-commercial'),
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
                } else if (sub === 'commercial') {
                    loadCommercialData();
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
                            // Render an empty-state table (keeps one <tr> in the DOM
                            // so downstream consumers and tests that expect a table
                            // structure still find rows, and gives the user a
                            // consistent layout rather than a bare message.)
                            tableContainer.innerHTML =
                                '<table style="width:100%;border-collapse:collapse;font-size:11px;">' +
                                  '<thead><tr style="background:#f5f5f5;border-bottom:1px solid #ddd;">' +
                                    '<th style="padding:6px 8px;text-align:left;">Property</th>' +
                                    '<th style="padding:6px 8px;text-align:right;">Damage</th>' +
                                  '</tr></thead>' +
                                  '<tbody><tr><td colspan="2" style="padding:40px;text-align:center;color:#999;font-size:13px;">' +
                                    'This storm does not cause any property flooding' +
                                  '</td></tr></tbody>' +
                                '</table>';
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
                            'Portfolio Storm Impact — ' + _stormLabel;

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
"""
    js = (
        state_dom_loaders
        + sp_table_blotter.get_js()
        + sp_table_commercial.get_js()
        + sp_table_trades.get_js()
        + sp_table_basis.get_js()
        + sp_table_damage.get_js()
    )
    return js.replace('__STORM_OPT__', _storm_opt('s'))
