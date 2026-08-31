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
                subTabBar.style.cssText = 'display:flex;gap:0;padding:var(--space-4) var(--space-8) 0;';
                var inactiveStyle = 'padding:var(--space-3) var(--space-8);font-size:var(--size-xs);border:1px solid var(--line-strong);border-bottom:none;border-radius:var(--radius-4) var(--radius-4) 0 0;cursor:pointer;background:var(--panel);color:var(--text-2);';
                var activeStyle = 'padding:var(--space-3) var(--space-8);font-size:var(--size-xs);border:1px solid var(--accent);border-bottom:none;border-radius:var(--radius-4) var(--radius-4) 0 0;cursor:pointer;background:var(--accent);color:var(--inverse);';

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
                summaryRow.style.cssText = 'padding:var(--space-5) var(--space-8);border-bottom:1px solid var(--line-soft);display:flex;gap:var(--space-5);flex-wrap:wrap;';

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
                    if (b) { b.style.background = Theme.value('panel'); b.style.color = Theme.value('text-2'); b.style.borderColor = Theme.value('line-strong'); }
                });
                var active = document.getElementById('sp-sub-' + sub);
                if (active) { active.style.background = Theme.value('accent'); active.style.color = Theme.value('panel'); active.style.borderColor = Theme.value('accent'); }

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

            // Full storm list cache used by the typhoon-only filter so the
            // checkbox can repopulate the dropdown without a re-fetch.
            var _spAllStorms = null;

            function _applyStormList(data) {
                var select = document.getElementById('sp-storm-select');
                if (!select) return;
                select.innerHTML = '';
                select.setAttribute('data-total', data.total_storms || (data.storms || []).length);
                if (data.status !== 'success' || !data.storms || data.storms.length === 0) {
                    console.log('[StormPortfolio] No flooding storms found');
                    select.innerHTML = '<option value="">No flooding storms found</option>';
                    _spAllStorms = [];
                    _updateTyphoonCount(0, 0);
                    return;
                }
                _spAllStorms = data.storms.slice();
                console.log('[StormPortfolio] Loaded', _spAllStorms.length, 'storms');
                _renderStormSelect();
            }

            function _renderStormSelect() {
                var select = document.getElementById('sp-storm-select');
                if (!select || !_spAllStorms) return;
                var chk = document.getElementById('sp-typhoon-only');
                var typhoonOnly = !!(chk && chk.checked);
                var list = typhoonOnly
                    ? _spAllStorms.filter(function(s){ return s.typhoon && s.typhoon.event_id; })
                    : _spAllStorms;
                select.innerHTML = '';
                if (list.length === 0) {
                    var opt = document.createElement('option');
                    opt.value = '';
                    opt.textContent = typhoonOnly
                        ? 'No typhoon-paired storms in current run'
                        : 'No storms';
                    select.appendChild(opt);
                } else {
                    list.forEach(function(s) {
                        var opt = document.createElement('option');
                        opt.value = s.storm_id;
                        opt.textContent = __STORM_OPT__;
                        select.appendChild(opt);
                    });
                    onStormChanged(list[0].storm_id);
                }
                var typhoonTotal = _spAllStorms.filter(function(s){ return s.typhoon && s.typhoon.event_id; }).length;
                _updateTyphoonCount(typhoonTotal, _spAllStorms.length);
            }

            function _updateTyphoonCount(typhoonCount, totalCount) {
                var el = document.getElementById('sp-typhoon-count');
                if (!el) return;
                el.textContent = '(' + typhoonCount + ' of ' + totalCount + ')';
            }

            // Hook called from the typhoon-only checkbox in the chrome row.
            function _applyTyphoonFilter() {
                _renderStormSelect();
            }
            window._applyTyphoonFilter = _applyTyphoonFilter;

            // Builds the bottom stats bar from whatever data has loaded so
            // far. Called twice when a storm changes — once after flood
            // portfolio-impact lands, again after wind-impact lands — so the
            // user sees flood-only totals first and combined totals once the
            // second fetch finishes.
            function _renderStatsBar() {
                var statsBar = document.getElementById('sp-stats-bar');
                if (!statsBar || !spData || !spData.portfolio) return;
                var pf = spData.portfolio;
                var floodDmg = (spData.properties || []).reduce(function(a,p){return a + (p.damage_amount||0);}, 0);
                var windDmg = (spWindData && spWindData.rows)
                    ? spWindData.rows.reduce(function(a,r){return a + (r.damage_amount||0);}, 0)
                    : 0;

                // Combined impaired count: assets where flood + wind damage
                // pushes outstanding above (value - combined damage). Built
                // from the flood + wind rows we already have; assets not
                // covered by either are treated as un-impacted (not
                // impaired).
                var combinedById = {};
                (spData.properties || []).forEach(function(p){
                    combinedById[p.property_id] = {
                        value: p.property_value || 0,
                        outstanding: p.outstanding_balance || 0,
                        flood: p.damage_amount || 0,
                        wind: 0,
                    };
                });
                if (spWindData && spWindData.rows) {
                    spWindData.rows.forEach(function(r){
                        var slot = combinedById[r.asset_id] || {value:r.value||0, outstanding:r.outstanding_balance||0, flood:0, wind:0};
                        slot.wind = r.damage_amount || 0;
                        if (!slot.value && r.value) slot.value = r.value;
                        if (!slot.outstanding && r.outstanding_balance) slot.outstanding = r.outstanding_balance;
                        combinedById[r.asset_id] = slot;
                    });
                }
                var combinedImpaired = 0;
                Object.keys(combinedById).forEach(function(id){
                    var s = combinedById[id];
                    if (!s.outstanding) return;
                    var dmg = Math.min(s.flood + s.wind, s.value);
                    var post = Math.max(s.value - dmg, 0);
                    var ltv = post > 0 ? (s.outstanding / post * 100) : 999;
                    if (ltv >= 100) combinedImpaired += 1;
                });

                var totalDmg = floodDmg + windDmg;
                var dmgPct = pf.total_portfolio_value > 0 ? (totalDmg / pf.total_portfolio_value * 100) : 0;
                var windLabel = (spWindData && spWindData.typhoon)
                    ? ' <span style="color:var(--orange-deep);">(\u26A1 ' + (spWindData.typhoon.event_id || '') + ')</span>'
                    : ' <span style="color:var(--muted);">(no typhoon)</span>';
                statsBar.innerHTML =
                    '<span>Combined loss: <b>' + dmgPct.toFixed(1) + '%</b> of portfolio</span>' +
                    '<span>Flood £: <b>' + fmtGBP(floodDmg) + '</b></span>' +
                    '<span>Wind £: <b>' + fmtGBP(windDmg) + '</b>' + windLabel + '</span>' +
                    '<span>Portfolio value: <b>' + fmtGBP(pf.total_portfolio_value) + '</b></span>' +
                    '<span>Portfolio loans: <b>' + fmtGBP(pf.total_portfolio_mortgages) + '</b></span>' +
                    '<span>Impaired (combined): <b>' + combinedImpaired + '</b></span>';
            }
            window._renderStatsBar = _renderStatsBar;

            function loadPortfolioImpact(stormId) {
                if (!stormId) return;
                console.log('[StormPortfolio] Loading impact for', stormId);
                var statsBar = document.getElementById('sp-stats-bar');
                statsBar.innerHTML = '<span>Loading portfolio impact...</span>';
                var summary = document.getElementById('sp-summary');
                summary.innerHTML = '<div style="padding:var(--space-4);color:var(--muted);font-size:var(--size-sm);">Loading...</div>';
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
                            statsBar.innerHTML = '<span style="color:var(--muted);">No properties affected by this storm</span>';
                            // Re-render whatever sub-tab the user is on so it
                            // shows the right empty state for the new storm.
                            switchSubTab(spTableSubTab || 'damage');
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

                        // Re-render whatever sub-tab the user is on so it
                        // refreshes for the new storm. Default to Flood Damage
                        // when no sub-tab is active yet.
                        switchSubTab(spTableSubTab || 'damage');

                        _renderStatsBar();

                        // Kick off a wind-impact fetch in parallel; the stats
                        // bar re-renders once it lands so the combined damage
                        // totals (flood + wind) replace the flood-only ones.
                        if (!spWindData || spWindData.storm_id !== stormId) {
                            fetch(baseUrl + '/api/v1/propertyts/' + stormId + '/wind-impact', {mode:'cors'})
                                .then(function(r){ return r.json(); })
                                .then(function(wd){
                                    if (wd.status === 'success') {
                                        spWindData = wd;
                                        _renderStatsBar();
                                    }
                                })
                                .catch(function(err) { console.error('Wind impact fetch error:', err); });
                        }
                    })
                    .catch(function(err) {
                        statsBar.innerHTML = '<span style="color:var(--red);">Failed to load portfolio impact</span>';
                        console.error('Portfolio impact error:', err);
                    });
            }
