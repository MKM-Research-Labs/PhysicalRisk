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

            // Hedges sub-tab: what the REIT's gauge hedges pay in this storm,
            // set against each asset's flood damage, and the market-maker's
            // side (paid to the REIT, received on its lay-off and other
            // gauge trades). A hedge pays when its gauge reaches severe.
            var spHedgeData = null;  // last /hedges response (has storm_id)

            // Fetch the hedge report for a storm; reuses the cached one.
            function fetchHedgeData(sid) {
                if (spHedgeData && spHedgeData.storm_id === sid) {
                    return Promise.resolve(spHedgeData);
                }
                return fetch(getBaseUrl() + '/api/v1/propertyts/' + sid + '/hedges', {mode:'cors'})
                    .then(function(r) { return r.json(); })
                    .then(function(d) {
                        if (d.status === 'success') spHedgeData = d;
                        return d;
                    });
            }

            // Commercial flood impact for the storm (shared with Summary).
            function _fetchCommercialImpact(sid) {
                if (spCommercialImpact && spCommercialImpact._storm_id === sid) {
                    return Promise.resolve(spCommercialImpact);
                }
                return fetch(getBaseUrl() + '/api/v1/commercial/' + sid + '/portfolio-impact', {mode:'cors'})
                    .then(function(r) { return r.json(); })
                    .then(function(d) {
                        if (d.status === 'success') { d._storm_id = sid; spCommercialImpact = d; }
                        return d;
                    })
                    .catch(function() { return null; });
            }

            function loadHedges() {
                var sid = (document.getElementById('sp-storm-select') || {}).value || '';
                var container = document.getElementById('sp-table-container');
                if (!sid) {
                    _renderHedgesEmpty('Select a storm to view hedge payouts.');
                    return;
                }
                container.innerHTML = '<div style="padding:var(--space-10);text-align:center;color:var(--muted-2);">Loading hedge payouts…</div>';
                Promise.all([fetchHedgeData(sid), _fetchCommercialImpact(sid)])
                    .then(function(res) {
                        var d = res[0];
                        if (spTableSubTab !== 'hedges') return;  // user moved on
                        if (!d || d.status !== 'success') {
                            _renderHedgesEmpty((d && d.message) || 'Hedge payouts unavailable.');
                            return;
                        }
                        _renderHedges(d);
                    })
                    .catch(function(err) {
                        console.error('Hedge payouts error:', err);
                        _renderHedgesEmpty('Failed to load hedge payouts.');
                    });
            }

            function _renderHedgesEmpty(msg) {
                document.getElementById('sp-summary').innerHTML = '';
                document.getElementById('sp-table-container').innerHTML =
                    '<div style="padding:48px 24px;text-align:center;color:var(--muted);font-size:var(--size-md);">' + _hEsc(msg) + '</div>';
            }

            function _hEsc(v) {
                return String(v == null ? '' : v).replace(/[&<>"]/g, function(c) {
                    return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];
                });
            }

            // Flood damage by asset id from the residential and commercial
            // impact responses already loaded for this storm.
            function _hedgeDamageByAsset() {
                var out = {};
                ((spData && spData.properties) || []).forEach(function(p) {
                    out[p.property_id] = p.damage_amount || 0;
                });
                ((spCommercialImpact && spCommercialImpact.assets) || []).forEach(function(a) {
                    out[a.property_id] = a.damage_amount || 0;
                });
                return out;
            }

            function _hMoney(v) {
                if (!v) return '—';
                var s = fmtGBP(Math.abs(v));
                return v < 0 ? '−' + s : s;
            }

            function _hSigned(v) {
                var colour = v > 0 ? 'var(--green-dark)' : (v < 0 ? 'var(--red-dark)' : 'var(--muted)');
                return '<span style="color:' + colour + ';font-weight:600;">' + (v ? (v > 0 ? '+' : '') + _hMoney(v) : '—') + '</span>';
            }

            function _hTable(cols, rows) {
                var th = 'padding:var(--space-3) var(--space-4);border-bottom:2px solid var(--line-strong);background:var(--raised);white-space:nowrap;font-size:var(--size-xxs);color:var(--text-2);position:sticky;top:0;';
                var html = '<table style="width:100%;border-collapse:collapse;font-size:var(--size-xs);"><thead><tr>';
                cols.forEach(function(c) { html += '<th style="' + th + 'text-align:' + c.align + ';">' + c.label + '</th>'; });
                html += '</tr></thead><tbody>';
                rows.forEach(function(r, i) {
                    var bg = r._hit ? 'var(--ok-bg)' : (i % 2 ? 'var(--sunken)' : 'transparent');
                    html += '<tr style="background:' + bg + ';">';
                    cols.forEach(function(c) {
                        html += '<td style="padding:var(--space-3) var(--space-4);border-bottom:1px solid var(--line-soft);text-align:' + c.align + ';white-space:nowrap;">' + c.cell(r) + '</td>';
                    });
                    html += '</tr>';
                });
                return html + '</tbody></table>';
            }

            function _hSection(title, note) {
                return '<div style="padding:var(--space-6) var(--space-8) var(--space-3);font-size:var(--size-xs);text-transform:uppercase;letter-spacing:0.5px;color:var(--muted);">' + title +
                    (note ? ' <span style="text-transform:none;letter-spacing:0;color:var(--muted-2);">— ' + note + '</span>' : '') + '</div>';
            }

            function _renderHedges(d) {
                var reit = d.reit || {}, desk = d.desk || {};
                var damage = _hedgeDamageByAsset();
                var hedges = (reit.hedges || []).map(function(h) {
                    var dmg = damage[h.asset_id] || 0;
                    return Object.assign({}, h, {damage: dmg, net: h.payout - dmg, _hit: h.triggered});
                });
                var hedgedDamage = hedges.reduce(function(a, h) { return a + h.damage; }, 0);
                var reitNet = (reit.total_payout || 0) - hedgedDamage;

                // Cards
                var cards = [
                    { label: 'Hedges Triggered', value: (reit.num_triggered || 0) + ' / ' + (reit.num_hedges || 0), color: 'var(--purple)' },
                    { label: 'REIT Payout', value: _hMoney(reit.total_payout || 0), color: 'var(--green-dark)' },
                    { label: 'Damage on Hedged Assets', value: _hMoney(hedgedDamage), color: 'var(--red)' },
                    { label: 'REIT Net (payout − damage)', value: _hSigned(reitNet), color: reitNet >= 0 ? 'var(--green-dark)' : 'var(--red-dark)' },
                    { label: 'Market-Maker Net', value: _hSigned(desk.net || 0), color: (desk.net || 0) >= 0 ? 'var(--green-dark)' : 'var(--red-dark)' },
                ];
                var summary = document.getElementById('sp-summary');
                summary.innerHTML = '';
                cards.forEach(function(card) {
                    var div = document.createElement('div');
                    div.style.cssText = 'flex:1;min-width:120px;padding:var(--space-4) var(--space-6);border-radius:var(--radius-md);background:var(--sunken);border-left:3px solid ' + card.color + ';';
                    div.innerHTML = '<div style="font-size:var(--size-xxs);color:var(--muted);text-transform:uppercase;letter-spacing:0.5px;">' + card.label + '</div>' +
                        '<div style="font-size:var(--size-lg);font-weight:700;color:' + card.color + ';margin-top:var(--space-1);">' + card.value + '</div>';
                    summary.appendChild(div);
                });

                var tick = function(r) { return r.triggered ? '<span style="color:var(--green-dark);font-weight:700;">✓ Severe</span>' : '<span style="color:var(--muted-2);">No</span>'; };
                var peak = function(r) { return r.gauge_peak_m == null ? '—' : r.gauge_peak_m.toFixed(2) + ' m'; };

                var html = _hSection('REIT hedges', 'bought from the market-maker; each pays its notional when its gauge reaches severe');
                html += hedges.length ? _hTable([
                    { label: 'Asset', align: 'left', cell: function(r) { return _hEsc(r.asset_id); } },
                    { label: 'Class', align: 'left', cell: function(r) { return r.asset_class === 'commercial' ? 'Commercial' : 'Residential'; } },
                    { label: 'Address', align: 'left', cell: function(r) { return _hEsc(r.address) || '—'; } },
                    { label: 'Trigger Gauge', align: 'left', cell: function(r) { return _hEsc(r.gauge_name || r.gauge_id); } },
                    { label: 'Gauge Peak', align: 'right', cell: peak },
                    { label: 'Triggered', align: 'left', cell: tick },
                    { label: 'Notional', align: 'right', cell: function(r) { return _hMoney(r.notional); } },
                    { label: 'Flood Damage', align: 'right', cell: function(r) { return _hMoney(r.damage); } },
                    { label: 'Payout', align: 'right', cell: function(r) { return _hSigned(r.payout); } },
                    { label: 'Net', align: 'right', cell: function(r) { return _hSigned(r.net); } },
                ], hedges) : '<div style="padding:var(--space-6) var(--space-8);color:var(--muted-2);">The REIT has no hedges in this book.</div>';

                var deskRows = (desk.trades || []).filter(function(t) { return t.role === 'layoff' || t.triggered; })
                    .map(function(t) { return Object.assign({}, t, {_hit: t.triggered && t.cash > 0}); });
                html += _hSection('Market-maker', 'pays the REIT, then recovers through its lay-off and other gauge trades');
                html += '<div style="display:flex;gap:var(--space-8);flex-wrap:wrap;padding:0 var(--space-8) var(--space-4);font-size:var(--size-xs);color:var(--text-2);">' +
                    '<span>Paid to REIT: <b>' + _hSigned(desk.paid_to_reit || 0) + '</b></span>' +
                    '<span>Lay-off trades: <b>' + _hSigned(desk.layoff_cash || 0) + '</b></span>' +
                    '<span>Other gauge trades: <b>' + _hSigned(desk.book_cash || 0) + '</b></span>' +
                    '<span>Net: <b>' + _hSigned(desk.net || 0) + '</b></span></div>';
                html += deskRows.length ? _hTable([
                    { label: 'Trade', align: 'left', cell: function(r) { return _hEsc(r.swap_id); } },
                    { label: 'Role', align: 'left', cell: function(r) { return r.role === 'layoff' ? 'Lay-off of REIT risk' : 'Gauge book'; } },
                    { label: 'Counterparty', align: 'left', cell: function(r) { return _hEsc(r.counterparty); } },
                    { label: 'Gauge', align: 'left', cell: function(r) { return _hEsc(r.gauge_name || r.gauge_id); } },
                    { label: 'Desk Side', align: 'left', cell: function(r) { return r.payer ? 'Bought protection' : 'Sold protection'; } },
                    { label: 'Gauge Peak', align: 'right', cell: peak },
                    { label: 'Triggered', align: 'left', cell: tick },
                    { label: 'Notional', align: 'right', cell: function(r) { return _hMoney(r.notional); } },
                    { label: 'Cash to Desk', align: 'right', cell: function(r) { return _hSigned(r.cash); } },
                ], deskRows) : '<div style="padding:var(--space-6) var(--space-8);color:var(--muted-2);">No market-maker trades triggered.</div>';

                var container = document.getElementById('sp-table-container');
                container.innerHTML = html;
            }
