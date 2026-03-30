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
            function createTableView() {
                var view = document.createElement('div');
                view.id = 'sp-table-view';
                view.style.cssText = 'display:flex;flex-direction:column;flex:1;overflow:hidden;';

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

            // ================================================================
            // Summary cards
            // ================================================================
            function renderSummary(portfolio) {
                var summary = document.getElementById('sp-summary');
                var cards = [
                    { label: 'Properties Affected', value: portfolio.properties_affected + ' / ' + portfolio.total_properties, color: '#1976d2' },
                    { label: 'Portfolio Value', value: fmtGBP(portfolio.total_affected_value), color: '#388e3c' },
                    { label: 'Total Damage', value: fmtGBP(portfolio.total_damage), color: '#d32f2f' },
                    { label: 'Post-Damage Value', value: fmtGBP(portfolio.total_post_damage_value), color: '#f57c00' },
                    { label: 'Mortgage Exposure', value: fmtGBP(portfolio.total_affected_mortgages), color: '#7b1fa2' },
                    { label: 'Negative Equity', value: portfolio.mortgages_in_negative_equity, color: portfolio.mortgages_in_negative_equity > 0 ? '#d32f2f' : '#388e3c' },
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

            // ================================================================
            // Sortable table
            // ================================================================
            var columns = [
                { key: 'property_id', label: 'Property', fmt: function(v) { return v; } },
                { key: 'property_value', label: 'Value', fmt: fmtGBP },
                { key: 'flood_depth_m', label: 'Depth', fmt: fmtDepth },
                { key: 'damage_ratio', label: 'Damage %', fmt: function(v) { return (v * 100).toFixed(1) + '%'; } },
                { key: 'damage_amount', label: 'Damage \u00a3', fmt: fmtGBP },
                { key: 'post_damage_value', label: 'Post Value', fmt: fmtGBP },
                { key: 'outstanding_balance', label: 'Mortgage', fmt: fmtGBP },
                { key: 'current_ltv', label: 'LTV', fmt: fmtPct },
                { key: 'post_damage_ltv', label: 'Post LTV', fmt: fmtPct },
                { key: 'remaining_term_months', label: 'Remaining', fmt: fmtMonths },
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
            function loadStormList() {
                var select = document.getElementById('sp-storm-select');
                select.innerHTML = '<option value="">Loading storms...</option>';
                var baseUrl = getBaseUrl();

                // Use page-load preloaded cache if available
                if (window._preStorms) {
                    var cached = window._preStorms;
                    window._preStorms = null;
                    _applyStormList(cached);
                    return;
                }

                console.log('[StormPortfolio] Fetching storm list');
                fetch(baseUrl + '/api/v1/propertyts/storms', {mode: 'cors'})
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
                            statsBar.innerHTML = '<span style="color:red;">Error: ' + (data.message || 'Unknown') + '</span>';
                            return;
                        }
                        spData = data;
                        console.log('[StormPortfolio] Impact loaded:', data.portfolio.properties_affected, 'affected, damage', data.portfolio.total_damage);
                        var _spSelect = document.getElementById('sp-storm-select');
                        var _stormLabel = _spSelect
                            ? _spSelect.options[_spSelect.selectedIndex].textContent
                            : stormId;
                        document.getElementById('sp-panel-title').textContent =
                            'Portfolio Storm Impact \u2014 ' + _stormLabel;

                        renderSummary(data.portfolio);
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
