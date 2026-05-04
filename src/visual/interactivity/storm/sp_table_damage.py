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
Storm portfolio Table tab — Damage sub-tab JS.

Summary cards (portfolio impact + derivative payouts) and the sortable
property damage table.
"""


def get_js() -> str:
    """Return JS fragment for the damage sub-tab (parent IIFE scope)."""
    return """
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
                { key: 'damage_amount', label: 'Damage £', fmt: fmtGBP },
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
                    th.textContent = col.label + (spSortCol === col.key ? (spSortAsc ? ' ▲' : ' ▼') : '');
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
"""
