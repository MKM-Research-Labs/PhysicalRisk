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
- sp_table_damage:     Flood Damage (combined residential + commercial) sub-tab
- sp_table_wind:       Wind Damage sub-tab (model pending)
- sp_table_mortgage:   Loan/Mortgage sub-tab (Flood + Wind LTV/Remaining)
- sp_table_summary:    Summary report card

This file owns the cross-sub-tab state, DOM creation, sub-tab switching,
and storm-list / portfolio-impact loaders (which reads the
``window._preStorms`` startup cache).
"""


from config.format import storm_option_js as _storm_opt

from . import (
    sp_table_blotter,
    sp_table_commercial,
    sp_table_damage,
    sp_table_mortgage,
    sp_table_summary,
    sp_table_wind,
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
            var spTableSubTab = 'damage';  // residential | commercial | damage (flood) | wind | mortgage | summary
            var spBlotterData = null;
            var spCommercialData = null;
            var spCommercialImpact = null;  // per-storm; invalidated on storm change
            var spTradesData = null;

            function createTableView() {
                var view = document.createElement('div');
                view.id = 'sp-table-view';
                view.style.cssText = 'display:flex;flex-direction:column;flex:1;overflow:hidden;';

                // Sub-tab toggle: Residential | Commercial | Flood Damage | Wind Damage | Loan/Mortgage | Summary
                var subTabBar = document.createElement('div');
                subTabBar.id = 'sp-sub-tab-bar';
                subTabBar.style.cssText = 'display:flex;gap:0;padding:8px 16px 0;';
                var inactiveStyle = 'padding:5px 16px;font-size:11px;border:1px solid #ddd;border-bottom:none;border-radius:4px 4px 0 0;cursor:pointer;background:white;color:#555;';
                var activeStyle = 'padding:5px 16px;font-size:11px;border:1px solid #1976d2;border-bottom:none;border-radius:4px 4px 0 0;cursor:pointer;background:#1976d2;color:white;';

                function mkBtn(id, label, key, active) {
                    var b = document.createElement('button');
                    b.id = 'sp-sub-' + id;
                    b.textContent = label;
                    b.style.cssText = active ? activeStyle : inactiveStyle;
                    b.onclick = function() { switchSubTab(key); };
                    subTabBar.appendChild(b);
                }
                mkBtn('portfolio',  'Residential',   'portfolio', false);
                mkBtn('commercial', 'Commercial',    'commercial', false);
                mkBtn('damage',     'Flood Damage',  'damage', true);
                mkBtn('wind',       'Wind Damage',   'wind', false);
                mkBtn('mortgage',   'Loan/Mortgage', 'mortgage', false);
                mkBtn('summary',    'Summary',       'summary', false);
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
                ['portfolio','commercial','damage','wind','mortgage','summary'].forEach(function(k) {
                    var b = document.getElementById('sp-sub-' + k);
                    if (b) { b.style.background = 'white'; b.style.color = '#555'; b.style.borderColor = '#ddd'; }
                });
                var active = document.getElementById('sp-sub-' + sub);
                if (active) { active.style.background = '#1976d2'; active.style.color = 'white'; active.style.borderColor = '#1976d2'; }

                // The Summary report card writes inline padding/overflow on the
                // table container — reset to the default so other tabs render
                // edge-to-edge as designed.
                var tableContainer = document.getElementById('sp-table-container');
                if (tableContainer) {
                    tableContainer.style.padding = '0';
                    tableContainer.style.overflowY = 'auto';
                }

                var ss = document.getElementById('sp-storm-select');
                var sid = ss ? ss.value : '';

                if (sub === 'portfolio') {
                    loadBlotterData();
                } else if (sub === 'commercial') {
                    loadCommercialData();
                } else if (sub === 'wind') {
                    loadWindDamage();
                } else if (sub === 'mortgage') {
                    loadMortgageData();
                } else if (sub === 'summary') {
                    loadSummary();
                } else {
                    // 'damage' — flood damage
                    loadFloodDamage(sid);
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
                        // Invalidate per-storm commercial cache regardless of
                        // residential outcome — Flood Damage refetches on demand.
                        spCommercialImpact = null;
                        if (data.status !== 'success') {
                            spData = null;
                            statsBar.innerHTML = '<span style="color:#888;">No properties affected by this storm</span>';
                            // Switch to flood damage so the user sees the empty
                            // combined state instead of stale residential.
                            switchSubTab('damage');
                            return;
                        }
                        spData = data;
                        console.log('[StormPortfolio] Impact loaded:', data.portfolio.properties_affected, 'affected, damage', data.portfolio.total_damage);
                        var _spSelect = document.getElementById('sp-storm-select');
                        var _stormLabel = _spSelect
                            ? _spSelect.options[_spSelect.selectedIndex].textContent
                            : stormId;
                        document.getElementById('sp-panel-title').textContent =
                            'Portfolio Storm Impact — ' + _stormLabel;

                        // Show the combined Flood Damage view by default.
                        switchSubTab('damage');

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
        + sp_table_damage.get_js()
        + sp_table_wind.get_js()
        + sp_table_mortgage.get_js()
        + sp_table_summary.get_js()
    )
    return js.replace('__STORM_OPT__', _storm_opt('s'))
